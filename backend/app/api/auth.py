from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import DbSession, UsuarioAtual
from app.core.config import get_settings
from app.core.limite_login import LimiteTentativas
from app.core.security import COOKIE_SESSAO, criar_token
from app.schemas.auth import LoginEntrada, UsuarioSaida
from app.services.usuarios import autenticar

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()
limite_login = LimiteTentativas(_settings.login_max_tentativas, _settings.login_janela_segundos)


@router.post("/login", response_model=UsuarioSaida)
def login(dados: LoginEntrada, request: Request, response: Response, db: DbSession) -> UsuarioSaida:
    chave = request.client.host if request.client else "desconhecido"
    if limite_login.bloqueado(chave):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Aguarde alguns minutos."
        )

    usuario = autenticar(db, dados.email, dados.senha)
    if usuario is None:
        limite_login.registrar_falha(chave)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")

    limite_login.resetar(chave)
    response.set_cookie(
        COOKIE_SESSAO,
        criar_token(usuario.id),
        max_age=_settings.sessao_expira_minutos * 60,
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="strict",
        path="/api",
    )
    return UsuarioSaida.model_validate(usuario)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_SESSAO, path="/api")


@router.get("/me", response_model=UsuarioSaida)
def me(usuario: UsuarioAtual) -> UsuarioSaida:
    return UsuarioSaida.model_validate(usuario)
