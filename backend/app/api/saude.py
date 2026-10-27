from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["saude"])


class Saude(BaseModel):
    status: str


@router.get("/saude", response_model=Saude)
def saude(db: DbSession) -> Saude:
    db.execute(text("SELECT 1"))
    return Saude(status="ok")
