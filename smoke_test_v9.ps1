$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

@'
import json
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

case = json.loads((Path("tests") / "golden" / "case_002_warning.json").read_text(encoding="utf-8"))
body = {
    "csv": case["input"]["csv"],
    "config": {
        "history_db_path": "data/history_live_smoke.db",
        "checkpoint_db_path": "data/checkpoints_live_smoke.db",
        "output_dir": "data/reports/live_smoke",
    },
}
response = requests.post("http://127.0.0.1:8000/analyze", json=body, timeout=120)
response.raise_for_status()
payload = response.json()
print(json.dumps({
    "schema": payload["spc_result"]["schema_version"],
    "status": payload["spc_result"]["overall_status"],
    "min_cpk": payload["spc_result"]["overall_min_cpk"],
    "harness": payload["harness_eval"]["passed"],
    "report": payload["report_paths"]["html_report_path"],
}, ensure_ascii=False, indent=2))
'@ | & $python -
