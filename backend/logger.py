"""Utilities for logging supervisor rejections."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config


def log_supervisor_rejection(session_id: str, attempt: int, payload: dict[str, Any]) -> None:
    """Append a supervisor rejection entry to a JSON lines log file."""
    log_file: Path = config.LOGS_DIR / "supervisor_rejections.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "attempt": attempt,
        "payload": payload,
    }
    with log_file.open("a", encoding="utf-8") as handler:
        handler.write(json.dumps(entry, ensure_ascii=False) + "\n")
