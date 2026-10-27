"""Worker de envio de e-mails. Uso: python -m app.worker

Lê a fila de destinatários no banco e envia por SMTP (Gmail com senha de app em
produção; Mailpit em dev), um e-mail por vez, no ritmo de EMAIL_INTERVALO_SEGUNDOS.
"""

import logging
import smtplib
import time
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import Settings, get_settings
from app.core.db import SessionLocal
from app.models import Destinatario
from app.services.mensagens import ha_pendentes, montar_email, processar_fila

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bizo_sala.worker")

ESPERA_FILA_VAZIA = 5  # segundos


@contextmanager
def conexao_smtp(settings: Settings) -> Iterator[smtplib.SMTP]:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        yield smtp


def main() -> None:
    settings = get_settings()
    remetente = settings.email_remetente or settings.smtp_user or "bizo-sala@localhost"
    logger.info("Worker de e-mail iniciado (%s:%s)", settings.smtp_host, settings.smtp_port)

    while True:
        try:
            with SessionLocal() as db:
                if not ha_pendentes(db):
                    time.sleep(ESPERA_FILA_VAZIA)
                    continue
            with SessionLocal() as db, conexao_smtp(settings) as smtp:

                def enviar(destinatario: Destinatario) -> None:
                    smtp.send_message(montar_email(destinatario, remetente))
                    time.sleep(settings.email_intervalo_segundos)

                enviados, falhas = processar_fila(db, enviar)
            logger.info("Lote: %s enviado(s), %s falha(s)", enviados, falhas)
        except Exception:
            # SMTP fora do ar, credenciais erradas etc.: espera e tenta de novo
            logger.exception("Falha no worker de e-mail")
            time.sleep(30)


if __name__ == "__main__":
    main()
