from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalPaths:
    base_dir: Path
    data_dir: Path
    logs_dir: Path
    vault_dir: Path
    file_sandbox_dir: Path


@dataclass(frozen=True)
class CameraConfig:
    enabled: bool
    backend: str
    device_index: int
    max_image_bytes: int
    max_dim: int


@dataclass(frozen=True)
class OrchestratorConfig:
    enable_llm_fallback: bool
    llm_enabled: bool
    llm_provider: str
    llm_allow_autoexec: bool
    llm_autoexec_min_confidence: float
    conf_execute: float
    conf_propose: float
    ollama_base_url: str
    model_priority: tuple[str, ...]
    enable_llm_formatting: bool


@dataclass(frozen=True)
class SecurityConfig:
    env: str
    max_memory_retrieval: int
    confidence_threshold: float
    log_redaction_enabled: bool
    enabled_tools: tuple[str, ...]


def _default_base_dir() -> Path:
    override = os.getenv("VICTUS_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "VictusAI"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "VictusAI"
    root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "victus_ai"


def get_local_paths() -> LocalPaths:
    base_dir = _default_base_dir()
    data_dir = base_dir / "data"
    logs_dir = base_dir / "logs"
    vault_dir = base_dir / "vault"
    file_sandbox_dir = Path(os.getenv("VICTUS_FILE_SANDBOX_DIR", data_dir / "sandbox_files")).expanduser()
    return LocalPaths(
        base_dir=base_dir,
        data_dir=data_dir,
        logs_dir=logs_dir,
        vault_dir=vault_dir,
        file_sandbox_dir=file_sandbox_dir,
    )


def ensure_directories() -> LocalPaths:
    paths = get_local_paths()
    for path in (
        paths.base_dir,
        paths.data_dir,
        paths.logs_dir,
        paths.vault_dir,
        paths.file_sandbox_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_camera_config() -> CameraConfig:
    enabled = _parse_bool(os.getenv("VICTUS_CAMERA_ENABLED"), False)
    backend = os.getenv("VICTUS_CAMERA_BACKEND", "stub").strip().lower()
    if backend not in {"stub", "opencv"}:
        backend = "stub"
    device_index = _parse_int(os.getenv("VICTUS_CAMERA_DEVICE_INDEX"), 0)
    max_image_bytes = _parse_int(os.getenv("VICTUS_CAMERA_MAX_IMAGE_BYTES"), 2_000_000)
    max_dim = _parse_int(os.getenv("VICTUS_CAMERA_MAX_DIM"), 1280)
    return CameraConfig(
        enabled=enabled,
        backend=backend,
        device_index=device_index,
        max_image_bytes=max_image_bytes,
        max_dim=max_dim,
    )


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_orchestrator_config() -> OrchestratorConfig:
    llm_enabled = _parse_bool(os.getenv("VICTUS_LLM_ENABLED"), False)
    # Legacy compatibility: fallback env still enables proposer path if set.
    legacy_fallback = _parse_bool(os.getenv("VICTUS_ENABLE_LLM_FALLBACK"), False)
    llm_provider = os.getenv("VICTUS_LLM_PROVIDER", "stub").strip().lower() or "stub"
    model_priority_raw = os.getenv("VICTUS_OLLAMA_MODEL_PRIORITY", "mistral,llama3.1:8b")
    model_priority = tuple(model.strip() for model in model_priority_raw.split(",") if model.strip())
    return OrchestratorConfig(
        enable_llm_fallback=(llm_enabled or legacy_fallback),
        llm_enabled=llm_enabled,
        llm_provider=llm_provider,
        llm_allow_autoexec=_parse_bool(os.getenv("VICTUS_LLM_ALLOW_AUTOEXEC"), False),
        llm_autoexec_min_confidence=_parse_float(os.getenv("VICTUS_LLM_AUTOEXEC_MIN_CONFIDENCE"), 0.90),
        conf_execute=_parse_float(
            os.getenv("VICTUS_LLM_CONF_EXECUTE", os.getenv("VICTUS_ORCHESTRATE_CONF_EXECUTE")),
            0.75,
        ),
        conf_propose=_parse_float(
            os.getenv("VICTUS_LLM_CONF_PROPOSE", os.getenv("VICTUS_ORCHESTRATE_CONF_PROPOSE")),
            0.45,
        ),
        ollama_base_url=(os.getenv("VICTUS_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip() or "http://127.0.0.1:11434"),
        model_priority=model_priority or ("mistral", "llama3.1:8b"),
        enable_llm_formatting=_parse_bool(os.getenv("VICTUS_ORCHESTRATE_ENABLE_LLM_FORMATTING"), False),
    )


def get_security_config() -> SecurityConfig:
    env = (os.getenv("VICTUS_ENV", "dev").strip().lower() or "dev")
    if env not in {"dev", "prod"}:
        env = "dev"

    max_memory_retrieval = _parse_int(os.getenv("VICTUS_MAX_MEMORY_RETRIEVAL"), 5)
    confidence_threshold = _parse_float(os.getenv("VICTUS_CONFIDENCE_THRESHOLD"), 0.45)
    log_redaction_enabled = _parse_bool(os.getenv("VICTUS_LOG_REDACTION_ENABLED"), True)
    enabled_tools_raw = os.getenv(
        "VICTUS_ENABLED_TOOLS",
        "camera.status,camera.capture,camera.recognize,memory.add,memory.search,memory.list,memory.delete,"
        "finance.add_transaction,finance.list_transactions,finance.summary,memory.create_note,mail.list_threads,mail.summarize_thread,files.list,files.read,files.write,files.create_workspace,files.generate_project_scaffold,chat.reply,noop",
    )
    enabled_tools = tuple(token.strip() for token in enabled_tools_raw.split(",") if token.strip())

    if env == "prod":
        max_memory_retrieval = min(max_memory_retrieval, 5)
        confidence_threshold = max(confidence_threshold, 0.8)
        log_redaction_enabled = True

    return SecurityConfig(
        env=env,
        max_memory_retrieval=max(1, max_memory_retrieval),
        confidence_threshold=max(0.0, min(1.0, confidence_threshold)),
        log_redaction_enabled=log_redaction_enabled,
        enabled_tools=enabled_tools,
    )
