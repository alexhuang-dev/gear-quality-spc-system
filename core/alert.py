from __future__ import annotations

import json
import urllib.request
from typing import Any

from core.config import STATUS_ABNORMAL


def build_payload(spc_result: dict[str, Any], report_url: str | None = None) -> dict[str, Any]:
    return {
        "batch_no": spc_result.get("batch_no"),
        "batch_numbers": spc_result.get("batch_numbers"),
        "overall_status": spc_result.get("overall_status"),
        "critical_metrics": spc_result.get("critical_metrics"),
        "min_cpk": spc_result.get("overall_min_cpk"),
        "timestamp": spc_result.get("generated_at"),
        "report_url": report_url,
    }


def build_alert(spc_result: dict[str, Any], config: dict[str, Any], report_url: str | None = None) -> dict[str, Any]:
    reasons = []
    if spc_result.get("overall_min_cpk") is not None and spc_result["overall_min_cpk"] < float(config.get("alert_cpk_threshold") or 1.0):
        reasons.append("overall_min_cpk_below_threshold")
    if spc_result.get("critical_metrics"):
        reasons.append("critical_metrics_present")
    if any((spc_result.get("western_electric") or {}).get("violations_by_metric", {}).values()):
        reasons.append("western_electric_rule_hits")

    payload = build_payload(spc_result, report_url=report_url)
    alert = {
        "required": bool(reasons),
        "level": "critical" if spc_result.get("overall_status") == STATUS_ABNORMAL else ("warning" if reasons else "normal"),
        "reasons": reasons,
        "payload": payload,
        "push_status": "not_sent_configure_webhook_or_scheduler",
    }
    if alert["required"] and config.get("send_alerts") and config.get("alert_webhook_url"):
        alert["push_status"] = send(alert, str(config["alert_webhook_url"]), str(config.get("alert_webhook_type") or "generic"))
    return alert


def send(alert_payload: dict[str, Any], webhook_url: str, webhook_type: str = "generic") -> str:
    payload = alert_payload.get("payload") or {}
    content = (
        "Gear SPC Alert\n"
        f"status: {payload.get('overall_status')}\n"
        f"min_cpk: {payload.get('min_cpk')}\n"
        f"critical: {', '.join(payload.get('critical_metrics') or [])}\n"
        f"batch: {payload.get('batch_no') or payload.get('batch_numbers')}\n"
        f"report: {payload.get('report_url')}"
    )
    if webhook_type == "wecom":
        body = {"msgtype": "markdown", "markdown": {"content": content}}
    elif webhook_type == "feishu":
        body = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "Gear SPC Alert"}},
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
    else:
        body = {"text": content, "alert": alert_payload}

    try:
        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return f"sent_http_{response.status}"
    except Exception as exc:
        return f"send_failed: {exc}"
