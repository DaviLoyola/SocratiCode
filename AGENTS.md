# AGENTS.md — SocratiCode

## Como rodar o projeto localmente
1. cp .env.example .env  (preencher OPENAI_API_KEY)
2. pip install -r requirements.txt
3. python backend/main.py
4. Acesse http://localhost:5000

## Como rodar os testes
python -m pytest backend/tests/ -v

## Estrutura dos agentes (não alterar a lógica sem ler a Regra de Ouro)
- backend/agents/diagnostic.py  → Agente 1: diagnóstico CoT (retorna JSON interno)
- backend/agents/socratic.py    → Agente 2: tutor socrático (interação com o aluno)
- backend/agents/supervisor.py  → Agente 3: filtro de segurança pedagógica
- backend/pipeline.py           → orquestra os 3 agentes em sequência

## Modelos de IA
Definidos em backend/config.py e sobrescríveis via .env.
Variáveis: AGENT_DIAGNOSTIC_MODEL, AGENT_SOCRATIC_MODEL, AGENT_SUPERVISOR_MODEL.

## A Regra de Ouro — NUNCA VIOLAR
Nenhuma resposta entregue ao aluno pode conter o código corrigido e funcional
do problema dele. O Agente 3 (supervisor.py) rejeita automaticamente e solicita
reescrita se detectar isso. Qualquer alteração nos agentes deve preservar este comportamento.

## Persistência
- Sessões: data/sessions/ (arquivos locais, ignorados pelo git)
- Logs de rejeições do Supervisor: data/logs/

## Padrões de código
- Python com docstrings em todas as funções e classes
- Nomes de variáveis em inglês, descritivos (sem abreviações)
- Constantes e configurações sempre em config.py ou .env
- Nunca hardcodar a chave de API em nenhum arquivo
