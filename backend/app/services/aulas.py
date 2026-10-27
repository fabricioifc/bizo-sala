"""Calendário de aulas, chamada, carga horária, frequência e registro de conteúdo."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    Aula,
    DiaNaoLetivo,
    Estudante,
    Frequencia,
    OrigemAula,
    RegistroConteudo,
    StatusAula,
    Turma,
)
from app.schemas.aulas import AulaEntrada, RegistroConteudoDados, RegistroFalta
from app.services.alertas import atualizar_alertas
from app.services.cadastros import horas_aula_previstas
from app.services.erros import ErroDeNegocio

FREQUENCIA_MINIMA = 0.75  # OD art. 224


def aulas_da_turma(db: Session, turma_id: int) -> list[Aula]:
    consulta = select(Aula).where(Aula.turma_id == turma_id).order_by(Aula.data, Aula.id)
    return list(db.scalars(consulta))


def dias_nao_letivos(db: Session, inicio: date, fim: date) -> dict[date, str]:
    consulta = select(DiaNaoLetivo).where(DiaNaoLetivo.data.between(inicio, fim))
    return {d.data: d.descricao for d in db.scalars(consulta)}


# --- Calendário --------------------------------------------------------------


def gerar_calendario(db: Session, turma: Turma) -> int:
    """Cria as aulas previstas pelos horários da turma em todo o período letivo.

    Pula dias não letivos e datas que já têm aula da grade. Pode ser executado de
    novo sem duplicar (ex.: depois de mudar os horários). Retorna quantas criou.
    """
    periodo = turma.periodo
    horarios = {h.dia_semana: h.aulas for h in turma.horarios}
    nao_letivos = dias_nao_letivos(db, periodo.data_inicio, periodo.data_fim)
    existentes = set(
        db.scalars(
            select(Aula.data).where(Aula.turma_id == turma.id, Aula.origem == OrigemAula.GRADE)
        )
    )

    criadas = 0
    dia = periodo.data_inicio
    while dia <= periodo.data_fim:
        aulas = horarios.get(dia.weekday())
        if aulas and dia not in nao_letivos and dia not in existentes:
            db.add(
                Aula(
                    turma_id=turma.id,
                    data=dia,
                    horas_aula=aulas,
                    status=StatusAula.PREVISTA,
                    origem=OrigemAula.GRADE,
                )
            )
            criadas += 1
        dia += timedelta(days=1)
    db.commit()
    return criadas


def _validar_data(turma: Turma, data: date) -> None:
    periodo = turma.periodo
    if not periodo.data_inicio <= data <= periodo.data_fim:
        raise ErroDeNegocio(f"A data deve estar dentro do período letivo {periodo.nome}")


def adicionar_aula_extra(db: Session, turma: Turma, dados: AulaEntrada) -> Aula:
    _validar_data(turma, dados.data)
    aula = Aula(
        turma_id=turma.id,
        data=dados.data,
        horas_aula=dados.horas_aula,
        status=StatusAula.PREVISTA,
        origem=OrigemAula.EXTRA,
    )
    db.add(aula)
    db.commit()
    return aula


def editar_aula(db: Session, aula: Aula, turma: Turma, dados: AulaEntrada) -> Aula:
    _validar_data(turma, dados.data)
    maior_falta = db.scalar(
        select(func.max(Frequencia.faltas)).where(Frequencia.aula_id == aula.id)
    )
    if maior_falta and maior_falta > dados.horas_aula:
        raise ErroDeNegocio(
            f"Há estudante com {maior_falta} faltas nesta aula; não é possível reduzir para "
            f"{dados.horas_aula} horas-aula"
        )
    aula.data = dados.data
    aula.horas_aula = dados.horas_aula
    db.flush()
    atualizar_alertas(db, turma)
    db.commit()
    return aula


def cancelar_aula(db: Session, aula: Aula, motivo: str) -> Aula:
    """Cancela a aula (não conta carga horária). Descarta a chamada, se houver."""
    db.execute(delete(Frequencia).where(Frequencia.aula_id == aula.id))
    aula.status = StatusAula.CANCELADA
    aula.motivo_cancelamento = motivo
    db.flush()
    atualizar_alertas(db, _turma_da_aula(db, aula))
    db.commit()
    return aula


def excluir_aula(db: Session, aula: Aula) -> None:
    turma = _turma_da_aula(db, aula)
    db.delete(aula)
    db.flush()
    atualizar_alertas(db, turma)
    db.commit()


def _turma_da_aula(db: Session, aula: Aula) -> Turma:
    turma = db.get(Turma, aula.turma_id)
    assert turma is not None
    return turma


def reabrir_aula(db: Session, aula: Aula) -> Aula:
    if aula.status != StatusAula.CANCELADA:
        raise ErroDeNegocio("Só aulas canceladas podem ser reabertas")
    aula.status = StatusAula.PREVISTA
    aula.motivo_cancelamento = None
    db.commit()
    return aula


# --- Chamada -----------------------------------------------------------------


def faltas_da_aula(db: Session, aula_id: int) -> dict[int, int]:
    consulta = select(Frequencia.estudante_id, Frequencia.faltas).where(
        Frequencia.aula_id == aula_id
    )
    return {estudante_id: faltas for estudante_id, faltas in db.execute(consulta).tuples()}


def salvar_chamada(
    db: Session, aula: Aula, turma: Turma, registros: Sequence[RegistroFalta]
) -> Aula:
    """Grava as faltas (substituindo as anteriores) e marca a aula como dada."""
    if aula.status == StatusAula.CANCELADA:
        raise ErroDeNegocio("A aula está cancelada; reabra-a antes de fazer a chamada")
    matriculados = {e.id for e in turma.estudantes}
    vistos: set[int] = set()
    for r in registros:
        if r.estudante_id not in matriculados:
            raise ErroDeNegocio(f"Estudante {r.estudante_id} não está matriculado na turma")
        if r.estudante_id in vistos:
            raise ErroDeNegocio(f"Estudante {r.estudante_id} repetido na chamada")
        if r.faltas > aula.horas_aula:
            raise ErroDeNegocio(
                f"Faltas ({r.faltas}) maiores que as horas-aula da aula ({aula.horas_aula})"
            )
        vistos.add(r.estudante_id)

    db.execute(delete(Frequencia).where(Frequencia.aula_id == aula.id))
    db.add_all(
        Frequencia(aula_id=aula.id, estudante_id=r.estudante_id, faltas=r.faltas) for r in registros
    )
    aula.status = StatusAula.DADA
    db.flush()
    atualizar_alertas(db, turma)
    db.commit()
    return aula


# --- Carga horária e frequência ---------------------------------------------


@dataclass(frozen=True)
class ResumoCarga:
    meta: int
    dadas: int
    previstas: int
    em_aberto: int
    aulas_em_aberto: int
    canceladas: int

    @property
    def projecao(self) -> int:
        return self.dadas + self.previstas

    @property
    def saldo(self) -> int:
        return self.projecao - self.meta


def resumo_carga(turma: Turma, aulas: Sequence[Aula], hoje: date) -> ResumoCarga:
    def soma(status: StatusAula) -> int:
        return sum(a.horas_aula for a in aulas if a.status == status)

    abertas = [a for a in aulas if a.status == StatusAula.PREVISTA and a.data < hoje]
    return ResumoCarga(
        meta=horas_aula_previstas(turma.carga_horaria_horas),
        dadas=soma(StatusAula.DADA),
        previstas=soma(StatusAula.PREVISTA),
        em_aberto=sum(a.horas_aula for a in abertas),
        aulas_em_aberto=len(abertas),
        canceladas=soma(StatusAula.CANCELADA),
    )


@dataclass(frozen=True)
class FrequenciaAluno:
    estudante: Estudante
    faltas: int
    horas_aula_registradas: int
    percentual_presenca: float | None
    faltas_restantes: int


def frequencia_da_turma(db: Session, turma: Turma) -> list[FrequenciaAluno]:
    """Faltas e % de presença de cada estudante, considerando só as aulas com chamada.

    `faltas_restantes` usa a carga horária total do componente (OD art. 224):
    pode faltar até 25% das horas-aula da disciplina.
    """
    consulta = (
        select(
            Frequencia.estudante_id,
            func.sum(Frequencia.faltas),
            func.sum(Aula.horas_aula),
        )
        .join(Aula, Aula.id == Frequencia.aula_id)
        .where(Aula.turma_id == turma.id, Aula.status == StatusAula.DADA)
        .group_by(Frequencia.estudante_id)
    )
    totais = {eid: (int(f), int(h)) for eid, f, h in db.execute(consulta).tuples()}
    limite = math.floor(horas_aula_previstas(turma.carga_horaria_horas) * (1 - FREQUENCIA_MINIMA))

    resultado = []
    for estudante in turma.estudantes:
        faltas, horas = totais.get(estudante.id, (0, 0))
        resultado.append(
            FrequenciaAluno(
                estudante=estudante,
                faltas=faltas,
                horas_aula_registradas=horas,
                percentual_presenca=round(100 * (horas - faltas) / horas, 1) if horas else None,
                faltas_restantes=limite - faltas,
            )
        )
    return resultado


# --- Registro de conteúdo ----------------------------------------------------


def conteudos_da_turma(db: Session, turma_id: int) -> list[RegistroConteudo]:
    consulta = (
        select(RegistroConteudo)
        .where(RegistroConteudo.turma_id == turma_id)
        .order_by(RegistroConteudo.data_inicio)
    )
    return list(db.scalars(consulta))


def salvar_conteudos(
    db: Session, turma: Turma, registros: Sequence[RegistroConteudoDados]
) -> list[RegistroConteudo]:
    """Substitui todos os registros de conteúdo da turma (a tela edita o ano inteiro)."""
    ordenados = sorted(registros, key=lambda r: r.data_inicio)
    for i, r in enumerate(ordenados):
        if r.data_fim < r.data_inicio:
            raise ErroDeNegocio(f"Registro de {r.data_inicio}: fim anterior ao início")
        if i and r.data_inicio <= ordenados[i - 1].data_fim:
            raise ErroDeNegocio(
                f"Registros de {ordenados[i - 1].data_inicio} e {r.data_inicio} se sobrepõem"
            )

    db.execute(delete(RegistroConteudo).where(RegistroConteudo.turma_id == turma.id))
    novos = [
        RegistroConteudo(
            turma_id=turma.id, data_inicio=r.data_inicio, data_fim=r.data_fim, texto=r.texto
        )
        for r in ordenados
    ]
    db.add_all(novos)
    db.commit()
    return novos
