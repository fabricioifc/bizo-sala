from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_usuario_atual
from app.models import Estudante
from app.schemas.cadastros import EstudanteEntrada, EstudanteSaida
from app.services import cadastros

router = APIRouter(
    prefix="/estudantes", tags=["estudantes"], dependencies=[Depends(get_usuario_atual)]
)


@router.put("/{estudante_id}", response_model=EstudanteSaida)
def atualizar(estudante_id: int, dados: EstudanteEntrada, db: DbSession) -> Estudante:
    estudante = cadastros.obter(db, Estudante, estudante_id, "Estudante")
    return cadastros.atualizar_estudante(db, estudante, dados)
