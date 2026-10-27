from fastapi import APIRouter, Depends, status
from sqlalchemy import extract, select

from app.api.deps import DbSession, get_usuario_atual
from app.models import DiaNaoLetivo
from app.schemas.cadastros import DiaNaoLetivoEntrada, DiaNaoLetivoSaida
from app.services import cadastros

router = APIRouter(
    prefix="/dias-nao-letivos",
    tags=["dias-nao-letivos"],
    dependencies=[Depends(get_usuario_atual)],
)


@router.get("", response_model=list[DiaNaoLetivoSaida])
def listar(db: DbSession, ano: int | None = None) -> list[DiaNaoLetivo]:
    consulta = select(DiaNaoLetivo).order_by(DiaNaoLetivo.data)
    if ano is not None:
        consulta = consulta.where(extract("year", DiaNaoLetivo.data) == ano)
    return list(db.scalars(consulta))


@router.post("", response_model=DiaNaoLetivoSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: DiaNaoLetivoEntrada, db: DbSession) -> DiaNaoLetivo:
    return cadastros.salvar_dia_nao_letivo(db, dados)


@router.put("/{dia_id}", response_model=DiaNaoLetivoSaida)
def atualizar(dia_id: int, dados: DiaNaoLetivoEntrada, db: DbSession) -> DiaNaoLetivo:
    dia = cadastros.obter(db, DiaNaoLetivo, dia_id, "Dia não letivo")
    return cadastros.salvar_dia_nao_letivo(db, dados, dia)


@router.delete("/{dia_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(dia_id: int, db: DbSession) -> None:
    dia = cadastros.obter(db, DiaNaoLetivo, dia_id, "Dia não letivo")
    db.delete(dia)
    db.commit()
