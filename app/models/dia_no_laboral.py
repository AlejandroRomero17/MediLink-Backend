from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class DiaNoLaboral(Base):
    """Días específicos en que el doctor no atiende (vacaciones, días festivos, etc.)"""

    __tablename__ = "dias_no_laborales"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(
        Integer, ForeignKey("doctores.id", ondelete="CASCADE"), nullable=False
    )
    fecha = Column(Date, nullable=False, index=True)
    motivo = Column(String(200))
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Constraint: No duplicar días no laborales
    __table_args__ = (UniqueConstraint("doctor_id", "fecha", name="uq_dia_no_laboral"),)

    # Relaciones
    doctor = relationship("Doctor", back_populates="dias_no_laborales")
