import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL: str = "sqlite:///./data/personas.db"
    
    # API externa apisperu.com
    APISPERU_TOKEN: str = ""
    APISPERU_BASE_URL: str = "https://dniruc.apisperu.com/api/v1"
    
    # Seguridad - Clave maestra para administración
    ADMIN_KEY: str = "admin-secret-key-change-me"
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
