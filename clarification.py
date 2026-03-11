from typing import List

from app.models.preferences import UserPreferenceProfile


def build_clarifying_questions(profile: UserPreferenceProfile) -> List[str]:
    """
    Return a short list of the most useful follow-up questions
    based on what the agent currently understands.
    """

    questions: List[str] = []

    hc = profile.hard_constraints
    sp = profile.soft_preferences
    needs = profile.inferred_needs

    # 1) Missing hard constraints
    if hc.fuel is None:
        questions.append("Do you have a fuel preference, or should I keep it open?")

    if hc.gearbox is None:
        questions.append("Do you want automatic, manual, or should I keep gearbox open?")

    if hc.body is None:
        if needs.compact_size_preference or needs.city_use:
            questions.append("Would you prefer a hatchback or any compact body style?")
        elif needs.family_use:
            questions.append("Would you prefer an SUV, wagon, or should I keep body style open?")
        else:
            questions.append("Do you have a preferred body style, or should I keep it open?")

    # 2) Budget often matters a lot if not provided
    if hc.budget_max is None:
        questions.append("Do you have a budget in mind?")

    # 3) Ask about use case if still unclear
    if not needs.city_use and not needs.highway_use and not needs.family_use and not needs.delivery_use:
        questions.append("Will this be mostly for city driving, highway trips, family use, or mixed driving?")

    # 4) Ask about tradeoffs only if still vague
    very_default_priorities = (
        sp.reliability_priority == 5
        and sp.comfort_priority == 5
        and sp.running_cost_priority == 5
        and sp.practicality_priority == 5
        and sp.performance_priority == 5
        and sp.safety_priority == 5
        and sp.resale_priority == 5
    )

    if very_default_priorities:
        questions.append("What matters most to you: reliability, comfort, low running costs, practicality, or performance?")

    return questions[:3]