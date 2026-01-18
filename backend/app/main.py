from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .database import get_db, init_db
from .auth import verificar_admin, verificar_api_token
from .schemas import (
    PersonaBusqueda, PersonaResponse, TokenCreate, TokenResponse, TokenList,
    ConfigUpdate, ConfigResponse, MessageResponse
)
from .services import dni_service, token_service
from .models import Config
from .config import get_settings
import secrets

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Diccionario de descripciones de códigos HTTP
HTTP_DESCRIPTIONS = {
    200: "OK - Solicitud procesada exitosamente",
    201: "Created - Recurso creado exitosamente",
    400: "Bad Request - Datos de entrada inválidos",
    401: "Unauthorized - Credenciales inválidas o no proporcionadas",
    403: "Forbidden - No tiene permisos para realizar esta acción",
    404: "Not Found - Recurso no encontrado",
    429: "Too Many Requests - Límite de peticiones excedido",
    500: "Internal Server Error - Error interno del servidor"
}

def serialize_value(obj):
    """Convierte objetos no serializables a JSON"""
    from datetime import datetime
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def model_to_dict(obj):
    """Convierte un modelo a diccionario con fechas serializables"""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "__dict__"):
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    else:
        return obj
    
    # Convertir fechas a string
    from datetime import datetime
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data

def create_api_response(success: bool, code: int, message: str, data=None):
    """Crea una respuesta estandarizada"""
    content = {
        "success": success,
        "code": code,
        "code_description": HTTP_DESCRIPTIONS.get(code, "Desconocido"),
        "message": message
    }
    
    if data is not None:
        # Si es un objeto Pydantic o modelo SQLAlchemy
        if hasattr(data, "model_dump") or hasattr(data, "__dict__"):
            content["data"] = model_to_dict(data)
        elif isinstance(data, list):
            content["data"] = [model_to_dict(i) for i in data]
        elif isinstance(data, dict):
            # Si es un diccionario, procesar sus valores
            from datetime import datetime
            processed = {}
            for k, v in data.items():
                if isinstance(v, list):
                    processed[k] = [model_to_dict(i) for i in v]
                elif isinstance(v, datetime):
                    processed[k] = v.isoformat()
                else:
                    processed[k] = v
            content["data"] = processed
        else:
            content["data"] = data
            
    return JSONResponse(status_code=code, content=content)

# Inicializar Limiter
limiter = Limiter(key_func=get_remote_address)

# Inicializar la aplicación
app = FastAPI(
    title="DNI Lookup API",
    description="API para consulta de DNI con caché local y sistema de tokens",
    version="1.0.0"
)

# Configurar Limiter en la app
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return create_api_response(
        False, 
        429, 
        "Ha excedido el límite de peticiones permitido"
    )

# Configurar CORS - Más restrictivo en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Middleware de seguridad para headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response

app.add_middleware(SecurityHeadersMiddleware)


@app.on_event("startup")
async def startup():
    """Inicializar base de datos al iniciar"""
    init_db()


# ==================== Login ====================

from pydantic import BaseModel, Field
import re

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

# Diccionario para tracking de intentos fallidos por IP
login_attempts = {}

@app.post("/api/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: LoginRequest):
    """
    Valida las credenciales de administrador.
    Limitado a 10 intentos por minuto por IP.
    """
    client_ip = get_remote_address(request)
    
    # Verificar intentos fallidos (bloqueo temporal después de 5 intentos)
    if client_ip in login_attempts:
        attempts, last_attempt = login_attempts[client_ip]
        from datetime import datetime, timedelta
        if attempts >= 5 and datetime.now() - last_attempt < timedelta(minutes=15):
            return create_api_response(
                False, 429, 
                "Demasiados intentos fallidos. Intente en 15 minutos."
            )
        # Reset si pasaron más de 15 minutos
        if datetime.now() - last_attempt >= timedelta(minutes=15):
            login_attempts[client_ip] = (0, datetime.now())
    
    settings = get_settings()
    
    admin_user = getattr(settings, 'ADMIN_USER', 'admin')
    admin_password = getattr(settings, 'ADMIN_PASSWORD', 'escolastica123')
    
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        admin_user.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        admin_password.encode("utf8")
    )
    
    if is_correct_username and is_correct_password:
        # Reset intentos en login exitoso
        if client_ip in login_attempts:
            del login_attempts[client_ip]
        return create_api_response(True, 200, "Login exitoso")
    else:
        # Registrar intento fallido
        from datetime import datetime
        if client_ip in login_attempts:
            attempts, _ = login_attempts[client_ip]
            login_attempts[client_ip] = (attempts + 1, datetime.now())
        else:
            login_attempts[client_ip] = (1, datetime.now())
        
        return create_api_response(False, 401, "Credenciales incorrectas")


