from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import DbSession, get_usuario_atual
from app.models import PeriodoLetivo
from app.schemas.cadastros import PeriodoEntrada, PeriodoSaida
from app.services import cadastros

router = APIRouter(prefix="/periodos", tags=["periodos"], dependencies=[Depends(get_usuario_atual)])


@router.get("", response_model=list[PeriodoSaida])
def listar(db: DbSession) -> list[PeriodoLetivo]:
    consulta = select(PeriodoLetivo).order_by(PeriodoLetivo.data_inicio.desc(), PeriodoLetivo.nome)
    return list(db.scalars(consulta))


@router.post("", response_model=PeriodoSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: PeriodoEntrada, db: DbSession) -> PeriodoLetivo:
    return cadastros.salvar_periodo(db, dados)


@router.put("/{periodo_id}", response_model=PeriodoSaida)
def atualizar(periodo_id: int, dados: PeriodoEntrada, db: DbSession) -> PeriodoLetivo:
    periodo = cadastros.obter(db, PeriodoLetivo, periodo_id, "Período letivo")
    return cadastros.salvar_periodo(db, dados, periodo)


@router.delete("/{periodo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(periodo_id: int, db: DbSession) -> None:
    periodo = cadastros.obter(db, PeriodoLetivo, periodo_id, "Período letivo")
    cadastros.excluir_periodo(db, periodo)
