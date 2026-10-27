from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, get_usuario_atual
from app.models import Avaliacao, Turma
from app.schemas.avaliacoes import (
    AvaliacaoEntrada,
    AvaliacaoSaida,
    Boletim,
    BoletimEstudante,
    CicloDoEstudante,
    CicloResumo,
    NotaEntrada,
    NotaSaida,
    SubstituicaoSaida,
)
from app.services import avaliacoes as servico
from app.services.cadastros import obter

router = APIRouter(tags=["avaliacoes"], dependencies=[Depends(get_usuario_atual)])


def _turma(db: DbSession, turma_id: int) -> Turma:
    return obter(db, Turma, turma_id, "Turma")


@router.get("/turmas/{turma_id}/avaliacoes", response_model=list[AvaliacaoSaida])
def listar(turma_id: int, db: DbSession) -> list[Avaliacao]:
    _turma(db, turma_id)
    return servico.avaliacoes_da_turma(db, turma_id)


@router.post(
    "/turmas/{turma_id}/avaliacoes",
    response_model=AvaliacaoSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar(turma_id: int, dados: AvaliacaoEntrada, db: DbSession) -> Avaliacao:
    return servico.salvar_avaliacao(db, _turma(db, turma_id), dados)


@router.put("/avaliacoes/{avaliacao_id}", response_model=AvaliacaoSaida)
def atualizar(avaliacao_id: int, dados: AvaliacaoEntrada, db: DbSession) -> Avaliacao:
    avaliacao = obter(db, Avaliacao, avaliacao_id, "Avaliação")
    return servico.salvar_avaliacao(db, _turma(db, avaliacao.turma_id), dados, avaliacao)


@router.delete("/avaliacoes/{avaliacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(avaliacao_id: int, db: DbSession) -> None:
    db.delete(obter(db, Avaliacao, avaliacao_id, "Avaliação"))
    db.commit()


@router.get("/turmas/{turma_id}/notas", response_model=list[NotaSaida])
def listar_notas(turma_id: int, db: DbSession) -> list[NotaSaida]:
    _turma(db, turma_id)
    return [NotaSaida.model_validate(n) for n in servico.notas_da_turma(db, turma_id)]


@router.put("/turmas/{turma_id}/notas", status_code=status.HTTP_204_NO_CONTENT)
def salvar_notas(turma_id: int, dados: list[NotaEntrada], db: DbSession) -> None:
    servico.salvar_notas(db, _turma(db, turma_id), dados)


@router.get("/turmas/{turma_id}/boletim", response_model=Boletim)
def boletim(turma_id: int, db: DbSession) -> Boletim:
    turma = _turma(db, turma_id)
    media = turma.curso.media_aprovacao
    estudantes = {e.id: e for e in turma.estudantes}
    return Boletim(
        media_aprovacao=float(media),
        ciclos=[
            CicloResumo(
                ciclo_id=c.ciclo.id,
                numero=c.ciclo.numero,
                nome=c.ciclo.nome,
                data_inicio=c.ciclo.data_inicio,
                data_fim=c.ciclo.data_fim,
                horas_aula_dadas=c.horas_aula_dadas,
                recuperacao_min=c.recuperacao_min,
                recuperacao_max=c.recuperacao_max,
            )
            for c in servico.ciclos_da_turma(db, turma)
        ],
        estudantes=[
            BoletimEstudante(
                estudante_id=linha.estudante_id,
                nome=estudantes[linha.estudante_id].nome,
                matricula=estudantes[linha.estudante_id].matricula,
                ativo=estudantes[linha.estudante_id].ativo,
                ciclos=[
                    CicloDoEstudante(
                        ciclo_id=ciclo_id,
                        media=r.media,
                        media_sem_recuperacao=r.media_sem_recuperacao,
                        abaixo_da_media=r.media is not None and r.media < media,
                        substituicoes=[
                            SubstituicaoSaida(
                                recuperacao_id=s.recuperacao_id, avaliacao_id=s.avaliacao_id
                            )
                            for s in r.substituicoes
                        ],
                    )
                    for ciclo_id, r in linha.ciclos.items()
                ],
                media_final=linha.media_final,
                percentual_presenca=linha.percentual_presenca,
                situacao=linha.situacao,
            )
            for linha in servico.boletim(db, turma)
        ],
    )
