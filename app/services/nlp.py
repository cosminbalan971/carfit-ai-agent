import re
import difflib
from app.models.preferences import UserPreferenceProfile


def _normalize_text(message: str) -> str:
    m = message.lower().strip()
    m = m.replace("-", " ")
    m = re.sub(r"[,/]+", " ", m)
    m = re.sub(r"\s+", " ", m)
    return m


def _tokens(message: str):
    return re.findall(r"[a-z0-9\+]+", message.lower())


def _has_similar_token(tokens, candidates, cutoff=0.82):
    for token in tokens:
        match = difflib.get_close_matches(token, candidates, n=1, cutoff=cutoff)
        if match:
            return match[0]
    return None


def _parse_number_token(raw: str):
    raw = raw.strip().lower().replace(",", "").replace(" ", "")
    if raw.endswith("k"):
        try:
            return int(float(raw[:-1]) * 1000)
        except Exception:
            return None
    try:
        return int(float(raw))
    except Exception:
        return None


def parse_message_to_agent_input(message: str) -> UserPreferenceProfile:
    m = _normalize_text(message)
    toks = _tokens(m)

    profile = UserPreferenceProfile()

    # ---------------------------
    # fuel understanding
    # ---------------------------
    if "diesel" in m or _has_similar_token(toks, ["diesel", "dizel", "disel", "desiel"]):
        profile.hard_constraints.fuel = "diesel"
    elif "hybrid" in m or _has_similar_token(toks, ["hybrid", "hibryd", "hibrid"]):
        profile.hard_constraints.fuel = "hybrid"
    elif "petrol" in m or "gasoline" in m or _has_similar_token(toks, ["petrol", "gasoline", "benzin", "benzina"]):
        profile.hard_constraints.fuel = "petrol"
    elif "phev" in m or "plug in hybrid" in m:
        profile.hard_constraints.fuel = "phev"
    elif "electric" in m or " ev " in f" {m} " or _has_similar_token(toks, ["electric", "electic", "ev"]):
        profile.hard_constraints.fuel = "ev"

    # ---------------------------
    # body understanding
    # ---------------------------
    if "suv" in m or "crossover" in m or "4x4" in m or _has_similar_token(toks, ["suv", "crossover"]):
        profile.hard_constraints.body = "suv"
    elif "wagon" in m or "estate" in m or "touring" in m or "combi" in m:
        profile.hard_constraints.body = "wagon"
    elif "sedan" in m or "saloon" in m or "berlina" in m:
        profile.hard_constraints.body = "sedan"
    elif "hatchback" in m or "hatch" in m or _has_similar_token(toks, ["hatch", "hatchback"]):
        profile.hard_constraints.body = "hatchback"

    # ---------------------------
    # gearbox understanding
    # ---------------------------
    if "automatic" in m or re.search(r"\bauto\b", m) or _has_similar_token(toks, ["automatic", "automtic", "automat", "auto"]):
        profile.hard_constraints.gearbox = "auto"
    elif "manual" in m or _has_similar_token(toks, ["manual", "manul", "manua"]):
        profile.hard_constraints.gearbox = "manual"

    # ---------------------------
    # year - only explicit year patterns
    # ---------------------------
    year_patterns = [
        r"(?:from|after|since|starting from|newer than)\s*(19\d{2}|20\d{2})",
        r"(19\d{2}|20\d{2})\s*\+",
        r"(19\d{2}|20\d{2})\s*(?:or newer|and newer)",
    ]

    for pattern in year_patterns:
        year_match = re.search(pattern, m)
        if year_match:
            profile.hard_constraints.year_min = int(year_match.group(1))
            break

    # ---------------------------
    # budget understanding
    # ---------------------------
    if re.fullmatch(r"\d{4,9}", m.strip()):
        profile.hard_constraints.budget_max = int(m.strip())
    else:
        budget_match = re.search(
            r"(?:budget|under|up to|upto|max|maximum|around|about)?\s*(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?k?)\s*(euro|euros|eur|€|gbp|pounds|£|usd|\$)?",
            m
        )
        if budget_match:
            number_raw = budget_match.group(1)
            number_val = _parse_number_token(number_raw)
            if number_val and number_val >= 1000:
                profile.hard_constraints.budget_max = number_val

                currency_raw = budget_match.group(2)
                if currency_raw:
                    currency_raw = currency_raw.lower()
                    if currency_raw in ("euro", "euros", "eur", "€"):
                        profile.hard_constraints.budget_currency = "EUR"
                    elif currency_raw in ("gbp", "pounds", "£"):
                        profile.hard_constraints.budget_currency = "GBP"
                    elif currency_raw in ("usd", "$"):
                        profile.hard_constraints.budget_currency = "USD"

    # ---------------------------
    # natural language meaning
    # ---------------------------
    if "comfort" in m or "quiet" in m or "silent" in m or "nice" in m or "comfortable" in m:
        profile.soft_preferences.comfort_priority = 8

    if "reliable" in m or "reliability" in m or "dependable" in m:
        profile.soft_preferences.reliability_priority = 8

    if "cheap to run" in m or "low running cost" in m or "low running costs" in m or "economical" in m or "efficient" in m:
        profile.soft_preferences.running_cost_priority = 9

    if "cheap to maintain" in m or "low maintenance" in m:
        profile.soft_preferences.running_cost_priority = 9
        profile.soft_preferences.reliability_priority = max(profile.soft_preferences.reliability_priority, 8)

    if "big trunk" in m or "extra space" in m or "roomy" in m or "spacious" in m or "big car" in m or "large car" in m:
        profile.soft_preferences.practicality_priority = 9
        profile.inferred_needs.family_use = True

    if "family" in m or "kids" in m or "child seat" in m:
        profile.inferred_needs.family_use = True
        profile.soft_preferences.practicality_priority = max(profile.soft_preferences.practicality_priority, 8)

    if "city" in m or "traffic" in m or "urban" in m:
        profile.inferred_needs.city_use = True
        profile.inferred_needs.easy_parking_preference = True

    if "delivery" in m or "pizza" in m or "courier" in m:
        profile.inferred_needs.delivery_use = True
        profile.inferred_needs.city_use = True
        profile.inferred_needs.compact_size_preference = True

    if "small" in m or "compact" in m:
        profile.inferred_needs.compact_size_preference = True

    if "highway" in m or "long drives" in m or "road trips" in m or "motorway" in m:
        profile.inferred_needs.highway_use = True
        profile.soft_preferences.comfort_priority = max(profile.soft_preferences.comfort_priority, 8)

    if "quiet" in m or "silent" in m:
        profile.inferred_needs.low_noise_preference = True

    if "premium" in m or "luxury" in m:
        profile.inferred_needs.premium_experience_preference = True

    if ("risk" in m) and (("detail" in m) or ("penalt" in m)):
        profile.conversation_context.user_goal = "explain"

    return profile