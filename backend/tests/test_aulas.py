from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models import Aula, OrigemAula, StatusAula, Turma
from app.services.aulas import resumo_carga
from tests.test_cadastros import _criar, _turma

# Período de teste: 09/02/2026 (segunda) a 11/12/2026 (sexta); turma às quartas.
# Quartas no período: 11/02 a 09/12 = 44 aulas de 2 horas-aula.
QUARTAS_NO_PERIODO = 44


@pytest.fixture
def turma(api: TestClient) -> dict[str, Any]:
    return _turma(api, horarios=[{"dia_semana": 2, "aulas": 2}])


def _gerar(api: TestClient, turma_id: int) -> int:
    r = api.post(f"/api/turmas/{turma_id}/aulas/gerar")
    assert r.status_code == 200, r.text
    criadas: int = r.json()["criadas"]
    return criadas


def _aulas(api: TestClient, turma_id: int) -> list[dict[str, Any]]:
    aulas: list[dict[str, Any]] = api.get(f"/api/turmas/{turma_id}/aulas").json()
    return aulas


def _estudantes(api: TestClient, turma_id: int, n: int) -> list[int]:
    url = f"/api/turmas/{turma_id}/estudantes"
    return [_criar(api, url, {"nome": f"Est {i}", "matricula": f"M{i}"})["id"] for i in range(n)]


# --- Calendário --------------------------------------------------------------


def test_gera_aulas_da_grade_sem_duplicar(api: TestClient, turma: dict[str, Any]) -> None:
    assert _gerar(api, turma["id"]) == QUARTAS_NO_PERIODO
    aulas = _aulas(api, turma["id"])
    assert aulas[0]["data"] == "2026-02-11"
    assert aulas[-1]["data"] == "2026-12-09"
    assert {(a["status"], a["origem"], a["horas_aula"]) for a in aulas} == {
        ("PREVISTA", "GRADE", 2)
    }
    assert _gerar(api, turma["id"]) == 0


def test_gerar_pula_dias_nao_letivos(api: TestClient, turma: dict[str, Any]) -> None:
    _criar(api, "/api/dias-nao-letivos", {"data": "2026-04-22", "descricao": "Recesso"})
    assert _gerar(api, turma["id"]) == QUARTAS_NO_PERIODO - 1
    assert "2026-04-22" not in {a["data"] for a in _aulas(api, turma["id"])}


def test_aula_em_dia_que_virou_nao_letivo_e_sinalizada(
    api: TestClient, turma: dict[str, Any]
) -> None:
    _gerar(api, turma["id"])
    _criar(api, "/api/dias-nao-letivos", {"data": "2026-04-22", "descricao": "Greve"})
    aula = next(a for a in _aulas(api, turma["id"]) if a["data"] == "2026-04-22")
    assert aula["dia_nao_letivo"] == "Greve"


