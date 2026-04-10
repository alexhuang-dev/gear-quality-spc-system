from __future__ import annotations

from typing import Any, TypedDict


class GearQualityState(TypedDict, total=False):
    csv_text: str
    specs: dict[str, dict[str, float]]
    config: dict[str, Any]
    expected: dict[str, Any] | None
    thread_id: str | None
    spc_result: dict[str, Any]
    response: dict[str, Any]
