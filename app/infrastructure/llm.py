from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "350"))
TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "12"))
REPAIR_RETRY = int(os.getenv("LLM_REPAIR_RETRY", "1"))

EXPECTED_KEYS = [
    "summary",
    "top_pick",
    "why_top_pick",
    "tradeoffs_vs_second",
    "risk_notes",
    "next_questions",
]

ROUTE_KEYS = ["intent", "should_reply_directly", "reply"]


def _call_llm(user_input: str, max_output_tokens: Optional[int] = None) -> str:
    response = client.responses.create(
        model=MODEL,
        input=user_input,
        max_output_tokens=max_output_tokens or MAX_OUTPUT_TOKENS,
        timeout=TIMEOUT_SECONDS,
    )
    return response.output_text.strip()


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None


def _safe_fallback_summary(
    prefs: Dict[str, Any],
    result: Dict[str, Any],
    assumptions: Optional[List[str]],
) -> Dict[str, Any]:
    top = None
    top_list = result.get("top_3") or []
    if isinstance(top_list, list) and top_list:
        top = top_list[0].get("name") or top_list[0].get("model") or top_list[0].get("title")

    total = result.get("total_matches", 0)
    a = assumptions or []

    summary = (
        f"Found {total} match(es) in the current dataset."
        if total
        else "No matches found in the current dataset for the applied filters."
    )
    if a:
        summary += " I applied a fallback: " + " ".join(a)

    return {
        "summary": summary,
        "top_pick": top,
        "why_top_pick": [],
        "tradeoffs_vs_second": [],
        "risk_notes": [],
        "next_questions": [
            "Do you want to adjust any preferences (fuel/body/gearbox/priorities)?"
        ],
    }


def _validate_summary_schema(obj: Any) -> Tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "Not a JSON object (dict)."

    missing = [k for k in EXPECTED_KEYS if k not in obj]
    extra = [k for k in obj.keys() if k not in EXPECTED_KEYS]
    if missing:
        return False, f"Missing keys: {missing}"
    if extra:
        return False, f"Extra keys not allowed: {extra}"

    if not (obj["top_pick"] is None or isinstance(obj["top_pick"], str)):
        return False, "top_pick must be string or null."

    for k in ["why_top_pick", "tradeoffs_vs_second", "risk_notes", "next_questions"]:
        if not isinstance(obj[k], list) or any(not isinstance(x, str) for x in obj[k]):
            return False, f"{k} must be a list of strings."

    if not isinstance(obj["summary"], str):
        return False, "summary must be a string."

    return True, "ok"


def _validate_route_schema(obj: Any) -> Tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "Not a JSON object."

    missing = [k for k in ROUTE_KEYS if k not in obj]
    extra = [k for k in obj.keys() if k not in ROUTE_KEYS]
    if missing:
        return False, f"Missing keys: {missing}"
    if extra:
        return False, f"Extra keys not allowed: {extra}"

    if not isinstance(obj["intent"], str):
        return False, "intent must be a string."

    if not isinstance(obj["should_reply_directly"], bool):
        return False, "should_reply_directly must be a boolean."

    if not isinstance(obj["reply"], str):
        return False, "reply must be a string."

    return True, "ok"


