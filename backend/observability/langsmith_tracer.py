"""LangSmith tracing integration with secret redaction and graceful offline fallback."""
from contextlib import asynccontextmanager
from datetime import datetime
import os
import re
import time
from typing import Any, AsyncGenerator, Dict, Optional
from backend.config import get_settings

settings = get_settings()

SECRET_KEYS_REGEX = re.compile(
    r"(?i)(api[_-]?key|secret|password|token|auth|bearer|credentials)"
)


def redact_sensitive_data(val: Any) -> Any:
    """Recursively scrub secrets and keys from tracing dictionaries."""
    if isinstance(val, dict):
        scrubbed = {}
        for k, v in val.items():
            if SECRET_KEYS_REGEX.search(str(k)):
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = redact_sensitive_data(v)
        return scrubbed
    elif isinstance(val, list):
        return [redact_sensitive_data(item) for item in val]
    elif isinstance(val, str):
        # Redact bearer tokens or sk- keys appearing in strings
        clean = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", val)
        clean = re.sub(r"sk-[A-Za-z0-9_\-\.]{15,}", "sk-[REDACTED]", clean)
        clean = re.sub(r"tvly-[A-Za-z0-9_\-\.]{15,}", "tvly-[REDACTED]", clean)
        return clean
    return val


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing is enabled via environment variables."""
    tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", str(settings.LANGCHAIN_TRACING_V2)).lower() in ("true", "1")
    has_api_key = bool(os.getenv("LANGCHAIN_API_KEY") or settings.LANGCHAIN_API_KEY)
    return tracing_v2 and has_api_key


_langsmith_client = None


def get_langsmith_client():
    """Return configured LangSmith Client if enabled, else None."""
    global _langsmith_client
    if not is_tracing_enabled():
        return None
    if _langsmith_client is None:
        try:
            from langsmith import Client
            _langsmith_client = Client(
                api_url=settings.LANGCHAIN_ENDPOINT,
                api_key=settings.LANGCHAIN_API_KEY or os.getenv("LANGCHAIN_API_KEY"),
            )
        except Exception:
            _langsmith_client = None
    return _langsmith_client


@asynccontextmanager
async def trace_span(
    node_name: str,
    task_id: str,
    inputs: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async context manager that wraps graph node operations in a LangSmith run
    if enabled, recording latency, redacted inputs/outputs, and error states.
    Always functions safely when tracing is disabled or unconfigured.
    """
    start_time = time.time()
    clean_inputs = redact_sensitive_data(inputs)
    span_meta = {
        "task_id": task_id,
        "node_name": node_name,
        "prompt_version": "v1.0.0",
        "model": settings.OPENAI_MODEL if not settings.DEMO_MODE else "mock-deterministic",
        "demo_mode": settings.DEMO_MODE,
        **(metadata or {}),
    }

    client = get_langsmith_client()
    run = None

    if client:
        try:
            project_name = settings.LANGCHAIN_PROJECT or "slurbuilds-research-agent"
            run = client.create_run(
                name=node_name,
                run_type="chain",
                inputs=clean_inputs,
                project_name=project_name,
                extra={"metadata": redact_sensitive_data(span_meta)},
            )
        except Exception:
            run = None

    run_output: Dict[str, Any] = {"outputs": None, "error": None}

    try:
        yield run_output
    except Exception as e:
        run_output["error"] = str(e)
        raise
    finally:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        if client and run:
            try:
                clean_outputs = redact_sensitive_data(run_output["outputs"] or {})
                client.update_run(
                    run.id,
                    outputs=clean_outputs,
                    error=run_output["error"],
                    end_time=datetime.utcnow(),
                    extra={"latency_ms": latency_ms},
                )
            except Exception:
                pass
