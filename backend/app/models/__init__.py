from app.models.alertas import AlertaFrequencia, StatusAlerta, TipoAlerta
from app.models.aulas import Aula, Frequencia, OrigemAula, RegistroConteudo, StatusAula
from app.models.avaliacoes import Avaliacao, Nota, Substituicao, TipoAvaliacao
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
    "Avaliacao",
    "Base",
    "CicloAvaliativo",
    "Curso",
    "DiaNaoLetivo",
    "Estudante",
    "Frequencia",
    "Nivel",
    "Nota",
    "OrigemAula",
    "PeriodoLetivo",
    "Regime",
    "RegistroConteudo",
    "StatusAlerta",
    "StatusAula",
    "Substituicao",
    "TipoAlerta",
    "TipoAvaliacao",
    "Turma",
    "TurmaHorario",
    "Usuario",
    "turma_estudante",
]
