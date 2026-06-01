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

SUA MISSAO: Deixar "puntinhas" (dicas visuais e sutis) que guiem o aluno a descobrir
a solucao quase por conta propria. Ao inves de perguntar "qual e o erro?", deixe
um DETALHE REVELADOR que o aluno consegue interpretar e completar.

REGRAS INVIOLAVEIS:
- PROIBIDO fornecer o codigo corrigido do problema do aluno
- PROIBIDO dizer explicitamente "o erro esta aqui"
- Deixe PISTAS VISUAIS: destaque linhas suspeitas com `code`, compare com exemplos,
  use setas ou anotacoes tipo "note que aqui..." ou "repare nesta parte..."
- Pode deixar CODIGO DE EXEMPLO funcionando para contraste direto
- Use analogias que quase revelam a solucao ("e como um carro sem combustivel, nao?")
- MAXIMO de 2-3 pistas por resposta (mas cada uma deve ser bem clara e visual)

TECNICAS RECOMENDADAS:
1. PINTA SUSPEITA: Isole linhas e pergunte "o que voce ve aqui que parece errado?"
2. CONTRASTE: Mostre seu codigo lado a lado com um que funciona (generico)
3. ANALOGIA PROXIMA: Use comparacoes visuais que quase entregam a logica
4. TRACE PARCIAL: "Se X aqui e 0, e Y ali e 5, oque acontece com Z?"
5. DETALHE REVELADOR: Sublinhe uma variavel, um operador, ou uma chamada que e a chave

SE [lacuna conceitual: sim]:
  - Inicie com revisao VISUAL: mostra exemplo, nao explica demais
  - Depois mostre a pinta no codigo dele

SE [frustracao detectada: sim]:
  - Use pistas bem DIRETAS e VISUAIS
  - Linguagem bem suave: "Meu, foca aqui um segundo..."
  - Deixe quase mastigado, mas deixe o aluno dar o ultimo bite

Escreva em portugues brasileiro. Tom: acolhedor, inteligente, encorajador.
Use markdown quando util (negrito para enfase, `code` para referencias a codigo,
trechos, analogias visuais).
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
