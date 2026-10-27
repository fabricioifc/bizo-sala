"""Comandos administrativos. Uso: python -m app.cli <comando>

usuario-inicial    cria o usuário a partir de ADMIN_* do .env, se o banco não tiver nenhum
                   (roda automaticamente ao iniciar o container da API)
redefinir-usuario  atualiza e-mail, nome e senha do usuário existente com ADMIN_* do .env
"""

import argparse
import sys

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services.usuarios import garantir_usuario_inicial, redefinir_usuario


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("comando", choices=["usuario-inicial", "redefinir-usuario"])
    comando = parser.parse_args().comando

    settings = get_settings()
    if not (settings.admin_email and settings.admin_senha):
        print("ADMIN_EMAIL e ADMIN_SENHA não definidos; nada a fazer.")
        return 0 if comando == "usuario-inicial" else 1

    with SessionLocal() as db:
        if comando == "usuario-inicial":
            if garantir_usuario_inicial(
                db, settings.admin_email, settings.admin_senha, settings.admin_nome
            ):
                print(f"Usuário inicial criado: {settings.admin_email}")
        else:
            usuario = redefinir_usuario(
                db, settings.admin_email, settings.admin_senha, settings.admin_nome
            )
            print(f"Usuário atualizado: {usuario.email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
