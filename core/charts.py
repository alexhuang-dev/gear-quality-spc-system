from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


def safe_filename(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "item")).strip("_") or "item"


def svg_line_chart(
    path: str,
    title: str,
    labels: list[str],
    values: list[float | None],
    lines: dict[str, float | None],
) -> str | None:
    valid = [float(value) for value in values if value is not None]
    if not valid:
        return None

    width, height, pad = 860, 280, 42
    line_values = [float(v) for v in lines.values() if v is not None]
    ymin, ymax = min(valid + line_values), max(valid + line_values)
    if ymin == ymax:
        ymin -= 1
        ymax += 1

    def point(index: int, value: float) -> tuple[float, float]:
        x = pad + (width - 2 * pad) * (index / max(1, len(values) - 1))
        y = pad + (height - 2 * pad) * (1 - ((float(value) - ymin) / max(1e-9, ymax - ymin)))
        return round(x, 2), round(y, 2)

    points = [point(index, value) for index, value in enumerate(values) if value is not None]
    polyline = " ".join(f"{x},{y}" for x, y in points)
    guides = ""
    for label, value in lines.items():
        if value is None:
            continue
        _, y = point(0, float(value))
        guides += (
            f'<line x1="{pad}" x2="{width-pad}" y1="{y}" y2="{y}" '
            f'stroke="#d62728" stroke-dasharray="5,4"/>'
            f'<text x="{pad+4}" y="{max(12, y-4)}" font-size="11" fill="#d62728">'
            f"{html.escape(str(label))}</text>"
        )
    circles = "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="#1f77b4"/>' for x, y in points)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        '<rect width="100%" height="100%" fill="white"/>'
        f'<text x="{pad}" y="26" font-size="18" font-family="Arial">{html.escape(title)}</text>'
        f'<line x1="{pad}" x2="{width-pad}" y1="{height-pad}" y2="{height-pad}" stroke="#999"/>'
        f'<line x1="{pad}" x2="{pad}" y1="{pad}" y2="{height-pad}" stroke="#999"/>'
        f"{guides}"
        f'<polyline fill="none" stroke="#1f77b4" stroke-width="2" points="{polyline}"/>'
        f"{circles}"
        f'<text x="{pad}" y="{height-10}" font-size="11" fill="#555">{html.escape(", ".join(labels[:12]))}</text>'
        "</svg>"
    )
    Path(path).write_text(svg, encoding="utf-8")
    return path


def write_control_charts(
    output_dir: str,
    run_id: str,
    metrics: dict[str, dict[str, Any]],
    series_by_metric: dict[str, list[float | None]],
) -> dict[str, str]:
    chart_dir = Path(output_dir) / f"charts_{safe_filename(run_id)}"
    chart_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for index, (metric, stats) in enumerate(metrics.items(), 1):
        values = series_by_metric.get(metric) or []
        path = chart_dir / f"control_{index}_{safe_filename(metric)}.svg"
        result = svg_line_chart(
            str(path),
            f"Control Chart: {metric}",
            [str(i + 1) for i in range(len(values))],
            values,
            {"UCL": stats.get("control_UCL"), "LCL": stats.get("control_LCL")},
        )
        if result:
            written[metric] = result
    return written


def write_cpk_trend_chart(output_dir: str, run_id: str, trend_labels: list[str], trend_values: list[float | None]) -> str | None:
    chart_dir = Path(output_dir) / f"charts_{safe_filename(run_id)}"
    chart_dir.mkdir(parents=True, exist_ok=True)
    return svg_line_chart(
        str(chart_dir / "cpk_trend.svg"),
        "Overall Min Cpk Trend",
        trend_labels,
        trend_values,
        {"1.00": 1.0, "1.33": 1.33, "1.67": 1.67},
    )
