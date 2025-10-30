from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Time,
    Boolean,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
from .enums import DiaSemanaEnum


class HorarioDoctor(Base):
    """Horarios regulares de atención del doctor por día de la semana"""

    __tablename__ = "horarios_doctor"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(
        Integer, ForeignKey("doctores.id", ondelete="CASCADE"), nullable=False
    )
    dia_semana = Column(Enum(DiaSemanaEnum), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Constraint: Un doctor no puede tener horarios superpuestos el mismo día
    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "dia_semana", "hora_inicio", name="uq_horario_doctor"
        ),
    )

    # Relaciones
    doctor = relationship("Doctor", back_populates="horarios")
