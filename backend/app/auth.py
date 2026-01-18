from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Optional
import secrets

from .database import get_db
from .config import get_settings
from .services import token_service

security = HTTPBasic()

# Credenciales de administración por defecto
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "escolastica123"


def verificar_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Verifica las credenciales de administrador usando HTTP Basic Auth.
    Credenciales por defecto: admin/escolastica123
    """
    settings = get_settings()
    
    # Usar credenciales de variable de entorno si están definidas, sino usar las por defecto
    admin_user = getattr(settings, 'ADMIN_USER', DEFAULT_ADMIN_USER)
    admin_password = getattr(settings, 'ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD)
    
    # Comparación segura para evitar timing attacks
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        admin_user.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        admin_password.encode("utf8")
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administrador incorrectas",
            # No enviar WWW-Authenticate para evitar popup nativo del navegador
        )
    
    return True


def verificar_api_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> bool:
    """
    Verifica el token de API para acceso de terceros.
    El token debe enviarse en el header Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extraer el token del header
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Validar el token en la base de datos
    api_token = token_service.validar_token(db, token)
    
    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True
