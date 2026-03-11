from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class HardConstraints:
    fuel: Optional[str] = None
    body: Optional[str] = None
    gearbox: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_max: Optional[int] = None
    brand_include: Optional[List[str]] = None
    brand_exclude: Optional[List[str]] = None
    budget_max: Optional[int] = None
    budget_currency: Optional[str] = None
    budget_open: bool = False
    clear_year: bool = False


@dataclass
class SoftPreferences:
    reliability_priority: int = 5
    comfort_priority: int = 5
    running_cost_priority: int = 5
    practicality_priority: int = 5
    performance_priority: int = 5
    safety_priority: int = 5
    resale_priority: int = 5


@dataclass
class InferredNeeds:
    city_use: bool = False
    highway_use: bool = False
    family_use: bool = False
    delivery_use: bool = False
    compact_size_preference: bool = False
    easy_parking_preference: bool = False
    low_noise_preference: bool = False
    premium_experience_preference: bool = False


@dataclass
class ConversationContext:
    user_goal: Optional[str] = None
    conversation_intent: Optional[str] = None
    missing_information: Optional[list] = None
    clarification_needed: bool = False


@dataclass
class UserPreferenceProfile:
    hard_constraints: HardConstraints = field(default_factory=HardConstraints)
    soft_preferences: SoftPreferences = field(default_factory=SoftPreferences)
    inferred_needs: InferredNeeds = field(default_factory=InferredNeeds)
    conversation_context: ConversationContext = field(default_factory=ConversationContext)

def profile_to_agent_prefs(profile: UserPreferenceProfile) -> dict:
    """
    Convert the structured preference profile into the flat dict
    expected by run_agent(), but only include values that were
    actually extracted from the current user message.

    This prevents default values (False / 5 / None) from overwriting
    remembered session state on follow-up turns like "yes" or
    "manual and mostly city".
    """

    prefs = {}

    
    if profile.hard_constraints.fuel is not None:
        prefs["fuel"] = profile.hard_constraints.fuel

    if profile.hard_constraints.body is not None:
        prefs["body"] = profile.hard_constraints.body

    if profile.hard_constraints.gearbox is not None:
        prefs["gearbox"] = profile.hard_constraints.gearbox

    if profile.hard_constraints.year_min is not None:
        prefs["year"] = profile.hard_constraints.year_min

    if profile.hard_constraints.budget_max is not None:
        prefs["budget_max"] = profile.hard_constraints.budget_max

    if profile.hard_constraints.budget_currency is not None:
        prefs["budget_currency"] = profile.hard_constraints.budget_currency

    if profile.hard_constraints.budget_open:
       prefs["budget_open"] = True

    if profile.hard_constraints.clear_year:
       prefs["clear_year"] = True

    if profile.soft_preferences.reliability_priority != 5:
        prefs["reliability_priority"] = profile.soft_preferences.reliability_priority

    if profile.soft_preferences.comfort_priority != 5:
        prefs["comfort_priority"] = profile.soft_preferences.comfort_priority

    if profile.soft_preferences.running_cost_priority != 5:
        prefs["running_cost_priority"] = profile.soft_preferences.running_cost_priority

    if profile.soft_preferences.practicality_priority != 5:
        prefs["practicality_priority"] = profile.soft_preferences.practicality_priority

    if profile.soft_preferences.performance_priority != 5:
        prefs["performance_priority"] = profile.soft_preferences.performance_priority

    if profile.soft_preferences.safety_priority != 5:
        prefs["safety_priority"] = profile.soft_preferences.safety_priority

    if profile.soft_preferences.resale_priority != 5:
        prefs["resale_priority"] = profile.soft_preferences.resale_priority

    
    if profile.inferred_needs.city_use:
        prefs["city_use"] = True

    if profile.inferred_needs.highway_use:
        prefs["highway_use"] = True

    if profile.inferred_needs.family_use:
        prefs["family_use"] = True

    if profile.inferred_needs.delivery_use:
        prefs["delivery_use"] = True

    if profile.inferred_needs.compact_size_preference:
        prefs["compact_size_preference"] = True

    if profile.inferred_needs.easy_parking_preference:
        prefs["easy_parking_preference"] = True

    if profile.inferred_needs.low_noise_preference:
        prefs["low_noise_preference"] = True

    if profile.inferred_needs.premium_experience_preference:
        prefs["premium_experience_preference"] = True

    
    if profile.conversation_context.user_goal != "recommend":
        prefs["user_goal"] = profile.conversation_context.user_goal

    if profile.conversation_context.conversation_intent is not None:
        prefs["conversation_intent"] = profile.conversation_context.conversation_intent

    if profile.conversation_context.missing_information:
        prefs["missing_information"] = profile.conversation_context.missing_information

    if profile.conversation_context.clarification_needed:
        prefs["clarification_needed"] = True

   
    if prefs.get("delivery_use"):
        prefs["running_cost_priority"] = max(prefs.get("running_cost_priority", 5), 9)
        prefs["reliability_priority"] = max(prefs.get("reliability_priority", 5), 8)
        prefs["practicality_priority"] = max(prefs.get("practicality_priority", 5), 7)

    if prefs.get("city_use"):
        prefs["running_cost_priority"] = max(prefs.get("running_cost_priority", 5), 8)
        prefs["practicality_priority"] = max(prefs.get("practicality_priority", 5), 6)

    if prefs.get("family_use"):
        prefs["practicality_priority"] = max(prefs.get("practicality_priority", 5), 9)
        prefs["safety_priority"] = max(prefs.get("safety_priority", 5), 8)
        prefs["reliability_priority"] = max(prefs.get("reliability_priority", 5), 8)

    if prefs.get("highway_use"):
        prefs["comfort_priority"] = max(prefs.get("comfort_priority", 5), 8)
        prefs["safety_priority"] = max(prefs.get("safety_priority", 5), 7)

    if prefs.get("low_noise_preference"):
        prefs["comfort_priority"] = max(prefs.get("comfort_priority", 5), 9)

    if prefs.get("premium_experience_preference"):
        prefs["comfort_priority"] = max(prefs.get("comfort_priority", 5), 8)
        prefs["resale_priority"] = max(prefs.get("resale_priority", 5), 6)

    return prefs
    