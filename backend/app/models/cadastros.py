from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Nivel(StrEnum):
    EMI = "EMI"
    GRADUACAO = "GRADUACAO"


class Regime(StrEnum):
    ANUAL = "ANUAL"
    SEMESTRAL = "SEMESTRAL"


class Curso(Base):
    __tablename__ = "curso"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    nivel: Mapped[Nivel] = mapped_column(String(20))
    regime: Mapped[Regime] = mapped_column(String(20))
    media_aprovacao: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    exame_final: Mapped[bool] = mapped_column(default=False)
    # Alerta ao SISAE (somente EMI): None desativa o critério
    alerta_faltas_consecutivas: Mapped[int | None] = mapped_column(SmallInteger)
    alerta_faltas_alternadas: Mapped[int | None] = mapped_column(SmallInteger)


class PeriodoLetivo(Base):
    __tablename__ = "periodo_letivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    regime: Mapped[Regime] = mapped_column(String(20))
    ano: Mapped[int] = mapped_column(SmallInteger)
    semestre: Mapped[int | None] = mapped_column(SmallInteger)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)

    ciclos: Mapped[list["CicloAvaliativo"]] = relationship(
        back_populates="periodo",
        cascade="all, delete-orphan",
        order_by="CicloAvaliativo.numero",
    )


class CicloAvaliativo(Base):
    __tablename__ = "ciclo_avaliativo"
    __table_args__ = (UniqueConstraint("periodo_id", "numero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodo_letivo.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(SmallInteger)
    nome: Mapped[str] = mapped_column(String(40))
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)

    periodo: Mapped[PeriodoLetivo] = relationship(back_populates="ciclos")


class DiaNaoLetivo(Base):
    __tablename__ = "dia_nao_letivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[date] = mapped_column(Date, unique=True)
    descricao: Mapped[str] = mapped_column(String(120))


turma_estudante = Table(
    "turma_estudante",
    Base.metadata,
    Column("turma_id", ForeignKey("turma.id", ondelete="CASCADE"), primary_key=True),
    Column("estudante_id", ForeignKey("estudante.id", ondelete="CASCADE"), primary_key=True),
    Column("criado_em", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class Turma(Base):
    __tablename__ = "turma"

    id: Mapped[int] = mapped_column(primary_key=True)
    disciplina: Mapped[str] = mapped_column(String(120))
    nome: Mapped[str] = mapped_column(String(60))
    curso_id: Mapped[int] = mapped_column(ForeignKey("curso.id", ondelete="RESTRICT"))
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodo_letivo.id", ondelete="RESTRICT"))
    carga_horaria_horas: Mapped[int] = mapped_column(SmallInteger)

    curso: Mapped[Curso] = relationship()
    periodo: Mapped[PeriodoLetivo] = relationship()
    horarios: Mapped[list["TurmaHorario"]] = relationship(
        back_populates="turma",
        cascade="all, delete-orphan",
        order_by="TurmaHorario.dia_semana",
    )
    estudantes: Mapped[list["Estudante"]] = relationship(
        secondary=turma_estudante, order_by="Estudante.nome"
    )


class TurmaHorario(Base):
    """Dia da semana com aula e quantas horas-aula (50 min) há nesse dia."""

    __tablename__ = "turma_horario"
    __table_args__ = (UniqueConstraint("turma_id", "dia_semana"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"))
    # 0 = segunda ... 6 = domingo (date.weekday())
    dia_semana: Mapped[int] = mapped_column(SmallInteger)
    aulas: Mapped[int] = mapped_column(SmallInteger)

    turma: Mapped[Turma] = relationship(back_populates="horarios")


class Estudante(Base):
    __tablename__ = "estudante"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    matricula: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str | None] = mapped_column(String(254))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    email_responsavel: Mapped[str | None] = mapped_column(String(254))
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