# ==================== Rutas de la API ====================

@app.get("/api/persona/{dni}", response_model=PersonaBusqueda)
@limiter.limit("200/minute")
async def buscar_persona(
    request: Request,
    dni: str,
    db: Session = Depends(get_db),
    api_token: str = Depends(verificar_api_token)
):
    """Busca una persona por DNI usando Token de API."""
    # Sanitizar y validar DNI
    dni = dni.strip()
    if not dni.isdigit() or len(dni) != 8:
        return create_api_response(False, 400, "El DNI debe ser un número de 8 dígitos")
    
    # Validar que no sea un DNI obviamente inválido
    if dni in ["00000000", "11111111", "22222222", "33333333", "44444444", 
               "55555555", "66666666", "77777777", "88888888", "99999999"]:
        return create_api_response(False, 400, "DNI inválido")
    
    persona, mensaje = await dni_service.buscar_persona(db, dni)
    
    if persona:
        data = PersonaResponse.model_validate(persona)
        return create_api_response(True, 200, mensaje, data)
    else:
        return create_api_response(False, 404, mensaje)


@app.get("/api/buscar/{dni}", response_model=PersonaBusqueda)
@limiter.limit("200/minute")
async def buscar_persona_admin(
    request: Request,
    dni: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Busca una persona por DNI (Panel Admin)."""
    # Sanitizar y validar DNI
    dni = dni.strip()
    if not dni.isdigit() or len(dni) != 8:
        return create_api_response(False, 400, "El DNI debe ser un número de 8 dígitos")
    
    # Validar que no sea un DNI obviamente inválido
    if dni in ["00000000", "11111111", "22222222", "33333333", "44444444", 
               "55555555", "66666666", "77777777", "88888888", "99999999"]:
        return create_api_response(False, 400, "DNI inválido")
        
    persona, mensaje = await dni_service.buscar_persona(db, dni)
    
    if persona:
        data = PersonaResponse.model_validate(persona)
        return create_api_response(True, 200, mensaje, data)
    else:
        return create_api_response(False, 404, mensaje)


@app.get("/api/backup")
@limiter.limit("5/hour")
async def descargar_backup(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """
    Descarga la base de datos SQLite como backup.
    Requiere autenticación de administrador.
    Limitado a 5 descargas por hora por seguridad.
    """
    settings = get_settings()
    # Extraer la ruta del archivo de DATABASE_URL
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    # Convertir rutas relativas a absolutas
    if db_path.startswith("./"):
        db_path = os.path.abspath(db_path)
    
    if os.path.exists(db_path):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_personas_{timestamp}.db"
        
        # Usar headers explícitos para evitar problemas con el filename
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        
        return FileResponse(
            path=db_path,
            headers=headers,
            media_type='application/octet-stream'
        )
    return create_api_response(False, 404, "Archivo de base de datos no encontrado")


# ==================== Gestión de Tokens ====================

@app.post("/api/tokens", response_model=TokenResponse)
async def crear_token(
    token_data: TokenCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Crea un nuevo token de API. Requiere autenticación de administrador."""
    nuevo_token = token_service.crear_token(db, token_data.nombre, token_data.descripcion)
    return create_api_response(True, 201, "Token creado exitosamente", nuevo_token)


@app.get("/api/tokens", response_model=TokenList)
async def listar_tokens(
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Lista todos los tokens de API. Requiere autenticación de administrador."""
    tokens = token_service.listar_tokens(db)
    return create_api_response(True, 200, "Tokens listados exitosamente", {"tokens": tokens, "total": len(tokens)})


@app.delete("/api/tokens/{token_id}", response_model=MessageResponse)
async def eliminar_token(
    token_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Elimina un token de API. Requiere autenticación de administrador."""
    if token_service.eliminar_token(db, token_id):
        return create_api_response(True, 200, "Token eliminado correctamente")
    else:
        return create_api_response(False, 404, "Token no encontrado")


@app.patch("/api/tokens/{token_id}/toggle", response_model=TokenResponse)
async def toggle_token_estado(
    token_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Activa/desactiva un token. Requiere autenticación de administrador."""
    token = token_service.toggle_token(db, token_id)
    
    if token:
        return create_api_response(True, 200, "Estado del token actualizado", token)
    else:
        return create_api_response(False, 404, "Token no encontrado")


# ==================== Configuración ====================

@app.get("/api/config", response_model=ConfigResponse)
async def obtener_config(
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Obtiene el estado de la configuración."""
    config_db = db.query(Config).filter(Config.clave == "apisperu_token").first()
    settings = get_settings()
    env_token = getattr(settings, 'APISPERU_TOKEN', None)
    
    is_configured = (config_db and config_db.valor) or (env_token and len(env_token) > 0)
    
    return create_api_response(
        True, 200, 
        "Token configurado" if is_configured else "Token no configurado",
        {"apisperu_token_configured": bool(is_configured)}
    )


@app.put("/api/config", response_model=MessageResponse)
async def actualizar_config(
    config_data: ConfigUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Actualiza la configuración. Requiere autenticación de administrador."""
    dni_service.guardar_token_apisperu(db, config_data.apisperu_token)
    return create_api_response(True, 200, "Token de apisperu.com actualizado correctamente")


# ==================== Gestión de Personas (Base de Datos) ====================

from .schemas import PersonasPaginadas, PersonaUpdate, PersonaCreate
from .models import Persona
from sqlalchemy import or_
import math

@app.get("/api/personas", response_model=PersonasPaginadas)
async def listar_personas(
    q: str = "",
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Lista personas con búsqueda y paginación."""
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    query = db.query(Persona)
    
    if q and len(q) >= 3:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Persona.nrodoc.ilike(search_term),
                Persona.nombres.ilike(search_term),
                Persona.apellido_paterno.ilike(search_term),
                Persona.apellido_materno.ilike(search_term)
            )
        )
    
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    offset = (page - 1) * per_page
    personas = query.order_by(Persona.id.desc()).offset(offset).limit(per_page).all()
    
    # El helper create_api_response se encargará de aplanar la estructura si detecta items y total
    data = {
        "items": personas,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }
    
    return create_api_response(True, 200, "Personas listadas exitosamente", data)


@app.get("/api/personas/{persona_id}", response_model=PersonaResponse)
async def obtener_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Obtiene una persona por ID."""
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        return create_api_response(False, 404, "Persona no encontrada")
    return create_api_response(True, 200, "Persona encontrada", persona)


@app.post("/api/personas", response_model=PersonaResponse)
async def crear_persona(
    persona_data: PersonaCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Crea una nueva persona manualmente."""
    existente = db.query(Persona).filter(Persona.nrodoc == persona_data.nrodoc).first()
    if existente:
        return create_api_response(False, 400, "Ya existe una persona con ese DNI")
    
    nueva_persona = Persona(**persona_data.model_dump())
    db.add(nueva_persona)
    db.commit()
    db.refresh(nueva_persona)
    return create_api_response(True, 201, "Persona creada exitosamente", nueva_persona)


@app.put("/api/personas/{persona_id}", response_model=PersonaResponse)
async def actualizar_persona(
    persona_id: int,
    persona_data: PersonaUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Actualiza una persona existente."""
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        return create_api_response(False, 404, "Persona no encontrada")
    
    update_data = persona_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(persona, key, value)
    
    db.commit()
    db.refresh(persona)
    return create_api_response(True, 200, "Persona actualizada exitosamente", persona)


@app.delete("/api/personas/{persona_id}", response_model=MessageResponse)
async def eliminar_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Elimina una persona de la base de datos."""
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        return create_api_response(False, 404, "Persona no encontrada")
    
    db.delete(persona)
    db.commit()
    return create_api_response(True, 200, "Persona eliminada correctamente")


# ==================== Servir Frontend ====================

# Montar archivos estáticos
# En Docker el frontend está en /app/frontend, en desarrollo usamos ruta relativa
frontend_path = "/app/frontend" if os.path.exists("/app/frontend") else os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def serve_frontend():
    """Sirve la página principal del frontend"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "DNI Lookup API - Frontend no disponible"}


@app.get("/health")
async def health_check():
    """Health check endpoint para Dokploy"""
    return {"status": "healthy"}
