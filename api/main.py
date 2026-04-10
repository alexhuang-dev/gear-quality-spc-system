from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from core.alert import send as send_alert
from core.config import (
    DEFAULT_CONFIG,
    STATUS_UNKNOWN,
    ensure_default_paths,
    load_runtime_config,
    public_runtime_config,
)
from core.history import count_runs, init_db, retrieve
from graph import invoke_analysis
from harness.regression import run_golden_regression


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("gear_quality.api")


def _parse_optional_json(raw: str | None) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc.msg}") from exc


def _runtime_status() -> dict[str, Any]:
    config = load_runtime_config({})
    reports_dir = Path(config.get("output_dir") or DEFAULT_CONFIG["output_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    init_db(config["history_db_path"])
    return {
        "ready": True,
        "history_db_path": config["history_db_path"],
        "checkpoint_db_path": config["checkpoint_db_path"],
        "output_dir": str(reports_dir),
        "history_run_count": count_runs(config["history_db_path"]),
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_default_paths()
    status = _runtime_status()
    logger.info("API startup ready: %s", status)
    yield


app = FastAPI(title="Gear Quality System", version="v9-production", lifespan=lifespan)


class AnalyzeRequest(BaseModel):
    csv: str = Field(..., description="CSV payload as raw text")
    specs: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    expected: dict[str, Any] | None = None
    thread_id: str | None = None


class AlertTestRequest(BaseModel):
    webhook_url: str
    webhook_type: str = "generic"
    payload: dict[str, Any] | None = None


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started) * 1000, 2)
        logger.exception("%s %s -> 500 (%sms)", request.method, request.url.path, duration_ms)
        raise
    duration_ms = round((perf_counter() - started) * 1000, 2)
    logger.info(
        "%s %s -> %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    try:
        return _runtime_status()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Runtime not ready: {exc}") from exc


@app.get("/config/public")
def config_public() -> dict[str, Any]:
    return public_runtime_config({})


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    return invoke_analysis(
        csv_text=request.csv,
        specs=request.specs,
        config=request.config,
        expected=request.expected,
        thread_id=request.thread_id,
    )


@app.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    specs_json: str = Form(""),
    config_json: str = Form(""),
    expected_json: str = Form(""),
    thread_id: str = Form(""),
) -> dict[str, Any]:
    raw = await file.read()
    csv_text = None
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            csv_text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if csv_text is None:
        csv_text = raw.decode("utf-8", errors="ignore")

    return invoke_analysis(
        csv_text=csv_text,
        specs=_parse_optional_json(specs_json),
        config=_parse_optional_json(config_json),
        expected=_parse_optional_json(expected_json),
        thread_id=thread_id or None,
    )


@app.get("/history")
def history(n: int = 10, batch_key: str = "") -> list[dict[str, Any]]:
    config = load_runtime_config({})
    return retrieve(config["history_db_path"], n=n, batch_key=batch_key)


@app.get("/report/{run_id}", response_class=HTMLResponse)
def report(run_id: str) -> str:
    config = load_runtime_config({})
    reports_dir = Path(config.get("output_dir") or DEFAULT_CONFIG["output_dir"])
    candidates = sorted(reports_dir.glob(f"report_{run_id}*.html"))
    if not candidates:
        for file in reports_dir.glob("report_*.json"):
            payload = json.loads(file.read_text(encoding="utf-8"))
            if payload.get("run_id") == run_id:
                html_path = reports_dir / f"report_{file.stem.replace('report_', '')}.html"
                if html_path.exists():
                    candidates = [html_path]
                    break
    if not candidates:
        raise HTTPException(status_code=404, detail="Report not found")
    return candidates[0].read_text(encoding="utf-8")


@app.get("/dashboard/summary")
def dashboard_summary(n: int = 20) -> dict[str, Any]:
    config = load_runtime_config({})
    rows = retrieve(config["history_db_path"], n=n)
    status_counts: dict[str, int] = {}
    critical_count = 0
    for row in rows:
        status = str(row.get("overall_status") or STATUS_UNKNOWN)
        status_counts[status] = status_counts.get(status, 0) + 1
        critical_count += len(row.get("critical_metrics") or [])
    return {
        "recent_runs": rows,
        "status_counts": status_counts,
        "critical_metric_total": critical_count,
        "latest_run": rows[0] if rows else None,
    }


@app.post("/regression")
def regression() -> dict[str, Any]:
    results = run_golden_regression("tests/golden")
    passed = all(item["passed"] for item in results)
    return {
        "passed": passed,
        "total": len(results),
        "failed": [item for item in results if not item["passed"]],
        "results": results,
    }


@app.post("/alerts/test")
def alert_test(request: AlertTestRequest) -> dict[str, Any]:
    payload = request.payload or {
        "batch_no": "TEST",
        "batch_numbers": ["TEST"],
        "overall_status": "warning",
        "critical_metrics": ["shape_error"],
        "min_cpk": 1.05,
        "timestamp": "manual-test",
        "report_url": "http://127.0.0.1:8000",
    }
    alert = {
        "required": True,
        "level": "warning",
        "reasons": ["manual_test"],
        "payload": payload,
    }
    return {
        "push_status": send_alert(alert, request.webhook_url, request.webhook_type),
        "payload": alert,
    }
