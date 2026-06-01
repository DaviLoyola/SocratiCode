"""Core pipeline orchestrating the three SocratiCode agents."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from . import config
from .logger import log_supervisor_rejection

try:
    from openai import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
    )
except Exception:  # pragma: no cover
    APIConnectionError = Exception
    APITimeoutError = Exception
    AuthenticationError = Exception
    BadRequestError = Exception
    NotFoundError = Exception
    PermissionDeniedError = Exception
    RateLimitError = Exception


DIAGNOSTIC_PARSE_ERROR_MESSAGE = (
    "Nao consegui interpretar o diagnostico interno agora. "
    "Pode reenviar sua duvida em instantes para tentarmos novamente?"
)


class PipelineResult(dict):
    """Typed dictionary-like container for pipeline outputs."""


class SocratiCodePipeline:
    """Run the diagnostic, Socratic, and supervisor agents in sequence."""

    def __init__(self, diagnostic_agent: Any, socratic_agent: Any, supervisor_agent: Any) -> None:
        """Store concrete agent implementations."""
        self.diagnostic_agent = diagnostic_agent
        self.socratic_agent = socratic_agent
        self.supervisor_agent = supervisor_agent

    def run_turn(
        self,
        session_id: str,
        code_input: str,
        question_input: str,
        conversation_history: list[dict[str, Any]],
    ) -> PipelineResult:
        """Process one tutoring turn and return a student-facing response."""
        code = sanitize_text(code_input)
        question = sanitize_text(question_input)
        validate_payload(code, question)

        try:
            diagnostic_result = self.diagnostic_agent.analyze(code, question)
        except ValueError:
            return PipelineResult(
                response=DIAGNOSTIC_PARSE_ERROR_MESSAGE,
                approved=False,
                used_fallback=True,
                metadata={"error_type": "diagnostic_parse_error"},
            )
        except Exception as error:
            return PipelineResult(
                response=map_upstream_exception_to_message(error),
                approved=False,
                used_fallback=True,
                metadata={"error_type": classify_upstream_exception(error)},
            )

        frustration_detected = detect_frustration(question)
        frustration_detected = frustration_detected or bool(
            diagnostic_result.get("frustacao_detectada", False)
        )

        rewrite_instruction: str | None = None
        max_retries = config.AGENT_SUPERVISOR_MAX_RETRIES

        for attempt in range(1, max_retries + 1):
            try:
                socratic_response = self.socratic_agent.generate_response(
                    code=code,
                    question=question,
                    diagnostic_result=diagnostic_result,
                    conversation_history=conversation_history,
                    frustration_detected=frustration_detected,
                    rewrite_instruction=rewrite_instruction,
                )
                supervisor_result = self.supervisor_agent.review(
                    student_code=code,
                    student_question=question,
                    draft_response=socratic_response,
                )
            except Exception as error:
                return PipelineResult(
                    response=map_upstream_exception_to_message(error),
                    approved=False,
                    used_fallback=True,
                    metadata={"error_type": classify_upstream_exception(error)},
                )

            if bool(supervisor_result.get("aprovado", False)):
                return PipelineResult(
                    response=socratic_response,
                    approved=True,
                    used_fallback=False,
                    metadata={
                        "attempts": attempt,
                        "frustration_detected": frustration_detected,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            log_supervisor_rejection(session_id=session_id, attempt=attempt, payload=supervisor_result)
            rewrite_instruction = supervisor_result.get("instrucao_correcao") or (
                "Reescreva de forma mais socratica, sem qualquer instrucao direta de correcao."
            )

        return PipelineResult(
            response=config.SUPERVISOR_FALLBACK_MESSAGE,
            approved=False,
            used_fallback=True,
            metadata={"error_type": "supervisor_max_retries"},
        )


def sanitize_text(value: str) -> str:
    """Remove control characters while preserving line breaks and tabs."""
    cleaned = value.replace("\x00", "")
    return re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\u024F]", "", cleaned).strip()


def validate_payload(code: str, question: str) -> None:
    """Validate required inputs and enforce anti-abuse size limits."""
    if not code and not question:
        raise ValueError("Codigo ou duvida sao obrigatorios.")

    if code and len(code) > config.MAX_CODE_CHARS:
        raise ValueError(f"Code must be at most {config.MAX_CODE_CHARS} characters.")

    if question and len(question) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"Question must be at most {config.MAX_QUESTION_CHARS} characters.")


def detect_frustration(question: str) -> bool:
    """Detect frustration or direct-answer requests using keyword heuristics."""
    normalized = question.casefold()
    return any(keyword in normalized for keyword in config.FRUSTRATION_KEYWORDS)


def classify_upstream_exception(error: Exception) -> str:
    """Return a coarse-grained category for upstream API errors."""
    message = str(error).lower()

    if isinstance(error, RateLimitError):
        if "insufficient_quota" in message or "exceeded your current quota" in message:
            return "insufficient_quota"
        return "rate_limited"
    if isinstance(error, AuthenticationError):
        return "invalid_api_key"
    if isinstance(error, PermissionDeniedError):
        return "permission_denied"
    if isinstance(error, (NotFoundError, BadRequestError)) and "model" in message:
        return "model_unavailable"
    if isinstance(error, (APIConnectionError, APITimeoutError, TimeoutError, ConnectionError)):
        return "upstream_unavailable"

    return "upstream_unavailable"


def map_upstream_exception_to_message(error: Exception) -> str:
    """Convert upstream exceptions into user-friendly messages."""
    category = classify_upstream_exception(error)

    if category == "insufficient_quota":
        return config.USER_FACING_QUOTA_ERROR_MESSAGE
    if category == "invalid_api_key":
        return config.USER_FACING_AUTH_ERROR_MESSAGE
    if category == "permission_denied":
        return config.USER_FACING_PERMISSION_ERROR_MESSAGE
    if category == "model_unavailable":
        return config.USER_FACING_MODEL_ERROR_MESSAGE

    return config.USER_FACING_API_ERROR_MESSAGE
