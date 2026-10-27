"""Avaliações, lançamento de notas e boletim da turma."""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import (
    Aula,
    Avaliacao,
    CicloAvaliativo,
    Nivel,
    Nota,
    StatusAula,
    Substituicao,
    TipoAvaliacao,
    Turma,
)
from app.schemas.avaliacoes import AvaliacaoEntrada, NotaEntrada, Situacao
from app.services.aulas import frequencia_da_turma
from app.services.erros import ErroDeNegocio
from app.services.notas import (
    AvaliacaoCalculo,
    NotaCalculo,
    ResultadoCiclo,
    calcular_ciclo,
    media_final,
)


def avaliacoes_da_turma(db: Session, turma_id: int) -> list[Avaliacao]:
    consulta = (
        select(Avaliacao)
        .join(CicloAvaliativo)
        .where(Avaliacao.turma_id == turma_id)
        .order_by(CicloAvaliativo.numero, Avaliacao.tipo.desc(), Avaliacao.data, Avaliacao.id)
    )
    return list(db.scalars(consulta))


def notas_da_turma(db: Session, turma_id: int) -> list[Nota]:
    consulta = (
        select(Nota)
        .join(Avaliacao, Avaliacao.id == Nota.avaliacao_id)
        .where(Avaliacao.turma_id == turma_id)
    )
    return list(db.scalars(consulta))


# --- Avaliações --------------------------------------------------------------


def _regular_do_ciclo(db: Session, turma: Turma, avaliacao_id: int, ciclo_id: int) -> None:
    alvo = db.get(Avaliacao, avaliacao_id)
    if (
        alvo is None
        or alvo.turma_id != turma.id
        or alvo.ciclo_id != ciclo_id
        or alvo.tipo != TipoAvaliacao.REGULAR
    ):
        raise ErroDeNegocio("A avaliação substituída deve ser uma avaliação regular do mesmo ciclo")


def salvar_avaliacao(
    db: Session, turma: Turma, dados: AvaliacaoEntrada, avaliacao: Avaliacao | None = None
) -> Avaliacao:
    ciclo = db.get(CicloAvaliativo, dados.ciclo_id)
    if ciclo is None or ciclo.periodo_id != turma.periodo_id:
        raise ErroDeNegocio("O ciclo não pertence ao período letivo da turma")
    if avaliacao is not None and avaliacao.ciclo_id != dados.ciclo_id:
        tem_notas = db.scalar(select(exists().where(Nota.avaliacao_id == avaliacao.id)))
        if tem_notas:
            raise ErroDeNegocio("Não é possível mudar o ciclo de uma avaliação que já tem notas")

    substituicao: Substituicao | None = None
    substitui: int | None = None
    if dados.tipo == TipoAvaliacao.RECUPERACAO:
        # Padrão: EMI substitui a nota do trimestre (art. 245); graduação, a que mais
        # aumenta a média (reavaliação com escolha da nota substituída)
        substituicao = dados.substituicao or (
            Substituicao.CICLO if turma.curso.nivel == Nivel.EMI else Substituicao.MELHOR
        )
        if substituicao == Substituicao.AVALIACAO:
            if dados.substitui_avaliacao_id is None:
                raise ErroDeNegocio("Escolha a avaliação que a recuperação substitui")
            _regular_do_ciclo(db, turma, dados.substitui_avaliacao_id, dados.ciclo_id)
            substitui = dados.substitui_avaliacao_id

    avaliacao = avaliacao or Avaliacao(turma_id=turma.id)
    avaliacao.ciclo_id = dados.ciclo_id
    avaliacao.nome = dados.nome
    avaliacao.data = dados.data
    avaliacao.peso = dados.peso
    avaliacao.tipo = dados.tipo
    avaliacao.substituicao = substituicao
    avaliacao.substitui_avaliacao_id = substitui
    db.add(avaliacao)
    db.commit()
    return avaliacao


# --- Notas -------------------------------------------------------------------


