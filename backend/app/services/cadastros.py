"""Regras de negócio dos cadastros: cursos, períodos, dias não letivos, turmas e estudantes."""

import math

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import (
    Avaliacao,
    CicloAvaliativo,
    Curso,
    DiaNaoLetivo,
    Estudante,
    Nivel,
    PeriodoLetivo,
    Regime,
    Turma,
    TurmaHorario,
)
from app.schemas.cadastros import (
    CursoEntrada,
    DiaNaoLetivoEntrada,
    EstudanteEntrada,
    PeriodoEntrada,
    TurmaEntrada,
)
from app.services.alertas import atualizar_alertas_das_turmas
from app.services.erros import Conflito, ErroDeNegocio, NaoEncontrado

MINUTOS_HORA_AULA = 50


def horas_aula_previstas(carga_horaria_horas: int) -> int:
    """Horas-aula de 50 min necessárias para cumprir a carga horária (60 h = 72)."""
    return math.ceil(carga_horaria_horas * 60 / MINUTOS_HORA_AULA)


def obter[T](db: Session, modelo: type[T], id_: int, nome: str) -> T:
    objeto = db.get(modelo, id_)
    if objeto is None:
        raise NaoEncontrado(f"{nome} não encontrado(a)")
    return objeto


# --- Curso -------------------------------------------------------------------


def salvar_curso(db: Session, dados: CursoEntrada, curso: Curso | None = None) -> Curso:
    duplicado = db.scalar(select(Curso.id).where(func.lower(Curso.nome) == dados.nome.lower()))
    if duplicado is not None and (curso is None or duplicado != curso.id):
        raise Conflito("Já existe um curso com esse nome")

    if curso is not None and curso.regime != dados.regime and _curso_em_uso(db, curso.id):
        raise Conflito("Não é possível mudar o regime de um curso que já tem turmas")

    curso = curso or Curso()
    for campo, valor in dados.model_dump().items():
        setattr(curso, campo, valor)
    if dados.nivel == Nivel.GRADUACAO:
        # Graduação não gera alerta ao SISAE
        curso.alerta_faltas_consecutivas = None
        curso.alerta_faltas_alternadas = None

    db.add(curso)
    if curso.id is not None:
        # Limites de alerta podem ter mudado
        db.flush()
        turmas = db.scalars(select(Turma).where(Turma.curso_id == curso.id))
        atualizar_alertas_das_turmas(db, turmas)
    db.commit()
    return curso


def _curso_em_uso(db: Session, curso_id: int) -> bool:
    return bool(db.scalar(select(exists().where(Turma.curso_id == curso_id))))


def excluir_curso(db: Session, curso: Curso) -> None:
    if _curso_em_uso(db, curso.id):
        raise Conflito("O curso tem turmas e não pode ser excluído")
    db.delete(curso)
    db.commit()


# --- Período letivo ----------------------------------------------------------


def _nome_ciclo(regime: Regime, numero: int) -> str:
    return f"{numero}º trimestre" if regime == Regime.ANUAL else f"{numero}º ciclo"


def salvar_periodo(
    db: Session, dados: PeriodoEntrada, periodo: PeriodoLetivo | None = None
) -> PeriodoLetivo:
    if dados.regime == Regime.SEMESTRAL and dados.semestre is None:
        raise ErroDeNegocio("Informe o semestre (1 ou 2) do período semestral")
    if dados.regime == Regime.ANUAL and dados.semestre is not None:
        raise ErroDeNegocio("Período anual não tem semestre")
    if dados.data_fim <= dados.data_inicio:
        raise ErroDeNegocio("A data de fim deve ser posterior à data de início")

    ciclos = sorted(dados.ciclos, key=lambda c: c.data_inicio)
    for i, ciclo in enumerate(ciclos, start=1):
        if ciclo.data_fim < ciclo.data_inicio:
            raise ErroDeNegocio(f"Ciclo {i}: a data de fim é anterior à de início")
        if ciclo.data_inicio < dados.data_inicio or ciclo.data_fim > dados.data_fim:
            raise ErroDeNegocio(f"Ciclo {i}: as datas devem estar dentro do período letivo")
        if i > 1 and ciclo.data_inicio <= ciclos[i - 2].data_fim:
            raise ErroDeNegocio(f"Ciclos {i - 1} e {i} se sobrepõem")

    duplicado = db.scalar(
        select(PeriodoLetivo.id).where(func.lower(PeriodoLetivo.nome) == dados.nome.lower())
    )
    if duplicado is not None and (periodo is None or duplicado != periodo.id):
        raise Conflito("Já existe um período letivo com esse nome")

    if periodo is not None and periodo.regime != dados.regime and _periodo_em_uso(db, periodo.id):
        raise Conflito("Não é possível mudar o regime de um período que já tem turmas")

    periodo = periodo or PeriodoLetivo()
    for campo, valor in dados.model_dump(exclude={"ciclos"}).items():
        setattr(periodo, campo, valor)

    # Atualiza os ciclos no lugar (avaliações apontam para eles) e remove os que sobrarem
    existentes = list(periodo.ciclos)
    for i, c in enumerate(ciclos, start=1):
        registro = existentes[i - 1] if i <= len(existentes) else CicloAvaliativo(numero=i)
        registro.nome = c.nome or _nome_ciclo(dados.regime, i)
        registro.data_inicio = c.data_inicio
        registro.data_fim = c.data_fim
        if i > len(existentes):
            periodo.ciclos.append(registro)
    for sobra in existentes[len(ciclos) :]:
        if db.scalar(select(exists().where(Avaliacao.ciclo_id == sobra.id))):
            raise Conflito(f"O {sobra.nome} tem avaliações e não pode ser removido")
        periodo.ciclos.remove(sobra)
    db.add(periodo)
    db.commit()
    return periodo


