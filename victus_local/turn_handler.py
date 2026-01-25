from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import json

from victus.app import VictusApp
from victus.core.schemas import Context, Plan, PlanStep, TurnEvent
from victus.core.llm_health import get_llm_circuit_breaker
from victus.memory.gate import MemoryGate
from victus.memory.models import MemoryRecord
from victus.memory.search import MemorySearch
from victus.memory.store import MemoryStore

from .app_aliases import build_clarify_message, resolve_candidate_choice
from .app_dictionary import load_app_dictionary
from .memory_store_v2 import VictusMemory, VictusMemoryStore


@dataclass
class SessionState:
    pending_tool: Optional[str] = None
    awaiting_slot: Optional[str] = None
    pending_slots: Dict[str, str] = field(default_factory=dict)
    pending_candidates: List[Dict[str, str]] = field(default_factory=list)
    pending_original: str = ""
    last_user_signature: Optional[str] = None

    def clear_pending(self) -> None:
        self.pending_tool = None
        self.awaiting_slot = None
        self.pending_slots = {}
        self.pending_candidates = []
        self.pending_original = ""


class TurnHandler:
    def __init__(
        self,
        app: VictusApp,
        store: MemoryStore | None = None,
        memory_store_v2: VictusMemoryStore | None = None,
    ) -> None:
        self.app = app
        self.store = store or MemoryStore()
        self.search = MemorySearch(self.store)
        self.gate = MemoryGate()
        self.memory_store_v2 = memory_store_v2 or VictusMemoryStore()
        self.sessions: Dict[str, SessionState] = {}

    async def run_turn(
        self,
        message: str,
        context: dict | None = None,
    ) -> AsyncIterator[TurnEvent]:
        session_state = self._get_session_state(context or {})
        signature = self._message_signature(message)
        if session_state.last_user_signature == signature:
            yield TurnEvent(event="status", status="done")
            return
        session_state.last_user_signature = signature

        if session_state.awaiting_slot == "app_name" and session_state.pending_tool == "local.open_app":
            resolved = self._resolve_pending_open_app(message, session_state)
            if resolved:
                requested_alias = resolved.get("requested_alias") or session_state.pending_original
                session_state.clear_pending()
                async for event in self._run_pending_open_app(message, resolved, requested_alias):
                    yield event
                return
            clarify_message = build_clarify_message(session_state.pending_candidates)
            yield TurnEvent(event="status", status="done")
            yield TurnEvent(event="clarify", message=clarify_message)
            return

        memory_hits = self.search.search(message, top_k=3)
        if memory_hits:
            yield TurnEvent(
                event="memory_used",
                result={
                    "count": len(memory_hits),
                    "ids": [record.id for record in memory_hits],
                    "items": [self._to_summary(record) for record in memory_hits],
                },
            )

        memory_prompt = self._format_v2_memory_prompt(message)
        streamed_text = ""
        async for event in self.app.run_request(message, memory_prompt=memory_prompt):
            if event.event == "token" and event.token:
                streamed_text += event.token
            if event.event == "tool_done" and event.action == "open_app":
                self._maybe_store_pending_action(event, session_state)
            if event.event == "clarify" and event.message:
                if event.message.strip().lower().startswith("which app should i open"):
                    self._set_pending_open_app(session_state, [], "")
            yield event

        candidate = self._extract_memory_candidate(streamed_text)
        if candidate:
            yield TurnEvent(event="memory_candidate", result={"memory_candidate": candidate})

        record = self._maybe_write_memory(message)
        if record:
            yield TurnEvent(
                event="memory_written",
                result=self._to_summary(record),
            )

    def _maybe_write_memory(self, message: str) -> MemoryRecord | None:
        candidate = self.gate.extract_candidate(message, source="user")
        if not candidate:
            return None
        record = self.gate.build_record(candidate)
        self.store.append(record)
        return record

    @staticmethod
    def _format_memory_prompt(records: List[MemoryRecord]) -> str:
        if not records:
            return ""
        lines = ["Relevant memory:"]
        for record in records:
            lines.append(f"- ({record.kind}) {record.text}")
        return "\n".join(lines)

    def _format_v2_memory_prompt(self, message: str) -> str:
        memories = self.memory_store_v2.search(message, limit=5)
        if not memories:
            return ""
        lines = ["Relevant memory:"]
        for memory in memories:
            lines.append(f"- ({memory.type}) {memory.content}")
        return "\n".join(lines)

    @staticmethod
    def _extract_memory_candidate(text: str) -> Dict[str, Any] | None:
        for payload in _extract_json_payloads(text):
            candidate = payload.get("memory_candidate")
            if not isinstance(candidate, dict):
                continue
            try:
                memory = VictusMemory(**candidate)
            except Exception:
                continue
            return memory.model_dump()
        return None

    @staticmethod
    def _merge_memory_prompts(v1_prompt: str, v2_prompt: str) -> str:
        prompts = [prompt for prompt in [v1_prompt, v2_prompt] if prompt.strip()]
        return "\n\n".join(prompts)

    def _format_v2_memory_prompt(self, message: str) -> str:
        memories = self.memory_store_v2.search(message, limit=5)
        if not memories:
            return ""
        lines = ["Relevant memory:"]
        for memory in memories:
            lines.append(f"- ({memory.type}) {memory.content}")
        return "\n".join(lines)

    @staticmethod
    def _extract_memory_candidate(text: str) -> Dict[str, Any] | None:
        for payload in _extract_json_payloads(text):
            candidate = payload.get("memory_candidate")
            if not isinstance(candidate, dict):
                continue
            try:
                memory = VictusMemory(**candidate)
            except Exception:
                continue
            return memory.model_dump()
        return None

    @staticmethod
    def _to_summary(record: MemoryRecord) -> dict:
        return {
            "id": record.id,
            "ts": record.ts,
            "scope": record.scope,
            "kind": record.kind,
            "text": record.text,
            "tags": record.tags,
            "source": record.source,
            "confidence": record.confidence,
            "pii_risk": record.pii_risk,
        }

    def _maybe_store_pending_action(self, event: TurnEvent, session_state: SessionState) -> None:
        result = event.result or {}
        if not isinstance(result, dict):
            return
        if result.get("decision") != "clarify":
            return
        candidates = result.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return
        self._set_pending_open_app(
            session_state,
            candidates,
            str(result.get("original") or ""),
        )

    def _set_pending_open_app(
        self,
        session_state: SessionState,
        candidates: List[Dict[str, str]],
        original: str,
    ) -> None:
        session_state.pending_tool = "local.open_app"
        session_state.awaiting_slot = "app_name"
        session_state.pending_slots = {"app_name": ""}
        session_state.pending_candidates = candidates
        session_state.pending_original = original

    @staticmethod
    def _resolve_pending_open_app(message: str, session_state: SessionState) -> Optional[Dict[str, str]]:
        normalized = message.strip()
        if not normalized:
            return None
        candidates = session_state.pending_candidates or []
        dictionary = load_app_dictionary()
        aliases = dictionary.alias_map()
        resolved = resolve_candidate_choice(message, candidates, aliases)
        if resolved:
            label = resolved.get("label") or resolved.get("target") or normalized
            target = resolved.get("target") or normalized
            requested_alias = label if normalized.isdigit() else normalized
            return {"target": target, "label": label, "requested_alias": requested_alias}
        return {"target": normalized, "label": normalized, "requested_alias": normalized}

    def _get_session_state(self, context: Dict[str, Any]) -> SessionState:
        session_key = context.get("session_key") or "default"
        state = self.sessions.get(session_key)
        if not state:
            state = SessionState()
            self.sessions[session_key] = state
        return state

    @staticmethod
    def _message_signature(message: str) -> str:
        normalized = message.strip().lower()
        bucket = int(time.time() / 2)
        return f"{normalized}:{bucket}"

    async def _run_pending_open_app(
        self,
        message: str,
        resolved: Dict[str, str],
        requested_alias: str,
    ) -> AsyncIterator[TurnEvent]:
        plan = Plan(
            goal=message,
            domain="productivity",
            steps=[
                PlanStep(
                    id="step-1",
                    tool="local",
                    action="open_app",
                    args={"name": resolved["target"], "requested_alias": requested_alias},
                )
            ],
            risk="low",
            origin="router",
        )
        context = self.app.context_factory() if self.app.context_factory else Context(
            session_id="victus-session",
            timestamp=datetime.utcnow(),
            mode="dev",
            foreground_app=None,
        )

        yield TurnEvent(event="status", status="thinking")
        confidence = self.app._evaluate_confidence(plan)
        if confidence.decision == "clarify":
            yield TurnEvent(event="status", status="done")
            yield TurnEvent(event="clarify", message=self.app.confidence_engine.build_clarification(confidence.primary))
            return
        if confidence.decision == "block":
            yield TurnEvent(event="status", status="denied")
            yield TurnEvent(event="error", message=self.app.confidence_engine.build_block_message(confidence.primary))
            return

        prepared_plan, approval = self.app.request_approval(plan, context)
        yield TurnEvent(event="status", status="executing")
        for step in prepared_plan.steps:
            yield TurnEvent(
                event="tool_start",
                tool=step.tool,
                action=step.action,
                args=step.args,
                step_id=step.id,
            )

        results = await asyncio.to_thread(self.app.execute_plan_streaming, prepared_plan, approval)
        error_messages = []
        assistant_messages = []
        for step in prepared_plan.steps:
            result = results.get(step.id)
            if isinstance(result, dict) and result.get("error"):
                error_messages.append(str(result["error"]))
            if isinstance(result, dict):
                assistant_message = result.get("assistant_message")
                if isinstance(assistant_message, str) and assistant_message.strip():
                    assistant_messages.append(assistant_message.strip())
            yield TurnEvent(
                event="tool_done",
                tool=step.tool,
                action=step.action,
                result=result,
                step_id=step.id,
            )

        if assistant_messages:
            combined = "\n".join(assistant_messages)
            yield TurnEvent(event="token", token=combined, step_id=prepared_plan.steps[0].id)

        if error_messages:
            yield TurnEvent(event="status", status="error")
            yield TurnEvent(event="error", message=error_messages[0])
        else:
            yield TurnEvent(event="status", status="done")

        self.app.audit.log_request(
            user_input=message,
            plan=prepared_plan,
            approval=approval,
            results=results,
            errors="; ".join(error_messages) if error_messages else None,
        )


def _extract_json_payloads(text: str) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    stack = 0
    start_index = None
    for index, char in enumerate(text):
        if char == "{":
            if stack == 0:
                start_index = index
            stack += 1
        elif char == "}":
            if stack == 0:
                continue
            stack -= 1
            if stack == 0 and start_index is not None:
                snippet = text[start_index : index + 1]
                try:
                    payloads.append(json.loads(snippet))
                except json.JSONDecodeError:
                    pass
                start_index = None
    return payloads
