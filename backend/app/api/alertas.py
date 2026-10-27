from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import DbSession, get_usuario_atual
from app.models import AlertaFrequencia, StatusAlerta
from app.schemas.alertas import AlertaSaida, ResolucaoEntrada, ResumoAlertas
from app.services import alertas as servico
from app.services.cadastros import obter

router = APIRouter(prefix="/alertas", tags=["alertas"], dependencies=[Depends(get_usuario_atual)])


def _saida(a: AlertaFrequencia) -> AlertaSaida:
    return AlertaSaida(
        id=a.id,
        turma_id=a.turma_id,
        disciplina=a.turma.disciplina,
        turma_nome=a.turma.nome,
        estudante_id=a.estudante_id,
        estudante_nome=a.estudante.nome,
        matricula=a.estudante.matricula,
        email_responsavel=a.estudante.email_responsavel,
        tipo=a.tipo,
        limite=a.limite,
        data_gatilho=a.data_gatilho,
        datas=[date.fromisoformat(d) for d in a.datas],
        status=a.status,
        resolvido_em=a.resolvido_em,
        observacao=a.observacao,
    )


@router.get("", response_model=list[AlertaSaida])
def listar(
    db: DbSession, status: StatusAlerta | None = None, turma_id: int | None = None
) -> list[AlertaSaida]:
    consulta = select(AlertaFrequencia).order_by(
        AlertaFrequencia.data_gatilho.desc(), AlertaFrequencia.id
    )
    if status is not None:
        consulta = consulta.where(AlertaFrequencia.status == status)
    if turma_id is not None:
        consulta = consulta.where(AlertaFrequencia.turma_id == turma_id)
    return [_saida(a) for a in db.scalars(consulta)]


@router.get("/resumo", response_model=ResumoAlertas)
def resumo(db: DbSession) -> ResumoAlertas:
    pendentes = db.scalar(
        select(func.count())
        .select_from(AlertaFrequencia)
        .where(AlertaFrequencia.status == StatusAlerta.PENDENTE)
    )
    return ResumoAlertas(pendentes=pendentes or 0)


@router.post("/{alerta_id}/resolver", response_model=AlertaSaida)
def resolver(alerta_id: int, dados: ResolucaoEntrada, db: DbSession) -> AlertaSaida:
    alerta = obter(db, AlertaFrequencia, alerta_id, "Alerta")
    return _saida(servico.resolver(db, alerta, dados.status, dados.observacao or None))
