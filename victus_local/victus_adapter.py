from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict

from victus.app import VictusApp
from victus.core.policy import PolicyError
from victus.core.schemas import Context, PlanStep, PrivacySettings
from victus.domains.productivity.allowlisted_plugins import (
    DocsPlugin,
    GmailPlugin,
    OpenAIPlugin,
    SpotifyPlugin,
)
from victus.domains.system.system_plugin import SystemPlugin
from victus.ui.renderers import render_system_result


class VictusAdapterError(RuntimeError):
    pass


def _build_victus_app() -> VictusApp:
    plugins = {
        "system": SystemPlugin(),
        "gmail": GmailPlugin(),
        "docs": DocsPlugin(),
        "spotify": SpotifyPlugin(),
        "openai": OpenAIPlugin(),
    }
    return VictusApp(plugins)


def _build_context() -> Context:
    return Context(
        session_id="victus-local-ui",
        timestamp=datetime.utcnow(),
        mode="dev",
        foreground_app=None,
        privacy=PrivacySettings(allow_send_to_openai=True),
    )


def _build_steps(user_text: str) -> list[PlanStep]:
    return [
        PlanStep(
            id="openai-1",
            tool="openai",
            action="generate_text",
            args={"prompt": user_text},
        )
    ]


def _format_results(results: Dict[str, object]) -> str:
    if not results:
        return "No response"
    first = next(iter(results.values()))
    if isinstance(first, dict):
        system_rendered = render_system_result(first)
        if system_rendered:
            return system_rendered
        for key in ("content", "summary"):
            if key in first:
                return str(first[key])
        return str(first)
    return str(first)


async def chat(message: str) -> str:
    victus = _build_victus_app()
    steps = _build_steps(message)
    context = _build_context()

    try:
        results = await asyncio.to_thread(
            victus.run_request,
            user_input=message,
            context=context,
            domain="productivity",
            steps=steps,
        )
    except PolicyError as exc:
        raise VictusAdapterError(f"Denied: {exc}") from exc
    except Exception as exc:
        raise VictusAdapterError(f"Victus error: {exc}") from exc

    return _format_results(results)
