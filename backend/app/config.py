import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos SQLite
    DATABASE_URL: str = "sqlite:///./data/personas.db"
    
    # Credenciales para acceso/backup de la base de datos
    # Estas credenciales protegen la descarga del backup de la BD
    DB_BACKUP_USER: str = "backup_admin"
    DB_BACKUP_PASSWORD: str = "backup_secure_123"
    
    # API externa apisperu.com
    APISPERU_TOKEN: str = ""
    APISPERU_BASE_URL: str = "https://dniruc.apisperu.com/api/v1"
    
    # Credenciales de administrador (para el panel web)
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # Rate Limiting (peticiones por minuto por IP)
    # Límite global: 200 peticiones/minuto por IP
    RATE_LIMIT_PER_IP: int = 200
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
