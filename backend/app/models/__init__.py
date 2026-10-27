from app.models.alertas import AlertaFrequencia, StatusAlerta, TipoAlerta
from app.models.aulas import Aula, Frequencia, OrigemAula, RegistroConteudo, StatusAula
from app.models.base import Base
from app.models.cadastros import (
    CicloAvaliativo,
    Curso,
    DiaNaoLetivo,
    Estudante,
    Nivel,
    PeriodoLetivo,
    Regime,
    Turma,
    TurmaHorario,
    turma_estudante,
)
from app.models.usuario import Usuario

__all__ = [
    "AlertaFrequencia",
    "Aula",
    "Base",
    "CicloAvaliativo",
    "Curso",
    "DiaNaoLetivo",
    "Estudante",
    "Frequencia",
    "Nivel",
    "OrigemAula",
    "PeriodoLetivo",
    "Regime",
    "RegistroConteudo",
    "StatusAlerta",
    "StatusAula",
    "TipoAlerta",
    "Turma",
    "TurmaHorario",
    "Usuario",
    "turma_estudante",
]
