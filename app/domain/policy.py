from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Callable

Prefs = Dict[str, Any]


@dataclass
class PolicyStep:
    name: str
    apply: Callable[[Prefs], Tuple[Prefs, str] | None]
    


def relax_gearbox_step(prefs: Prefs) -> Tuple[Prefs, str] | None:
    original = prefs.get("gearbox")
    if original in (None, "any"):
        return None

    new_prefs = dict(prefs)
    new_prefs["gearbox"] = None
    assumption = f"No exact matches with {original} gearbox, so I widened gearbox to any."
    return new_prefs, assumption


def relax_fuel_step(prefs: Prefs) -> Tuple[Prefs, str] | None:
    original = prefs.get("fuel")
    if original in (None, "any"):
        return None

    new_prefs = dict(prefs)
    new_prefs["fuel"] = None
    assumption = f"No exact matches with {original} fuel, so I widened fuel type."
    return new_prefs, assumption


def relax_body_step(prefs: Prefs) -> Tuple[Prefs, str] | None:
    original = prefs.get("body")
    if original in (None, "any"):
        return None

    new_prefs = dict(prefs)

    if original == "hatchback" and (
        prefs.get("compact_size_preference")
        or prefs.get("city_use")
        or prefs.get("delivery_use")
    ):
        new_prefs["body"] = None
        new_prefs["compact_size_preference"] = True
        new_prefs["easy_parking_preference"] = True
        assumption = (
            "No exact hatchback match was found, so I widened body type slightly "
            "while still prioritizing compact, city-friendly cars."
        )
        return new_prefs, assumption

    # Preserve strong family body intent for SUV / wagon
    if prefs.get("family_use") and original in ("suv", "wagon"):
        return None

    new_prefs["body"] = None
    assumption = f"No exact matches with {original} body type, so I widened body type."
    return new_prefs, assumption


DEFAULT_POLICY: List[PolicyStep] = [
    PolicyStep(name="relax_gearbox", apply=relax_gearbox_step),
    PolicyStep(name="relax_fuel", apply=relax_fuel_step),
    PolicyStep(name="relax_body", apply=relax_body_step),
]