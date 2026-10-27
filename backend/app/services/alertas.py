"""Alertas ao SISAE por faltas (somente cursos com limites configurados, ou seja, o EMI).

Critérios (OD art. 228 e regra do professor), contados em **encontros** (dias de aula):
- consecutivas: o estudante faltou N encontros seguidos → um alerta por sequência;
- alternadas: a cada M encontros de falta no total → um alerta.

Falta no encontro = faltou todas as horas-aula do dia. Atraso (falta parcial) conta
como presença para o alerta. Dias sem registro do estudante (ex.: matriculado depois)
são ignorados: não contam como falta nem interrompem a sequência.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AlertaFrequencia,
    Aula,
    Frequencia,
    StatusAlerta,
    StatusAula,
    TipoAlerta,
    Turma,
)
from app.services.erros import ErroDeNegocio


@dataclass(frozen=True)
class Ocorrencia:
    tipo: TipoAlerta
    limite: int
    data_gatilho: date
    datas: tuple[date, ...]


def detectar(
    encontros: Sequence[tuple[date, bool]],
    consecutivas: int | None,
    alternadas: int | None,
) -> list[Ocorrencia]:
    """Encontros do estudante em ordem de data, como (data, faltou o dia inteiro)."""
    ocorrencias: list[Ocorrencia] = []
    sequencia: list[date] = []
    faltas: list[date] = []
    for dia, faltou in encontros:
        if not faltou:
            sequencia = []
            continue
        sequencia.append(dia)
        faltas.append(dia)
        if consecutivas and len(sequencia) == consecutivas:
            ocorrencias.append(
                Ocorrencia(TipoAlerta.CONSECUTIVAS, consecutivas, dia, tuple(sequencia))
            )
        if alternadas and len(faltas) % alternadas == 0:
            ocorrencias.append(
                Ocorrencia(TipoAlerta.ALTERNADAS, alternadas, dia, tuple(faltas[-alternadas:]))
            )
    return ocorrencias


def _encontros_por_estudante(db: Session, turma_id: int) -> dict[int, list[tuple[date, bool]]]:
    consulta = (
        select(
            Frequencia.estudante_id,
            Aula.data,
            func.sum(Frequencia.faltas),
            func.sum(Aula.horas_aula),
        )
        .join(Aula, Aula.id == Frequencia.aula_id)
        .where(Aula.turma_id == turma_id, Aula.status == StatusAula.DADA)
        .group_by(Frequencia.estudante_id, Aula.data)
        .order_by(Aula.data)
    )
    encontros: dict[int, list[tuple[date, bool]]] = defaultdict(list)
    for estudante_id, dia, faltas, horas in db.execute(consulta).tuples():
        encontros[estudante_id].append((dia, faltas >= horas))
    return encontros


def atualizar_alertas(db: Session, turma: Turma) -> None:
    """Recalcula os alertas da turma a partir das chamadas (sem commit).

    Cria os novos como pendentes, ajusta os pendentes e remove pendentes que deixaram
    de valer (ex.: chamada corrigida). Alertas já avisados ou descartados são mantidos.
    """
    curso = turma.curso
    existentes = {
        (a.estudante_id, a.tipo, a.data_gatilho): a
        for a in db.scalars(select(AlertaFrequencia).where(AlertaFrequencia.turma_id == turma.id))
    }
    validas: set[tuple[int, TipoAlerta, date]] = set()

    if curso.alerta_faltas_consecutivas or curso.alerta_faltas_alternadas:
        for estudante_id, encontros in _encontros_por_estudante(db, turma.id).items():
            for o in detectar(
                encontros, curso.alerta_faltas_consecutivas, curso.alerta_faltas_alternadas
            ):
                chave = (estudante_id, o.tipo, o.data_gatilho)
                validas.add(chave)
                datas = [d.isoformat() for d in o.datas]
                alerta = existentes.get(chave)
                if alerta is None:
                    db.add(
                        AlertaFrequencia(
                            turma_id=turma.id,
                            estudante_id=estudante_id,
                            tipo=o.tipo,
                            limite=o.limite,
                            data_gatilho=o.data_gatilho,
                            datas=datas,
                            status=StatusAlerta.PENDENTE,
                        )
                    )
                elif alerta.status == StatusAlerta.PENDENTE:
                    alerta.datas = datas
                    alerta.limite = o.limite

    for chave, alerta in existentes.items():
        if chave not in validas and alerta.status == StatusAlerta.PENDENTE:
            db.delete(alerta)
    db.flush()


def atualizar_alertas_das_turmas(db: Session, turmas: Iterable[Turma]) -> None:
    for turma in turmas:
        atualizar_alertas(db, turma)


def resolver(
    db: Session, alerta: AlertaFrequencia, status: StatusAlerta, observacao: str | None
) -> AlertaFrequencia:
    if status == StatusAlerta.PENDENTE:
        alerta.resolvido_em = None
    elif alerta.status != StatusAlerta.PENDENTE:
        raise ErroDeNegocio("O alerta já foi resolvido")
    else:
        alerta.resolvido_em = datetime.now(UTC)
    alerta.status = status
    alerta.observacao = observacao
    db.commit()
    return alerta
