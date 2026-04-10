from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.evaluate import evaluate_case
from harness.golden import load_golden_cases


def run_golden_regression(golden_dir: str | Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in load_golden_cases(golden_dir):
        harness = evaluate_case(
            case["input"]["csv"],
            specs=case["input"].get("specs"),
            config=case["input"].get("config"),
            expected=case.get("expected"),
        )
        results.append(
            {
                "case_file": case["_case_file"],
                "passed": harness["passed"],
                "score": harness["score"],
                "failed_checks": harness["failed_checks"],
            }
        )
    return results
