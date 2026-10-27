from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StatusEnvio(StrEnum):
    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"
    ERRO = "ERRO"  # desistiu após as tentativas


class TipoDestinatario(StrEnum):
    ESTUDANTE = "ESTUDANTE"
    RESPONSAVEL = "RESPONSAVEL"


class Mensagem(Base):
    __tablename__ = "mensagem"

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int | None] = mapped_column(ForeignKey("turma.id", ondelete="SET NULL"))
    assunto: Mapped[str] = mapped_column(String(200))
    corpo: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    destinatarios: Mapped[list["Destinatario"]] = relationship(
        back_populates="mensagem", cascade="all, delete-orphan", order_by="Destinatario.id"
    )


class Destinatario(Base):
    """Um e-mail da fila: cada destinatário recebe o seu, já personalizado."""

    __tablename__ = "mensagem_destinatario"
    __table_args__ = (Index("ix_destinatario_fila", "status", "proxima_tentativa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    mensagem_id: Mapped[int] = mapped_column(ForeignKey("mensagem.id", ondelete="CASCADE"))
    estudante_id: Mapped[int | None] = mapped_column(
        ForeignKey("estudante.id", ondelete="SET NULL")
    )
    tipo: Mapped[TipoDestinatario] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(254))
    assunto: Mapped[str] = mapped_column(String(200))
    corpo: Mapped[str] = mapped_column(Text)
    status: Mapped[StatusEnvio] = mapped_column(String(20), default=StatusEnvio.PENDENTE)
    tentativas: Mapped[int] = mapped_column(SmallInteger, default=0)
    proxima_tentativa: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erro: Mapped[str | None] = mapped_column(String(500))

    mensagem: Mapped[Mensagem] = relationship(back_populates="destinatarios")
