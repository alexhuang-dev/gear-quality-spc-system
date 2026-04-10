import json
from pathlib import Path

import pytest

from core.config import load_runtime_config, load_specs
from core.harness import evaluate
from core.spc import calculate, parse_csv


GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.mark.parametrize("case_file", sorted(GOLDEN_DIR.glob("*.json")))
def test_golden_cases(case_file: Path):
    case = json.loads(case_file.read_text(encoding="utf-8"))
    csv_text = case["input"]["csv"]
    df = parse_csv(csv_text)
    result = calculate(
        df,
        load_specs(case["input"].get("specs")),
        load_runtime_config(case["input"].get("config")),
        csv_text=csv_text,
    )
    harness = evaluate(result, case.get("expected"))
    assert harness["passed"], f"{case_file.name}: {harness['failed_checks']}"
