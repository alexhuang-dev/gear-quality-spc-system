from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def begin_trace(name: str, metadata: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    trace = {
        "enabled": False,
        "provider": "none",
        "name": name,
        "started_at": datetime.now(UTC).isoformat(),
        "metadata": metadata,
    }
    if not config.get("langfuse_enabled"):
        return trace
    try:
        from langfuse import Langfuse  # type: ignore

        client = Langfuse(
            public_key=str(config.get("langfuse_public_key") or ""),
            secret_key=str(config.get("langfuse_secret_key") or ""),
            host=str(config.get("langfuse_host") or "https://cloud.langfuse.com"),
        )
        span = client.trace(name=name, metadata=metadata)
        trace.update(
            {
                "enabled": True,
                "provider": "langfuse",
                "_client": client,
                "_span": span,
            }
        )
    except Exception as exc:
        trace.update({"provider": "langfuse_error", "error": str(exc)})
    return trace


def finish_trace(trace: dict[str, Any], output: dict[str, Any] | None = None, error: str | None = None) -> dict[str, Any]:
    finished_at = datetime.now(UTC).isoformat()
    summary = {
        "enabled": bool(trace.get("enabled")),
        "provider": trace.get("provider"),
        "name": trace.get("name"),
        "started_at": trace.get("started_at"),
        "finished_at": finished_at,
    }
    if error:
        summary["error"] = error
    try:
        span = trace.get("_span")
        if span is not None:
            span.update(output=output, metadata={"error": error} if error else None)
    except Exception as exc:
        summary["finalize_error"] = str(exc)
    return summary
