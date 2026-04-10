from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
SPECS_DIR = DATA_DIR / "specs"
HARNESS_FAILURES_DIR = DATA_DIR / "harness_failures"
INCOMING_DIR = DATA_DIR / "incoming"
PROCESSED_DIR = DATA_DIR / "processed"
FAILED_INPUTS_DIR = DATA_DIR / "failed_inputs"
DEFAULT_SPECS_PATH = SPECS_DIR / "default.json"
DEFAULT_HISTORY_DB = DATA_DIR / "history.db"
DEFAULT_CHECKPOINT_DB = DATA_DIR / "langgraph_checkpoints.sqlite"


class DefectRateMode(str, Enum):
    PER_UNIT = "per_unit"
    BINARY = "binary"


DEFAULT_SPECS: dict[str, dict[str, float]] = {
    "齿距累计偏差(μm)": {"USL": 20.0, "LSL": 0.0},
    "齿圈径向跳动(μm)": {"USL": 25.0, "LSL": 0.0},
    "公法线长度变动(μm)": {"USL": 15.0, "LSL": 0.0},
    "齿形误差(μm)": {"USL": 10.0, "LSL": 0.0},
    "齿向误差(μm)": {"USL": 12.0, "LSL": 0.0},
}

DEFAULT_CONFIG: dict[str, Any] = {
    "history_db_path": str(DEFAULT_HISTORY_DB),
    "checkpoint_db_path": str(DEFAULT_CHECKPOINT_DB),
    "output_dir": str(REPORTS_DIR),
    "history_limit": 10,
    "generate_artifacts": True,
    "generate_pdf": False,
    "western_electric_enabled": True,
    "alert_cpk_threshold": 1.0,
    "alert_webhook_url": "",
    "alert_webhook_type": "generic",
    "send_alerts": False,
    "langfuse_enabled": False,
    "langfuse_public_key": "",
    "langfuse_secret_key": "",
    "langfuse_host": "https://cloud.langfuse.com",
    "history_query_batch_key": "",
    "defect_rate_mode": DefectRateMode.BINARY.value,
    "archive_failed_harness_cases": True,
    "harness_failure_dir": str(HARNESS_FAILURES_DIR),
    "watch_dir": str(INCOMING_DIR),
    "processed_dir": str(PROCESSED_DIR),
    "failed_inputs_dir": str(FAILED_INPUTS_DIR),
    "scan_interval_seconds": 30,
}

PUBLIC_RUNTIME_CONFIG_KEYS = [
    "history_db_path",
    "checkpoint_db_path",
    "output_dir",
    "history_limit",
    "generate_artifacts",
    "generate_pdf",
    "western_electric_enabled",
    "alert_cpk_threshold",
    "alert_webhook_type",
    "send_alerts",
    "langfuse_enabled",
    "langfuse_host",
    "history_query_batch_key",
    "defect_rate_mode",
    "archive_failed_harness_cases",
    "harness_failure_dir",
    "watch_dir",
    "processed_dir",
    "failed_inputs_dir",
    "scan_interval_seconds",
]

ENV_KEY_MAP = {
    "history_db_path": "GEAR_HISTORY_DB_PATH",
    "checkpoint_db_path": "GEAR_CHECKPOINT_DB_PATH",
    "output_dir": "GEAR_OUTPUT_DIR",
    "history_limit": "GEAR_HISTORY_LIMIT",
    "generate_artifacts": "GEAR_GENERATE_ARTIFACTS",
    "generate_pdf": "GEAR_GENERATE_PDF",
    "western_electric_enabled": "GEAR_WESTERN_ELECTRIC_ENABLED",
    "alert_cpk_threshold": "GEAR_ALERT_CPK_THRESHOLD",
    "alert_webhook_url": "GEAR_ALERT_WEBHOOK_URL",
    "alert_webhook_type": "GEAR_ALERT_WEBHOOK_TYPE",
    "send_alerts": "GEAR_SEND_ALERTS",
    "langfuse_enabled": "GEAR_LANGFUSE_ENABLED",
    "langfuse_public_key": "GEAR_LANGFUSE_PUBLIC_KEY",
    "langfuse_secret_key": "GEAR_LANGFUSE_SECRET_KEY",
    "langfuse_host": "GEAR_LANGFUSE_HOST",
    "history_query_batch_key": "GEAR_HISTORY_QUERY_BATCH_KEY",
    "defect_rate_mode": "GEAR_DEFECT_RATE_MODE",
    "archive_failed_harness_cases": "GEAR_ARCHIVE_FAILED_HARNESS_CASES",
    "harness_failure_dir": "GEAR_HARNESS_FAILURE_DIR",
    "watch_dir": "GEAR_WATCH_DIR",
    "processed_dir": "GEAR_PROCESSED_DIR",
    "failed_inputs_dir": "GEAR_FAILED_INPUTS_DIR",
    "scan_interval_seconds": "GEAR_SCAN_INTERVAL_SECONDS",
}

