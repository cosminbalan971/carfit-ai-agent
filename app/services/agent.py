from typing import Any, Dict, List

from providers.static_json_provider import StaticJsonProvider
from app.infrastructure.llm import explain_recommendation, route_conversation_turn
from app.infrastructure.memory import get_or_create_session_id, load_state, save_state
from app.services.render import render_final_answer
from app.domain.fallback import apply_fallback_policy


def build_clarifying_questions(prefs: Dict[str, Any]) -> List[str]:
    fuel = prefs.get("fuel")
    body = prefs.get("body")
    gearbox = prefs.get("gearbox")
    budget_max = prefs.get("budget_max")

    city_use = prefs.get("city_use", False)
    highway_use = prefs.get("highway_use", False)
    family_use = prefs.get("family_use", False)
    delivery_use = prefs.get("delivery_use", False)
    compact_size_preference = prefs.get("compact_size_preference", False)
    low_noise_preference = prefs.get("low_noise_preference", False)

    practicality_priority = prefs.get("practicality_priority", 5)
    reliability_priority = prefs.get("reliability_priority", 5)
    comfort_priority = prefs.get("comfort_priority", 5)
    running_cost_priority = prefs.get("running_cost_priority", 5)

    hard_constraints_count = sum(
        1 for v in [fuel, body, gearbox, budget_max] if v not in (None, "", "any")
    )

    needs_count = sum(
        1
        for v in [
            city_use,
            highway_use,
            family_use,
            delivery_use,
            compact_size_preference,
            low_noise_preference,
        ]
        if v
    )

    # If we know almost nothing, ask one broad conversational question.
    if hard_constraints_count == 0 and needs_count == 0:
        return [
            "Tell me what matters most to you — for example comfort, reliability, size, fuel type, gearbox, or budget."
        ]

    # Ask only one natural next question.
    if not body or body == "any":
        if delivery_use or city_use or compact_size_preference:
            return ["Would you prefer something compact like a hatchback, or should I keep body style open?"]
        if family_use or practicality_priority >= 8:
            return ["Would you prefer an SUV or wagon for the extra space, or should I keep body style open?"]
        return ["Do you have a preferred body type, or should I keep it open?"]

    if not gearbox or gearbox == "any":
        if city_use:
            return ["Will this be mostly in traffic, and do you prefer automatic or manual?"]
        return ["Do you want automatic, manual, or should I keep gearbox open?"]

    if not fuel or fuel == "any":
        if city_use or delivery_use:
            return ["Do you have a fuel preference, or should I keep it open for city-friendly options?"]
        return ["Do you have a fuel preference, or should I keep it open?"]

    # Budget is optional, not blocking.
    if budget_max is None and hard_constraints_count <= 1:
        return ["Do you have a budget in mind, or should I keep budget open?"]

    # Tradeoff question only if core slots are mostly covered.
    if delivery_use and reliability_priority == 5 and running_cost_priority == 5:
        return ["For delivery use, do you care more about low running costs or reliability?"]

    if family_use and reliability_priority == 5 and comfort_priority == 5 and running_cost_priority == 5:
        return ["For a family car, do you care more about reliability, comfort, or low running costs?"]

    if (highway_use or low_noise_preference) and comfort_priority == 5 and running_cost_priority == 5:
        return ["Do you care more about comfort and quietness, or low running costs?"]

    return []


def _base_response(
    session_id: str,
    state: Dict[str, Any],
    final_answer: str,
    clarifying_questions: List[str] | None = None,
) -> Dict[str, Any]:
    clarifying_questions = clarifying_questions or []
    return {
        "session_id": session_id,
        "state": state,
        "requested_filters": {},
        "applied_filters": {},
        "policy_steps_taken": [],
        "clarifying_questions": clarifying_questions,
        "recommendations": [],
        "raw_result": {},
        "llm_summary": {},
        "final_answer": final_answer,
        "assumptions": [],
        "sources": [],
    }


def run_agent(prefs: Dict[str, Any]) -> Dict[str, Any]:
    session_id = get_or_create_session_id(prefs.get("session_id"))
    remembered = load_state(session_id)

    raw_message = (prefs.get("raw_message") or "").strip()

    merged_user = dict(remembered)
    merged_user.update({k: v for k, v in prefs.items() if v is not None and k != "raw_message"})

    for k in ("fuel", "body", "gearbox"):
        if merged_user.get(k) == "any":
            merged_user[k] = None

    if not remembered:
        merged_user.setdefault("reliability_priority", 5)
        merged_user.setdefault("comfort_priority", 3)
        merged_user.setdefault("running_cost_priority", 3)
        merged_user.setdefault("practicality_priority", 2)
        merged_user.setdefault("performance_priority", 1)
        merged_user.setdefault("safety_priority", 2)
        merged_user.setdefault("resale_priority", 2)

    # 1) LLM conversation routing first
    if raw_message:
        route = route_conversation_turn(
            message=raw_message,
            remembered_state=remembered,
            merged_state=merged_user,
        )
        if route.get("should_reply_directly") and route.get("reply"):
            save_state(session_id, merged_user)
            return _base_response(
                session_id=session_id,
                state=merged_user,
                final_answer=route["reply"],
                clarifying_questions=[],
            )

    # 2) Ask only the next best question if still needed
    clarifying = build_clarifying_questions(merged_user)
    if clarifying:
        save_state(session_id, merged_user)
        return {
            "session_id": session_id,
            "state": merged_user,
            "requested_filters": {
                "fuel": prefs.get("fuel"),
                "body": prefs.get("body"),
                "gearbox": prefs.get("gearbox"),
                "year": prefs.get("year"),
                "budget_max": prefs.get("budget_max"),
            },
            "applied_filters": {
                "fuel": merged_user.get("fuel"),
                "body": merged_user.get("body"),
                "gearbox": merged_user.get("gearbox"),
                "year": merged_user.get("year"),
                "budget_max": merged_user.get("budget_max"),
            },
            "policy_steps_taken": [],
            "clarifying_questions": clarifying,
            "recommendations": [],
            "raw_result": {},
            "llm_summary": {
                "summary": "I need a bit more information before recommending cars.",
                "top_pick": None,
                "why_top_pick": [],
                "tradeoffs_vs_second": [],
                "risk_notes": [],
                "next_questions": clarifying,
            },
            "final_answer": "I need a bit more info first:\n- " + "\n- ".join(clarifying),
            "assumptions": [],
            "sources": [],
        }

    # 3) Run deterministic recommendation flow
    provider = StaticJsonProvider()
    cars = provider.get_cars(merged_user)

    search_prefs = dict(merged_user)
    relaxed_prefs, result, assumptions, policy_steps_taken = apply_fallback_policy(cars, search_prefs)

    llm_summary = explain_recommendation(relaxed_prefs, result, assumptions)
    final_answer = render_final_answer(relaxed_prefs, result, llm_summary, assumptions)

    save_state(session_id, merged_user)

    return {
        "session_id": session_id,
        "state": merged_user,
        "requested_filters": {
            "fuel": prefs.get("fuel"),
            "body": prefs.get("body"),
            "gearbox": prefs.get("gearbox"),
            "year": prefs.get("year"),
            "budget_max": prefs.get("budget_max"),
        },
        "applied_filters": result.get("filters_applied", {}),
        "policy_steps_taken": policy_steps_taken,
        "clarifying_questions": [],
        "recommendations": result.get("top_3", []),
        "raw_result": result,
        "llm_summary": llm_summary,
        "final_answer": final_answer,
        "assumptions": assumptions,
        "sources": result.get("sources", []),
    }