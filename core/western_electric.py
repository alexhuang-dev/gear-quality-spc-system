from __future__ import annotations

from typing import Any

import numpy as np


def _add_rule(rules: list[dict[str, Any]], rule: str, points: list[int], description: str) -> None:
    if points:
        rules.append(
            {
                "rule": rule,
                "points": sorted(set(int(point) for point in points)),
                "description": description,
            }
        )


def evaluate(values: list[float | None], mean: float | None, std: float | None) -> list[dict[str, Any]]:
    clean = [(index, float(value)) for index, value in enumerate(values) if value is not None and np.isfinite(value)]
    if mean is None or std is None or not np.isfinite(std) or std <= 0:
        return []

    idx = [item[0] for item in clean]
    vals = [item[1] for item in clean]
    signs = [1 if value > mean else (-1 if value < mean else 0) for value in vals]
    rules: list[dict[str, Any]] = []

    _add_rule(rules, "WE-1", [idx[i] for i, value in enumerate(vals) if abs(value - mean) > 3 * std], "one point beyond 3 sigma")

    for start in range(max(0, len(vals) - 9 + 1)):
        window = signs[start : start + 9]
        if all(sign > 0 for sign in window) or all(sign < 0 for sign in window):
            _add_rule(rules, "WE-2", idx[start : start + 9], "9 consecutive points on same side")

    for start in range(max(0, len(vals) - 6 + 1)):
        window = vals[start : start + 6]
        if all(window[i] < window[i + 1] for i in range(5)) or all(window[i] > window[i + 1] for i in range(5)):
            _add_rule(rules, "WE-3", idx[start : start + 6], "6 consecutive increasing/decreasing")

    for start in range(max(0, len(vals) - 14 + 1)):
        window = vals[start : start + 14]
        diffs = [window[i + 1] - window[i] for i in range(13)]
        if all(diff != 0 for diff in diffs) and all((diffs[i] > 0) != (diffs[i + 1] > 0) for i in range(12)):
            _add_rule(rules, "WE-4", idx[start : start + 14], "14 alternating points")

    for start in range(max(0, len(vals) - 3 + 1)):
        window = vals[start : start + 3]
        high = [idx[start + i] for i, value in enumerate(window) if value > mean + 2 * std]
        low = [idx[start + i] for i, value in enumerate(window) if value < mean - 2 * std]
        if len(high) >= 2:
            _add_rule(rules, "WE-5", high, "2 of 3 beyond +2 sigma")
        if len(low) >= 2:
            _add_rule(rules, "WE-5", low, "2 of 3 beyond -2 sigma")

    for start in range(max(0, len(vals) - 5 + 1)):
        window = vals[start : start + 5]
        high = [idx[start + i] for i, value in enumerate(window) if value > mean + std]
        low = [idx[start + i] for i, value in enumerate(window) if value < mean - std]
        if len(high) >= 4:
            _add_rule(rules, "WE-6", high, "4 of 5 beyond +1 sigma")
        if len(low) >= 4:
            _add_rule(rules, "WE-6", low, "4 of 5 beyond -1 sigma")

    for start in range(max(0, len(vals) - 15 + 1)):
        window = vals[start : start + 15]
        if all(abs(value - mean) < std for value in window):
            _add_rule(rules, "WE-7", idx[start : start + 15], "15 consecutive within 1 sigma")

    for start in range(max(0, len(vals) - 8 + 1)):
        window = vals[start : start + 8]
        if all(abs(value - mean) > std for value in window):
            _add_rule(rules, "WE-8", idx[start : start + 8], "8 consecutive beyond 1 sigma")

    seen: set[tuple[str, tuple[int, ...]]] = set()
    deduped: list[dict[str, Any]] = []
    for rule in rules:
        key = (rule["rule"], tuple(rule["points"]))
        if key not in seen:
            seen.add(key)
            deduped.append(rule)
    return deduped
