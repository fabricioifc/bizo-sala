from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.usuarios import garantir_usuario_inicial, redefinir_usuario

EMAIL = "professor@ifc.edu.br"
SENHA = "senha-de-teste-123"


def _criar_usuario(db: Session) -> None:
    garantir_usuario_inicial(db, EMAIL, SENHA, "Professor")


def test_saude(client: TestClient) -> None:
    assert client.get("/api/saude").json() == {"status": "ok"}


def test_me_sem_sessao_retorna_401(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_login_com_senha_errada(client: TestClient, db: Session) -> None:
    _criar_usuario(db)
    r = client.post("/api/auth/login", json={"email": EMAIL, "senha": "errada"})
    assert r.status_code == 401


def test_login_logout(client: TestClient, db: Session) -> None:
    _criar_usuario(db)
    r = client.post("/api/auth/login", json={"email": EMAIL.upper(), "senha": SENHA})
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL

    assert client.get("/api/auth/me").json()["email"] == EMAIL

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_login_bloqueia_apos_muitas_falhas(client: TestClient, db: Session) -> None:
    _criar_usuario(db)
    for _ in range(5):
        client.post("/api/auth/login", json={"email": EMAIL, "senha": "errada"})
    r = client.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert r.status_code == 429


def test_usuario_inicial_so_e_criado_uma_vez(db: Session) -> None:
    assert garantir_usuario_inicial(db, EMAIL, SENHA, "Professor") is True
    assert garantir_usuario_inicial(db, "outro@ifc.edu.br", SENHA, "Outro") is False


def test_redefinir_usuario_troca_email_e_senha(client: TestClient, db: Session) -> None:
    _criar_usuario(db)
    redefinir_usuario(db, "Novo@ifc.edu.br", "nova-senha-456", "Novo")

    antigo = client.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert antigo.status_code == 401
    novo = client.post(
        "/api/auth/login", json={"email": "novo@ifc.edu.br", "senha": "nova-senha-456"}
    )
    assert novo.json()["nome"] == "Novo"
