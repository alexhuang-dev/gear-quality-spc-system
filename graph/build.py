from __future__ import annotations

import hashlib
from typing import Any

from core.config import load_runtime_config, load_specs
from core.observability import begin_trace, finish_trace
from graph.checkpoints import get_checkpointer
from graph.nodes import (
    attach_alert,
    attach_history,
    build_response,
    persist_history,
    rewrite_artifacts_final,
    run_harness,
    run_spc_core,
    write_artifacts_draft,
)
from graph.state import GearQualityState


class SequentialGraphApp:
    def invoke(self, state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        current = dict(state)
        for node in (
            run_spc_core,
            attach_history,
            attach_alert,
            write_artifacts_draft,
            rewrite_artifacts_final,
            run_harness,
            persist_history,
            build_response,
        ):
            current.update(node(current))
        return current


def build_app(config: dict[str, Any] | None = None) -> Any:
    try:
        from langgraph.graph import END, START, StateGraph  # type: ignore
    except Exception:
        return SequentialGraphApp()

    graph = StateGraph(GearQualityState)
    graph.add_node("run_spc_core", run_spc_core)
    graph.add_node("attach_history", attach_history)
    graph.add_node("attach_alert", attach_alert)
    graph.add_node("write_artifacts_draft", write_artifacts_draft)
    graph.add_node("rewrite_artifacts_final", rewrite_artifacts_final)
    graph.add_node("run_harness", run_harness)
    graph.add_node("persist_history", persist_history)
    graph.add_node("build_response", build_response)

    graph.add_edge(START, "run_spc_core")
    graph.add_edge("run_spc_core", "attach_history")
    graph.add_edge("attach_history", "attach_alert")
    graph.add_edge("attach_alert", "write_artifacts_draft")
    graph.add_edge("write_artifacts_draft", "rewrite_artifacts_final")
    graph.add_edge("rewrite_artifacts_final", "run_harness")
    graph.add_edge("run_harness", "persist_history")
    graph.add_edge("persist_history", "build_response")
    graph.add_edge("build_response", END)

    runtime_config = load_runtime_config(config or {})
    checkpointer = get_checkpointer(runtime_config)
    return graph.compile(checkpointer=checkpointer)


def invoke_analysis(
    csv_text: str,
    specs: dict[str, dict[str, float]] | None = None,
    config: dict[str, Any] | None = None,
    expected: dict[str, Any] | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    runtime_config = load_runtime_config(config or {})
    trace = begin_trace(
        "gear_quality_analyze",
        {
            "thread_id": thread_id,
            "csv_length": len(csv_text or ""),
            "history_limit": runtime_config.get("history_limit"),
        },
        runtime_config,
    )
    app = build_app(runtime_config)
    effective_thread_id = thread_id or f"analysis-{hashlib.sha256(csv_text.encode('utf-8')).hexdigest()[:12]}"
    state: dict[str, Any] = {
        "csv_text": csv_text,
        "specs": load_specs(specs),
        "config": runtime_config,
        "expected": expected,
        "thread_id": effective_thread_id,
    }
    invoke_config = {"configurable": {"thread_id": effective_thread_id}}
    try:
        result = app.invoke(state, config=invoke_config)
    except Exception as exc:
        finish_trace(trace, error=str(exc))
        raise
    response = result["response"]
    response.setdefault("metadata", {})
    response["metadata"]["observability"] = finish_trace(trace, output=response)
    return response
