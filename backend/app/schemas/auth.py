from pydantic import BaseModel, ConfigDict, EmailStr


class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nome: str
