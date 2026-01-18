from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


# ==================== Estructura de Respuesta Estándar ====================
# Todas las respuestas de la API siguen esta estructura para facilitar
# la integración con otros sistemas.
#
# Estructura:
# {
#     "success": true/false,           # Indica si la operación fue exitosa
#     "code": 200,                      # Código HTTP de respuesta
#     "code_description": "OK - ...",  # Descripción del código HTTP
#     "message": "Mensaje descriptivo", # Mensaje legible para el usuario
#     "data": { ... }                   # Datos de respuesta (opcional)
# }
#
# Códigos de respuesta:
# - 200: OK - Solicitud procesada exitosamente
# - 201: Created - Recurso creado exitosamente
# - 400: Bad Request - Datos de entrada inválidos
# - 401: Unauthorized - Credenciales inválidas o no proporcionadas
# - 403: Forbidden - No tiene permisos para realizar esta acción
# - 404: Not Found - Recurso no encontrado
# - 429: Too Many Requests - Límite de peticiones excedido (200/min por IP)
# - 500: Internal Server Error - Error interno del servidor
# =========================================================================


# ==================== Persona ====================

class PersonaBase(BaseModel):
    """Datos básicos de una persona"""
    tipodoc: str = Field(default="DNI", description="Tipo de documento (DNI)")
    nrodoc: str = Field(..., description="Número de documento (8 dígitos)")
    nombres: Optional[str] = Field(None, description="Nombres de la persona")
    apellido_paterno: Optional[str] = Field(None, description="Apellido paterno")
    apellido_materno: Optional[str] = Field(None, description="Apellido materno")
    codigo_verificacion: Optional[str] = Field(None, description="Código de verificación")


class PersonaCreate(PersonaBase):
    """Esquema para crear una nueva persona"""
    pass


# ==================== Respuestas Estandarizadas ====================

class APIResponse(BaseModel):
    """
    Estructura base de respuesta de la API.
    Todas las respuestas siguen este formato estándar.
    """
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    code: int = Field(..., description="Código HTTP de respuesta")
    code_description: str = Field(..., description="Descripción del código HTTP")
    message: str = Field(..., description="Mensaje descriptivo de la operación")
    data: Optional[Any] = Field(None, description="Datos de respuesta (opcional)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "code": 200,
                "code_description": "OK - Solicitud procesada exitosamente",
                "message": "Operación completada correctamente",
                "data": None
            }
        }


# Alias para compatibilidad
BaseResponse = APIResponse


class PersonaResponse(PersonaBase):
    """Respuesta con datos completos de una persona"""
    id: int = Field(..., description="ID único en la base de datos")
    fecha_registro: Optional[datetime] = Field(None, description="Fecha de registro en el sistema")
    desde_cache: bool = Field(default=False, description="Indica si el dato proviene del caché local")
    
    class Config:
        from_attributes = True


class PersonaUpdate(BaseModel):
    """Esquema para actualizar datos de una persona"""
    tipodoc: Optional[str] = None
    nombres: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    codigo_verificacion: Optional[str] = None


class PersonasPaginadas(BaseModel):
    """Respuesta paginada de personas"""
    items: List[PersonaResponse] = Field(..., description="Lista de personas")
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas")


class PersonaBusqueda(APIResponse):
    """Respuesta de búsqueda de persona"""
    data: Optional[PersonaResponse] = None


# ==================== API Token ====================

class TokenBase(BaseModel):
    """Datos básicos de un token de API"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre identificador del token")
    descripcion: Optional[str] = Field(None, description="Descripción del uso del token")


class TokenCreate(TokenBase):
    """Esquema para crear un nuevo token"""
    pass


class TokenResponse(TokenBase):
    """Respuesta con datos completos de un token"""
    id: int = Field(..., description="ID único del token")
    token: str = Field(..., description="Token de acceso (64 caracteres)")
    activo: bool = Field(..., description="Estado del token (activo/inactivo)")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    ultimo_uso: Optional[datetime] = Field(None, description="Última vez que se usó el token")
    
    class Config:
        from_attributes = True


class TokenList(APIResponse):
    """Respuesta con lista de tokens"""
    tokens: List[TokenResponse]
    total: int


# ==================== Configuración ====================

class ConfigUpdate(BaseModel):
    """Esquema para actualizar configuración"""
    apisperu_token: str = Field(..., min_length=1, description="Token de apisperu.com")


class ConfigResponse(APIResponse):
    """Respuesta de estado de configuración"""
    apisperu_token_configured: bool = Field(..., description="Indica si el token está configurado")


class MessageResponse(APIResponse):
    """Respuesta simple con mensaje"""
    pass
