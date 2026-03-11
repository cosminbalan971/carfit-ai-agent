import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


def format_budget_text(state: dict) -> str | None:
    budget_max = state.get("budget_max")
    currency = state.get("budget_currency")

    if not budget_max:
        return None

    if currency == "EUR":
        return f"€{budget_max}"
    if currency == "GBP":
        return f"£{budget_max}"
    if currency == "USD":
        return f"${budget_max}"

    return str(budget_max)


def build_user_context_summary(state: dict) -> str:
    parts = []

    body = state.get("body")
    fuel = state.get("fuel")
    gearbox = state.get("gearbox")
    year = state.get("year")

    if fuel:
        parts.append(f"{fuel}")
    if gearbox:
        parts.append(f"{gearbox}")
    if body:
        parts.append(f"{body}")

    if year:
        parts.append(f"{year}+")

    context_bits = []

    if state.get("city_use"):
        context_bits.append("mostly city use")
    if state.get("delivery_use"):
        context_bits.append("delivery use")
    if state.get("family_use"):
        context_bits.append("family use")
    if state.get("highway_use"):
        context_bits.append("highway driving")
    if state.get("compact_size_preference"):
        context_bits.append("compact size")
    if state.get("easy_parking_preference"):
        context_bits.append("easy parking")
    if state.get("low_noise_preference"):
        context_bits.append("quietness")
    if state.get("premium_experience_preference"):
        context_bits.append("premium feel")

    summary = ", ".join(parts) if parts else "your stated preferences"

    if context_bits:
        summary += f" for {', '.join(context_bits)}"

    return summary


def render_final_answer(state: dict, result: dict, llm_summary: dict, assumptions: list) -> str:
    """
    Returns a natural-language response for humans.
    Must be grounded in result.filters_applied + result.top_3 + issues.
    """

    budget_text = format_budget_text(state)
    user_context = build_user_context_summary(state)

    prompt = f"""
You are CarFit. Write a natural, helpful answer for a user looking for a car recommendation.

RULES:
- Use filters_applied and STATE as the truth for what constraints are currently known.
- If a filter in filters_applied is null/missing, treat it as "any".
- Only mention cars that exist in top_3.
- If total_matches == 0: explain that no strong match was found in the current dataset and suggest 1-2 ways to relax constraints.
- Mention issues only if present in the 'issues' list for that car.
- Be concise and friendly.
- Use bullet points when presenting recommended cars.
- DO NOT invent currencies.
- If a budget is present, preserve it exactly as written.
- Do NOT claim recommendations come from live market listings.
- If a budget exists and there are no matches, explain that budget is used as a guidance signal rather than a strict market filter.
- Do not mention any car outside top_3.
- Do not invent technical facts not present in the input.
- Start by briefly reflecting what you understood from the user.
- If fuel/body/gearbox are already present in STATE, do NOT ask the user for them again.
- Only ask a follow-up question if a truly important preference is still missing.
- If the current answer is already strong enough, end confidently without asking another question.
- If one of the top_3 cars is clearly a weaker fit for the use case (for example a larger SUV for compact city delivery use), mention it as a weaker alternative rather than presenting it as equally strong.
- If assumptions exist, explain them naturally.

USER CONTEXT SUMMARY:
{user_context}

USER BUDGET:
{budget_text}

STATE (merged preferences):
{json.dumps(state, indent=2)}

ENGINE RESULT:
{json.dumps(result, indent=2)}

STRUCTURED SUMMARY:
{json.dumps(llm_summary, indent=2)}

ASSUMPTIONS:
{json.dumps(assumptions, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "You are a helpful car recommendation assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't generate a natural explanation right now. Error: {str(e)}"