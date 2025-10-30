from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class ValoracionDoctor(Base):
    """Valoraciones y reseñas de pacientes sobre doctores"""

    __tablename__ = "valoraciones_doctor"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(
        Integer, ForeignKey("doctores.id", ondelete="CASCADE"), nullable=False
    )
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    cita_id = Column(Integer, ForeignKey("citas.id", ondelete="SET NULL"))
    calificacion = Column(Integer, nullable=False)  # 1-5 estrellas
    comentario = Column(Text)
    # Criterios específicos
    puntualidad = Column(Integer)  # 1-5
    trato = Column(Integer)  # 1-5
    instalaciones = Column(Integer)  # 1-5
    fecha_valoracion = Column(DateTime, default=datetime.now)

    # Constraint: Un paciente solo puede valorar una vez por cita
    __table_args__ = (
        UniqueConstraint("cita_id", name="uq_valoracion_cita"),
        Index("idx_valoracion_doctor", "doctor_id", "calificacion"),
    )

    # Relaciones
    doctor = relationship("Doctor", back_populates="valoraciones")
    paciente = relationship("Paciente", back_populates="valoraciones")
    cita = relationship("Cita", back_populates="valoracion")
