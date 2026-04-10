from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_golden_cases(golden_dir: str | Path) -> list[dict[str, Any]]:
    path = Path(golden_dir)
    cases: list[dict[str, Any]] = []
    for file in sorted(path.glob("*.json")):
        case = json.loads(file.read_text(encoding="utf-8"))
        case["_case_file"] = str(file)
        cases.append(case)
    return cases
