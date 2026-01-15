from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from victus.memory.store import MemoryStore
from victus.memory.search import MemorySearch

class MemoryResponse(BaseModel):
    items: list[dict]


def create_memory_router(store: MemoryStore) -> APIRouter:
    router = APIRouter()
    searcher = MemorySearch(store)

    @router.get("/api/memory/recent", response_model=MemoryResponse)
    async def memory_recent(limit: int = 10) -> MemoryResponse:
        records = searcher.recent(limit)
        return MemoryResponse(items=[record.to_dict() for record in records])

    @router.get("/api/memory/search", response_model=MemoryResponse)
    async def memory_search(query: str, limit: int = 5) -> MemoryResponse:
        records = searcher.search(query, top_k=limit)
        return MemoryResponse(items=[record.to_dict() for record in records])

    return router
