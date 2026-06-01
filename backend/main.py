"""Flask entrypoint for the SocratiCode MVP."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request, send_from_directory
from openai import OpenAI

load_dotenv()

from backend import config, session
from backend.agents.diagnostic import DiagnosticAgent
from backend.agents.socratic import SocraticAgent
from backend.agents.supervisor import SupervisorAgent
from backend.pipeline import SocratiCodePipeline


FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/frontend")
app.secret_key = config.SESSION_SECRET_KEY


def build_pipeline() -> SocratiCodePipeline:
    """Build and return a pipeline with concrete OpenAI-powered agents."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    diagnostic_agent = DiagnosticAgent(
        client=client,
        model=config.AGENT_DIAGNOSTIC_MODEL,
        max_tokens=config.AGENT_MAX_TOKENS,
        temperature=config.AGENT_TEMPERATURE_DIAGNOSTIC,
    )
    socratic_agent = SocraticAgent(
        client=client,
        model=config.AGENT_SOCRATIC_MODEL,
        max_tokens=config.AGENT_MAX_TOKENS,
        temperature=config.AGENT_TEMPERATURE_SOCRATIC,
    )
    supervisor_agent = SupervisorAgent(
        client=client,
        model=config.AGENT_SUPERVISOR_MODEL,
    )
    return SocratiCodePipeline(diagnostic_agent, socratic_agent, supervisor_agent)


pipeline = build_pipeline()


def ensure_session() -> tuple[str, dict[str, Any], bool]:
    """Resolve session from cookie and return (id, payload, is_new_cookie)."""
    session_id = request.cookies.get("socraticode_session_id")
    is_new_cookie = False

    if not session_id:
        session_id = session.generate_session_id()
        session_payload = session.create_empty_session()
        session.save_session(session_id, session_payload)
        return session_id, session_payload, True

    session_payload = session.load_session(session_id)
    if session.is_session_expired(session_payload):
        session_payload = session.clear_session(session_id)

    return session_id, session_payload, is_new_cookie


def attach_session_cookie(response: Any, session_id: str) -> Any:
    """Attach or refresh the session cookie in HTTP responses."""
    expires = datetime.now(timezone.utc) + timedelta(hours=config.SESSION_EXPIRY_HOURS)
    response.set_cookie(
        "socraticode_session_id",
        session_id,
        httponly=True,
        secure=False,
        samesite="Lax",
        expires=expires,
    )
    return response


@app.get("/")
def home() -> Any:
    """Serve the main frontend entrypoint."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/history")
def get_history() -> Any:
    """Return persisted chat history for the active session."""
    session_id, session_payload, _ = ensure_session()
    response = make_response(
        jsonify(
            {
                "session_id": session_id,
                "messages": session_payload.get("messages", []),
            }
        )
    )
    return attach_session_cookie(response, session_id)


@app.post("/api/analyze")
def analyze() -> Any:
    """Run one SocratiCode tutoring turn for the submitted code and question."""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    question = payload.get("question", "")

    if not isinstance(code, str) or not isinstance(question, str):
        return jsonify({"error": "Payload invalido. Informe texto em code e question."}), 400

    if not code and not question:
        return jsonify({"error": "Envie codigo ou duvida."}), 400

    session_id, session_payload, _ = ensure_session()
    history = session_payload.get("messages", [])

    try:
        result = pipeline.run_turn(
            session_id=session_id,
            code_input=code,
            question_input=question,
            conversation_history=history,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    user_message = {
        "role": "user",
        "content": question,
        "code": code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    tutor_message = {
        "role": "assistant",
        "content": result["response"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": result.get("metadata", {}),
    }

    updated_payload = session.append_messages(session_id, user_message, tutor_message)
    response = make_response(
        jsonify(
            {
                "reply": result["response"],
                "approved": result.get("approved", False),
                "used_fallback": result.get("used_fallback", False),
                "metadata": result.get("metadata", {}),
                "messages": updated_payload.get("messages", []),
            }
        )
    )
    return attach_session_cookie(response, session_id)


@app.post("/api/new-conversation")
def new_conversation() -> Any:
    """Clear the active session history while keeping the same session id."""
    session_id, _, _ = ensure_session()
    cleared = session.clear_session(session_id)
    response = make_response(jsonify({"messages": cleared.get("messages", [])}))
    return attach_session_cookie(response, session_id)


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
