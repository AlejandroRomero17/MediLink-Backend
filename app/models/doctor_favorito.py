from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class DoctorFavorito(Base):
    """Doctores favoritos de los pacientes"""

    __tablename__ = "doctores_favoritos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = Column(
        Integer, ForeignKey("doctores.id", ondelete="CASCADE"), nullable=False
    )
    fecha_agregado = Column(DateTime, default=datetime.now)

    # Constraint: Un paciente no puede tener el mismo doctor favorito dos veces
    __table_args__ = (
        UniqueConstraint("paciente_id", "doctor_id", name="uq_doctor_favorito"),
    )

    # Relaciones
    paciente = relationship("Paciente", back_populates="doctores_favoritos")
    doctor = relationship("Doctor", back_populates="favoritos")
