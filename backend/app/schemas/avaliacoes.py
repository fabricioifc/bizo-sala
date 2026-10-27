from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints

from app.models import Substituicao, TipoAvaliacao
from app.schemas.cadastros import Nota as ValorNota

Peso = Annotated[
    Decimal,
    Field(gt=0, le=100, max_digits=4, decimal_places=1),
    PlainSerializer(float, return_type=float, when_used="json"),
]
NotaOpcional = Annotated[
    Decimal | None,
    PlainSerializer(
        lambda v: float(v) if v is not None else None, return_type=float | None, when_used="json"
    ),
]


class AvaliacaoEntrada(BaseModel):
    ciclo_id: int
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    data: date | None = None
    peso: Peso = Decimal("1")
    tipo: TipoAvaliacao = TipoAvaliacao.REGULAR
    substituicao: Substituicao | None = Field(
        default=None, description="Só recuperação; vazio = padrão do curso"
    )
    substitui_avaliacao_id: int | None = None


class AvaliacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ciclo_id: int
    nome: str
    data: date | None
    peso: Peso
    tipo: TipoAvaliacao
    substituicao: Substituicao | None
    substitui_avaliacao_id: int | None


class NotaEntrada(BaseModel):
    avaliacao_id: int
    estudante_id: int
    valor: ValorNota | None = Field(description="None apaga a nota")
    substitui_avaliacao_id: int | None = None


class NotaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avaliacao_id: int
    estudante_id: int
    valor: ValorNota
    substitui_avaliacao_id: int | None


# --- Boletim -----------------------------------------------------------------


class SubstituicaoSaida(BaseModel):
    recuperacao_id: int
    avaliacao_id: int | None = Field(description="None = substituiu a nota do ciclo")


class CicloDoEstudante(BaseModel):
    ciclo_id: int
    media: NotaOpcional
    media_sem_recuperacao: NotaOpcional
    abaixo_da_media: bool
    substituicoes: list[SubstituicaoSaida]


Situacao = Literal["EM_ANDAMENTO", "APROVADO", "ABAIXO_DA_MEDIA", "REPROVADO_POR_FALTA"]


class BoletimEstudante(BaseModel):
    estudante_id: int
    nome: str
    matricula: str
    ativo: bool
    ciclos: list[CicloDoEstudante]
    media_final: NotaOpcional
    percentual_presenca: float | None
    situacao: Situacao


class CicloResumo(BaseModel):
    ciclo_id: int
    numero: int
    nome: str
    data_inicio: date
    data_fim: date
    horas_aula_dadas: int
    recuperacao_min: int = Field(description="10% das horas-aula dadas no ciclo (OD art. 242)")
    recuperacao_max: int = Field(description="20% das horas-aula dadas no ciclo")


class Boletim(BaseModel):
    media_aprovacao: float
    ciclos: list[CicloResumo]
    estudantes: list[BoletimEstudante]
