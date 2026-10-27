from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StatusAula(StrEnum):
    PREVISTA = "PREVISTA"  # ainda sem chamada (inclui aulas passadas em aberto)
    DADA = "DADA"  # chamada registrada
    CANCELADA = "CANCELADA"  # não conta carga horária


class OrigemAula(StrEnum):
    GRADE = "GRADE"  # gerada pelos horários da turma
    EXTRA = "EXTRA"  # adicionada manualmente


class Aula(Base):
    """Encontro da turma em uma data, com uma ou mais horas-aula (50 min)."""

    __tablename__ = "aula"
    __table_args__ = (Index("ix_aula_turma_data", "turma_id", "data"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"))
    data: Mapped[date] = mapped_column(Date)
    horas_aula: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[StatusAula] = mapped_column(String(20), default=StatusAula.PREVISTA)
    origem: Mapped[OrigemAula] = mapped_column(String(10))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(120))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Frequencia(Base):
    """Faltas do estudante na aula, em horas-aula (0 = presente em todas)."""

    __tablename__ = "frequencia"

    aula_id: Mapped[int] = mapped_column(
        ForeignKey("aula.id", ondelete="CASCADE"), primary_key=True
    )
    estudante_id: Mapped[int] = mapped_column(
        ForeignKey("estudante.id", ondelete="CASCADE"), primary_key=True
    )
    faltas: Mapped[int] = mapped_column(SmallInteger)


class RegistroConteudo(Base):
    """O que foi (ou será) trabalhado num intervalo de datas da turma."""

    __tablename__ = "registro_conteudo"

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)
    texto: Mapped[str] = mapped_column(Text)
