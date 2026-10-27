from decimal import Decimal as D
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models import Substituicao, TipoAvaliacao
from app.services.notas import AvaliacaoCalculo, NotaCalculo, calcular_ciclo, media_final
from tests.test_cadastros import PERIODO_2026, _criar, _turma

REG = TipoAvaliacao.REGULAR
REC = TipoAvaliacao.RECUPERACAO


def _regular(id_: int, peso: str = "1", lancada: bool = True) -> AvaliacaoCalculo:
    return AvaliacaoCalculo(id=id_, peso=D(peso), tipo=REG, lancada=lancada)


def _rec(id_: int, substituicao: Substituicao, alvo: int | None = None) -> AvaliacaoCalculo:
    return AvaliacaoCalculo(
        id=id_, peso=D("1"), tipo=REC, substituicao=substituicao, substitui_avaliacao_id=alvo
    )


def _notas(**valores: str) -> dict[int, NotaCalculo]:
    return {int(k[1:]): NotaCalculo(D(v)) for k, v in valores.items()}


# --- Cálculo (funções puras) -------------------------------------------------


def test_media_ponderada() -> None:
    r = calcular_ciclo([_regular(1, "1"), _regular(2, "2")], _notas(a1="6", a2="9"))
    assert r.media == D("8.0")


def test_arredondamento_uma_casa() -> None:
    # (7 + 7 + 8) / 3 = 7,333 → 7,3
    tres = [_regular(1), _regular(2), _regular(3)]
    assert calcular_ciclo(tres, _notas(a1="7", a2="7", a3="8")).media == D("7.3")
    # (6,0 + 5,1) / 2 = 5,55 → 5,6 (arredonda a segunda casa para cima, art. 206)
    duas = [_regular(1), _regular(2)]
    assert calcular_ciclo(duas, _notas(a1="6", a2="5.1")).media == D("5.6")


def test_sem_nota_conta_zero_e_avaliacao_nao_lancada_e_ignorada() -> None:
    avaliacoes = [_regular(1), _regular(2), _regular(3, lancada=False)]
    assert calcular_ciclo(avaliacoes, _notas(a1="8")).media == D("4.0")


def test_sem_avaliacao_lancada_nao_tem_media() -> None:
    assert calcular_ciclo([_regular(1, lancada=False)], {}).media is None


def test_recuperacao_do_ciclo_so_substitui_quando_maior() -> None:
    avaliacoes = [_regular(1), _regular(2), _rec(9, Substituicao.CICLO)]
    r = calcular_ciclo(avaliacoes, _notas(a1="4", a2="5", a9="7"))
    assert (r.media_sem_recuperacao, r.media) == (D("4.5"), D("7.0"))
    assert [(s.recuperacao_id, s.avaliacao_id) for s in r.substituicoes] == [(9, None)]

    r = calcular_ciclo(avaliacoes, _notas(a1="4", a2="5", a9="3"))
    assert r.media == D("4.5")
    assert r.substituicoes == []


def test_recuperacao_de_avaliacao_especifica() -> None:
    avaliacoes = [_regular(1), _regular(2), _rec(9, Substituicao.AVALIACAO, alvo=1)]
    assert calcular_ciclo(avaliacoes, _notas(a1="2", a2="8", a9="6")).media == D("7.0")


def test_reavaliacao_substitui_a_que_mais_aumenta_a_media() -> None:
    # A1 (peso 1) = 2,0; A2 (peso 3) = 5,0; reavaliação 8,0
    # Trocar A2 ganha 3 * 3 = 9 pontos ponderados; trocar A1 ganha 6. Escolhe A2.
    avaliacoes = [_regular(1, "1"), _regular(2, "3"), _rec(9, Substituicao.MELHOR)]
    r = calcular_ciclo(avaliacoes, _notas(a1="2", a2="5", a9="8"))
    assert r.media == D("6.5")
    assert r.substituicoes[0].avaliacao_id == 2


def test_reavaliacao_respeita_escolha_do_professor() -> None:
    avaliacoes = [_regular(1, "1"), _regular(2, "3"), _rec(9, Substituicao.MELHOR)]
    notas = _notas(a1="2", a2="5")
    notas[9] = NotaCalculo(D("8"), substitui_avaliacao_id=1)
    r = calcular_ciclo(avaliacoes, notas)
    assert r.media == D("5.8")  # (8 + 15) / 4 = 5,75 → 5,8
    assert r.substituicoes[0].avaliacao_id == 1


def test_media_final_dos_ciclos() -> None:
    assert media_final([D("6"), D("7"), D("5.5")]) == D("6.2")
    assert media_final([D("6"), None]) == D("6.0")
    assert media_final([None, None]) is None


# --- API ---------------------------------------------------------------------


