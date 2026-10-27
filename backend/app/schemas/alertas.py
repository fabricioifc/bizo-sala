from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models import StatusAlerta, TipoAlerta


class AlertaSaida(BaseModel):
    id: int
    turma_id: int
    disciplina: str
    turma_nome: str
    estudante_id: int
    estudante_nome: str
    matricula: str
    email_responsavel: str | None
    tipo: TipoAlerta
    limite: int
    data_gatilho: date
    datas: list[date]
    status: StatusAlerta
    resolvido_em: datetime | None
    observacao: str | None


class ResolucaoEntrada(BaseModel):
    status: StatusAlerta
    observacao: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = (
        None
    )


class ResumoAlertas(BaseModel):
    pendentes: int