BOOL_CONFIG_KEYS = {
    "generate_artifacts",
    "generate_pdf",
    "western_electric_enabled",
    "send_alerts",
    "langfuse_enabled",
    "archive_failed_harness_cases",
}
INT_CONFIG_KEYS = {"history_limit", "scan_interval_seconds"}
FLOAT_CONFIG_KEYS = {"alert_cpk_threshold"}
PATH_CONFIG_KEYS = {
    "history_db_path",
    "checkpoint_db_path",
    "output_dir",
    "harness_failure_dir",
    "watch_dir",
    "processed_dir",
    "failed_inputs_dir",
}

BATCH_COLS = ["批次号", "批次", "batch_no", "batch", "Batch", "lot_no", "Lot"]
DEFECT_COLS = ["缺陷数量", "defect_count", "defects", "不良数量"]
TIME_COLS = ["检测时间", "time", "timestamp", "datetime", "date"]
PART_COLS = ["件号", "part_no", "part_id", "serial_no"]
OPERATOR_COLS = ["检测人员", "操作员", "operator"]
EQUIPMENT_COLS = ["设备编号", "机台", "equipment_id", "machine_id"]

STATUS_EXCELLENT = "优秀"
STATUS_PASS = "合格"
STATUS_WARN = "警告"
STATUS_ABNORMAL = "异常"
STATUS_UNKNOWN = "无法评估"


def ensure_default_paths() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    HARNESS_FAILURES_DIR.mkdir(parents=True, exist_ok=True)
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_SPECS_PATH.exists():
        DEFAULT_SPECS_PATH.write_text(
            json.dumps(DEFAULT_SPECS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _loads(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    path = Path(str(value))
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    try:
        parsed = json.loads(str(value))
    except Exception:
        return default
    return parsed if parsed is not None else default


def _parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    merged = dict(config)
    for key, env_name in ENV_KEY_MAP.items():
        raw = os.getenv(env_name)
        if raw is None or raw == "":
            continue
        if key in BOOL_CONFIG_KEYS:
            merged[key] = _parse_bool(raw)
        elif key in INT_CONFIG_KEYS:
            merged[key] = int(raw)
        elif key in FLOAT_CONFIG_KEYS:
            merged[key] = float(raw)
        elif key in PATH_CONFIG_KEYS:
            merged[key] = str(Path(raw).expanduser())
        else:
            merged[key] = raw
    return merged


def public_runtime_config(config_input: Any = None) -> dict[str, Any]:
    config = load_runtime_config(config_input)
    return {key: config.get(key) for key in PUBLIC_RUNTIME_CONFIG_KEYS}


def load_specs(specs_input: Any = None) -> dict[str, dict[str, float]]:
    ensure_default_paths()
    parsed = _loads(specs_input, None)
    if parsed is None:
        try:
            parsed = json.loads(DEFAULT_SPECS_PATH.read_text(encoding="utf-8"))
        except Exception:
            parsed = DEFAULT_SPECS
    specs: dict[str, dict[str, float]] = {}
    if isinstance(parsed, dict):
        for metric, spec in parsed.items():
            try:
                specs[str(metric)] = {
                    "USL": float(spec["USL"]),
                    "LSL": float(spec["LSL"]),
                }
            except Exception:
                continue
    return specs or dict(DEFAULT_SPECS)


def load_runtime_config(config_input: Any = None) -> dict[str, Any]:
    ensure_default_paths()
    parsed = _loads(config_input, {})
    config = dict(DEFAULT_CONFIG)
    if isinstance(parsed, dict):
        config.update(parsed)
    config = _apply_env_overrides(config)
    config["history_limit"] = int(config.get("history_limit") or 10)
    config["alert_cpk_threshold"] = float(config.get("alert_cpk_threshold") or 1.0)
    config["scan_interval_seconds"] = int(config.get("scan_interval_seconds") or 30)
    mode = str(config.get("defect_rate_mode") or DefectRateMode.BINARY.value).lower()
    config["defect_rate_mode"] = (
        DefectRateMode.PER_UNIT.value if mode == DefectRateMode.PER_UNIT.value else DefectRateMode.BINARY.value
    )
    for key in PATH_CONFIG_KEYS:
        if config.get(key):
            config[key] = str(Path(str(config[key])).expanduser())
    return config


def status_from_cpk(cpk: float | None) -> str:
    if cpk is None:
        return STATUS_UNKNOWN
    if cpk >= 1.67:
        return STATUS_EXCELLENT
    if cpk >= 1.33:
        return STATUS_PASS
    if cpk >= 1.00:
        return STATUS_WARN
    return STATUS_ABNORMAL
