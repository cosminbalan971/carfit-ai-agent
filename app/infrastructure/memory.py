from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 30)))  

_r = Redis.from_url(REDIS_URL, decode_responses=True)


def _key(session_id: str) -> str:
    return f"carfit:session:{session_id}"


def get_or_create_session_id(session_id: Optional[str]) -> str:
    if session_id:
        try:
            if _r.exists(_key(session_id)):
                return session_id
        except Exception:
            pass

    new_id = uuid.uuid4().hex[:12]
    _r.set(_key(new_id), json.dumps({}), ex=TTL_SECONDS)
    return new_id


def load_state(session_id: str) -> Dict[str, Any]:
    raw = _r.get(_key(session_id))
    if not raw:
        return {}

    try:
        data = json.loads(raw)
        return dict(data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(session_id: str, state: Dict[str, Any]) -> None:
    _r.set(_key(session_id), json.dumps(dict(state)), ex=TTL_SECONDS)


def reset_session(session_id: str) -> None:
    _r.delete(_key(session_id))