@pytest.fixture
def turma(api: TestClient) -> dict[str, Any]:
    t = _turma(api)
    periodo = api.get("/api/periodos").json()[0]
    t["ciclos"] = [c["id"] for c in periodo["ciclos"]]
    return t


def _avaliacao(api: TestClient, turma: dict[str, Any], **dados: Any) -> dict[str, Any]:
    return _criar(api, f"/api/turmas/{turma['id']}/avaliacoes", dados)


def test_lancar_notas_e_boletim(api: TestClient, turma: dict[str, Any]) -> None:
    c1 = turma["ciclos"][0]
    ana = _criar(api, f"/api/turmas/{turma['id']}/estudantes", {"nome": "Ana", "matricula": "1"})
    p1 = _avaliacao(api, turma, ciclo_id=c1, nome="Prova 1", peso=2)
    t1 = _avaliacao(api, turma, ciclo_id=c1, nome="Trabalho", peso=1)
    rec = _avaliacao(api, turma, ciclo_id=c1, nome="Recuperação", tipo="RECUPERACAO")
    assert rec["substituicao"] == "CICLO"  # padrão do EMI

    url = f"/api/turmas/{turma['id']}/notas"
    notas = [
        {"avaliacao_id": p1["id"], "estudante_id": ana["id"], "valor": 4},
        {"avaliacao_id": t1["id"], "estudante_id": ana["id"], "valor": 5.5},
    ]
    assert api.put(url, json=notas).status_code == 204

    boletim = api.get(f"/api/turmas/{turma['id']}/boletim").json()
    assert boletim["media_aprovacao"] == 6.0
    (linha,) = boletim["estudantes"]
    ciclo1 = linha["ciclos"][0]
    assert ciclo1["media"] == 4.5  # (8 + 5,5) / 3
    assert ciclo1["abaixo_da_media"] is True
    assert linha["situacao"] == "EM_ANDAMENTO"

    # Recuperação 7,0 substitui a nota do trimestre
    api.put(url, json=[{"avaliacao_id": rec["id"], "estudante_id": ana["id"], "valor": 7}])
    ciclo1 = api.get(f"/api/turmas/{turma['id']}/boletim").json()["estudantes"][0]["ciclos"][0]
    assert (ciclo1["media"], ciclo1["media_sem_recuperacao"]) == (7.0, 4.5)

    # Apagar nota
    api.put(url, json=[{"avaliacao_id": rec["id"], "estudante_id": ana["id"], "valor": None}])
    assert len(api.get(url).json()) == 2


def test_nota_invalida(api: TestClient, turma: dict[str, Any]) -> None:
    ana = _criar(api, f"/api/turmas/{turma['id']}/estudantes", {"nome": "Ana", "matricula": "1"})
    p1 = _avaliacao(api, turma, ciclo_id=turma["ciclos"][0], nome="P1")
    url = f"/api/turmas/{turma['id']}/notas"
    nota = {"avaliacao_id": p1["id"], "estudante_id": ana["id"]}
    assert api.put(url, json=[{**nota, "valor": 10.5}]).status_code == 422
    assert api.put(url, json=[{**nota, "valor": 7.25}]).status_code == 422
    r = api.put(url, json=[{**nota, "estudante_id": 9999, "valor": 7}])
    assert r.status_code == 422


def test_recuperacao_de_avaliacao_especifica_exige_regular_do_mesmo_ciclo(
    api: TestClient, turma: dict[str, Any]
) -> None:
    c1, c2 = turma["ciclos"][:2]
    p_c2 = _avaliacao(api, turma, ciclo_id=c2, nome="P1 do 2º")
    r = api.post(
        f"/api/turmas/{turma['id']}/avaliacoes",
        json={
            "ciclo_id": c1,
            "nome": "Rec",
            "tipo": "RECUPERACAO",
            "substituicao": "AVALIACAO",
            "substitui_avaliacao_id": p_c2["id"],
        },
    )
    assert r.status_code == 422


def test_editar_periodo_preserva_ciclos_com_avaliacoes(
    api: TestClient, turma: dict[str, Any]
) -> None:
    _avaliacao(api, turma, ciclo_id=turma["ciclos"][2], nome="P1 do 3º")
    periodo = api.get("/api/periodos").json()[0]
    url = f"/api/periodos/{periodo['id']}"

    # Mudar datas mantém os mesmos ciclos (mesmos ids)
    ciclos = [{**c, "nome": None} for c in PERIODO_2026["ciclos"]]
    ciclos[0]["data_fim"] = "2026-05-14"
    r = api.put(url, json={**PERIODO_2026, "ciclos": ciclos})
    assert [c["id"] for c in r.json()["ciclos"]] == turma["ciclos"]

    # Remover o 3º trimestre, que tem avaliação, é bloqueado
    r = api.put(url, json={**PERIODO_2026, "ciclos": PERIODO_2026["ciclos"][:2]})
    assert r.status_code == 409
