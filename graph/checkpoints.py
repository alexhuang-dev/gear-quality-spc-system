from __future__ import annotations

from typing import Any


def get_checkpointer(config: dict[str, Any]) -> Any:
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore
    except Exception:
        SqliteSaver = None  # type: ignore

    if SqliteSaver is not None:
        try:
            return SqliteSaver.from_conn_string(config["checkpoint_db_path"])
        except Exception:
            pass

    try:
        from langgraph.checkpoint.memory import InMemorySaver  # type: ignore
    except Exception:
        return None
    return InMemorySaver()
