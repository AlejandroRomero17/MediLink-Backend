from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Float,
    Boolean,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
from .enums import EstadoCitaEnum


class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = Column(
        Integer, ForeignKey("doctores.id", ondelete="CASCADE"), nullable=False
    )
    fecha_hora = Column(DateTime, nullable=False, index=True)
    duracion_minutos = Column(Integer, default=30)
    motivo = Column(Text, nullable=False)
    sintomas = Column(Text)
    notas_paciente = Column(Text)
    notas_doctor = Column(Text)
    diagnostico = Column(Text)
    tratamiento = Column(Text)
    receta = Column(Text)
    es_videollamada = Column(Boolean, default=False)
    url_videollamada = Column(String(500))
    estado = Column(Enum(EstadoCitaEnum), default=EstadoCitaEnum.PENDIENTE)
    costo = Column(Float)
    # Recordatorios
    recordatorio_enviado = Column(Boolean, default=False)
    fecha_recordatorio = Column(DateTime)
    # Cancelación
    motivo_cancelacion = Column(Text)
    cancelado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_cancelacion = Column(DateTime)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Índices compuestos para búsquedas comunes
    __table_args__ = (
        Index("idx_cita_doctor_fecha", "doctor_id", "fecha_hora"),
        Index("idx_cita_paciente_fecha", "paciente_id", "fecha_hora"),
        Index("idx_cita_estado_fecha", "estado", "fecha_hora"),
    )

    # Relaciones
    paciente = relationship(
        "Paciente", back_populates="citas", foreign_keys=[paciente_id]
    )
    doctor = relationship("Doctor", back_populates="citas", foreign_keys=[doctor_id])
    valoracion = relationship("ValoracionDoctor", back_populates="cita", uselist=False)
    expedientes = relationship("ExpedienteMedico", back_populates="cita")
