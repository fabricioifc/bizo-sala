from fastapi import APIRouter, FastAPI

from app.api import auth, saude

app = FastAPI(
    title="Bizo Sala",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

api = APIRouter(prefix="/api")
api.include_router(saude.router)
api.include_router(auth.router)
app.include_router(api)
