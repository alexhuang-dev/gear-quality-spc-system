from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import status_from_cpk


def _range_match(value: float | None, expected_range: list[float] | tuple[float, float] | None) -> bool:
    if expected_range is None or value is None:
        return True
    if len(expected_range) != 2:
        return False
    lower, upper = float(expected_range[0]), float(expected_range[1])
    return lower <= float(value) <= upper


def evaluate(spc_result: dict[str, Any], expected: dict[str, Any] | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: dict[str, Any] | None = None, severity: str = "error") -> None:
        checks.append(
            {
                "name": name,
                "passed": bool(passed),
                "severity": severity,
                "evidence": evidence or {},
            }
        )

    required = [
        "schema_version",
        "run_id",
        "dataset_hash",
        "total",
        "metrics",
        "overall_min_cpk",
        "overall_status",
        "critical_metrics",
        "western_electric",
    ]
    add(
        "required_fields_present",
        all(key in spc_result for key in required),
        {"missing": [key for key in required if key not in spc_result]},
    )

    cpk_values = [metric.get("Cpk") for metric in spc_result.get("metrics", {}).values() if metric.get("Cpk") is not None]
    expected_min = round(min(cpk_values), 3) if cpk_values else None
    add(
        "min_cpk_matches_metrics",
        spc_result.get("overall_min_cpk") == expected_min,
        {"expected": expected_min, "actual": spc_result.get("overall_min_cpk")},
    )
    add(
        "status_matches_min_cpk",
        spc_result.get("overall_status") == status_from_cpk(spc_result.get("overall_min_cpk")),
        {"expected": status_from_cpk(spc_result.get("overall_min_cpk")), "actual": spc_result.get("overall_status")},
    )

    expected_critical = sorted(
        [
            name
            for name, metric in spc_result.get("metrics", {}).items()
            if metric.get("status") in ("警告", "异常") or metric.get("western_electric_rule_violations")
        ]
    )
    add(
        "critical_metrics_match_status_and_rules",
        sorted(spc_result.get("critical_metrics") or []) == expected_critical,
        {"expected": expected_critical, "actual": sorted(spc_result.get("critical_metrics") or [])},
    )

    history = spc_result.get("history_summary") or {}
    previous = history.get("previous_run")
    comparison = history.get("comparison") or {}
    if previous and spc_result.get("overall_min_cpk") is not None and previous.get("overall_min_cpk") is not None:
        expected_delta = round(float(spc_result["overall_min_cpk"]) - float(previous["overall_min_cpk"]), 3)
        add(
            "history_delta_matches_previous",
            comparison.get("cpk_delta_vs_previous") == expected_delta,
            {"expected": expected_delta, "actual": comparison.get("cpk_delta_vs_previous")},
        )
    else:
        if not previous:
            evidence = {"skipped": "no previous run"}
        elif spc_result.get("overall_min_cpk") is None:
            evidence = {"skipped": "current run has no valid overall_min_cpk"}
        elif previous.get("overall_min_cpk") is None:
            evidence = {
                "skipped": "previous run has no valid overall_min_cpk",
                "previous_run": {
                    "run_id": previous.get("run_id"),
                    "batch_key": previous.get("batch_key"),
                    "overall_status": previous.get("overall_status"),
                    "overall_min_cpk": previous.get("overall_min_cpk"),
                },
            }
        else:
            evidence = {"skipped": "delta comparison unavailable"}
        add("history_delta_matches_previous", True, evidence, severity="info")

    artifacts = spc_result.get("artifacts") or {}
    if artifacts:
        artifact_paths = [
            artifacts.get("json_report_path"),
            artifacts.get("html_report_path"),
            artifacts.get("cpk_trend_svg_path"),
        ] + list((artifacts.get("control_chart_svg_paths") or {}).values())
        add(
            "artifact_paths_exist",
            all((not path) or Path(path).exists() for path in artifact_paths),
            {"missing": [path for path in artifact_paths if path and not Path(path).exists()]},
        )
    else:
        add("artifact_paths_exist", True, {"skipped": "no artifacts yet"}, severity="info")

    alert = spc_result.get("alert") or {}
    if alert:
        payload = alert.get("payload") or {}
        add(
            "alert_payload_matches_summary",
            payload.get("min_cpk", payload.get("overall_min_cpk")) in (spc_result.get("overall_min_cpk"), None)
            and payload.get("overall_status") == spc_result.get("overall_status"),
            {"alert": payload},
        )
    else:
        add("alert_payload_matches_summary", True, {"skipped": "no alert yet"}, severity="info")

    if expected:
        if "overall_status" in expected:
            add(
                "expected_overall_status",
                spc_result.get("overall_status") == expected["overall_status"],
                {"expected": expected["overall_status"], "actual": spc_result.get("overall_status")},
            )
        if "critical_metrics" in expected:
            add(
                "expected_critical_metrics",
                sorted(spc_result.get("critical_metrics") or []) == sorted(expected["critical_metrics"] or []),
                {"expected": expected["critical_metrics"], "actual": spc_result.get("critical_metrics")},
            )
        if "overall_min_cpk_range" in expected:
            add(
                "expected_overall_min_cpk_range",
                _range_match(spc_result.get("overall_min_cpk"), expected["overall_min_cpk_range"]),
                {"expected": expected["overall_min_cpk_range"], "actual": spc_result.get("overall_min_cpk")},
            )

    failed = [check for check in checks if not check["passed"] and check["severity"] != "info"]
    return {
        "passed": not failed,
        "checks": checks,
        "failed_checks": failed,
        "score": round((len(checks) - len(failed)) / max(1, len(checks)), 3),
    }
