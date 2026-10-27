from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import (
    aulas,
    auth,
    cursos,
    dias_nao_letivos,
    estudantes,
    periodos,
    saude,
    turmas,
)
from app.services.erros import ErroDeNegocio

app = FastAPI(
    title="Bizo Sala",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)


@app.exception_handler(ErroDeNegocio)
def erro_de_negocio(_: Request, erro: ErroDeNegocio) -> JSONResponse:
    return JSONResponse(status_code=erro.status_code, content={"detail": erro.mensagem})


api = APIRouter(prefix="/api")
api.include_router(saude.router)
api.include_router(auth.router)
api.include_router(cursos.router)
api.include_router(periodos.router)
api.include_router(dias_nao_letivos.router)
api.include_router(turmas.router)
api.include_router(estudantes.router)
api.include_router(aulas.router)
app.include_router(api)
