from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base


class Persona(Base):
    """Modelo para almacenar datos de personas consultadas"""
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True, index=True)
    tipodoc = Column(String(10), default="DNI")
    nrodoc = Column(String(20), unique=True, index=True, nullable=False)
    nombres = Column(String(100))
    apellido_paterno = Column(String(100))
    apellido_materno = Column(String(100))
    codigo_verificacion = Column(String(10))
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())


class ApiToken(Base):
    """Tokens para acceso a la API por terceros"""
    __tablename__ = "api_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_uso = Column(DateTime(timezone=True))


class Config(Base):
    """Configuraciones almacenadas en base de datos"""
    __tablename__ = "configuraciones"
    
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(50), unique=True, index=True, nullable=False)
    valor = Column(String(500))
    descripcion = Column(String(255))
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
