from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TipoAvaliacao(StrEnum):
    REGULAR = "REGULAR"
    RECUPERACAO = "RECUPERACAO"  # recuperação paralela (EMI) ou reavaliação (graduação)


class Substituicao(StrEnum):
    """O que a nota de recuperação substitui (quando for maior)."""

    CICLO = "CICLO"  # a nota do ciclo (trimestre) inteiro
    AVALIACAO = "AVALIACAO"  # uma avaliação específica
    MELHOR = "MELHOR"  # a avaliação que mais aumenta a média (escolha por estudante)


class Avaliacao(Base):
    __tablename__ = "avaliacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), index=True)
    ciclo_id: Mapped[int] = mapped_column(ForeignKey("ciclo_avaliativo.id", ondelete="RESTRICT"))
    nome: Mapped[str] = mapped_column(String(80))
    data: Mapped[date | None] = mapped_column(Date)
    peso: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    tipo: Mapped[TipoAvaliacao] = mapped_column(String(20))
    substituicao: Mapped[Substituicao | None] = mapped_column(String(20))
    substitui_avaliacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("avaliacao.id", ondelete="SET NULL")
    )


class Nota(Base):
    __tablename__ = "nota"

    avaliacao_id: Mapped[int] = mapped_column(
        ForeignKey("avaliacao.id", ondelete="CASCADE"), primary_key=True
    )
    estudante_id: Mapped[int] = mapped_column(
        ForeignKey("estudante.id", ondelete="CASCADE"), primary_key=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    # Recuperação: avaliação escolhida para este estudante (sobrepõe a regra da avaliação)
    substitui_avaliacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("avaliacao.id", ondelete="SET NULL")
    )