def _periodo_em_uso(db: Session, periodo_id: int) -> bool:
    return bool(db.scalar(select(exists().where(Turma.periodo_id == periodo_id))))


def excluir_periodo(db: Session, periodo: PeriodoLetivo) -> None:
    if _periodo_em_uso(db, periodo.id):
        raise Conflito("O período letivo tem turmas e não pode ser excluído")
    db.delete(periodo)
    db.commit()


# --- Dia não letivo ----------------------------------------------------------


def salvar_dia_nao_letivo(
    db: Session, dados: DiaNaoLetivoEntrada, dia: DiaNaoLetivo | None = None
) -> DiaNaoLetivo:
    duplicado = db.scalar(select(DiaNaoLetivo.id).where(DiaNaoLetivo.data == dados.data))
    if duplicado is not None and (dia is None or duplicado != dia.id):
        raise Conflito("Essa data já está cadastrada como dia não letivo")
    dia = dia or DiaNaoLetivo()
    dia.data = dados.data
    dia.descricao = dados.descricao
    db.add(dia)
    db.commit()
    return dia


# --- Turma -------------------------------------------------------------------


def salvar_turma(db: Session, dados: TurmaEntrada, turma: Turma | None = None) -> Turma:
    curso = obter(db, Curso, dados.curso_id, "Curso")
    periodo = obter(db, PeriodoLetivo, dados.periodo_id, "Período letivo")
    if curso.regime != periodo.regime:
        raise ErroDeNegocio(
            f"O curso é {curso.regime.lower()}, mas o período é {periodo.regime.lower()}"
        )
    dias = [h.dia_semana for h in dados.horarios]
    if len(dias) != len(set(dias)):
        raise ErroDeNegocio("Há dias da semana repetidos nos horários")

    turma = turma or Turma()
    turma.disciplina = dados.disciplina
    turma.nome = dados.nome
    turma.curso = curso
    turma.periodo = periodo
    turma.carga_horaria_horas = dados.carga_horaria_horas

    # Remove os horários antigos antes de inserir os novos (unicidade de turma+dia)
    if turma.horarios:
        turma.horarios.clear()
        db.flush()
    turma.horarios = [
        TurmaHorario(dia_semana=h.dia_semana, aulas=h.aulas)
        for h in sorted(dados.horarios, key=lambda h: h.dia_semana)
    ]
    db.add(turma)
    db.commit()
    return turma


def excluir_turma(db: Session, turma: Turma) -> None:
    db.delete(turma)
    db.commit()


# --- Estudante ---------------------------------------------------------------


def _estudante_por_matricula(db: Session, matricula: str) -> Estudante | None:
    return db.scalar(select(Estudante).where(Estudante.matricula == matricula))


def adicionar_estudante(db: Session, turma: Turma, dados: EstudanteEntrada) -> Estudante:
    existente = _estudante_por_matricula(db, dados.matricula)
    if existente is not None:
        raise Conflito(f"Já existe estudante com a matrícula {dados.matricula} ({existente.nome})")
    estudante = Estudante(**dados.model_dump())
    turma.estudantes.append(estudante)
    db.commit()
    return estudante


def atualizar_estudante(db: Session, estudante: Estudante, dados: EstudanteEntrada) -> Estudante:
    existente = _estudante_por_matricula(db, dados.matricula)
    if existente is not None and existente.id != estudante.id:
        raise Conflito(f"A matrícula {dados.matricula} já pertence a {existente.nome}")
    for campo, valor in dados.model_dump().items():
        setattr(estudante, campo, valor)
    db.commit()
    return estudante


def desmatricular(db: Session, turma: Turma, estudante: Estudante) -> None:
    if estudante not in turma.estudantes:
        raise NaoEncontrado("O estudante não está matriculado nesta turma")
    turma.estudantes.remove(estudante)
    db.commit()