def test_aula_extra_no_mesmo_dia_e_fora_do_periodo(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    url = f"/api/turmas/{turma['id']}/aulas"
    extra = _criar(api, url, {"data": "2026-02-11", "horas_aula": 1})
    assert extra["origem"] == "EXTRA"
    assert len([a for a in _aulas(api, turma["id"]) if a["data"] == "2026-02-11"]) == 2

    assert api.post(url, json={"data": "2027-01-10", "horas_aula": 1}).status_code == 422


def test_aulas_do_dia(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    aulas = api.get("/api/aulas", params={"data": "2026-03-04"}).json()
    assert [(a["disciplina"], a["turma_nome"]) for a in aulas] == [("Programação I", "1º INFO")]
    assert api.get("/api/aulas", params={"data": "2026-03-05"}).json() == []


# --- Chamada -----------------------------------------------------------------


def test_chamada_registra_faltas_por_hora_aula(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    ana, bruno = _estudantes(api, turma["id"], 2)
    aula = _aulas(api, turma["id"])[0]
    url = f"/api/aulas/{aula['id']}/chamada"

    assert [e["faltas"] for e in api.get(url).json()["estudantes"]] == [None, None]

    # Ana chegou atrasada: 1 falta das 2 horas-aula
    registros = [{"estudante_id": ana, "faltas": 1}, {"estudante_id": bruno, "faltas": 0}]
    r = api.put(url, json={"registros": registros})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "DADA"
    assert {e["estudante_id"]: e["faltas"] for e in api.get(url).json()["estudantes"]} == {
        ana: 1,
        bruno: 0,
    }

    # Refazer a chamada substitui a anterior
    api.put(url, json={"registros": [{"estudante_id": ana, "faltas": 2}]})
    assert {e["estudante_id"]: e["faltas"] for e in api.get(url).json()["estudantes"]} == {
        ana: 2,
        bruno: None,
    }


def test_chamada_valida_faltas_e_matricula(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    (ana,) = _estudantes(api, turma["id"], 1)
    url = f"/api/aulas/{_aulas(api, turma['id'])[0]['id']}/chamada"

    r = api.put(url, json={"registros": [{"estudante_id": ana, "faltas": 3}]})
    assert r.status_code == 422
    r = api.put(url, json={"registros": [{"estudante_id": 9999, "faltas": 0}]})
    assert r.status_code == 422


def test_cancelar_descarta_chamada_e_reabrir(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    (ana,) = _estudantes(api, turma["id"], 1)
    aula_id = _aulas(api, turma["id"])[0]["id"]
    api.put(
        f"/api/aulas/{aula_id}/chamada", json={"registros": [{"estudante_id": ana, "faltas": 2}]}
    )

    r = api.post(f"/api/aulas/{aula_id}/cancelar", json={"motivo": "Recuperação paralela"})
    assert (r.json()["status"], r.json()["motivo_cancelamento"]) == (
        "CANCELADA",
        "Recuperação paralela",
    )
    assert api.get(f"/api/turmas/{turma['id']}/frequencia").json()[0]["faltas"] == 0

    r = api.put(f"/api/aulas/{aula_id}/chamada", json={"registros": []})
    assert r.status_code == 422

    assert api.post(f"/api/aulas/{aula_id}/reabrir").json()["status"] == "PREVISTA"
    assert api.post(f"/api/aulas/{aula_id}/reabrir").status_code == 422


def test_editar_aula_nao_reduz_abaixo_das_faltas(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    (ana,) = _estudantes(api, turma["id"], 1)
    aula = _aulas(api, turma["id"])[0]
    api.put(
        f"/api/aulas/{aula['id']}/chamada", json={"registros": [{"estudante_id": ana, "faltas": 2}]}
    )
    r = api.put(f"/api/aulas/{aula['id']}", json={"data": aula["data"], "horas_aula": 1})
    assert r.status_code == 422
    r = api.put(f"/api/aulas/{aula['id']}", json={"data": "2026-02-12", "horas_aula": 3})
    assert r.json()["data"] == "2026-02-12"


# --- Carga horária e frequência ---------------------------------------------


def _aula(data_: date, horas: int, status: StatusAula) -> Aula:
    return Aula(data=data_, horas_aula=horas, status=status, origem=OrigemAula.GRADE)


def test_resumo_carga() -> None:
    turma = Turma(carga_horaria_horas=60)  # meta: 72 horas-aula
    aulas = [
        _aula(date(2026, 3, 4), 2, StatusAula.DADA),
        _aula(date(2026, 3, 11), 2, StatusAula.PREVISTA),  # passada, em aberto
        _aula(date(2026, 3, 18), 2, StatusAula.CANCELADA),
        _aula(date(2026, 3, 25), 2, StatusAula.PREVISTA),  # futura
    ]
    r = resumo_carga(turma, aulas, hoje=date(2026, 3, 20))
    assert (r.meta, r.dadas, r.previstas, r.canceladas) == (72, 2, 4, 2)
    assert (r.em_aberto, r.aulas_em_aberto) == (2, 1)
    assert (r.projecao, r.saldo) == (6, -66)


def test_carga_horaria_da_turma(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    aula_id = _aulas(api, turma["id"])[0]["id"]
    api.post(f"/api/aulas/{aula_id}/cancelar", json={"motivo": "Evento"})
    r = api.get(f"/api/turmas/{turma['id']}/carga-horaria").json()
    assert r["meta"] == 72
    assert r["canceladas"] == 2
    assert r["projecao"] == (QUARTAS_NO_PERIODO - 1) * 2
    assert r["saldo"] == r["projecao"] - 72


def test_frequencia_por_estudante(api: TestClient, turma: dict[str, Any]) -> None:
    _gerar(api, turma["id"])
    ana, bruno = _estudantes(api, turma["id"], 2)
    for aula in _aulas(api, turma["id"])[:2]:
        api.put(
            f"/api/aulas/{aula['id']}/chamada",
            json={"registros": [{"estudante_id": ana, "faltas": 1}]},
        )
    freq = {f["estudante_id"]: f for f in api.get(f"/api/turmas/{turma['id']}/frequencia").json()}
    assert freq[ana]["faltas"] == 2
    assert freq[ana]["horas_aula_registradas"] == 4
    assert freq[ana]["percentual_presenca"] == 50.0
    assert freq[ana]["faltas_restantes"] == 18 - 2  # 25% de 72 = 18
    assert freq[bruno]["percentual_presenca"] is None


# --- Conteúdo ----------------------------------------------------------------


def test_registro_de_conteudo(api: TestClient, turma: dict[str, Any]) -> None:
    url = f"/api/turmas/{turma['id']}/conteudos"
    registros = [
        {"data_inicio": "2026-02-18", "data_fim": "2026-03-04", "texto": "Variáveis e tipos"},
        {"data_inicio": "2026-02-11", "data_fim": "2026-02-11", "texto": " Apresentação "},
    ]
    r = api.put(url, json=registros)
    assert r.status_code == 200, r.text
    assert [x["texto"] for x in api.get(url).json()] == ["Apresentação", "Variáveis e tipos"]

    # Substitui tudo
    api.put(url, json=[registros[0]])
    assert len(api.get(url).json()) == 1


def test_registro_de_conteudo_rejeita_sobreposicao(api: TestClient, turma: dict[str, Any]) -> None:
    r = api.put(
        f"/api/turmas/{turma['id']}/conteudos",
        json=[
            {"data_inicio": "2026-02-11", "data_fim": "2026-02-18", "texto": "A"},
            {"data_inicio": "2026-02-18", "data_fim": "2026-02-25", "texto": "B"},
        ],
    )
    assert r.status_code == 422
