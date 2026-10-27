from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str
    secret_key: str
    sessao_expira_minutos: int = 60 * 24 * 7
    cookie_secure: bool = True

    # Usuário criado na primeira inicialização, se o banco não tiver nenhum
    admin_email: str | None = None
    admin_senha: str | None = None
    admin_nome: str = "Professor"

    login_max_tentativas: int = 5
    login_janela_segundos: int = 15 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
