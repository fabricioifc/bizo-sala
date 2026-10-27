"""Mensagens por e-mail para estudantes e responsáveis.

A mensagem vira uma fila de destinatários (um e-mail personalizado para cada, sem
expor a lista). O worker (`python -m app.worker`) envia em ritmo controlado e tenta de
novo em caso de falha.
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Destinatario,
    Estudante,
    Mensagem,
    Nivel,
    StatusEnvio,
    TipoDestinatario,
    Turma,
)
from app.services.erros import ErroDeNegocio

MAX_TENTATIVAS = 3
CAMPOS = ("primeiro_nome", "nome", "disciplina", "turma")
_PADRAO_CAMPO = re.compile(r"\{(" + "|".join(CAMPOS) + r")\}")


def personalizar(texto: str, contexto: dict[str, str]) -> str:
    """Troca {nome}, {primeiro_nome}, {disciplina} e {turma}; outras chaves ficam como estão."""
    return _PADRAO_CAMPO.sub(lambda m: contexto[m.group(1)], texto)


@dataclass(frozen=True)
class DestinatarioPrevio:
    estudante: Estudante
    tipo: TipoDestinatario
    email: str


@dataclass(frozen=True)
class Selecao:
    destinatarios: list[DestinatarioPrevio]
    sem_email: list[Estudante]


def selecionar(
    turma: Turma,
    estudante_ids: Sequence[int] | None,
    incluir_estudantes: bool,
    incluir_responsaveis: bool,
) -> Selecao:
    """Estudantes ativos da turma (ou os escolhidos) e seus e-mails."""
    if not incluir_estudantes and not incluir_responsaveis:
        raise ErroDeNegocio("Escolha enviar aos estudantes, aos responsáveis ou a ambos")
    if incluir_responsaveis and turma.curso.nivel != Nivel.EMI:
        raise ErroDeNegocio("Envio a responsáveis só se aplica ao ensino médio integrado")

    matriculados = {e.id: e for e in turma.estudantes}
    if estudante_ids is None:
        escolhidos = [e for e in turma.estudantes if e.ativo]
    else:
        fora = [i for i in estudante_ids if i not in matriculados]
        if fora:
            raise ErroDeNegocio("Há estudantes que não estão matriculados na turma")
        escolhidos = [matriculados[i] for i in dict.fromkeys(estudante_ids)]

    destinatarios: list[DestinatarioPrevio] = []
    sem_email: list[Estudante] = []
    for e in escolhidos:
        enderecos = []
        if incluir_estudantes and e.email:
            enderecos.append((TipoDestinatario.ESTUDANTE, e.email))
        if incluir_responsaveis and e.email_responsavel:
            enderecos.append((TipoDestinatario.RESPONSAVEL, e.email_responsavel))
        if not enderecos:
            sem_email.append(e)
        destinatarios.extend(DestinatarioPrevio(e, tipo, email) for tipo, email in enderecos)
    return Selecao(destinatarios, sem_email)


def contexto(estudante: Estudante, turma: Turma) -> dict[str, str]:
    return {
        "nome": estudante.nome,
        "primeiro_nome": estudante.nome.split()[0],
        "disciplina": turma.disciplina,
        "turma": turma.nome,
    }


def criar_mensagem(
    db: Session, turma: Turma, selecao: Selecao, assunto: str, corpo: str
) -> Mensagem:
    if not selecao.destinatarios:
        raise ErroDeNegocio("Nenhum destinatário com e-mail cadastrado")
    mensagem = Mensagem(turma_id=turma.id, assunto=assunto, corpo=corpo)
    for d in selecao.destinatarios:
        ctx = contexto(d.estudante, turma)
        mensagem.destinatarios.append(
            Destinatario(
                estudante_id=d.estudante.id,
                tipo=d.tipo,
                nome=d.estudante.nome,
                email=d.email,
                assunto=personalizar(assunto, ctx),
                corpo=personalizar(corpo, ctx),
                status=StatusEnvio.PENDENTE,
                tentativas=0,
            )
        )
    db.add(mensagem)
    db.commit()
    return mensagem


def reenviar_falhas(db: Session, mensagem: Mensagem) -> int:
    falhas = [d for d in mensagem.destinatarios if d.status == StatusEnvio.ERRO]
    for d in falhas:
        d.status = StatusEnvio.PENDENTE
        d.tentativas = 0
        d.erro = None
        d.proxima_tentativa = datetime.now(UTC)
    db.commit()
    return len(falhas)


# --- Fila --------------------------------------------------------------------


def montar_email(destinatario: Destinatario, remetente: str) -> EmailMessage:
    email = EmailMessage()
    email["From"] = remetente
    email["To"] = destinatario.email
    email["Subject"] = destinatario.assunto
    email.set_content(destinatario.corpo)
    return email


def ha_pendentes(db: Session, agora: datetime | None = None) -> bool:
    consulta = select(Destinatario.id).where(
        Destinatario.status == StatusEnvio.PENDENTE,
        Destinatario.proxima_tentativa <= (agora or datetime.now(UTC)),
    )
    return db.scalar(consulta.limit(1)) is not None


def proximos_da_fila(db: Session, agora: datetime, limite: int) -> list[Destinatario]:
    consulta = (
        select(Destinatario)
        .where(
            Destinatario.status == StatusEnvio.PENDENTE,
            Destinatario.proxima_tentativa <= agora,
        )
        .order_by(Destinatario.id)
        .limit(limite)
        .with_for_update(skip_locked=True)
    )
    return list(db.scalars(consulta))


def processar_fila(
    db: Session,
    enviar: Callable[[Destinatario], None],
    agora: datetime | None = None,
    limite: int = 20,
) -> tuple[int, int]:
    """Envia um lote da fila. Retorna (enviados, falhas). Falha agenda nova tentativa
    (1, 2, 4 min...) e, após MAX_TENTATIVAS, marca como ERRO."""
    agora = agora or datetime.now(UTC)
    enviados = falhas = 0
    for d in proximos_da_fila(db, agora, limite):
        d.tentativas += 1
        try:
            enviar(d)
        except Exception as e:
            falhas += 1
            d.erro = str(e)[:500]
            if d.tentativas >= MAX_TENTATIVAS:
                d.status = StatusEnvio.ERRO
            else:
                d.proxima_tentativa = agora + timedelta(minutes=2 ** (d.tentativas - 1))
        else:
            enviados += 1
            d.status = StatusEnvio.ENVIADO
            d.enviado_em = agora
            d.erro = None
        db.commit()
    return enviados, falhas
