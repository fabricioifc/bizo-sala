import os
from collections.abc import Iterator

# Precisa vir antes de importar a aplicação: o engine é criado na importação.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://bizo:bizo@db:5432/bizo_sala_test"
)
os.environ["COOKIE_SECURE"] = "false"
os.environ.pop("ADMIN_EMAIL", None)
os.environ.pop("ADMIN_SENHA", None)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.auth import limite_login
from app.core.db import SessionLocal, engine
from app.main import app
from app.models import Base


def _criar_banco_de_teste() -> None:
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        existe = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": url.database}
        )
        if not existe:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def banco() -> Iterator[None]:
    _criar_banco_de_teste()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def limpar_tabelas() -> Iterator[None]:
    yield
    with engine.begin() as conn:
        for tabela in reversed(Base.metadata.sorted_tables):
            conn.execute(tabela.delete())
    limite_login.resetar()


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
