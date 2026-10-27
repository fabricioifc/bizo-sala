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

    # E-mail (Google Workspace com senha de app; em dev, Mailpit)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    email_remetente: str | None = None  # padrão: smtp_user
    email_intervalo_segundos: float = 1.0  # ritmo de envio (limite diário do Workspace)

    login_max_tentativas: int = 5
    login_janela_segundos: int = 15 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
