from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.services.cadastros import horas_aula_previstas

CURSO_EMI = {
    "nome": "Técnico em Informática Integrado",
    "nivel": "EMI",
    "regime": "ANUAL",
    "media_aprovacao": 6.0,
    "alerta_faltas_consecutivas": 2,
    "alerta_faltas_alternadas": 5,
}
PERIODO_2026 = {
    "nome": "2026",
    "regime": "ANUAL",
    "ano": 2026,
    "data_inicio": "2026-02-09",
    "data_fim": "2026-12-11",
    "ciclos": [
        {"data_inicio": "2026-02-09", "data_fim": "2026-05-15"},
        {"data_inicio": "2026-05-18", "data_fim": "2026-08-28"},
        {"data_inicio": "2026-08-31", "data_fim": "2026-12-11"},
    ],
}


def _criar(api: TestClient, url: str, dados: dict[str, Any]) -> dict[str, Any]:
    r = api.post(url, json=dados)
    assert r.status_code == 201, r.text
    resposta: dict[str, Any] = r.json()
    return resposta


def _turma(api: TestClient, **extra: Any) -> dict[str, Any]:
    curso = _criar(api, "/api/cursos", CURSO_EMI)
    periodo = _criar(api, "/api/periodos", PERIODO_2026)
    dados = {
        "disciplina": "Programação I",
        "nome": "1º INFO",
        "curso_id": curso["id"],
        "periodo_id": periodo["id"],
        "carga_horaria_horas": 60,
        "horarios": [{"dia_semana": 2, "aulas": 2}],
        **extra,
    }
    return _criar(api, "/api/turmas", dados)


def test_rotas_exigem_login(client: TestClient) -> None:
    assert client.get("/api/cursos").status_code == 401


@pytest.mark.parametrize(("horas", "esperado"), [(60, 72), (120, 144), (30, 36), (1, 2)])
def test_horas_aula_previstas(horas: int, esperado: int) -> None:
    assert horas_aula_previstas(horas) == esperado


# --- Curso -------------------------------------------------------------------


def test_curso_crud(api: TestClient) -> None:
    curso = _criar(api, "/api/cursos", CURSO_EMI)
    assert curso["media_aprovacao"] == 6.0

    r = api.put(f"/api/cursos/{curso['id']}", json={**CURSO_EMI, "media_aprovacao": 7})
    assert r.json()["media_aprovacao"] == 7.0

    assert api.post("/api/cursos", json=CURSO_EMI).status_code == 409
    assert api.delete(f"/api/cursos/{curso['id']}").status_code == 204
    assert api.get("/api/cursos").json() == []


def test_graduacao_nao_tem_alerta_sisae(api: TestClient) -> None:
    curso = _criar(
        api,
        "/api/cursos",
        {**CURSO_EMI, "nome": "Ciência da Computação", "nivel": "GRADUACAO", "regime": "SEMESTRAL"},
    )
    assert curso["alerta_faltas_consecutivas"] is None
    assert curso["alerta_faltas_alternadas"] is None


def test_curso_com_turma_nao_pode_ser_excluido(api: TestClient) -> None:
    turma = _turma(api)
    r = api.delete(f"/api/cursos/{turma['curso_id']}")
    assert r.status_code == 409
    assert "turmas" in r.json()["detail"]


# --- Período -----------------------------------------------------------------


def test_periodo_gera_nomes_dos_trimestres(api: TestClient) -> None:
    periodo = _criar(api, "/api/periodos", PERIODO_2026)
    assert [c["nome"] for c in periodo["ciclos"]] == [
        "1º trimestre",
        "2º trimestre",
        "3º trimestre",
    ]


def test_periodo_semestral_exige_semestre(api: TestClient) -> None:
    dados = {**PERIODO_2026, "nome": "2026/1", "regime": "SEMESTRAL"}
    r = api.post("/api/periodos", json=dados)
    assert r.status_code == 422
    assert "semestre" in r.json()["detail"]


def test_periodo_rejeita_ciclo_fora_das_datas(api: TestClient) -> None:
    ciclos = [{"data_inicio": "2026-01-01", "data_fim": "2026-05-15"}]
    r = api.post("/api/periodos", json={**PERIODO_2026, "ciclos": ciclos})
    assert r.status_code == 422
    assert "dentro do período" in r.json()["detail"]


