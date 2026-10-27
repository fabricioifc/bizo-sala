from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import DbSession, get_usuario_atual
from app.models import Mensagem, StatusEnvio, Turma
from app.schemas.mensagens import (
    DestinatarioPrevia,
    DestinatarioSaida,
    MensagemDetalhe,
    MensagemEntrada,
    MensagemResumo,
    Previa,
    SemEmail,
)
from app.services import mensagens as servico
from app.services.cadastros import obter

router = APIRouter(
    prefix="/mensagens", tags=["mensagens"], dependencies=[Depends(get_usuario_atual)]
)


def _selecao(db: DbSession, dados: MensagemEntrada) -> tuple[Turma, servico.Selecao]:
    turma = obter(db, Turma, dados.turma_id, "Turma")
    selecao = servico.selecionar(
        turma, dados.estudante_ids, dados.incluir_estudantes, dados.incluir_responsaveis
    )
    return turma, selecao


def _resumo(m: Mensagem, turma: Turma | None) -> MensagemResumo:
    contagem = dict.fromkeys(StatusEnvio, 0)
    for d in m.destinatarios:
        contagem[d.status] += 1
    return MensagemResumo(
        id=m.id,
        turma_id=m.turma_id,
        disciplina=turma.disciplina if turma else None,
        turma_nome=turma.nome if turma else None,
        assunto=m.assunto,
        criado_em=m.criado_em,
        total=len(m.destinatarios),
        enviados=contagem[StatusEnvio.ENVIADO],
        pendentes=contagem[StatusEnvio.PENDENTE],
        erros=contagem[StatusEnvio.ERRO],
    )


def _detalhe(db: DbSession, m: Mensagem) -> MensagemDetalhe:
    turma = db.get(Turma, m.turma_id) if m.turma_id else None
    return MensagemDetalhe(
        **_resumo(m, turma).model_dump(),
        corpo=m.corpo,
        destinatarios=[DestinatarioSaida.model_validate(d) for d in m.destinatarios],
    )


@router.post("/previa", response_model=Previa)
def previa(dados: MensagemEntrada, db: DbSession) -> Previa:
    turma, selecao = _selecao(db, dados)
    primeiro = selecao.destinatarios[0].estudante if selecao.destinatarios else None
    ctx = servico.contexto(primeiro, turma) if primeiro else None
    return Previa(
        destinatarios=[
            DestinatarioPrevia(
                estudante_id=d.estudante.id, nome=d.estudante.nome, tipo=d.tipo, email=d.email
            )
            for d in selecao.destinatarios
        ],
        sem_email=[SemEmail(estudante_id=e.id, nome=e.nome) for e in selecao.sem_email],
        exemplo_assunto=servico.personalizar(dados.assunto, ctx) if ctx else None,
        exemplo_corpo=servico.personalizar(dados.corpo, ctx) if ctx else None,
    )


@router.post("", response_model=MensagemDetalhe, status_code=status.HTTP_201_CREATED)
def enviar(dados: MensagemEntrada, db: DbSession) -> MensagemDetalhe:
    turma, selecao = _selecao(db, dados)
    mensagem = servico.criar_mensagem(db, turma, selecao, dados.assunto, dados.corpo)
    return _detalhe(db, mensagem)


@router.get("", response_model=list[MensagemResumo])
def listar(db: DbSession, turma_id: int | None = None) -> list[MensagemResumo]:
    consulta = select(Mensagem).order_by(Mensagem.criado_em.desc(), Mensagem.id.desc())
    if turma_id is not None:
        consulta = consulta.where(Mensagem.turma_id == turma_id)
    turmas = {t.id: t for t in db.scalars(select(Turma))}
    return [_resumo(m, turmas.get(m.turma_id or 0)) for m in db.scalars(consulta)]


@router.get("/{mensagem_id}", response_model=MensagemDetalhe)
def detalhar(mensagem_id: int, db: DbSession) -> MensagemDetalhe:
    return _detalhe(db, obter(db, Mensagem, mensagem_id, "Mensagem"))


@router.post("/{mensagem_id}/reenviar-falhas", response_model=MensagemDetalhe)
def reenviar_falhas(mensagem_id: int, db: DbSession) -> MensagemDetalhe:
    mensagem = obter(db, Mensagem, mensagem_id, "Mensagem")
    servico.reenviar_falhas(db, mensagem)
    return _detalhe(db, mensagem)
