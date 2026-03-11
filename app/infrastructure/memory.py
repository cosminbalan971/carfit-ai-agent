from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

from redis import Redis

REDIS_URL = os.getenv("REDIS_URL")

try:
    if REDIS_URL:
        _r = Redis.from_url(REDIS_URL, decode_responses=True)
        _r.ping()
    else:
        raise Exception("Redis not configured")
except Exception:
    _r = None
    _memory_store = {}

TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 30)))


def _key(session_id: str) -> str:
    return f"carfit:session:{session_id}"


def get_or_create_session_id(session_id: Optional[str]) -> str:
    if session_id:
        try:
            if _r:
                if _r.exists(_key(session_id)):
                    return session_id
            else:
                if session_id in _memory_store:
                    return session_id
        except Exception:
            pass

    new_id = uuid.uuid4().hex[:12]

    if _r:
        _r.set(_key(new_id), json.dumps({}), ex=TTL_SECONDS)
    else:
        _memory_store[new_id] = {}

    return new_id


def load_state(session_id: str) -> Dict[str, Any]:
    if _r:
        raw = _r.get(_key(session_id))
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}
    else:
        return _memory_store.get(session_id, {})


def save_state(session_id: str, state: Dict[str, Any]) -> None:
    if _r:
        _r.set(_key(session_id), json.dumps(state), ex=TTL_SECONDS)
    else:
        _memory_store[session_id] = state


def reset_session(session_id: Optional[str]) -> Dict[str, Any]:
    if session_id:
        if _r:
            _r.delete(_key(session_id))
        else:
            _memory_store.pop(session_id, None)

    new_id = uuid.uuid4().hex[:12]

    if _r:
        _r.set(_key(new_id), json.dumps({}), ex=TTL_SECONDS)
    else:
        _memory_store[new_id] = {}

    return {"session_id": new_id}