"""Centralized configuration for the SocratiCode MVP."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
LOGS_DIR = DATA_DIR / "logs"


def get_env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean environment variable with safe parsing."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# [CODEX: DECISAO LIVRE] We use gpt-4o-mini in all agents for MVP cost efficiency.
AGENT_DIAGNOSTIC_MODEL = os.getenv("AGENT_DIAGNOSTIC_MODEL", "gpt-4o-mini")
AGENT_SOCRATIC_MODEL = os.getenv("AGENT_SOCRATIC_MODEL", "gpt-4o-mini")
AGENT_SUPERVISOR_MODEL = os.getenv("AGENT_SUPERVISOR_MODEL", "gpt-4o-mini")

AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "1000"))
AGENT_TEMPERATURE_SOCRATIC = float(os.getenv("AGENT_TEMPERATURE_SOCRATIC", "0.7"))
AGENT_TEMPERATURE_DIAGNOSTIC = float(os.getenv("AGENT_TEMPERATURE_DIAGNOSTIC", "0.2"))
AGENT_SUPERVISOR_MAX_RETRIES = int(os.getenv("AGENT_SUPERVISOR_MAX_RETRIES", "3"))

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change_me")
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = get_env_bool("DEBUG", False)

MAX_CODE_CHARS = 10000
MAX_QUESTION_CHARS = 2000

SUPERVISOR_FALLBACK_MESSAGE = (
    "Vamos reconstruir isso juntos sem pular etapas. "
    "Qual foi o ultimo comportamento observavel do seu codigo antes de quebrar?"
)

USER_FACING_API_ERROR_MESSAGE = (
    "O tutor esta temporariamente indisponivel. Tente novamente em instantes."
)
USER_FACING_QUOTA_ERROR_MESSAGE = (
    "Sua chave esta valida, mas o projeto esta sem cota/saldo na OpenAI API. "
    "Adicione creditos e tente novamente."
)
USER_FACING_AUTH_ERROR_MESSAGE = (
    "A chave OPENAI_API_KEY parece invalida ou expirada. Gere uma nova chave e atualize o .env."
)
USER_FACING_PERMISSION_ERROR_MESSAGE = (
    "A chave nao tem permissao para este projeto/modelo. Revise permissoes da chave no painel da OpenAI."
)
USER_FACING_MODEL_ERROR_MESSAGE = (
    "O modelo configurado nao esta disponivel para esta chave/projeto. Ajuste AGENT_*_MODEL no .env."
)

FRUSTRATION_KEYWORDS = [
    "me da a resposta",
    "me dá a resposta",
    "nao entendi nada",
    "não entendi nada",
    "so me fala",
    "só me fala",
    "desisti",
    "isso nao funciona",
    "isso não funciona",
    "me ajuda",
    "resposta pronta",
]

for required_dir in (DATA_DIR, SESSIONS_DIR, LOGS_DIR):
    required_dir.mkdir(parents=True, exist_ok=True)
