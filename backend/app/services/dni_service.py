import httpx
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..models import Persona, Config
from ..schemas import PersonaResponse
from ..config import get_settings


async def buscar_persona(db: Session, nrodoc: str) -> tuple[Optional[PersonaResponse], str]:
    """
    Busca una persona primero en la base de datos local.
    Si no existe, consulta la API externa de apisperu.com
    
    Returns:
        (PersonaResponse, message) o (None, error_message)
    """
    # 1. Buscar primero en la base de datos local
    persona_db = db.query(Persona).filter(Persona.nrodoc == nrodoc).first()
    
    if persona_db:
        return PersonaResponse(
            id=persona_db.id,
            tipodoc=persona_db.tipodoc,
            nrodoc=persona_db.nrodoc,
            nombres=persona_db.nombres,
            apellido_paterno=persona_db.apellido_paterno,
            apellido_materno=persona_db.apellido_materno,
            codigo_verificacion=persona_db.codigo_verificacion,
            fecha_registro=persona_db.fecha_registro,
            desde_cache=True
        ), "Datos obtenidos de la base de datos local"
    
    # 2. Si no existe, consultar API externa
    token = obtener_token_apisperu(db)
    
    if not token:
        return None, "Token de apisperu.com no configurado. Configure el token en Configuración."
    
    try:
        settings = get_settings()
        url = f"{settings.APISPERU_BASE_URL}/dni/{nrodoc}?token={token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar si la respuesta tiene datos válidos
                if data.get("success", True) and data.get("dni"):
                    # Guardar en base de datos
                    nueva_persona = Persona(
                        tipodoc="DNI",
                        nrodoc=data.get("dni", nrodoc),
                        nombres=data.get("nombres", ""),
                        apellido_paterno=data.get("apellidoPaterno", ""),
                        apellido_materno=data.get("apellidoMaterno", ""),
                        codigo_verificacion=data.get("codVerifica", "")
                    )
                    db.add(nueva_persona)
                    db.commit()
                    db.refresh(nueva_persona)
                    
                    return PersonaResponse(
                        id=nueva_persona.id,
                        tipodoc=nueva_persona.tipodoc,
                        nrodoc=nueva_persona.nrodoc,
                        nombres=nueva_persona.nombres,
                        apellido_paterno=nueva_persona.apellido_paterno,
                        apellido_materno=nueva_persona.apellido_materno,
                        codigo_verificacion=nueva_persona.codigo_verificacion,
                        fecha_registro=nueva_persona.fecha_registro,
                        desde_cache=False
                    ), "Datos obtenidos de la API externa y guardados en base de datos"
                else:
                    return None, data.get("message", "DNI no encontrado en la API externa")
            
            elif response.status_code == 401:
                return None, "Token de apisperu.com inválido o expirado"
            else:
                return None, f"Error en la API externa: {response.status_code}"
                
    except httpx.TimeoutException:
        return None, "Timeout al consultar la API externa"
    except Exception as e:
        return None, f"Error al consultar la API externa: {str(e)}"


def obtener_token_apisperu(db: Session) -> Optional[str]:
    """Obtiene el token de apisperu.com de la base de datos o de las variables de entorno"""
    # Primero buscar en la base de datos
    config = db.query(Config).filter(Config.clave == "apisperu_token").first()
    
    if config and config.valor:
        return config.valor
    
    # Si no está en BD, usar el de las variables de entorno
    settings = get_settings()
    return settings.APISPERU_TOKEN if settings.APISPERU_TOKEN else None


def guardar_token_apisperu(db: Session, token: str) -> bool:
    """Guarda o actualiza el token de apisperu.com"""
    config = db.query(Config).filter(Config.clave == "apisperu_token").first()
    
    if config:
        config.valor = token
        config.fecha_actualizacion = datetime.utcnow()
    else:
        config = Config(
            clave="apisperu_token",
            valor=token,
            descripcion="Token de acceso para la API de apisperu.com"
        )
        db.add(config)
    
    db.commit()
    return True
