# risk.py
from __future__ import annotations

from typing import Any, Dict, List


def calc_risk_penalty(issues: List[Dict[str, Any]]) -> int:
    """
    Simple risk model:
    - More severe issues = higher penalty
    - More recent issues = higher penalty
    Returns an integer penalty that will be subtracted from the base score.
    """
    penalty = 0

    for item in issues:
        sev = int(item.get("severity", 1))
        months = int(item.get("recency_months", 999))

        # recency multiplier
        if months <= 6:
            recency_mult = 3
        elif months <= 12:
            recency_mult = 2
        elif months <= 24:
            recency_mult = 1
        else:
            recency_mult = 0  # too old / low signal

        penalty += sev * recency_mult

    # cap so it doesn't dominate the whole score
    return min(penalty, 25)