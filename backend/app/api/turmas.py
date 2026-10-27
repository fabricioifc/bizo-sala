from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import DbSession, get_usuario_atual
from app.models import Estudante, PeriodoLetivo, Turma
from app.schemas.cadastros import (
    EstudanteEntrada,
    EstudanteSaida,
    Horario,
    ImportacaoEntrada,
    ImportacaoErro,
    ImportacaoResultado,
    TurmaEntrada,
    TurmaSaida,
)
from app.services import cadastros
from app.services.importacao_estudantes import importar_estudantes

router = APIRouter(prefix="/turmas", tags=["turmas"], dependencies=[Depends(get_usuario_atual)])


def _saida(turma: Turma) -> TurmaSaida:
    return TurmaSaida(
        id=turma.id,
        disciplina=turma.disciplina,
        nome=turma.nome,
        curso_id=turma.curso_id,
        curso_nome=turma.curso.nome,
        nivel=turma.curso.nivel,
        periodo_id=turma.periodo_id,
        periodo_nome=turma.periodo.nome,
        carga_horaria_horas=turma.carga_horaria_horas,
        horas_aula_previstas=cadastros.horas_aula_previstas(turma.carga_horaria_horas),
        aulas_por_semana=sum(h.aulas for h in turma.horarios),
        horarios=[Horario.model_validate(h) for h in turma.horarios],
        total_estudantes=len(turma.estudantes),
    )


def _turma(db: DbSession, turma_id: int) -> Turma:
    return cadastros.obter(db, Turma, turma_id, "Turma")


@router.get("", response_model=list[TurmaSaida])
def listar(db: DbSession, periodo_id: int | None = None) -> list[TurmaSaida]:
    consulta = (
        select(Turma)
        .join(Turma.periodo)
        .order_by(PeriodoLetivo.data_inicio.desc(), Turma.disciplina, Turma.nome)
    )
    if periodo_id is not None:
        consulta = consulta.where(Turma.periodo_id == periodo_id)
    return [_saida(t) for t in db.scalars(consulta)]


@router.get("/{turma_id}", response_model=TurmaSaida)
def detalhar(turma_id: int, db: DbSession) -> TurmaSaida:
    return _saida(_turma(db, turma_id))


@router.post("", response_model=TurmaSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: TurmaEntrada, db: DbSession) -> TurmaSaida:
    return _saida(cadastros.salvar_turma(db, dados))


@router.put("/{turma_id}", response_model=TurmaSaida)
def atualizar(turma_id: int, dados: TurmaEntrada, db: DbSession) -> TurmaSaida:
    return _saida(cadastros.salvar_turma(db, dados, _turma(db, turma_id)))


@router.delete("/{turma_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(turma_id: int, db: DbSession) -> None:
    cadastros.excluir_turma(db, _turma(db, turma_id))


# --- Estudantes da turma -----------------------------------------------------


@router.get("/{turma_id}/estudantes", response_model=list[EstudanteSaida])
def listar_estudantes(turma_id: int, db: DbSession) -> list[Estudante]:
    return _turma(db, turma_id).estudantes


@router.post(
    "/{turma_id}/estudantes",
    response_model=EstudanteSaida,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_estudante(turma_id: int, dados: EstudanteEntrada, db: DbSession) -> Estudante:
    return cadastros.adicionar_estudante(db, _turma(db, turma_id), dados)


@router.delete("/{turma_id}/estudantes/{estudante_id}", status_code=status.HTTP_204_NO_CONTENT)
def desmatricular(turma_id: int, estudante_id: int, db: DbSession) -> None:
    estudante = cadastros.obter(db, Estudante, estudante_id, "Estudante")
    cadastros.desmatricular(db, _turma(db, turma_id), estudante)


@router.post("/{turma_id}/estudantes/importar", response_model=ImportacaoResultado)
def importar(turma_id: int, dados: ImportacaoEntrada, db: DbSession) -> ImportacaoResultado:
    r = importar_estudantes(db, _turma(db, turma_id), dados.conteudo, dados.simular)
    return ImportacaoResultado(
        total_linhas=r.total_linhas,
        criados=r.criados,
        atualizados=r.atualizados,
        matriculados=r.matriculados,
        ja_matriculados=r.ja_matriculados,
        erros=[ImportacaoErro(linha=e.linha, mensagem=e.mensagem) for e in r.erros],
        aplicado=r.aplicado,
    )
