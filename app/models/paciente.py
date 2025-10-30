from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
from .enums import GeneroEnum


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(Enum(GeneroEnum), nullable=False)
    direccion = Column(Text)
    ciudad = Column(String(100))
    estado = Column(String(100))
    codigo_postal = Column(String(10))
    numero_seguro = Column(String(50))
    alergias = Column(Text)
    tipo_sangre = Column(String(5))
    contacto_emergencia_nombre = Column(String(200))
    contacto_emergencia_telefono = Column(String(20))
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Relaciones
    usuario = relationship("Usuario", back_populates="paciente")
    citas = relationship(
        "Cita", back_populates="paciente", foreign_keys="Cita.paciente_id"
    )
    valoraciones = relationship("ValoracionDoctor", back_populates="paciente")
    doctores_favoritos = relationship("DoctorFavorito", back_populates="paciente")
