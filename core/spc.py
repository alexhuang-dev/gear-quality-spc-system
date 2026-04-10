from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from io import StringIO
from typing import Any

import numpy as np
import pandas as pd

from core.config import (
    BATCH_COLS,
    DEFECT_COLS,
    DEFAULT_SPECS,
    PART_COLS,
    TIME_COLS,
    DefectRateMode,
    status_from_cpk,
)
from core.western_electric import evaluate as evaluate_western_electric


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    fenced = re.match(r"^```(?:csv)?\s*(.*?)\s*```$", text, flags=re.S | re.I)
    return fenced.group(1).strip() if fenced else text


def dataset_hash(csv_text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in csv_text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def parse_csv(csv_text: str) -> pd.DataFrame:
    cleaned = clean_text(csv_text)
    if not cleaned:
        raise ValueError("Empty CSV input.")
    df = pd.read_csv(StringIO(cleaned))
    df.columns = [str(col).strip() for col in df.columns]
    return df.dropna(how="all")


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    exact = {str(col).strip(): col for col in df.columns}
    lower = {str(col).strip().lower(): col for col in df.columns}
    for name in candidates:
        if name in exact:
            return exact[name]
        if name.lower() in lower:
            return lower[name.lower()]
    return None


def finite(value: Any, digits: int = 3) -> float | None:
    try:
        value = float(value)
    except Exception:
        return None
    return round(value, digits) if np.isfinite(value) else None


def safe_unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        if pd.isna(value):
            continue
        item = str(value)
        if item not in result:
            result.append(item)
    return result


def metric_stats(series: pd.Series, usl: float, lsl: float) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    count = int(numeric.count())
    mean = float(numeric.mean()) if count else None
    std = float(numeric.std(ddof=1)) if count >= 2 else None
    cp = None if std is None or not np.isfinite(std) or std <= 0 else finite((usl - lsl) / (6 * std))
    cpk = None if mean is None or std is None or not np.isfinite(std) or std <= 0 else finite(
        min((usl - mean) / (3 * std), (mean - lsl) / (3 * std))
    )
    ucl = finite(mean + 3 * std) if mean is not None and std is not None else None
    lcl = finite(mean - 3 * std) if mean is not None and std is not None else None
    return {
        "count": count,
        "mean": finite(mean),
        "std": finite(std),
        "UCL": ucl,
        "LCL": lcl,
        "control_UCL": ucl,
        "control_LCL": lcl,
        "spec_USL": float(usl),
        "spec_LSL": float(lsl),
        "Cp": cp,
        "Cpk": cpk,
        "status": status_from_cpk(cpk),
    }


def summarize_batches(df: pd.DataFrame, batch_col: str | None, specs: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    if not batch_col:
        return []
    rows: list[dict[str, Any]] = []
    for batch_no, group in df.groupby(batch_col, sort=False):
        metrics: dict[str, Any] = {}
        cpk_values: list[float] = []
        for metric, spec in specs.items():
            if metric not in group.columns:
                continue
            stats = metric_stats(group[metric], spec["USL"], spec["LSL"])
            metrics[metric] = {
                "mean": stats["mean"],
                "std": stats["std"],
                "Cpk": stats["Cpk"],
                "status": stats["status"],
            }
            if stats["Cpk"] is not None:
                cpk_values.append(stats["Cpk"])
        min_cpk = round(min(cpk_values), 3) if cpk_values else None
        rows.append(
            {
                "batch_no": str(batch_no),
                "total": int(len(group)),
                "overall_min_cpk": min_cpk,
                "overall_status": status_from_cpk(min_cpk),
                "metrics": metrics,
            }
        )
    return rows


def calculate(
    df: pd.DataFrame,
    specs: dict[str, dict[str, float]] | None = None,
    config: dict[str, Any] | None = None,
    csv_text: str | None = None,
) -> dict[str, Any]:
    specs = specs or DEFAULT_SPECS
    config = config or {}
    data_hash = dataset_hash(csv_text or df.to_csv(index=False))
    now_utc = dt.datetime.now(dt.UTC)
    run_id = now_utc.strftime("%Y%m%d%H%M%S") + "_" + data_hash[:8]

    batch_col = find_column(df, BATCH_COLS)
    defect_col = find_column(df, DEFECT_COLS)
    time_col = find_column(df, TIME_COLS)
    part_col = find_column(df, PART_COLS)
    if time_col:
        df = df.sort_values(time_col, kind="stable")

    batch_numbers = safe_unique(df[batch_col].tolist()) if batch_col else []
    total = int(len(df))

    defect_count_total = int(pd.to_numeric(df[defect_col], errors="coerce").fillna(0).sum()) if defect_col else 0
    defective_units = (
        int((pd.to_numeric(df[defect_col], errors="coerce").fillna(0) > 0).sum())
        if defect_col
        else 0
    )
    defect_rate_mode = str(config.get("defect_rate_mode") or DefectRateMode.BINARY.value)
    defect_rate = round(
        (defect_count_total / max(1, total)) if defect_rate_mode == DefectRateMode.PER_UNIT.value else (defective_units / max(1, total)),
        6,
    )

    metrics: dict[str, Any] = {}
    missing_metric_columns: list[str] = []
    western_electric_by_metric: dict[str, list[dict[str, Any]]] = {}
    series_by_metric: dict[str, list[float | None]] = {}
    for metric, spec in specs.items():
        if metric not in df.columns:
            missing_metric_columns.append(metric)
            continue
        raw = pd.to_numeric(df[metric], errors="coerce")
        stats = metric_stats(raw, spec["USL"], spec["LSL"])
        mask = raw.lt(spec["LSL"]) | raw.gt(spec["USL"])
        stats["violations"] = (
            safe_unique(df.loc[mask, batch_col].tolist())
            if batch_col
            else [str(index) for index in df.index[mask].tolist()]
        )
        series = [finite(value) for value in raw.tolist()]
        stats["western_electric_rule_violations"] = (
            evaluate_western_electric(series, stats.get("mean"), stats.get("std"))
            if config.get("western_electric_enabled", True)
            else []
        )
        metrics[metric] = stats
        western_electric_by_metric[metric] = stats["western_electric_rule_violations"]
        series_by_metric[metric] = series

    cpk_values = [metric["Cpk"] for metric in metrics.values() if metric["Cpk"] is not None]
    overall_min_cpk = round(min(cpk_values), 3) if cpk_values else None
    critical_metrics = [name for name, metric in metrics.items() if metric["status"] in ("警告", "异常")]
    for name, rules in western_electric_by_metric.items():
        if rules and name not in critical_metrics:
            critical_metrics.append(name)

    result = {
        "schema_version": "gear_spc_v9",
        "generated_at": now_utc.isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "dataset_hash": data_hash,
        "batch_no": batch_numbers[0] if len(batch_numbers) == 1 else None,
        "batch_numbers": batch_numbers,
        "total": total,
        "batches": len(batch_numbers),
        "defect_count_total": defect_count_total,
        "defective_units": defective_units,
        "defect_rate_mode": defect_rate_mode,
        "defect_rate": defect_rate,
        "defects_per_unit": round(defect_count_total / max(1, total), 6),
        "metrics": metrics,
        "per_batch_summary": summarize_batches(df, batch_col, specs),
        "overall_min_cpk": overall_min_cpk,
        "overall_status": status_from_cpk(overall_min_cpk),
        "critical_metrics": sorted(critical_metrics),
        "missing_metric_columns": missing_metric_columns,
        "batch_context": {
            "batch_column": batch_col,
            "time_column": time_col,
            "defect_column": defect_col,
            "part_column": part_col,
        },
        "western_electric": {
            "enabled": bool(config.get("western_electric_enabled", True)),
            "rules_applied": ["WE-1", "WE-2", "WE-3", "WE-4", "WE-5", "WE-6", "WE-7", "WE-8"],
            "violations_by_metric": western_electric_by_metric,
        },
        "config_used": {
            "history_limit": config.get("history_limit"),
            "western_electric_enabled": config.get("western_electric_enabled", True),
            "alert_cpk_threshold": config.get("alert_cpk_threshold"),
            "defect_rate_mode": defect_rate_mode,
        },
        "runtime_series": series_by_metric,
        "runtime_labels": safe_unique(df[part_col].tolist()) if part_col and part_col in df.columns else [str(index + 1) for index in range(total)],
    }
    return result
