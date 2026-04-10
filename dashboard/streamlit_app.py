from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.config import load_runtime_config
from core.history import retrieve


def load_latest_report(reports_dir: Path) -> dict | None:
    files = sorted(reports_dir.glob("report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(page_title="Gear Quality Dashboard", layout="wide")
    config = load_runtime_config({})
    history_rows = retrieve(config["history_db_path"], n=50)
    reports_dir = Path(config["output_dir"])
    latest_report = load_latest_report(reports_dir)

    st.title("Gear Quality Dashboard")
    st.caption("Recent SPC quality runs, status trends, and report outputs.")
    st.sidebar.header("Runtime")
    st.sidebar.code(f"history_db: {config['history_db_path']}")
    st.sidebar.code(f"reports: {config['output_dir']}")

    latest = history_rows[0] if history_rows else {}
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Status", str(latest.get("overall_status") or "N/A"))
    col2.metric("Latest Min Cpk", str(latest.get("overall_min_cpk") or "N/A"))
    col3.metric("Recent Runs", len(history_rows))

    if history_rows:
        df = pd.DataFrame(history_rows)
        st.subheader("Recent History")
        st.dataframe(df[["created_at", "batch_key", "overall_status", "overall_min_cpk", "defect_rate"]], use_container_width=True)
        trend_df = df[["created_at", "overall_min_cpk"]].dropna().iloc[::-1]
        if not trend_df.empty:
            st.subheader("Overall Min Cpk Trend")
            st.line_chart(trend_df.set_index("created_at"))

    if latest_report:
        st.subheader("Latest Metrics Snapshot")
        st.caption(f"Run ID: {latest_report.get('run_id')}")
        metrics = latest_report.get("metrics") or {}
        metric_rows = []
        for name, metric in metrics.items():
            metric_rows.append(
                {
                    "metric": name,
                    "mean": metric.get("mean"),
                    "std": metric.get("std"),
                    "Cpk": metric.get("Cpk"),
                    "status": metric.get("status"),
                }
            )
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True)

        artifacts = latest_report.get("artifacts") or {}
        alert = latest_report.get("alert") or {}
        if alert:
            st.subheader("Latest Alert")
            st.json(alert)
        svg_path = artifacts.get("cpk_trend_svg_path")
        if svg_path and Path(svg_path).exists():
            st.subheader("Latest Trend SVG")
            st.markdown(Path(svg_path).read_text(encoding="utf-8"), unsafe_allow_html=True)
        html_report_path = artifacts.get("html_report_path")
        if html_report_path:
            st.subheader("Latest Report Path")
            st.code(str(html_report_path))


if __name__ == "__main__":
    main()
