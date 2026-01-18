import secrets
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from ..models import ApiToken


def generar_token() -> str:
    """Genera un token aleatorio seguro de 32 bytes (64 caracteres hex)"""
    return secrets.token_hex(32)


def crear_token(db: Session, nombre: str, descripcion: Optional[str] = None) -> ApiToken:
    """Crea un nuevo token de API"""
    nuevo_token = ApiToken(
        token=generar_token(),
        nombre=nombre,
        descripcion=descripcion,
        activo=True
    )
    db.add(nuevo_token)
    db.commit()
    db.refresh(nuevo_token)
    return nuevo_token


def listar_tokens(db: Session) -> List[ApiToken]:
    """Lista todos los tokens"""
    return db.query(ApiToken).order_by(ApiToken.fecha_creacion.desc()).all()


def obtener_token(db: Session, token_id: int) -> Optional[ApiToken]:
    """Obtiene un token por su ID"""
    return db.query(ApiToken).filter(ApiToken.id == token_id).first()


def validar_token(db: Session, token: str) -> Optional[ApiToken]:
    """Valida un token y actualiza su último uso"""
    api_token = db.query(ApiToken).filter(
        ApiToken.token == token,
        ApiToken.activo == True
    ).first()
    
    if api_token:
        api_token.ultimo_uso = datetime.utcnow()
        db.commit()
    
    return api_token


def eliminar_token(db: Session, token_id: int) -> bool:
    """Elimina un token por su ID"""
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    
    if token:
        db.delete(token)
        db.commit()
        return True
    
    return False


def toggle_token(db: Session, token_id: int) -> Optional[ApiToken]:
    """Activa/desactiva un token"""
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    
    if token:
        token.activo = not token.activo
        db.commit()
        db.refresh(token)
        return token
    
    return None