def explain_recommendation(
    prefs: Dict[str, Any],
    result: Dict[str, Any],
    assumptions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    assumptions = assumptions or []

    prompt = f"""
You are CarFit. Return ONLY valid JSON. No markdown. No extra text.

STRICT RULES:
- Use ONLY the provided data (prefs, engine result, assumptions).
- Do NOT invent cars, issues, prices, or facts.
- If assumptions exist, mention them briefly in the summary.
- If total_matches == 0: say no matches because dataset has no cars matching the APPLIED filters.
- Mention risk_penalty only if it exists in the engine output.
- Keep it short and actionable.
- Treat result.filters_applied as the SOURCE OF TRUTH for what constraints were actually applied.
- Do NOT claim a constraint unless it appears in result.filters_applied.
- If a filter is null or missing in result.filters_applied, treat it as 'any' and do NOT state it as a constraint.

Return JSON with EXACTLY these keys:
{{
  "summary": "string",
  "top_pick": "string or null",
  "why_top_pick": ["string"],
  "tradeoffs_vs_second": ["string"],
  "risk_notes": ["string"],
  "next_questions": ["string"]
}}

USER PREFERENCES (json):
{json.dumps(prefs, ensure_ascii=False)}

ENGINE RESULT (json):
{json.dumps(result, ensure_ascii=False)}

ASSUMPTIONS (json):
{json.dumps(assumptions, ensure_ascii=False)}
"""

    try:
        text = _call_llm(prompt)
        obj = _extract_json(text)
        if obj is not None:
            ok, _ = _validate_summary_schema(obj)
            if ok:
                return obj
    except Exception:
        obj = None

    if REPAIR_RETRY > 0:
        repair_prompt = f"""
Your previous output was not valid per schema.

Return ONLY valid JSON with EXACTLY these keys:
{EXPECTED_KEYS}

No extra keys. No markdown.

USER PREFERENCES (json):
{json.dumps(prefs, ensure_ascii=False)}

ENGINE RESULT (json):
{json.dumps(result, ensure_ascii=False)}

ASSUMPTIONS (json):
{json.dumps(assumptions, ensure_ascii=False)}
"""
        try:
            text = _call_llm(repair_prompt)
            obj = _extract_json(text)
            if obj is not None:
                ok, _ = _validate_summary_schema(obj)
                if ok:
                    return obj
        except Exception:
            pass

    return _safe_fallback_summary(prefs, result, assumptions)


def route_conversation_turn(
    message: str,
    remembered_state: Optional[Dict[str, Any]] = None,
    merged_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Decide whether the current user turn should be handled conversationally by the LLM
    (small talk, thanks, capability question, vague social turn) or passed to the
    deterministic recommendation flow.

    Returns:
    {
      "intent": "social|capability|car_request|clarification_answer|correction|other",
      "should_reply_directly": bool,
      "reply": "..."
    }
    """
    remembered_state = remembered_state or {}
    merged_state = merged_state or {}
    message = (message or "").strip()

    if not message:
        return {"intent": "other", "should_reply_directly": False, "reply": ""}

    prompt = f"""
You are the conversation router for an AI car recommendation assistant called CarFit.

Your job:
- Decide what kind of user turn this is.
- If it is social/small-talk/capability-related, reply naturally and briefly.
- If it is a real preference update, clarification answer, correction, or recommendation request, DO NOT answer directly. Let the deterministic agent handle it.

Return ONLY valid JSON with EXACTLY these keys:
{{
  "intent": "social|capability|car_request|clarification_answer|correction|other",
  "should_reply_directly": true or false,
  "reply": "string"
}}

Rules:
- Use should_reply_directly = true for:
  - greetings
  - thanks / appreciation
  - capability questions like "what can you do?"
  - social turns like "sounds good", "okay thanks", "great"
  - vague meta conversation like "can you explain how this works?"
- Use should_reply_directly = false for:
  - car preferences
  - answers to follow-up questions
  - corrections to preferences
  - recommendation requests
- Keep direct replies warm, concise, and natural.
- If replying directly, keep it to 1 short paragraph, optionally inviting the user to continue.
- Never invent car facts in the direct reply.
- If the user says thanks after recommendations, reply politely and invite refinement if useful.

Remembered state:
{json.dumps(remembered_state, ensure_ascii=False)}

Current merged state:
{json.dumps(merged_state, ensure_ascii=False)}

User message:
{json.dumps(message, ensure_ascii=False)}
"""

    try:
        text = _call_llm(prompt, max_output_tokens=180)
        obj = _extract_json(text)
        if obj is not None:
            ok, _ = _validate_route_schema(obj)
            if ok:
                return obj
    except Exception:
        pass

    return {"intent": "other", "should_reply_directly": False, "reply": ""}