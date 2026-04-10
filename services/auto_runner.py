from __future__ import annotations

import argparse
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any

from core.config import load_runtime_config
from graph import invoke_analysis


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("gear_quality.auto_runner")


def read_csv_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def process_file(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    csv_text = read_csv_text(path)
    result = invoke_analysis(csv_text=csv_text, config=config)
    processed_dir = Path(config["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_dir / path.name))
    logger.info(
        "Processed %s -> run_id=%s status=%s",
        path.name,
        result.get("metadata", {}).get("run_id"),
        result.get("spc_result", {}).get("overall_status"),
    )
    return result


def scan_once(config: dict[str, Any]) -> list[dict[str, Any]]:
    watch_dir = Path(config["watch_dir"])
    watch_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(watch_dir.glob("*.csv")):
        try:
            results.append({"file": str(path), "result": process_file(path, config)})
        except Exception as exc:
            failed_dir = Path(config["failed_inputs_dir"])
            failed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(failed_dir / path.name))
            logger.exception("Failed to process %s", path.name)
            results.append({"file": str(path), "error": str(exc)})
    return results


def watch_loop(config: dict[str, Any]) -> None:
    interval = int(config.get("scan_interval_seconds") or 30)
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore

        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(lambda: scan_once(config), "interval", seconds=interval, max_instances=1, coalesce=True)
        scheduler.start()
        return
    except Exception:
        while True:
            scan_once(config)
            time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatic runner for incoming gear SPC CSV files.")
    parser.add_argument("--once", action="store_true", help="Process current incoming CSV files once and exit.")
    parser.add_argument("--watch", action="store_true", help="Continuously scan the incoming directory.")
    parser.add_argument(
        "--config-json",
        default="",
        help="Optional runtime config JSON string or JSON file path.",
    )
    args = parser.parse_args()

    config_input: Any = {}
    if args.config_json:
        raw = args.config_json.strip()
        config_path = Path(raw)
        if config_path.exists():
            config_input = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            config_input = json.loads(raw)

    config = load_runtime_config(config_input)
    if args.once:
        print(scan_once(config))
        return
    watch_loop(config)


if __name__ == "__main__":
    main()