def test_periodo_rejeita_ciclos_sobrepostos(api: TestClient) -> None:
    ciclos = [
        {"data_inicio": "2026-02-09", "data_fim": "2026-06-01"},
        {"data_inicio": "2026-05-18", "data_fim": "2026-12-11"},
    ]
    r = api.post("/api/periodos", json={**PERIODO_2026, "ciclos": ciclos})
    assert r.status_code == 422
    assert "sobrepõem" in r.json()["detail"]


def test_periodo_atualiza_ciclos(api: TestClient) -> None:
    periodo = _criar(api, "/api/periodos", PERIODO_2026)
    ciclos = [{"nome": "Ano todo", "data_inicio": "2026-02-09", "data_fim": "2026-12-11"}]
    r = api.put(f"/api/periodos/{periodo['id']}", json={**PERIODO_2026, "ciclos": ciclos})
    assert r.status_code == 200, r.text
    assert [c["nome"] for c in r.json()["ciclos"]] == ["Ano todo"]


# --- Dia não letivo ----------------------------------------------------------


def test_dia_nao_letivo(api: TestClient) -> None:
    _criar(api, "/api/dias-nao-letivos", {"data": "2026-04-21", "descricao": "Tiradentes"})
    r = api.post("/api/dias-nao-letivos", json={"data": "2026-04-21", "descricao": "Outro"})
    assert r.status_code == 409
    assert len(api.get("/api/dias-nao-letivos", params={"ano": 2026}).json()) == 1
    assert api.get("/api/dias-nao-letivos", params={"ano": 2025}).json() == []


# --- Turma -------------------------------------------------------------------


def test_turma_calcula_carga_horaria(api: TestClient) -> None:
    turma = _turma(api, horarios=[{"dia_semana": 0, "aulas": 2}, {"dia_semana": 3, "aulas": 2}])
    assert turma["horas_aula_previstas"] == 72
    assert turma["aulas_por_semana"] == 4
    assert turma["curso_nome"] == CURSO_EMI["nome"]
    assert turma["nivel"] == "EMI"


def test_turma_rejeita_regime_diferente_do_periodo(api: TestClient) -> None:
    curso = _criar(
        api,
        "/api/cursos",
        {**CURSO_EMI, "nome": "Ciência da Computação", "nivel": "GRADUACAO", "regime": "SEMESTRAL"},
    )
    periodo = _criar(api, "/api/periodos", PERIODO_2026)
    r = api.post(
        "/api/turmas",
        json={
            "disciplina": "Web",
            "nome": "BCC",
            "curso_id": curso["id"],
            "periodo_id": periodo["id"],
            "carga_horaria_horas": 60,
            "horarios": [{"dia_semana": 1, "aulas": 2}],
        },
    )
    assert r.status_code == 422


