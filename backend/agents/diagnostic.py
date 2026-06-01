"""Diagnostic agent implementation."""

from __future__ import annotations

import json
import re
from typing import Any


DIAGNOSTIC_SYSTEM_PROMPT = """
Voce e um sistema de analise tecnica de codigo. Sua funcao e EXCLUSIVAMENTE
 diagnostica - voce nao interage com o aluno.

Dado um bloco de codigo e a duvida de um estudante, voce deve:

1. Executar uma simulacao mental de execucao do codigo (trace linha a linha).
2. Identificar TODOS os erros: sintaxe, logica, semantica, boas praticas.
3. Identificar lacunas conceituais (conceitos que o aluno aparentemente nao domina).
4. Estimar o nivel de dificuldade: [basico | intermediario | avancado].

Retorne APENAS um JSON valido com a seguinte estrutura, sem texto adicional:
{
  "erros": [
    {
      "tipo": "logica|sintaxe|semantica|boas_praticas",
      "linha_aproximada": <numero ou null>,
      "descricao": "descricao tecnica interna do erro",
      "causa_raiz": "por que esse erro acontece"
    }
  ],
  "lacunas_conceituais": {
    "detectado": true|false,
    "conceitos": ["loop", "escopo de variavel", "etc"]
  },
  "nivel_dificuldade": "basico|intermediario|avancado",
  "frustacao_detectada": true|false
}
""".strip()


class DiagnosticAgent:
    """Analyze student code and return an internal JSON diagnostic."""

    def __init__(self, client: Any, model: str, max_tokens: int, temperature: float) -> None:
        """Store API client and inference parameters."""
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def analyze(self, code: str, question: str) -> dict[str, Any]:
        """Request a structured diagnostic and parse the returned JSON."""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": DIAGNOSTIC_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Codigo do aluno:\n"
                        f"```\n{code}\n```\n\n"
                        "Duvida do aluno:\n"
                        f"{question}"
                    ),
                },
            ],
        )
        raw_content = response.choices[0].message.content or ""
        return parse_json_payload(raw_content)


def parse_json_payload(raw_content: str) -> dict[str, Any]:
    """Parse JSON from model output, including fenced blocks when present."""
    text = raw_content.strip()
    if not text:
        raise ValueError("Diagnostic agent returned empty content.")

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            raise ValueError("Diagnostic agent returned non-JSON content.")
        return json.loads(json_match.group(0))
