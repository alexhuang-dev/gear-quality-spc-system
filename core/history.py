from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


TABLE_NAME = "spc_runs_v9"


def init_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                run_id TEXT,
                dataset_hash TEXT,
                batch_key TEXT,
                batch_numbers_json TEXT,
                total INTEGER,
                defect_count_total INTEGER,
                defective_units INTEGER,
                defect_rate REAL,
                overall_min_cpk REAL,
                overall_status TEXT,
                critical_metrics_json TEXT,
                payload_json TEXT
            )"""
        )
        conn.commit()


def retrieve(db_path: str, n: int = 10, batch_key: str = "") -> list[dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if batch_key:
            rows = conn.execute(
                f"SELECT * FROM {TABLE_NAME} WHERE batch_key LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{batch_key}%", int(n)),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC LIMIT ?",
                (int(n),),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def count_runs(db_path: str) -> int:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0])


def compare(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    if not previous:
        return {
            "cpk_delta_vs_previous": None,
            "cpk_direction_vs_previous": None,
            "repeated_critical_metrics_vs_previous": [],
        }

    delta = None
    direction = None
    repeated = sorted(
        set(current.get("critical_metrics") or []).intersection(
            set(previous.get("critical_metrics") or [])
        )
    )
    current_cpk = current.get("overall_min_cpk")
    previous_cpk = previous.get("overall_min_cpk")
    if current_cpk is not None and previous_cpk is not None:
        delta = round(float(current_cpk) - float(previous_cpk), 3)
        direction = "up" if delta > 0 else ("down" if delta < 0 else "flat")

    return {
        "cpk_delta_vs_previous": delta,
        "cpk_direction_vs_previous": direction,
        "repeated_critical_metrics_vs_previous": repeated,
    }


def build_summary(current: dict[str, Any], recent_runs: list[dict[str, Any]]) -> dict[str, Any]:
    previous = recent_runs[0] if recent_runs else None
    return {
        "enabled": True,
        "has_history": bool(previous),
        "history_count_total": len(recent_runs),
        "recent_runs": recent_runs,
        "previous_run": previous,
        "comparison": compare(current, previous),
    }


def build_history_summary(db_path: str, current: dict[str, Any], limit: int = 10, query_batch_key: str = "") -> dict[str, Any]:
    total = count_runs(db_path)
    recent = retrieve(db_path, n=limit, batch_key=query_batch_key)
    summary = build_summary(current, recent)
    summary["history_count_total"] = total
    return summary


def store(db_path: str, spc_result: dict[str, Any]) -> None:
    init_db(db_path)
    payload = dict(spc_result)
    payload.pop("history_summary", None)
    payload.pop("runtime_series", None)
    payload.pop("runtime_labels", None)
    batch_numbers = spc_result.get("batch_numbers") or []
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"""INSERT INTO {TABLE_NAME}
            (run_id,dataset_hash,batch_key,batch_numbers_json,total,defect_count_total,defective_units,defect_rate,overall_min_cpk,overall_status,critical_metrics_json,payload_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                spc_result.get("run_id"),
                spc_result.get("dataset_hash"),
                ",".join(batch_numbers) or "NO_BATCH",
                json.dumps(batch_numbers, ensure_ascii=False),
                spc_result.get("total"),
                spc_result.get("defect_count_total"),
                spc_result.get("defective_units"),
                spc_result.get("defect_rate"),
                spc_result.get("overall_min_cpk"),
                spc_result.get("overall_status"),
                json.dumps(spc_result.get("critical_metrics") or [], ensure_ascii=False),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "run_id": row["run_id"],
        "dataset_hash": row["dataset_hash"],
        "batch_key": row["batch_key"],
        "batch_numbers": json.loads(row["batch_numbers_json"] or "[]"),
        "total": row["total"],
        "defect_count_total": row["defect_count_total"],
        "defective_units": row["defective_units"],
        "defect_rate": row["defect_rate"],
        "overall_min_cpk": row["overall_min_cpk"],
        "overall_status": row["overall_status"],
        "critical_metrics": json.loads(row["critical_metrics_json"] or "[]"),
    }
