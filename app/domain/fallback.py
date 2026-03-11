from __future__ import annotations

from typing import Optional
from app.domain.engine import recommend_cars
from app.domain.policy import DEFAULT_POLICY, PolicyStep
from typing import Any, Dict, List, Tuple, Sequence
Prefs = Dict[str, Any]


...
def apply_fallback_policy(
    cars: Sequence[Dict[str, Any]],
    prefs: Prefs,
    policy: List[PolicyStep] = DEFAULT_POLICY,
) -> Tuple[Prefs, dict, List[str], List[str]]:
    """
    Returns:
      - final_prefs (may be relaxed)
      - result (from recommend_cars)
      - assumptions (human readable)
      - policy_steps_taken (machine readable)
    """
    assumptions: List[str] = []
    steps_taken: List[str] = []

    result = recommend_cars(cars, prefs)
    if result.get("total_matches", 0) > 0:
        return prefs, result, assumptions, steps_taken

    current = dict(prefs)

    for step in policy:
        applied = step.apply(current)
        if not applied:
            continue

        relaxed, assumption = applied
        steps_taken.append(step.name)
        assumptions.append(assumption)

        result = recommend_cars(cars, relaxed)
        current = relaxed

        if result.get("total_matches", 0) > 0:
            break

    return current, result, assumptions, steps_taken