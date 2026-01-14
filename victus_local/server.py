from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .task_runner import TaskError, run_task
from .victus_adapter import VictusAdapterError, chat as victus_chat


class LogHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._sse_queues: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        await self.emit("info", "ui_connected", {"clients": len(self._clients)})

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        await self.emit("info", "ui_disconnected", {"clients": len(self._clients)})

    async def connect_sse(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._sse_queues.add(queue)
        return queue

    async def disconnect_sse(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._sse_queues.discard(queue)

    async def emit(self, level: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            "level": level,
            "event": event,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        await self._broadcast(payload)

    async def _broadcast(self, payload: Dict[str, Any]) -> None:
        message = json.dumps(payload)
        async with self._lock:
            clients = list(self._clients)
            sse_queues = list(self._sse_queues)

        stale: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_text(message)
            except WebSocketDisconnect:
                stale.append(client)
            except Exception:
                stale.append(client)

        if stale:
            async with self._lock:
                for client in stale:
                    self._clients.discard(client)

        for queue in sse_queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                continue


app = FastAPI()
log_hub = LogHub()
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class TaskRequest(BaseModel):
    action: str
    args: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    ok: bool
    result: Dict[str, Any]


@app.on_event("startup")
async def startup_event() -> None:
    await log_hub.emit("info", "server_started", {"host": "127.0.0.1"})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest = Body(...)) -> ChatResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    await log_hub.emit("info", "llm_start", {"message": message})
    try:
        reply = await victus_chat(message)
    except VictusAdapterError as exc:
        await log_hub.emit("error", "llm_done", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        await log_hub.emit("error", "llm_done", {"error": str(exc)})
        raise HTTPException(status_code=500, detail="Victus failed to respond") from exc

    await log_hub.emit("info", "llm_done", {"reply": reply})
    return ChatResponse(reply=reply)


@app.post("/api/task", response_model=TaskResponse)
async def task_endpoint(payload: TaskRequest = Body(...)) -> TaskResponse:
    await log_hub.emit("info", "task_start", {"action": payload.action, "args": payload.args})
    try:
        result = await run_task(payload.action, payload.args)
    except TaskError as exc:
        await log_hub.emit("error", "task_done", {"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_hub.emit("error", "task_done", {"error": str(exc)})
        raise HTTPException(status_code=500, detail="Task execution failed") from exc

    await log_hub.emit("info", "task_done", {"action": payload.action, "result": result})
    return TaskResponse(ok=True, result=result)


@app.websocket("/ws/logs")
async def logs_websocket(websocket: WebSocket) -> None:
    await log_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await log_hub.disconnect(websocket)


@app.get("/api/logs/stream")
async def logs_stream() -> StreamingResponse:
    queue = await log_hub.connect_sse()

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n".encode("utf-8")
        finally:
            await log_hub.disconnect_sse(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
