from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==================== Persona ====================

class PersonaBase(BaseModel):
    tipodoc: str = "DNI"
    nrodoc: str
    nombres: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    codigo_verificacion: Optional[str] = None


class PersonaCreate(PersonaBase):
    pass


class PersonaResponse(PersonaBase):
    id: int
    fecha_registro: Optional[datetime] = None
    desde_cache: bool = False  # Indica si vino de la BD local
    
    class Config:
        from_attributes = True


class PersonaBusqueda(BaseModel):
    """Respuesta de búsqueda de persona"""
    success: bool
    message: str
    data: Optional[PersonaResponse] = None


# ==================== API Token ====================

class TokenBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


class TokenCreate(TokenBase):
    pass


class TokenResponse(TokenBase):
    id: int
    token: str
    activo: bool
    fecha_creacion: datetime
    ultimo_uso: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenList(BaseModel):
    tokens: list[TokenResponse]
    total: int


# ==================== Configuración ====================

class ConfigUpdate(BaseModel):
    apisperu_token: str = Field(..., min_length=1)


class ConfigResponse(BaseModel):
    apisperu_token_configured: bool
    mensaje: str


# ==================== Respuestas generales ====================

class MessageResponse(BaseModel):
    success: bool
    message: str
