# SocratiCode MVP

![Status](https://img.shields.io/badge/status-MVP-blue)

## O que é o SocratiCode
O SocratiCode é um tutor inteligente de programação orientado pelo método socrático.
Ele não entrega a solução pronta: conduz o aluno com perguntas estratégicas para
estimular raciocínio, depuração e autonomia. A arquitetura usa três agentes encadeados
(diagnóstico, tutoria socrática e supervisão pedagógica) para proteger a Regra de Ouro.

## Como funciona
```text
[ALUNO]
  ├── Campo 1: Código com erro
  └── Campo 2: Dúvida em texto
          │
          ▼
  ┌───────────────────┐
  │ AGENTE 1          │ Diagnóstico interno estruturado
  └────────┬──────────┘
           ▼
  ┌───────────────────┐
  │ AGENTE 2          │ Resposta socrática ao aluno
  └────────┬──────────┘
           ▼
  ┌───────────────────┐
  │ AGENTE 3          │ Aprova/Reprova (loop até 3x)
  └────────┬──────────┘
           ▼
      [Resposta final]
```

## Instalação e execução local
1. `git clone <repo>`
2. `cd socraticode`
3. `cp .env.example .env` e preencha `OPENAI_API_KEY`
4. `pip install -r requirements.txt`
5. `python backend/main.py`

## Como rodar testes
```bash
pip install pytest
python -m pytest backend/tests/ -v
```

## Deploy em produção (Render)
1. Suba o repositório no GitHub.
2. No Render, crie um novo serviço `Web Service` apontando para o repo.
3. Defina `Build Command`: `pip install -r requirements.txt`.
4. Defina `Start Command`: `python backend/main.py`.
5. Adicione as variáveis do `.env.example` no painel de ambiente do Render.

## Variáveis de ambiente
| Variável | Descrição | Obrigatória |
|---|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI API | Sim |
| `AGENT_DIAGNOSTIC_MODEL` | Modelo do Agente 1 | Sim |
| `AGENT_SOCRATIC_MODEL` | Modelo do Agente 2 | Sim |
| `AGENT_SUPERVISOR_MODEL` | Modelo do Agente 3 | Sim |
| `AGENT_MAX_TOKENS` | Limite de saída por chamada | Não |
| `AGENT_TEMPERATURE_SOCRATIC` | Temperatura do tutor socrático | Não |
| `AGENT_TEMPERATURE_DIAGNOSTIC` | Temperatura do diagnóstico | Não |
| `AGENT_SUPERVISOR_MAX_RETRIES` | Máximo de tentativas de reescrita | Não |
| `SESSION_SECRET_KEY` | Segredo da sessão Flask | Sim |
| `SESSION_EXPIRY_HOURS` | Tempo de expiração da sessão | Não |
| `HOST` | Host de execução | Não |
| `PORT` | Porta de execução | Não |
| `DEBUG` | Modo debug | Não |

## Estrutura do projeto
```text
socraticode/
├── backend/
│   ├── main.py               # Servidor Flask e APIs
│   ├── config.py             # Configurações centrais e constantes
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── diagnostic.py     # Agente 1 (diagnóstico CoT)
│   │   ├── socratic.py       # Agente 2 (tutor socrático)
│   │   └── supervisor.py     # Agente 3 (supervisor pedagógico)
│   ├── pipeline.py           # Orquestração e loop de aprovação
│   ├── session.py            # Persistência de sessão em arquivo
│   ├── logger.py             # Log de reprovações do supervisor
│   └── tests/
│       └── test_pipeline.py  # Testes com mock da API
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── assets/
├── data/
│   ├── sessions/             # Persistência de histórico por usuário
│   └── logs/                 # Logs de rejeição do supervisor
├── .env.example
├── .gitignore
├── AGENTS.md
├── Procfile
├── README.md
└── requirements.txt
```

## A Regra de Ouro
Nenhuma resposta entregue ao aluno pode conter o código corrigido e funcional do
problema dele. O Agente 3 aplica esse filtro automaticamente e força reescrita do
Agente 2 em caso de violação, com fallback seguro após 3 tentativas.

## Roadmap futuro
- RAG de erros e padrões pedagógicos
- Integração com linters e execução segura de snippets
- Suporte multiusuário com autenticação
- Métricas de aprendizagem por sessão

## Licença
MIT
