from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from core.charts import safe_filename


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    return str(value)


def _read_svg(path: str | None) -> str:
    if not path:
        return ""
    svg_path = Path(path)
    if not svg_path.exists():
        return ""
    return svg_path.read_text(encoding="utf-8")


def _build_metrics_rows(metrics: dict[str, Any]) -> str:
    rows = []
    for metric_name, metric in metrics.items():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(metric_name))}</td>"
            f"<td>{html.escape(_format_value(metric.get('mean')))}</td>"
            f"<td>{html.escape(_format_value(metric.get('std')))}</td>"
            f"<td>{html.escape(_format_value(metric.get('Cp')))}</td>"
            f"<td>{html.escape(_format_value(metric.get('Cpk')))}</td>"
            f"<td>{html.escape(_format_value(metric.get('status')))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _build_history_rows(recent_runs: list[dict[str, Any]]) -> str:
    rows = []
    for row in recent_runs[:10]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(_format_value(row.get('created_at')))}</td>"
            f"<td>{html.escape(_format_value(row.get('batch_key')))}</td>"
            f"<td>{html.escape(_format_value(row.get('overall_status')))}</td>"
            f"<td>{html.escape(_format_value(row.get('overall_min_cpk')))}</td>"
            f"<td>{html.escape(_format_value(row.get('defect_rate')))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _plain_summary(spc_result: dict[str, Any], history_summary: dict[str, Any]) -> str:
    status = _format_value(spc_result.get("overall_status"))
    min_cpk = _format_value(spc_result.get("overall_min_cpk"))
    critical = spc_result.get("critical_metrics") or []
    critical_text = "、".join(str(item) for item in critical) if critical else "当前没有明显的重点风险指标"
    previous = (history_summary or {}).get("previous_run") or {}
    comparison = (history_summary or {}).get("comparison") or {}
    delta = comparison.get("cpk_delta_vs_previous")

    parts = [
        f"这次批次的综合状态是“{status}”，最小 Cpk 是 {min_cpk}。",
        f"重点关注项：{critical_text}。",
    ]

    if previous and previous.get("overall_min_cpk") is not None and delta is not None:
        direction = comparison.get("cpk_direction_vs_previous") or "flat"
        direction_text = {"up": "比上一批变好", "down": "比上一批变差", "flat": "和上一批基本持平"}.get(direction, "和上一批相比有变化")
        parts.append(
            f"和上一批相比，最小 Cpk 变化 {delta}，说明当前过程能力{direction_text}。"
        )
    elif history_summary.get("has_history"):
        parts.append("系统里已经有历史记录，但上一条没有形成可直接对比的有效 Cpk 数值。")
    else:
        parts.append("目前还没有可用于趋势判断的历史批次。")

    if spc_result.get("defect_rate") is not None:
        parts.append(f"本次不良率为 {_format_value(spc_result.get('defect_rate'))}。")

    if critical:
        parts.append("建议优先检查最弱指标对应的刀具、机床补偿、装夹和测量一致性。")
    else:
        parts.append("当前没有明显告警项，建议继续按批次稳定采样并观察趋势。")
    return "".join(parts)