def test_turma_atualiza_horarios_trocando_dias(api: TestClient) -> None:
    turma = _turma(api, horarios=[{"dia_semana": 0, "aulas": 2}, {"dia_semana": 2, "aulas": 2}])
    dados = {k: turma[k] for k in ("disciplina", "nome", "curso_id", "periodo_id")}
    r = api.put(
        f"/api/turmas/{turma['id']}",
        json={
            **dados,
            "carga_horaria_horas": 120,
            "horarios": [{"dia_semana": 2, "aulas": 3}, {"dia_semana": 4, "aulas": 1}],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["horarios"] == [{"dia_semana": 2, "aulas": 3}, {"dia_semana": 4, "aulas": 1}]


def test_turma_rejeita_dia_repetido(api: TestClient) -> None:
    curso = _criar(api, "/api/cursos", CURSO_EMI)
    periodo = _criar(api, "/api/periodos", PERIODO_2026)
    r = api.post(
        "/api/turmas",
        json={
            "disciplina": "Web",
            "nome": "2º INFO",
            "curso_id": curso["id"],
            "periodo_id": periodo["id"],
            "carga_horaria_horas": 60,
            "horarios": [{"dia_semana": 1, "aulas": 1}, {"dia_semana": 1, "aulas": 1}],
        },
    )
    assert r.status_code == 422


# --- Estudantes --------------------------------------------------------------


def test_estudantes_da_turma(api: TestClient) -> None:
    turma = _turma(api)
    url = f"/api/turmas/{turma['id']}/estudantes"
    est = _criar(api, url, {"nome": "Ana Souza", "matricula": "2026001", "email": "ana@x.com"})

    assert api.post(url, json={"nome": "Outra", "matricula": "2026001"}).status_code == 409
    assert api.get(f"/api/turmas/{turma['id']}").json()["total_estudantes"] == 1

    r = api.put(f"/api/estudantes/{est['id']}", json={"nome": "Ana S.", "matricula": "2026001"})
    assert r.json()["nome"] == "Ana S."

    assert api.delete(f"{url}/{est['id']}").status_code == 204
    assert api.get(url).json() == []


# --- Importação CSV ----------------------------------------------------------

CSV_EXCEL = (
    "﻿Nome Completo;Matrícula;E-mail;Data de Nascimento;E-mail Responsável\n"
    "Ana Souza;2026001;ANA@exemplo.com;15/03/2010;mae.ana@exemplo.com\n"
    "Bruno Lima;2026002;;2009-11-02;\n"
    ";;;;\n"
)


def _importar(api: TestClient, turma_id: int, conteudo: str, simular: bool) -> dict[str, Any]:
    r = api.post(
        f"/api/turmas/{turma_id}/estudantes/importar",
        json={"conteudo": conteudo, "simular": simular},
    )
    assert r.status_code == 200, r.text
    resultado: dict[str, Any] = r.json()
    return resultado


def test_importacao_simulada_nao_grava(api: TestClient) -> None:
    turma = _turma(api)
    r = _importar(api, turma["id"], CSV_EXCEL, simular=True)
    assert (r["total_linhas"], r["criados"], r["matriculados"], r["aplicado"]) == (2, 2, 2, False)
    assert api.get(f"/api/turmas/{turma['id']}/estudantes").json() == []


def test_importacao_grava_e_normaliza(api: TestClient) -> None:
    turma = _turma(api)
    r = _importar(api, turma["id"], CSV_EXCEL, simular=False)
    assert r["aplicado"] is True and r["erros"] == []

    ana, bruno = api.get(f"/api/turmas/{turma['id']}/estudantes").json()
    assert ana["email"] == "ana@exemplo.com"
    assert ana["data_nascimento"] == "2010-03-15"
    assert ana["email_responsavel"] == "mae.ana@exemplo.com"
    assert bruno["email"] is None


def test_importacao_atualiza_existentes_sem_apagar_dados(api: TestClient) -> None:
    turma = _turma(api)
    _importar(api, turma["id"], CSV_EXCEL, simular=False)

    csv_virgula = "nome,matricula,email\nAna Souza Lima,2026001,\nCarla,2026003,carla@x.com\n"
    r = _importar(api, turma["id"], csv_virgula, simular=False)
    assert (r["criados"], r["atualizados"], r["matriculados"], r["ja_matriculados"]) == (1, 1, 1, 1)

    ana = api.get(f"/api/turmas/{turma['id']}/estudantes").json()[0]
    assert ana["nome"] == "Ana Souza Lima"
    assert ana["email"] == "ana@exemplo.com"  # vazio no CSV não apaga


def test_importacao_com_erro_nao_grava_nada(api: TestClient) -> None:
    turma = _turma(api)
    csv_ruim = (
        "nome;matricula;email;data_nascimento\n"
        "Ana;1;ana@x.com;15/03/2010\n"
        "Bruno;2;email-invalido;\n"
        "Carla;1;;\n"
        "Davi;4;;31/02/2010\n"
    )
    r = _importar(api, turma["id"], csv_ruim, simular=False)
    assert r["aplicado"] is False
    assert [e["linha"] for e in r["erros"]] == [3, 4, 5]
    assert api.get(f"/api/turmas/{turma['id']}/estudantes").json() == []


def test_importacao_sem_coluna_obrigatoria(api: TestClient) -> None:
    turma = _turma(api)
    r = _importar(api, turma["id"], "nome;email\nAna;a@x.com\n", simular=True)
    assert r["erros"] == [
        {"linha": 1, "mensagem": "Coluna(s) obrigatória(s) ausente(s): matricula"}
    ]
