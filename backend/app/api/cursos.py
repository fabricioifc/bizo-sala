from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import DbSession, get_usuario_atual
from app.models import Curso
from app.schemas.cadastros import CursoEntrada, CursoSaida
from app.services import cadastros

router = APIRouter(prefix="/cursos", tags=["cursos"], dependencies=[Depends(get_usuario_atual)])


@router.get("", response_model=list[CursoSaida])
def listar(db: DbSession) -> list[Curso]:
    return list(db.scalars(select(Curso).order_by(Curso.nome)))


@router.post("", response_model=CursoSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: CursoEntrada, db: DbSession) -> Curso:
    return cadastros.salvar_curso(db, dados)


@router.put("/{curso_id}", response_model=CursoSaida)
def atualizar(curso_id: int, dados: CursoEntrada, db: DbSession) -> Curso:
    return cadastros.salvar_curso(db, dados, cadastros.obter(db, Curso, curso_id, "Curso"))


@router.delete("/{curso_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(curso_id: int, db: DbSession) -> None:
    cadastros.excluir_curso(db, cadastros.obter(db, Curso, curso_id, "Curso"))
