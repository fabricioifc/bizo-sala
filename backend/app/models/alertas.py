from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.cadastros import Estudante, Turma


class TipoAlerta(StrEnum):
    CONSECUTIVAS = "CONSECUTIVAS"
    ALTERNADAS = "ALTERNADAS"


class StatusAlerta(StrEnum):
    PENDENTE = "PENDENTE"
    AVISADO = "AVISADO"  # SISAE informado
    DESCARTADO = "DESCARTADO"  # ex.: falta justificada


class AlertaFrequencia(Base):
    """Estudante do EMI que atingiu o limite de faltas e precisa ser informado ao SISAE."""

    __tablename__ = "alerta_frequencia"
    __table_args__ = (UniqueConstraint("turma_id", "estudante_id", "tipo", "data_gatilho"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"))
    estudante_id: Mapped[int] = mapped_column(ForeignKey("estudante.id", ondelete="CASCADE"))
    tipo: Mapped[TipoAlerta] = mapped_column(String(20))
    limite: Mapped[int] = mapped_column(SmallInteger)
    # Dia em que o limite foi atingido (identifica o alerta) e os dias de falta que o compõem
    data_gatilho: Mapped[date] = mapped_column(Date)
    datas: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[StatusAlerta] = mapped_column(String(20), default=StatusAlerta.PENDENTE)
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observacao: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    turma: Mapped[Turma] = relationship()
    estudante: Mapped[Estudante] = relationship()
