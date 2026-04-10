from __future__ import annotations

from typing import Any

from core.config import load_runtime_config, load_specs
from core.harness import evaluate as evaluate_harness
from core.spc import calculate, parse_csv


def evaluate_case(csv_text: str, specs: dict[str, Any] | None = None, config: dict[str, Any] | None = None, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    df = parse_csv(csv_text)
    result = calculate(df, load_specs(specs), load_runtime_config(config or {}), csv_text=csv_text)
    return evaluate_harness(result, expected)
