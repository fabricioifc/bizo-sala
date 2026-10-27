import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import auth, saude
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services.usuarios import garantir_usuario_inicial

logger = logging.getLogger("bizo_sala")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.admin_email and settings.admin_senha:
        with SessionLocal() as db:
            if garantir_usuario_inicial(
                db, settings.admin_email, settings.admin_senha, settings.admin_nome
            ):
                logger.warning("Usuário inicial criado: %s", settings.admin_email)
    yield


app = FastAPI(
    title="Bizo Sala",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

api = APIRouter(prefix="/api")
api.include_router(saude.router)
api.include_router(auth.router)
app.include_router(api)
