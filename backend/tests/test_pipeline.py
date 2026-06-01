"""Mocked tests for SocratiCode pipeline behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend import config
from backend.pipeline import DIAGNOSTIC_PARSE_ERROR_MESSAGE, SocratiCodePipeline


def build_pipeline() -> tuple[SocratiCodePipeline, MagicMock, MagicMock, MagicMock]:
    """Create a pipeline with mocked agents for deterministic tests."""
    diagnostic_agent = MagicMock()
    socratic_agent = MagicMock()
    supervisor_agent = MagicMock()
    pipeline = SocratiCodePipeline(diagnostic_agent, socratic_agent, supervisor_agent)
    return pipeline, diagnostic_agent, socratic_agent, supervisor_agent


def valid_diagnostic() -> dict:
    """Return a standard diagnostic payload used across tests."""
    return {
        "erros": [
            {
                "tipo": "logica",
                "linha_aproximada": 3,
                "descricao": "loop nao atualiza a variavel",
                "causa_raiz": "incremento ausente",
            }
        ],
        "lacunas_conceituais": {"detectado": True, "conceitos": ["loop"]},
        "nivel_dificuldade": "basico",
        "frustacao_detectada": False,
    }


def test_pipeline_complete_approved() -> None:
    """Case 1: pipeline returns first approved Socratic answer."""
    pipeline, diagnostic_agent, socratic_agent, supervisor_agent = build_pipeline()
    diagnostic_agent.analyze.return_value = valid_diagnostic()
    socratic_agent.generate_response.return_value = "Vamos refletir: o que muda no contador?"
    supervisor_agent.review.return_value = {"aprovado": True, "motivo": None, "instrucao_correcao": None}

    result = pipeline.run_turn("session-a", "print('oi')", "Nao funciona", [])

    assert result["response"] == "Vamos refletir: o que muda no contador?"
    assert result["approved"] is True
    assert result["used_fallback"] is False


def test_supervisor_rejects_then_approves() -> None:
    """Case 2: supervisor rejects twice and approves on third attempt."""
    pipeline, diagnostic_agent, socratic_agent, supervisor_agent = build_pipeline()
    diagnostic_agent.analyze.return_value = valid_diagnostic()
    socratic_agent.generate_response.side_effect = [
        "Resposta 1",
        "Resposta 2",
        "Resposta 3",
    ]
    supervisor_agent.review.side_effect = [
        {"aprovado": False, "motivo": "direto demais", "instrucao_correcao": "Reformule com perguntas."},
        {"aprovado": False, "motivo": "ainda direto", "instrucao_correcao": "Nao entregue passos prontos."},
        {"aprovado": True, "motivo": None, "instrucao_correcao": None},
    ]

    with patch("backend.pipeline.log_supervisor_rejection") as rejection_logger:
        result = pipeline.run_turn("session-b", "x=1", "me ajuda", [])

    assert result["response"] == "Resposta 3"
    assert socratic_agent.generate_response.call_count == 3
    assert rejection_logger.call_count == 2


def test_fallback_after_three_rejections() -> None:
    """Case 3: fallback is returned after max supervisor rejections."""
    pipeline, diagnostic_agent, socratic_agent, supervisor_agent = build_pipeline()
    diagnostic_agent.analyze.return_value = valid_diagnostic()
    socratic_agent.generate_response.side_effect = ["A", "B", "C"]
    supervisor_agent.review.side_effect = [
        {"aprovado": False, "motivo": "1", "instrucao_correcao": "corrigir"},
        {"aprovado": False, "motivo": "2", "instrucao_correcao": "corrigir"},
        {"aprovado": False, "motivo": "3", "instrucao_correcao": "corrigir"},
    ]

    with patch("backend.pipeline.log_supervisor_rejection") as rejection_logger:
        result = pipeline.run_turn("session-c", "x=1", "desisti", [])

    assert result["response"] == config.SUPERVISOR_FALLBACK_MESSAGE
    assert result["used_fallback"] is True
    assert rejection_logger.call_count == 3


def test_malformed_diagnostic_json() -> None:
    """Case 4: malformed diagnostic output returns graceful user message."""
    pipeline, diagnostic_agent, _, _ = build_pipeline()
    diagnostic_agent.analyze.side_effect = ValueError("non-json diagnostic")

    result = pipeline.run_turn("session-d", "x=1", "duvida", [])

    assert result["response"] == DIAGNOSTIC_PARSE_ERROR_MESSAGE
    assert result["used_fallback"] is True
    assert result["metadata"]["error_type"] == "diagnostic_parse_error"


def test_api_unavailable_exception() -> None:
    """Case 5: upstream exception returns friendly temporary-unavailable message."""
    pipeline, diagnostic_agent, _, _ = build_pipeline()
    diagnostic_agent.analyze.side_effect = TimeoutError("connection timeout")

    result = pipeline.run_turn("session-e", "x=1", "duvida", [])

    assert result["response"] == config.USER_FACING_API_ERROR_MESSAGE
    assert result["used_fallback"] is True
    assert result["metadata"]["error_type"] == "upstream_unavailable"


def test_pipeline_accepts_question_only() -> None:
    """The pipeline should accept a question without code."""
    pipeline, diagnostic_agent, socratic_agent, supervisor_agent = build_pipeline()
    diagnostic_agent.analyze.return_value = valid_diagnostic()
    socratic_agent.generate_response.return_value = "Vamos refletir sem codigo especifico."
    supervisor_agent.review.return_value = {"aprovado": True, "motivo": None, "instrucao_correcao": None}

    result = pipeline.run_turn("session-f", "", "Me ajuda com esse erro", [])

    assert result["response"] == "Vamos refletir sem codigo especifico."
    assert result["approved"] is True
    assert result["used_fallback"] is False


def test_pipeline_accepts_code_only() -> None:
    """The pipeline should accept code without a separate question."""
    pipeline, diagnostic_agent, socratic_agent, supervisor_agent = build_pipeline()
    diagnostic_agent.analyze.return_value = valid_diagnostic()
    socratic_agent.generate_response.return_value = "Vamos analisar seu codigo e pensar sobre o comportamento."
    supervisor_agent.review.return_value = {"aprovado": True, "motivo": None, "instrucao_correcao": None}

    result = pipeline.run_turn("session-g", "print('oi')", "", [])

    assert result["response"] == "Vamos analisar seu codigo e pensar sobre o comportamento."
    assert result["approved"] is True
    assert result["used_fallback"] is False
