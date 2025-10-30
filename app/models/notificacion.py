from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Notificacion(Base):
    """Sistema de notificaciones para usuarios"""

    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(50))  # 'cita', 'recordatorio', 'cancelacion', 'sistema'
    leida = Column(Boolean, default=False)
    url = Column(String(500))  # Link relacionado (ej: detalles de cita)
    fecha_creacion = Column(DateTime, default=datetime.now, index=True)

    # Índices para consultas comunes
    __table_args__ = (
        Index("idx_notificacion_usuario_leida", "usuario_id", "leida"),
        Index("idx_notificacion_fecha", "fecha_creacion"),
    )

    # Relaciones
    usuario = relationship("Usuario")
