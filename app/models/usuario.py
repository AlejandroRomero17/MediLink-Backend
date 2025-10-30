from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
from .enums import TipoUsuarioEnum


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuarioEnum), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Índices compuestos para búsquedas comunes
    __table_args__ = (
        Index("idx_usuario_email_activo", "email", "activo"),
        Index("idx_usuario_tipo", "tipo_usuario", "activo"),
    )

    # Relaciones (se definirán en los modelos respectivos)
    paciente = relationship(
        "Paciente",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    doctor = relationship(
        "Doctor", back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )
