from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from app.core.config import get_settings

COOKIE_SESSAO = "bizo_sessao"
_ALGORITMO = "HS256"
_hasher = PasswordHasher()


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha_hash: str, senha: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except VerificationError:
        return False


def criar_token(usuario_id: int) -> str:
    settings = get_settings()
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.sessao_expira_minutos),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITMO)


def ler_token(token: str) -> int | None:
    """Retorna o id do usuário do token, ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[_ALGORITMO])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
