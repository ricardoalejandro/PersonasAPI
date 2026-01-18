from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .database import get_db, init_db
from .auth import verificar_admin, verificar_api_token
from .schemas import (
    PersonaBusqueda, TokenCreate, TokenResponse, TokenList,
    ConfigUpdate, ConfigResponse, MessageResponse
)
from .services import dni_service, token_service
from .models import Config

# Inicializar la aplicación
app = FastAPI(
    title="DNI Lookup API",
    description="API para consulta de DNI con caché local y sistema de tokens",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Inicializar base de datos al iniciar"""
    init_db()


# ==================== Rutas de la API ====================

@app.get("/api/persona/{dni}", response_model=PersonaBusqueda)
async def buscar_persona(
    dni: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_api_token)
):
    """
    Busca una persona por DNI.
    Primero consulta la base de datos local, si no existe consulta la API externa.
    
    Requiere token de API en el header: Authorization: Bearer <token>
    """
    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI debe ser un número de 8 dígitos"
        )
    
    persona, mensaje = await dni_service.buscar_persona(db, dni)
    
    if persona:
        return PersonaBusqueda(success=True, message=mensaje, data=persona)
    else:
        return PersonaBusqueda(success=False, message=mensaje, data=None)


@app.get("/api/buscar/{dni}", response_model=PersonaBusqueda)
async def buscar_persona_admin(
    dni: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """
    Busca una persona por DNI (endpoint para el panel de administración).
    Requiere autenticación de administrador.
    """
    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI debe ser un número de 8 dígitos"
        )
    
    persona, mensaje = await dni_service.buscar_persona(db, dni)
    
    if persona:
        return PersonaBusqueda(success=True, message=mensaje, data=persona)
    else:
        return PersonaBusqueda(success=False, message=mensaje, data=None)


# ==================== Gestión de Tokens ====================

@app.post("/api/tokens", response_model=TokenResponse)
async def crear_token(
    token_data: TokenCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Crea un nuevo token de API. Requiere autenticación de administrador."""
    nuevo_token = token_service.crear_token(db, token_data.nombre, token_data.descripcion)
    return nuevo_token


@app.get("/api/tokens", response_model=TokenList)
async def listar_tokens(
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Lista todos los tokens de API. Requiere autenticación de administrador."""
    tokens = token_service.listar_tokens(db)
    return TokenList(tokens=tokens, total=len(tokens))


@app.delete("/api/tokens/{token_id}", response_model=MessageResponse)
async def eliminar_token(
    token_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Elimina un token de API. Requiere autenticación de administrador."""
    if token_service.eliminar_token(db, token_id):
        return MessageResponse(success=True, message="Token eliminado correctamente")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token no encontrado"
        )


@app.patch("/api/tokens/{token_id}/toggle", response_model=TokenResponse)
async def toggle_token_estado(
    token_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Activa/desactiva un token. Requiere autenticación de administrador."""
    token = token_service.toggle_token(db, token_id)
    
    if token:
        return token
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token no encontrado"
        )


# ==================== Configuración ====================

@app.get("/api/config", response_model=ConfigResponse)
async def obtener_config(
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Obtiene el estado de la configuración. Requiere autenticación de administrador."""
    config = db.query(Config).filter(Config.clave == "apisperu_token").first()
    
    if config and config.valor:
        return ConfigResponse(
            apisperu_token_configured=True,
            mensaje="Token de apisperu.com configurado"
        )
    else:
        return ConfigResponse(
            apisperu_token_configured=False,
            mensaje="Token de apisperu.com no configurado"
        )


@app.put("/api/config", response_model=MessageResponse)
async def actualizar_config(
    config_data: ConfigUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verificar_admin)
):
    """Actualiza la configuración. Requiere autenticación de administrador."""
    dni_service.guardar_token_apisperu(db, config_data.apisperu_token)
    
    return MessageResponse(
        success=True,
        message="Token de apisperu.com actualizado correctamente"
    )


# ==================== Servir Frontend ====================

# Montar archivos estáticos
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
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
