from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.alert import build_alert
from core.charts import write_control_charts, write_cpk_trend_chart
from core.harness import evaluate as evaluate_harness
from core.history import build_history_summary, store
from core.report import write_bundle
from core.spc import calculate, parse_csv
from harness.archive import archive_failure


def run_spc_core(state: dict[str, Any]) -> dict[str, Any]:
    df = parse_csv(state["csv_text"])
    spc_result = calculate(df, state["specs"], state["config"], csv_text=state["csv_text"])
    return {"spc_result": spc_result}


def attach_history(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    config = state["config"]
    history_summary = build_history_summary(
        config["history_db_path"],
        spc_result,
        limit=int(config.get("history_limit", 10)),
        query_batch_key=str(config.get("history_query_batch_key") or ""),
    )
    spc_result["history_summary"] = history_summary
    return {"spc_result": spc_result}


def attach_alert(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    spc_result["alert"] = build_alert(spc_result, state["config"])
    return {"spc_result": spc_result}


def write_artifacts_draft(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    config = state["config"]
    if not config.get("generate_artifacts", True):
        spc_result["artifacts"] = {
            "generated": False,
            "control_chart_svg_paths": {},
            "cpk_trend_svg_path": None,
            "json_report_path": None,
            "html_report_path": None,
            "pdf_report_path": None,
            "pdf_status": "not_generated_artifacts_disabled",
        }
        return {"spc_result": spc_result}
    runtime_series = spc_result.get("runtime_series") or {}
    recent = list(reversed((spc_result.get("history_summary") or {}).get("recent_runs") or []))
    trend_values = [row.get("overall_min_cpk") for row in recent] + [spc_result.get("overall_min_cpk")]
    trend_labels = [str(row.get("batch_key") or row.get("id")) for row in recent] + ["current"]

    control_chart_paths = write_control_charts(
        config["output_dir"],
        spc_result["run_id"],
        spc_result.get("metrics") or {},
        runtime_series,
    )
    cpk_trend_svg_path = write_cpk_trend_chart(
        config["output_dir"],
        spc_result["run_id"],
        trend_labels,
        trend_values,
    )
    bundle = write_bundle(
        spc_result,
        config["output_dir"],
        generate_pdf_file=bool(config.get("generate_pdf")),
    )
    spc_result["artifacts"] = {
        "generated": True,
        "control_chart_svg_paths": control_chart_paths,
        "cpk_trend_svg_path": cpk_trend_svg_path,
        **bundle,
    }
    return {"spc_result": spc_result}


def run_harness(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    spc_result["harness_eval"] = evaluate_harness(spc_result, state.get("expected"))
    archive_path = archive_failure(spc_result, spc_result["harness_eval"], state["config"])
    if archive_path:
        spc_result["harness_eval"]["failure_archive_path"] = archive_path
    return {"spc_result": spc_result}


def rewrite_artifacts_final(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    config = state["config"]
    if not config.get("generate_artifacts", True):
        spc_result["alert"] = build_alert(spc_result, config, report_url=None)
        return {"spc_result": spc_result}
    existing = deepcopy(spc_result.get("artifacts") or {})
    bundle = write_bundle(
        spc_result,
        config["output_dir"],
        generate_pdf_file=bool(config.get("generate_pdf")),
    )
    existing.update(bundle)
    spc_result["artifacts"] = existing
    spc_result["alert"] = build_alert(
        spc_result,
        config,
        report_url=existing.get("html_report_path"),
    )
    return {"spc_result": spc_result}


def persist_history(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    store(state["config"]["history_db_path"], spc_result)
    return {"spc_result": spc_result}


def build_response(state: dict[str, Any]) -> dict[str, Any]:
    spc_result = deepcopy(state["spc_result"])
    spc_result.pop("runtime_series", None)
    spc_result.pop("runtime_labels", None)
    response = {
        "spc_result": spc_result,
        "harness_eval": spc_result.get("harness_eval"),
        "history_comparison": (spc_result.get("history_summary") or {}).get("comparison"),
        "charts": {
            "control_chart_svg_paths": (spc_result.get("artifacts") or {}).get("control_chart_svg_paths"),
            "cpk_trend_svg_path": (spc_result.get("artifacts") or {}).get("cpk_trend_svg_path"),
        },
        "report_paths": {
            "json_report_path": (spc_result.get("artifacts") or {}).get("json_report_path"),
            "html_report_path": (spc_result.get("artifacts") or {}).get("html_report_path"),
            "pdf_report_path": (spc_result.get("artifacts") or {}).get("pdf_report_path"),
            "pdf_status": (spc_result.get("artifacts") or {}).get("pdf_status"),
        },
        "alert_payload": (spc_result.get("alert") or {}).get("payload"),
        "metadata": {
            "schema_version": spc_result.get("schema_version"),
            "run_id": spc_result.get("run_id"),
        },
    }
    return {"response": response}
