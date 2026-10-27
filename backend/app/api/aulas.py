from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import DbSession, get_usuario_atual
from app.models import Aula, Turma
from app.schemas.aulas import (
    AulaDoDia,
    AulaEntrada,
    AulaSaida,
    CancelamentoEntrada,
    CargaHorariaSaida,
    ChamadaEntrada,
    ChamadaEstudante,
    ChamadaSaida,
    FrequenciaEstudante,
    GeracaoResultado,
    RegistroConteudoDados,
)
from app.services import aulas as servico
from app.services.cadastros import obter

router = APIRouter(tags=["aulas"], dependencies=[Depends(get_usuario_atual)])


def _turma(db: DbSession, turma_id: int) -> Turma:
    return obter(db, Turma, turma_id, "Turma")


def _aula(db: DbSession, aula_id: int) -> Aula:
    return obter(db, Aula, aula_id, "Aula")


def _saida(aula: Aula, nao_letivos: dict[date, str]) -> AulaSaida:
    return AulaSaida.model_validate(aula).model_copy(
        update={"dia_nao_letivo": nao_letivos.get(aula.data)}
    )


def _saida_unica(db: DbSession, aula: Aula) -> AulaSaida:
    return _saida(aula, servico.dias_nao_letivos(db, aula.data, aula.data))


# --- Calendário da turma -----------------------------------------------------


@router.get("/turmas/{turma_id}/aulas", response_model=list[AulaSaida])
def listar(turma_id: int, db: DbSession) -> list[AulaSaida]:
    turma = _turma(db, turma_id)
    nao_letivos = servico.dias_nao_letivos(db, turma.periodo.data_inicio, turma.periodo.data_fim)
    return [_saida(a, nao_letivos) for a in servico.aulas_da_turma(db, turma_id)]


@router.post("/turmas/{turma_id}/aulas/gerar", response_model=GeracaoResultado)
def gerar(turma_id: int, db: DbSession) -> GeracaoResultado:
    return GeracaoResultado(criadas=servico.gerar_calendario(db, _turma(db, turma_id)))


@router.post(
    "/turmas/{turma_id}/aulas", response_model=AulaSaida, status_code=status.HTTP_201_CREATED
)
def adicionar_extra(turma_id: int, dados: AulaEntrada, db: DbSession) -> AulaSaida:
    aula = servico.adicionar_aula_extra(db, _turma(db, turma_id), dados)
    return _saida_unica(db, aula)


@router.get("/turmas/{turma_id}/carga-horaria", response_model=CargaHorariaSaida)
def carga_horaria(turma_id: int, db: DbSession) -> CargaHorariaSaida:
    turma = _turma(db, turma_id)
    r = servico.resumo_carga(turma, servico.aulas_da_turma(db, turma_id), date.today())
    return CargaHorariaSaida(
        meta=r.meta,
        dadas=r.dadas,
        previstas=r.previstas,
        em_aberto=r.em_aberto,
        aulas_em_aberto=r.aulas_em_aberto,
        canceladas=r.canceladas,
        projecao=r.projecao,
        saldo=r.saldo,
    )


@router.get("/turmas/{turma_id}/frequencia", response_model=list[FrequenciaEstudante])
def frequencia(turma_id: int, db: DbSession) -> list[FrequenciaEstudante]:
    return [
        FrequenciaEstudante(
            estudante_id=f.estudante.id,
            nome=f.estudante.nome,
            matricula=f.estudante.matricula,
            ativo=f.estudante.ativo,
            faltas=f.faltas,
            horas_aula_registradas=f.horas_aula_registradas,
            percentual_presenca=f.percentual_presenca,
            faltas_restantes=f.faltas_restantes,
        )
        for f in servico.frequencia_da_turma(db, _turma(db, turma_id))
    ]


# --- Aula --------------------------------------------------------------------


@router.get("/aulas", response_model=list[AulaDoDia])
def aulas_do_dia(db: DbSession, data: date) -> list[AulaDoDia]:
    consulta = select(Aula, Turma).join(Turma).where(Aula.data == data).order_by(Turma.disciplina)
    nao_letivos = servico.dias_nao_letivos(db, data, data)
    return [
        AulaDoDia(
            **_saida(aula, nao_letivos).model_dump(),
            disciplina=turma.disciplina,
            turma_nome=turma.nome,
        )
        for aula, turma in db.execute(consulta).tuples()
    ]


@router.put("/aulas/{aula_id}", response_model=AulaSaida)
def editar(aula_id: int, dados: AulaEntrada, db: DbSession) -> AulaSaida:
    aula = _aula(db, aula_id)
    servico.editar_aula(db, aula, _turma(db, aula.turma_id), dados)
    return _saida_unica(db, aula)


@router.post("/aulas/{aula_id}/cancelar", response_model=AulaSaida)
def cancelar(aula_id: int, dados: CancelamentoEntrada, db: DbSession) -> AulaSaida:
    return _saida_unica(db, servico.cancelar_aula(db, _aula(db, aula_id), dados.motivo))


@router.post("/aulas/{aula_id}/reabrir", response_model=AulaSaida)
def reabrir(aula_id: int, db: DbSession) -> AulaSaida:
    return _saida_unica(db, servico.reabrir_aula(db, _aula(db, aula_id)))


@router.delete("/aulas/{aula_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(aula_id: int, db: DbSession) -> None:
    servico.excluir_aula(db, _aula(db, aula_id))


@router.get("/aulas/{aula_id}/chamada", response_model=ChamadaSaida)
def obter_chamada(aula_id: int, db: DbSession) -> ChamadaSaida:
    aula = _aula(db, aula_id)
    turma = _turma(db, aula.turma_id)
    faltas = servico.faltas_da_aula(db, aula.id)
    # Ativos + inativos que já têm registro nesta aula
    estudantes = [e for e in turma.estudantes if e.ativo or e.id in faltas]
    return ChamadaSaida(
        aula=_saida_unica(db, aula),
        disciplina=turma.disciplina,
        turma_nome=turma.nome,
        estudantes=[
            ChamadaEstudante(
                estudante_id=e.id, nome=e.nome, matricula=e.matricula, faltas=faltas.get(e.id)
            )
            for e in estudantes
        ],
    )


@router.put("/aulas/{aula_id}/chamada", response_model=AulaSaida)
def salvar_chamada(aula_id: int, dados: ChamadaEntrada, db: DbSession) -> AulaSaida:
    aula = _aula(db, aula_id)
    servico.salvar_chamada(db, aula, _turma(db, aula.turma_id), dados.registros)
    return _saida_unica(db, aula)


# --- Conteúdo ----------------------------------------------------------------


@router.get("/turmas/{turma_id}/conteudos", response_model=list[RegistroConteudoDados])
def listar_conteudos(turma_id: int, db: DbSession) -> list[RegistroConteudoDados]:
    _turma(db, turma_id)
    return [
        RegistroConteudoDados.model_validate(r) for r in servico.conteudos_da_turma(db, turma_id)
    ]


@router.put("/turmas/{turma_id}/conteudos", response_model=list[RegistroConteudoDados])
def salvar_conteudos(
    turma_id: int, dados: list[RegistroConteudoDados], db: DbSession
) -> list[RegistroConteudoDados]:
    registros = servico.salvar_conteudos(db, _turma(db, turma_id), dados)
    return [RegistroConteudoDados.model_validate(r) for r in registros]
