from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Destinatario
from app.services.mensagens import montar_email, personalizar, processar_fila
from tests.test_cadastros import CURSO_EMI, _criar, _turma


def test_personalizar() -> None:
    ctx = {"nome": "Ana Souza", "primeiro_nome": "Ana", "disciplina": "Web", "turma": "1A"}
    texto = "Olá, {primeiro_nome}! {disciplina} ({turma}) {desconhecido} {"
    assert personalizar(texto, ctx) == "Olá, Ana! Web (1A) {desconhecido} {"


@pytest.fixture
def turma(api: TestClient) -> dict[str, Any]:
    t = _turma(api)
    url = f"/api/turmas/{t['id']}/estudantes"
    t["ana"] = _criar(
        api,
        url,
        {
            "nome": "Ana Souza",
            "matricula": "1",
            "email": "ana@x.com",
            "email_responsavel": "mae@x.com",
        },
    )["id"]
    t["bruno"] = _criar(api, url, {"nome": "Bruno", "matricula": "2"})["id"]  # sem e-mail
    t["carla"] = _criar(api, url, {"nome": "Carla", "matricula": "3", "email": "c@x.com"})["id"]
    return t


def _dados(turma: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "turma_id": turma["id"],
        "assunto": "Aviso de {disciplina}",
        "corpo": "Olá, {primeiro_nome}.",
        **extra,
    }


def test_previa(api: TestClient, turma: dict[str, Any]) -> None:
    r = api.post("/api/mensagens/previa", json=_dados(turma, incluir_responsaveis=True)).json()
    assert [(d["nome"], d["tipo"], d["email"]) for d in r["destinatarios"]] == [
        ("Ana Souza", "ESTUDANTE", "ana@x.com"),
        ("Ana Souza", "RESPONSAVEL", "mae@x.com"),
        ("Carla", "ESTUDANTE", "c@x.com"),
    ]
    assert [s["nome"] for s in r["sem_email"]] == ["Bruno"]
    assert (r["exemplo_assunto"], r["exemplo_corpo"]) == ("Aviso de Programação I", "Olá, Ana.")


def test_enviar_para_estudantes_escolhidos(api: TestClient, turma: dict[str, Any]) -> None:
    r = api.post("/api/mensagens", json=_dados(turma, estudante_ids=[turma["carla"]]))
    assert r.status_code == 201, r.text
    m = r.json()
    assert (m["total"], m["pendentes"]) == (1, 1)
    assert m["destinatarios"][0]["email"] == "c@x.com"
    resumo = api.get("/api/mensagens").json()[0]
    assert (resumo["disciplina"], resumo["turma_nome"]) == ("Programação I", "1º INFO")


def test_sem_destinatario_com_email(api: TestClient, turma: dict[str, Any]) -> None:
    r = api.post("/api/mensagens", json=_dados(turma, estudante_ids=[turma["bruno"]]))
    assert r.status_code == 422


def test_responsaveis_so_no_emi(api: TestClient) -> None:
    curso = _criar(
        api,
        "/api/cursos",
        {**CURSO_EMI, "nome": "BCC", "nivel": "GRADUACAO", "regime": "SEMESTRAL"},
    )
    periodo = _criar(
        api,
        "/api/periodos",
        {
            "nome": "2026/2",
            "regime": "SEMESTRAL",
            "ano": 2026,
            "semestre": 2,
            "data_inicio": "2026-08-03",
            "data_fim": "2026-12-11",
            "ciclos": [{"data_inicio": "2026-08-03", "data_fim": "2026-12-11"}],
        },
    )
    t = _criar(
        api,
        "/api/turmas",
        {
            "disciplina": "Web",
            "nome": "BCC",
            "curso_id": curso["id"],
            "periodo_id": periodo["id"],
            "carga_horaria_horas": 60,
            "horarios": [{"dia_semana": 1, "aulas": 2}],
        },
    )
    r = api.post("/api/mensagens/previa", json=_dados(t, incluir_responsaveis=True))
    assert r.status_code == 422


# --- Fila --------------------------------------------------------------------


def test_fila_envia_e_tenta_de_novo(api: TestClient, turma: dict[str, Any], db: Session) -> None:
    m = api.post("/api/mensagens", json=_dados(turma)).json()  # Ana e Carla
    enviados: list[str] = []

    def enviar(d: Destinatario) -> None:
        if d.email == "c@x.com":
            raise ConnectionError("SMTP indisponível")
        enviados.append(d.email)

    agora = datetime.now(UTC) + timedelta(seconds=1)
    assert processar_fila(db, enviar, agora) == (1, 1)
    assert enviados == ["ana@x.com"]

    # A falha só é tentada de novo depois do intervalo
    assert processar_fila(db, enviar, agora) == (0, 0)
    assert processar_fila(db, enviar, agora + timedelta(minutes=2)) == (0, 1)
    assert processar_fila(db, enviar, agora + timedelta(minutes=10)) == (0, 1)

    detalhe = api.get(f"/api/mensagens/{m['id']}").json()
    assert (detalhe["enviados"], detalhe["erros"]) == (1, 1)
    erro = next(d for d in detalhe["destinatarios"] if d["status"] == "ERRO")
    assert (erro["tentativas"], erro["erro"]) == (3, "SMTP indisponível")

    # Reenviar falhas volta para a fila
    r = api.post(f"/api/mensagens/{m['id']}/reenviar-falhas").json()
    assert (r["pendentes"], r["erros"]) == (1, 0)


def test_montar_email() -> None:
    d = Destinatario(email="ana@x.com", assunto="Aviso", corpo="Olá, Ana.")
    email = montar_email(d, "professor@ifc.edu.br")
    assert (email["From"], email["To"], email["Subject"]) == (
        "professor@ifc.edu.br",
        "ana@x.com",
        "Aviso",
    )
    assert email.get_content().strip() == "Olá, Ana."
