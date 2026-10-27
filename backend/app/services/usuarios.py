from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_senha, verificar_senha
from app.models import Usuario


def autenticar(db: Session, email: str, senha: str) -> Usuario | None:
    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))
    if usuario is None or not verificar_senha(usuario.senha_hash, senha):
        return None
    return usuario


def garantir_usuario_inicial(db: Session, email: str, senha: str, nome: str) -> bool:
    """Cria o usuário inicial se não houver nenhum. Retorna True se criou."""
    if db.scalar(select(func.count()).select_from(Usuario)):
        return False
    db.add(Usuario(email=email.lower(), nome=nome, senha_hash=hash_senha(senha)))
    db.commit()
    return True


def redefinir_usuario(db: Session, email: str, senha: str, nome: str) -> Usuario:
    """Atualiza e-mail, nome e senha do usuário (sistema de usuário único)."""
    usuario = db.scalar(select(Usuario).order_by(Usuario.id))
    if usuario is None:
        usuario = Usuario()
        db.add(usuario)
    usuario.email = email.lower()
    usuario.nome = nome
    usuario.senha_hash = hash_senha(senha)
    db.commit()
    return usuario