def generate_html(spc_result: dict[str, Any], history_summary: dict[str, Any] | None = None) -> str:
    history_summary = history_summary or spc_result.get("history_summary") or {}
    artifacts = spc_result.get("artifacts") or {}
    pretty = html.escape(json.dumps(spc_result, ensure_ascii=False, indent=2))
    alert = spc_result.get("alert") or {}
    metrics = spc_result.get("metrics") or {}

    cards = [
        ("Run ID", spc_result.get("run_id")),
        ("Overall Status", spc_result.get("overall_status")),
        ("Overall Min Cpk", spc_result.get("overall_min_cpk")),
        ("Defect Rate", spc_result.get("defect_rate")),
        ("Batch Numbers", spc_result.get("batch_numbers")),
        ("Critical Metrics", spc_result.get("critical_metrics")),
    ]

    cards_html = "".join(
        f"<div class='card'><div class='label'>{html.escape(title)}</div><div class='value'>{html.escape(_format_value(value))}</div></div>"
        for title, value in cards
    )

    alert_html = ""
    if alert:
        alert_html = (
            "<section class='panel'>"
            "<h2>Alert</h2>"
            f"<p><strong>Required:</strong> {html.escape(_format_value(alert.get('required')))}</p>"
            f"<p><strong>Level:</strong> {html.escape(_format_value(alert.get('level')))}</p>"
            f"<p><strong>Reasons:</strong> {html.escape(_format_value(alert.get('reasons')))}</p>"
            f"<p><strong>Push Status:</strong> {html.escape(_format_value(alert.get('push_status')))}</p>"
            "</section>"
        )

    trend_svg = _read_svg(artifacts.get("cpk_trend_svg_path"))
    control_svgs = []
    for metric_name, path in (artifacts.get("control_chart_svg_paths") or {}).items():
        svg = _read_svg(path)
        if svg:
            control_svgs.append(
                "<div class='chart-card'>"
                f"<h3>{html.escape(str(metric_name))}</h3>"
                f"{svg}"
                "</div>"
            )
    control_svg_html = "".join(control_svgs)

    previous = history_summary.get("previous_run") or {}
    comparison = history_summary.get("comparison") or {}

    return (
        "<html><head><meta charset='utf-8'><title>Gear SPC Report</title>"
        "<style>"
        "body{font-family:Segoe UI,Arial,sans-serif;max-width:1280px;margin:24px auto;padding:0 16px;line-height:1.5;color:#1f2937;background:#fff}"
        "h1,h2,h3{margin:0 0 10px 0}"
        ".muted{color:#6b7280}"
        ".grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0 24px}"
        ".card,.panel,.chart-card{border:1px solid #d1d5db;border-radius:8px;padding:14px;background:#f9fafb}"
        ".label{font-size:12px;color:#6b7280;margin-bottom:6px}"
        ".value{font-size:20px;font-weight:600;word-break:break-word}"
        "table{width:100%;border-collapse:collapse;margin-top:8px}"
        "th,td{border:1px solid #e5e7eb;padding:8px;text-align:left;font-size:13px;vertical-align:top}"
        "th{background:#f3f4f6}"
        ".charts{display:grid;grid-template-columns:1fr;gap:16px}"
        ".control-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}"
        ".summary{font-size:15px;background:#eef6ff;border-left:4px solid #2563eb;padding:14px;border-radius:6px}"
        "pre{white-space:pre-wrap;word-break:break-word;background:#111827;color:#f9fafb;padding:16px;border-radius:8px;overflow:auto}"
        "@media (max-width:960px){.grid,.control-grid{grid-template-columns:1fr}}"
        "</style></head><body>"
        "<h1>Gear SPC Production Report</h1>"
        f"<p class='muted'>Generated at {html.escape(_format_value(spc_result.get('generated_at')))}</p>"
        "<section class='panel'>"
        "<h2>白话总结</h2>"
        f"<div class='summary'>{html.escape(_plain_summary(spc_result, history_summary))}</div>"
        "</section>"
        f"<div class='grid'>{cards_html}</div>"
        f"{alert_html}"
        "<section class='panel'>"
        "<h2>Metric Summary</h2>"
        "<table><thead><tr><th>Metric</th><th>Mean</th><th>Std</th><th>Cp</th><th>Cpk</th><th>Status</th></tr></thead>"
        f"<tbody>{_build_metrics_rows(metrics)}</tbody></table>"
        "</section>"
        "<section class='panel'>"
        "<h2>History</h2>"
        f"<p><strong>Has History:</strong> {html.escape(_format_value(history_summary.get('has_history')))}</p>"
        f"<p><strong>Previous Batch:</strong> {html.escape(_format_value(previous.get('batch_key')))}</p>"
        f"<p><strong>Cpk Delta vs Previous:</strong> {html.escape(_format_value(comparison.get('cpk_delta_vs_previous')))}</p>"
        f"<p><strong>Repeated Critical Metrics:</strong> {html.escape(_format_value(comparison.get('repeated_critical_metrics_vs_previous')))}</p>"
        "<table><thead><tr><th>Created At</th><th>Batch</th><th>Status</th><th>Overall Min Cpk</th><th>Defect Rate</th></tr></thead>"
        f"<tbody>{_build_history_rows(history_summary.get('recent_runs') or [])}</tbody></table>"
        "</section>"
        "<section class='panel charts'>"
        "<h2>Charts</h2>"
        f"<div class='chart-card'>{trend_svg or '<p>No trend chart generated.</p>'}</div>"
        f"<div class='control-grid'>{control_svg_html or '<p>No control charts generated.</p>'}</div>"
        "</section>"
        "<section class='panel'>"
        "<h2>Artifacts</h2>"
        f"<p><strong>JSON:</strong> {html.escape(_format_value(artifacts.get('json_report_path')))}</p>"
        f"<p><strong>HTML:</strong> {html.escape(_format_value(artifacts.get('html_report_path')))}</p>"
        f"<p><strong>PDF:</strong> {html.escape(_format_value(artifacts.get('pdf_report_path')))} ({html.escape(_format_value(artifacts.get('pdf_status')))})</p>"
        "</section>"
        "<section class='panel'>"
        "<h2>Structured Output</h2>"
        f"<pre>{pretty}</pre>"
        "</section>"
        "</body></html>"
    )


def generate_pdf(html_content: str) -> tuple[bytes | None, str]:
    try:
        from weasyprint import HTML  # type: ignore
    except ImportError:
        return None, "weasyprint_not_installed"
    except Exception as exc:
        return None, f"import_failed: {exc}"

    try:
        return HTML(string=html_content).write_pdf(), "success"
    except Exception as exc:
        return None, f"failed: {exc}"


def write_bundle(
    spc_result: dict[str, Any],
    output_dir: str,
    generate_pdf_file: bool = False,
) -> dict[str, Any]:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    run_id = safe_filename(spc_result.get("run_id"))
    json_path = outdir / f"report_{run_id}.json"
    html_path = outdir / f"report_{run_id}.html"

    json_path.write_text(json.dumps(spc_result, ensure_ascii=False, indent=2), encoding="utf-8")
    html_content = generate_html(spc_result)
    html_path.write_text(html_content, encoding="utf-8")

    pdf_path = None
    pdf_status = "not_requested_set_generate_pdf_true_later"
    if generate_pdf_file:
        pdf_bytes, pdf_status = generate_pdf(html_content)
        if pdf_bytes is not None:
            pdf_path = outdir / f"report_{run_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)

    return {
        "json_report_path": str(json_path),
        "html_report_path": str(html_path),
        "pdf_report_path": str(pdf_path) if pdf_path else None,
        "pdf_status": pdf_status,
    }
