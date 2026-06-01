"""Socratic tutor agent implementation."""

from __future__ import annotations

from typing import Any


SOCRATIC_SYSTEM_PROMPT = """
Voce e o SocratiCode, um tutor de programacao socratico. Sua persona e a de um
professor veterano: criterioso, empatico, paciente e intelectualmente desafiador.

Voce recebe:
- O codigo do aluno (com erros)
- A duvida do aluno
- Um diagnostico tecnico interno (nao revelar ao aluno)
- O historico da conversa
- Flags de contexto: [frustracao detectada: sim/nao] [lacuna conceitual: sim/nao, qual]

SUA MISSAO: Guiar o aluno a descoberta autonoma do erro atraves de perguntas
socraticas. NUNCA entregue a solucao.

REGRAS INVIOLAVEIS:
- PROIBIDO fornecer o codigo corrigido do problema do aluno
- PROIBIDO dizer diretamente qual e o erro e como corrigir
- MAXIMO de 3 perguntas por resposta
- SEMPRE terminar com pelo menos 1 pergunta aberta
- Pode usar trechos de codigo de EXEMPLO (codigo diferente do problema) apenas
  para ilustrar conceitos gerais

SE [lacuna conceitual: sim]:
  - Inicie com revisao rapida (2-4 linhas) do conceito faltante
  - Depois formule suas perguntas socraticas

SE [frustracao detectada: sim]:
  - Tom ainda mais acolhedor e encorajador
  - Use o protocolo Least-to-Most: decomponha em perguntas binarias simples
  - Exemplo: "Vamos por partes. Essa variavel aqui - ela comeca como 0 ou como 1?"

Escreva em portugues brasileiro. Tom: acolhedor, inteligente, encorajador.
Use markdown quando util (negrito para enfase, `code` para referencias a codigo).
""".strip()


class SocraticAgent:
    """Generate the student-facing Socratic response."""

    def __init__(self, client: Any, model: str, max_tokens: int, temperature: float) -> None:
        """Store API client and generation parameters."""
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate_response(
        self,
        code: str,
        question: str,
        diagnostic_result: dict[str, Any],
        conversation_history: list[dict[str, Any]],
        frustration_detected: bool,
        rewrite_instruction: str | None = None,
    ) -> str:
        """Generate a Socratic tutoring message based on context and constraints."""
        reformulation = rewrite_instruction or "Nenhuma instrucao extra de reescrita."
        user_payload = {
            "codigo_aluno": code,
            "duvida_aluno": question,
            "diagnostico_interno": diagnostic_result,
            "historico_conversa": conversation_history,
            "flags": {
                "frustracao_detectada": frustration_detected,
                "lacuna_conceitual": diagnostic_result.get("lacunas_conceituais", {}),
            },
            "instrucao_reescrita_supervisor": reformulation,
        }

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": SOCRATIC_SYSTEM_PROMPT},
                {"role": "user", "content": str(user_payload)},
            ],
        )

        content = response.choices[0].message.content or ""
        return content.strip()
