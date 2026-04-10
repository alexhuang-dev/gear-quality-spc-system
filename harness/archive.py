from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def archive_failure(spc_result: dict[str, Any], harness_eval: dict[str, Any], config: dict[str, Any]) -> str | None:
    if not config.get("archive_failed_harness_cases", True):
        return None
    if harness_eval.get("passed", False):
        return None
    outdir = Path(str(config.get("harness_failure_dir") or "data/harness_failures"))
    outdir.mkdir(parents=True, exist_ok=True)
    run_id = str(spc_result.get("run_id") or "unknown")
    path = outdir / f"failed_{run_id}.json"
    payload = {
        "spc_result": spc_result,
        "harness_eval": harness_eval,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
