"""Supervisor agent implementation."""

from __future__ import annotations

import json
import re
from typing import Any


SUPERVISOR_SYSTEM_PROMPT = """
Voce e um supervisor pedagogico. Analise a resposta abaixo de um tutor de
programacao e determine se ela viola a Regra de Ouro.

REGRA DE OURO: E PROIBIDO fornecer ao aluno o codigo corrigido e funcional
que resolve o problema descrito. A resposta deve ser socratica: perguntas,
orientacoes conceituais, exemplos com codigo diferente do problema.

APROVADO se a resposta contem:
- Perguntas reflexivas sobre o codigo do aluno
- Revisao de conceitos teoricos
- Exemplos com codigo DIFERENTE do problema
- Orientacoes gerais de depuracao

REPROVADO se a resposta contem:
- Bloco de codigo que corrige diretamente o bug do aluno
- Instrucao explicita do tipo "troque X por Y no seu codigo"
- A solucao completa funcional para o problema

Retorne APENAS um JSON valido:
{
  "aprovado": true|false,
  "motivo": "explicacao se reprovado, null se aprovado",
  "instrucao_correcao": "instrucao para o Agente Socratico reescrever, null se aprovado"
}
""".strip()


class SupervisorAgent:
    """Review Socratic drafts and block direct solutions."""

    def __init__(self, client: Any, model: str, max_tokens: int = 400) -> None:
        """Store API client and model settings."""
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

    def review(self, student_code: str, student_question: str, draft_response: str) -> dict[str, Any]:
        """Classify a Socratic draft as approved or rejected."""
        payload = {
            "codigo_aluno": student_code,
            "duvida_aluno": student_question,
            "rascunho_tutor": draft_response,
        }

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
                {"role": "user", "content": str(payload)},
            ],
        )

        content = response.choices[0].message.content or ""
        return parse_supervisor_json(content)


def parse_supervisor_json(raw_content: str) -> dict[str, Any]:
    """Parse supervisor JSON output from plain or fenced text."""
    text = raw_content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("Supervisor returned invalid JSON.") from error

    if "aprovado" not in payload:
        raise ValueError("Supervisor JSON missing required field 'aprovado'.")

    if payload["aprovado"]:
        payload.setdefault("motivo", None)
        payload.setdefault("instrucao_correcao", None)

    return payload
