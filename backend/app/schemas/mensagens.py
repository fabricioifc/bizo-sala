from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import StatusEnvio, TipoDestinatario


class MensagemEntrada(BaseModel):
    turma_id: int
    estudante_ids: list[int] | None = Field(
        default=None, description="None = todos os estudantes ativos da turma"
    )
    incluir_estudantes: bool = True
    incluir_responsaveis: bool = False
    assunto: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    corpo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]


class DestinatarioPrevia(BaseModel):
    estudante_id: int
    nome: str
    tipo: TipoDestinatario
    email: str


class SemEmail(BaseModel):
    estudante_id: int
    nome: str


class Previa(BaseModel):
    destinatarios: list[DestinatarioPrevia]
    sem_email: list[SemEmail]
    exemplo_assunto: str | None
    exemplo_corpo: str | None


class DestinatarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estudante_id: int | None
    tipo: TipoDestinatario
    nome: str
    email: str
    status: StatusEnvio
    tentativas: int
    enviado_em: datetime | None
    erro: str | None


class MensagemResumo(BaseModel):
    id: int
    turma_id: int | None
    disciplina: str | None
    turma_nome: str | None
    assunto: str
    criado_em: datetime
    total: int
    enviados: int
    pendentes: int
    erros: int


class MensagemDetalhe(MensagemResumo):
    corpo: str
    destinatarios: list[DestinatarioSaida]
