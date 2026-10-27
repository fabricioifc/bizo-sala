from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models import TipoAlerta
from app.services.alertas import detectar
from tests.test_cadastros import CURSO_EMI, _criar, _turma

# --- Detecção (função pura) --------------------------------------------------

INICIO = date(2026, 3, 2)


def _encontros(padrao: str) -> list[tuple[date, bool]]:
    """'F' = faltou o dia inteiro, 'P' = presente (ou atraso), um encontro por semana."""
    return [(INICIO + timedelta(weeks=i), c == "F") for i, c in enumerate(padrao)]


def _resumo(padrao: str, consecutivas: int | None, alternadas: int | None) -> list[tuple[str, int]]:
    return [
        (o.tipo.value, (o.data_gatilho - INICIO).days // 7)
        for o in detectar(_encontros(padrao), consecutivas, alternadas)
    ]


def test_duas_consecutivas_gera_um_alerta_por_sequencia() -> None:
    # Sequência de 3 faltas gera só um alerta (no 2º encontro); nova sequência, novo alerta
    assert _resumo("PFFFPFF", 2, None) == [("CONSECUTIVAS", 2), ("CONSECUTIVAS", 6)]


def test_presenca_interrompe_a_sequencia() -> None:
    assert _resumo("FPFPF", 2, None) == []


def test_alternadas_a_cada_cinco_faltas() -> None:
    assert _resumo("FPFPFPFPF" + "PFFFFF", None, 5) == [("ALTERNADAS", 8), ("ALTERNADAS", 14)]


def test_datas_do_alerta() -> None:
    (o,) = detectar(_encontros("PFF"), 2, None)
    assert o.tipo == TipoAlerta.CONSECUTIVAS
    assert o.datas == (INICIO + timedelta(weeks=1), INICIO + timedelta(weeks=2))


def test_sem_limites_nao_gera_alerta() -> None:
    assert _resumo("FFFFFFFFFF", None, None) == []


# --- Integração com a chamada ------------------------------------------------


@pytest.fixture
def cenario(api: TestClient) -> dict[str, Any]:
    turma = _turma(api, horarios=[{"dia_semana": 2, "aulas": 2}])
    api.post(f"/api/turmas/{turma['id']}/aulas/gerar")
    estudante = _criar(
        api, f"/api/turmas/{turma['id']}/estudantes", {"nome": "Ana", "matricula": "1"}
    )
    aulas = api.get(f"/api/turmas/{turma['id']}/aulas").json()
    return {"turma": turma, "estudante": estudante["id"], "aulas": [a["id"] for a in aulas]}


def _chamada(api: TestClient, aula_id: int, estudante_id: int, faltas: int) -> None:
    r = api.put(
        f"/api/aulas/{aula_id}/chamada",
        json={"registros": [{"estudante_id": estudante_id, "faltas": faltas}]},
    )
    assert r.status_code == 200, r.text


def _pendentes(api: TestClient) -> list[dict[str, Any]]:
    alertas: list[dict[str, Any]] = api.get("/api/alertas", params={"status": "PENDENTE"}).json()
    return alertas


def test_duas_faltas_seguidas_geram_alerta(api: TestClient, cenario: dict[str, Any]) -> None:
    a1, a2 = cenario["aulas"][:2]
    _chamada(api, a1, cenario["estudante"], 2)
    assert _pendentes(api) == []
    _chamada(api, a2, cenario["estudante"], 2)

    (alerta,) = _pendentes(api)
    assert alerta["tipo"] == "CONSECUTIVAS"
    assert alerta["estudante_nome"] == "Ana"
    assert alerta["datas"] == ["2026-02-11", "2026-02-18"]
    assert api.get("/api/alertas/resumo").json() == {"pendentes": 1}


def test_atraso_nao_conta_para_o_alerta(api: TestClient, cenario: dict[str, Any]) -> None:
    a1, a2 = cenario["aulas"][:2]
    _chamada(api, a1, cenario["estudante"], 2)
    _chamada(api, a2, cenario["estudante"], 1)  # chegou atrasada
    assert _pendentes(api) == []


def test_corrigir_chamada_remove_alerta_pendente(api: TestClient, cenario: dict[str, Any]) -> None:
    a1, a2 = cenario["aulas"][:2]
    _chamada(api, a1, cenario["estudante"], 2)
    _chamada(api, a2, cenario["estudante"], 2)
    _chamada(api, a2, cenario["estudante"], 0)
    assert _pendentes(api) == []

    _chamada(api, a2, cenario["estudante"], 2)
    api.post(f"/api/aulas/{a2}/cancelar", json={"motivo": "Evento"})
    assert _pendentes(api) == []


def test_alerta_avisado_e_mantido(api: TestClient, cenario: dict[str, Any]) -> None:
    a1, a2 = cenario["aulas"][:2]
    _chamada(api, a1, cenario["estudante"], 2)
    _chamada(api, a2, cenario["estudante"], 2)
    (alerta,) = _pendentes(api)

    r = api.post(
        f"/api/alertas/{alerta['id']}/resolver",
        json={"status": "AVISADO", "observacao": "Avisado por e-mail"},
    )
    assert r.json()["status"] == "AVISADO"
    assert r.json()["resolvido_em"] is not None

    # Mesmo corrigindo a chamada, o alerta já avisado continua no histórico
    _chamada(api, a2, cenario["estudante"], 0)
    assert len(api.get("/api/alertas", params={"status": "AVISADO"}).json()) == 1

    # Resolver de novo não é permitido; reabrir é
    url = f"/api/alertas/{alerta['id']}/resolver"
    assert api.post(url, json={"status": "DESCARTADO"}).status_code == 422
    assert api.post(url, json={"status": "PENDENTE"}).json()["status"] == "PENDENTE"


def test_desativar_alerta_no_curso_remove_pendentes(
    api: TestClient, cenario: dict[str, Any]
) -> None:
    a1, a2 = cenario["aulas"][:2]
    _chamada(api, a1, cenario["estudante"], 2)
    _chamada(api, a2, cenario["estudante"], 2)
    assert len(_pendentes(api)) == 1

    curso_id = cenario["turma"]["curso_id"]
    sem_alerta = {**CURSO_EMI, "alerta_faltas_consecutivas": None, "alerta_faltas_alternadas": None}
    api.put(f"/api/cursos/{curso_id}", json=sem_alerta)
    assert _pendentes(api) == []
