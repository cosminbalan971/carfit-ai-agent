from __future__ import annotations

from typing import Any, Dict, List

from app.domain.risk_data import ENGINE_ISSUES

SCORE_KEYS = ["reliability", "comfort", "running_cost", "practicality", "performance", "safety", "resale"]


def compute_weighted_score(car: dict, prefs: dict) -> float:
    scores = car.get("scores", {})

    total_weight = 0
    weighted_sum = 0.0

    for key in SCORE_KEYS:
        w = int(prefs.get(f"{key}_priority", 0) or 0)
        s = float(scores.get(key, 0) or 0)
        total_weight += w
        weighted_sum += w * s

    # If user didn't provide priorities, use sensible defaults
    if total_weight == 0:
        reliability = float(scores.get("reliability", 0) or 0)
        comfort = float(scores.get("comfort", 0) or 0)
        total_weight = 8
        weighted_sum = 5 * reliability + 3 * comfort

    base = weighted_sum / total_weight  # 0–10 scale
    penalty = float(car.get("risk_penalty", 0) or 0)  # 0–5
    return base - penalty


def compute_needs_adjustment(car: dict, prefs: dict) -> tuple[float, List[str]]:
    """
    Adds stronger bonus/penalty adjustments based on inferred needs.
    This version is intentionally stronger so city/delivery/family use
    has a clearer effect on final ranking.
    """
    adjustment = 0.0
    reasons: List[str] = []

    body = car.get("body")
    scores = car.get("scores", {})

    city_use = bool(prefs.get("city_use"))
    highway_use = bool(prefs.get("highway_use"))
    family_use = bool(prefs.get("family_use"))
    delivery_use = bool(prefs.get("delivery_use"))
    compact_size_preference = bool(prefs.get("compact_size_preference"))
    easy_parking_preference = bool(prefs.get("easy_parking_preference"))
    low_noise_preference = bool(prefs.get("low_noise_preference"))
    premium_experience_preference = bool(prefs.get("premium_experience_preference"))

    running_cost = float(scores.get("running_cost", 0) or 0)
    reliability = float(scores.get("reliability", 0) or 0)
    practicality = float(scores.get("practicality", 0) or 0)
    comfort = float(scores.get("comfort", 0) or 0)
    safety = float(scores.get("safety", 0) or 0)
    resale = float(scores.get("resale", 0) or 0)

    
    if city_use or compact_size_preference or easy_parking_preference or delivery_use:
        if body == "hatchback":
            adjustment += 2.5
            reasons.append("Excellent fit for compact city/delivery use")
        elif body == "sedan":
            adjustment += 0.8
            reasons.append("Reasonable fit for city use")
        elif body == "wagon":
            adjustment -= 1.0
            reasons.append("Less ideal for compact city/delivery use")
        elif body == "suv":
            adjustment -= 3.0
            reasons.append("Poor fit for compact city/delivery use")

    
    if delivery_use:
        if running_cost >= 8:
            adjustment += 1.2
            reasons.append("Strong running-cost fit for delivery use")
        elif running_cost <= 5:
            adjustment -= 0.8

        if reliability >= 8:
            adjustment += 1.0
            reasons.append("Strong reliability fit for delivery use")
        elif reliability <= 5:
            adjustment -= 0.5

    
    if easy_parking_preference:
        if body == "hatchback":
            adjustment += 1.0
        elif body == "sedan":
            adjustment += 0.2
        elif body == "suv":
            adjustment -= 1.0

  
    if family_use:
        if body in ("wagon", "suv"):
            adjustment += 1.4
            reasons.append("Better fit for family/practical use")
        elif body == "hatchback":
            adjustment -= 0.8

        if practicality >= 8:
            adjustment += 0.8
        if safety >= 8:
            adjustment += 0.5

    
    if highway_use:
        if comfort >= 8:
            adjustment += 0.8
            reasons.append("Comfort-oriented for highway driving")
        if safety >= 8:
            adjustment += 0.4

    if low_noise_preference:
        if comfort >= 8:
            adjustment += 0.7
            reasons.append("Better match for quietness preference")

   
    if premium_experience_preference:
        if comfort >= 8:
            adjustment += 0.5
        if resale >= 7:
            adjustment += 0.2

    return adjustment, reasons

def recommend_cars(cars: List[Dict[str, Any]], prefs: Dict[str, Any]) -> Dict[str, Any]:
    filtered = []

    for car in cars:
        # Basic filtering
        if prefs.get("fuel") and prefs.get("fuel") != "any" and car["fuel"] != prefs["fuel"]:
            continue

        if prefs.get("body") and prefs.get("body") != "any" and car["body"] != prefs["body"]:
            continue

        if prefs.get("gearbox") and prefs.get("gearbox") != "any" and car["gearbox"] != prefs["gearbox"]:
            continue

        if prefs.get("year") is not None:
            y = int(prefs["year"])
            ys = int(car.get("year_start", 0) or 0)
            ye = int(car.get("year_end", 9999) or 9999)
            if not (ys <= y <= ye):
                continue

        reliability_priority = int(prefs.get("reliability_priority", 5))
        comfort_priority = int(prefs.get("comfort_priority", 5))

        reasons = []

        if reliability_priority >= comfort_priority:
            reasons.append("Strong reliability focus")
        if comfort_priority > reliability_priority:
            reasons.append("Comfort & quietness focus")

       
        core_score = compute_weighted_score(car, prefs)

    
        needs_adjustment, needs_reasons = compute_needs_adjustment(car, prefs)
        final_score = core_score + needs_adjustment

        reasons.extend(needs_reasons)

    
        risk_penalty = float(car.get("risk_penalty", 0) or 0)
        base_score = round(core_score + risk_penalty, 2)

        issues = ENGINE_ISSUES.get(car.get("name", ""), [])
        if issues:
            reasons.append("Known issues data available")

        if risk_penalty > 0:
            reasons.append(f"Risk penalty applied: -{risk_penalty}")

        filtered.append({
            "name": car.get("name", f"{car.get('brand', '?')} {car.get('model', '?')}"),
            "base_score": base_score,
            "risk_penalty": risk_penalty,
            "final_score": round(final_score, 4),
            "why": reasons,
            "issues": issues,
        })

    filtered.sort(key=lambda x: x["final_score"], reverse=True)

    return {
        "top_3": filtered[:3],
        "total_matches": len(filtered),
        "filters_applied": {
            "fuel": prefs.get("fuel"),
            "body": prefs.get("body"),
            "gearbox": prefs.get("gearbox"),
            "year": prefs.get("year"),
        },
        "no_match_reason": "No cars matched the selected filters." if len(filtered) == 0 else None,
    }