from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class ExpedienteMedico(Base):
    """Expediente médico del paciente"""

    __tablename__ = "expedientes_medicos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    cita_id = Column(Integer, ForeignKey("citas.id", ondelete="SET NULL"))
    doctor_id = Column(Integer, ForeignKey("doctores.id", ondelete="SET NULL"))
    fecha = Column(Date, nullable=False, index=True)
    tipo = Column(String(50))  # 'consulta', 'estudio', 'receta', 'vacuna', etc.
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    diagnostico = Column(Text)
    tratamiento = Column(Text)
    archivo_url = Column(String(500))  # PDF, imagen, etc.
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Índices
    __table_args__ = (Index("idx_expediente_paciente_fecha", "paciente_id", "fecha"),)

    # Relaciones
    paciente = relationship("Paciente")
    doctor = relationship("Doctor", back_populates="expedientes")
    cita = relationship("Cita", back_populates="expedientes")