def salvar_notas(db: Session, turma: Turma, entradas: Sequence[NotaEntrada]) -> None:
    """Grava (ou apaga, com valor None) as notas informadas; as demais ficam como estão."""
    avaliacoes = {a.id: a for a in avaliacoes_da_turma(db, turma.id)}
    matriculados = {e.id for e in turma.estudantes}
    for e in entradas:
        avaliacao = avaliacoes.get(e.avaliacao_id)
        if avaliacao is None:
            raise ErroDeNegocio(f"Avaliação {e.avaliacao_id} não pertence à turma")
        if e.estudante_id not in matriculados:
            raise ErroDeNegocio(f"Estudante {e.estudante_id} não está matriculado na turma")
        if e.substitui_avaliacao_id is not None:
            if avaliacao.tipo != TipoAvaliacao.RECUPERACAO:
                raise ErroDeNegocio("Só notas de recuperação substituem outra avaliação")
            _regular_do_ciclo(db, turma, e.substitui_avaliacao_id, avaliacao.ciclo_id)

        nota = db.get(Nota, (e.avaliacao_id, e.estudante_id))
        if e.valor is None:
            if nota is not None:
                db.delete(nota)
            continue
        if nota is None:
            nota = Nota(avaliacao_id=e.avaliacao_id, estudante_id=e.estudante_id)
            db.add(nota)
        nota.valor = e.valor
        nota.substitui_avaliacao_id = e.substitui_avaliacao_id
    db.commit()


# --- Boletim -----------------------------------------------------------------


@dataclass(frozen=True)
class CicloInfo:
    ciclo: CicloAvaliativo
    horas_aula_dadas: int

    @property
    def recuperacao_min(self) -> int:
        return math.ceil(self.horas_aula_dadas * 0.10)

    @property
    def recuperacao_max(self) -> int:
        return math.floor(self.horas_aula_dadas * 0.20)


@dataclass(frozen=True)
class LinhaBoletim:
    estudante_id: int
    ciclos: dict[int, ResultadoCiclo]
    media_final: Decimal | None
    percentual_presenca: float | None
    situacao: Situacao


def ciclos_da_turma(db: Session, turma: Turma) -> list[CicloInfo]:
    resultado = []
    for ciclo in turma.periodo.ciclos:
        horas = db.scalar(
            select(func.coalesce(func.sum(Aula.horas_aula), 0)).where(
                Aula.turma_id == turma.id,
                Aula.status == StatusAula.DADA,
                Aula.data.between(ciclo.data_inicio, ciclo.data_fim),
            )
        )
        resultado.append(CicloInfo(ciclo, int(horas or 0)))
    return resultado


def boletim(db: Session, turma: Turma) -> list[LinhaBoletim]:
    avaliacoes = avaliacoes_da_turma(db, turma.id)
    notas = notas_da_turma(db, turma.id)
    lancadas = {n.avaliacao_id for n in notas}

    por_ciclo: dict[int, list[AvaliacaoCalculo]] = defaultdict(list)
    for a in avaliacoes:
        por_ciclo[a.ciclo_id].append(
            AvaliacaoCalculo(
                id=a.id,
                peso=a.peso,
                tipo=a.tipo,
                lancada=a.id in lancadas,
                substituicao=a.substituicao,
                substitui_avaliacao_id=a.substitui_avaliacao_id,
            )
        )
    notas_por_estudante: dict[int, dict[int, NotaCalculo]] = defaultdict(dict)
    for n in notas:
        notas_por_estudante[n.estudante_id][n.avaliacao_id] = NotaCalculo(
            n.valor, n.substitui_avaliacao_id
        )
    frequencia = {f.estudante.id: f for f in frequencia_da_turma(db, turma)}
    ciclos = turma.periodo.ciclos
    media_aprovacao = turma.curso.media_aprovacao

    linhas = []
    for estudante in turma.estudantes:
        resultados = {
            c.id: calcular_ciclo(por_ciclo.get(c.id, []), notas_por_estudante[estudante.id])
            for c in ciclos
        }
        final = media_final([r.media for r in resultados.values()])
        freq = frequencia[estudante.id]
        situacao: Situacao
        if freq.faltas_restantes < 0:
            situacao = "REPROVADO_POR_FALTA"
        elif any(r.media is None for r in resultados.values()) or final is None:
            situacao = "EM_ANDAMENTO"
        elif final >= media_aprovacao:
            situacao = "APROVADO"
        else:
            situacao = "ABAIXO_DA_MEDIA"
        linhas.append(
            LinhaBoletim(estudante.id, resultados, final, freq.percentual_presenca, situacao)
        )
    return linhas
