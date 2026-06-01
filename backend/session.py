"""Session persistence and conversation history management."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from . import config


def now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def generate_session_id() -> str:
    """Generate a random session identifier."""
    return uuid4().hex


def get_session_path(session_id: str) -> Path:
    """Return the file path used to persist one session."""
    return config.SESSIONS_DIR / f"{session_id}.json"


def create_empty_session() -> dict[str, Any]:
    """Create a new empty session payload."""
    timestamp = now_iso()
    return {
        "created_at": timestamp,
        "updated_at": timestamp,
        "messages": [],
    }


def load_session(session_id: str) -> dict[str, Any]:
    """Load a session from disk or create a new structure when absent."""
    session_path = get_session_path(session_id)
    if not session_path.exists():
        return create_empty_session()

    with session_path.open("r", encoding="utf-8") as handler:
        payload = json.load(handler)

    if "messages" not in payload or not isinstance(payload["messages"], list):
        payload["messages"] = []
    return payload


def save_session(session_id: str, session_payload: dict[str, Any]) -> None:
    """Persist a full session payload to disk."""
    session_payload["updated_at"] = now_iso()
    session_path = get_session_path(session_id)
    with session_path.open("w", encoding="utf-8") as handler:
        json.dump(session_payload, handler, ensure_ascii=False, indent=2)


def append_messages(
    session_id: str,
    user_message: dict[str, Any],
    tutor_message: dict[str, Any],
) -> dict[str, Any]:
    """Append user and tutor messages to a session and persist it."""
    session_payload = load_session(session_id)
    session_payload["messages"].append(user_message)
    session_payload["messages"].append(tutor_message)
    save_session(session_id, session_payload)
    return session_payload


def clear_session(session_id: str) -> dict[str, Any]:
    """Reset a session conversation history while preserving the same id."""
    payload = create_empty_session()
    save_session(session_id, payload)
    return payload


def is_session_expired(session_payload: dict[str, Any]) -> bool:
    """Check if session timestamp is older than configured expiry window."""
    created_at = session_payload.get("created_at")
    if not isinstance(created_at, str):
        return True

    try:
        created_dt = datetime.fromisoformat(created_at)
    except ValueError:
        return True

    expiry = created_dt + timedelta(hours=config.SESSION_EXPIRY_HOURS)
    return datetime.now(timezone.utc) > expiry
