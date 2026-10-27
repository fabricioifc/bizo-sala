from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, StringConstraints

from app.models import Nivel, Regime


def _texto(max_length: int) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)


Texto30 = Annotated[str, _texto(30)]
Texto40 = Annotated[str, _texto(40)]
Texto60 = Annotated[str, _texto(60)]
Texto120 = Annotated[str, _texto(120)]
Texto150 = Annotated[str, _texto(150)]


Nota = Annotated[
    Decimal,
    Field(ge=0, le=10, max_digits=3, decimal_places=1),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class _Saida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Curso -------------------------------------------------------------------


class CursoEntrada(BaseModel):
    nome: Texto120
    nivel: Nivel
    regime: Regime
    media_aprovacao: Nota = Decimal("6.0")
    exame_final: bool = False
    alerta_faltas_consecutivas: int | None = Field(default=None, ge=1, le=20)
    alerta_faltas_alternadas: int | None = Field(default=None, ge=1, le=50)


class CursoSaida(_Saida):
    id: int
    nome: str
    nivel: Nivel
    regime: Regime
    media_aprovacao: Nota
    exame_final: bool
    alerta_faltas_consecutivas: int | None
    alerta_faltas_alternadas: int | None


# --- Período letivo ----------------------------------------------------------


class CicloEntrada(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)] | None = None
    data_inicio: date
    data_fim: date


class CicloSaida(_Saida):
    id: int
    numero: int
    nome: str
    data_inicio: date
    data_fim: date


class PeriodoEntrada(BaseModel):
    nome: Texto40
    regime: Regime
    ano: int = Field(ge=2000, le=2100)
    semestre: Literal[1, 2] | None = None
    data_inicio: date
    data_fim: date
    ciclos: list[CicloEntrada] = Field(min_length=1, max_length=6)


class PeriodoSaida(_Saida):
    id: int
    nome: str
    regime: Regime
    ano: int
    semestre: int | None
    data_inicio: date
    data_fim: date
    ciclos: list[CicloSaida]


# --- Dia não letivo ----------------------------------------------------------


class DiaNaoLetivoEntrada(BaseModel):
    data: date
    descricao: Texto120


class DiaNaoLetivoSaida(_Saida):
    id: int
    data: date
    descricao: str


# --- Turma -------------------------------------------------------------------


class Horario(_Saida):
    dia_semana: int = Field(ge=0, le=6, description="0 = segunda ... 6 = domingo")
    aulas: int = Field(ge=1, le=8, description="Horas-aula (50 min) no dia")


class TurmaEntrada(BaseModel):
    disciplina: Texto120
    nome: Texto60
    curso_id: int
    periodo_id: int
    carga_horaria_horas: int = Field(ge=1, le=1000)
    horarios: list[Horario] = Field(min_length=1, max_length=7)


class TurmaSaida(BaseModel):
    id: int
    disciplina: str
    nome: str
    curso_id: int
    curso_nome: str
    nivel: Nivel
    periodo_id: int
    periodo_nome: str
    carga_horaria_horas: int
    horas_aula_previstas: int
    aulas_por_semana: int
    horarios: list[Horario]
    total_estudantes: int


# --- Estudante ---------------------------------------------------------------


class EstudanteEntrada(BaseModel):
    nome: Texto150
    matricula: Texto30
    email: EmailStr | None = None
    data_nascimento: date | None = None
    email_responsavel: EmailStr | None = None
    ativo: bool = True


class EstudanteSaida(_Saida):
    id: int
    nome: str
    matricula: str
    email: str | None
    data_nascimento: date | None
    email_responsavel: str | None
    ativo: bool


class ImportacaoEntrada(BaseModel):
    conteudo: str = Field(max_length=2_000_000, description="Texto do arquivo CSV")
    simular: bool = Field(default=True, description="Só valida e conta, sem gravar")


class ImportacaoErro(BaseModel):
    linha: int
    mensagem: str


class ImportacaoResultado(BaseModel):
    total_linhas: int
    criados: int
    atualizados: int
    matriculados: int
    ja_matriculados: int
    erros: list[ImportacaoErro]
    aplicado: bool
