from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import OrigemAula, StatusAula

HorasAula = Annotated[int, Field(ge=1, le=8, description="Horas-aula de 50 min")]


class AulaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turma_id: int
    data: date
    horas_aula: int
    status: StatusAula
    origem: OrigemAula
    motivo_cancelamento: str | None
    dia_nao_letivo: str | None = Field(
        default=None, description="Descrição, se a data estiver cadastrada como não letiva"
    )


class AulaEntrada(BaseModel):
    data: date
    horas_aula: HorasAula


class CancelamentoEntrada(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class GeracaoResultado(BaseModel):
    criadas: int


class AulaDoDia(AulaSaida):
    disciplina: str
    turma_nome: str


# --- Chamada -----------------------------------------------------------------


class ChamadaEstudante(BaseModel):
    estudante_id: int
    nome: str
    matricula: str
    faltas: int | None = Field(description="None = sem registro nesta aula")


class ChamadaSaida(BaseModel):
    aula: AulaSaida
    disciplina: str
    turma_nome: str
    estudantes: list[ChamadaEstudante]


class RegistroFalta(BaseModel):
    estudante_id: int
    faltas: int = Field(ge=0, le=8)


class ChamadaEntrada(BaseModel):
    registros: list[RegistroFalta]


# --- Carga horária e frequência ---------------------------------------------


class CargaHorariaSaida(BaseModel):
    meta: int = Field(description="Horas-aula necessárias para a carga horária")
    dadas: int
    previstas: int = Field(description="Horas-aula ainda sem chamada (passadas e futuras)")
    em_aberto: int = Field(description="Horas-aula passadas ainda sem chamada")
    aulas_em_aberto: int
    canceladas: int
    projecao: int = Field(description="Dadas + previstas")
    saldo: int = Field(description="Projeção menos meta (negativo = vai faltar)")


class FrequenciaEstudante(BaseModel):
    estudante_id: int
    nome: str
    matricula: str
    ativo: bool
    faltas: int
    horas_aula_registradas: int
    percentual_presenca: float | None
    faltas_restantes: int = Field(description="Faltas ainda possíveis sem ficar abaixo de 75%")


# --- Conteúdo ----------------------------------------------------------------


class RegistroConteudoDados(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_inicio: date
    data_fim: date
    texto: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
