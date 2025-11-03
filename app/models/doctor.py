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
from .enums import EspecialidadEnum


class Doctor(Base):
    __tablename__ = "doctores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    especialidad = Column(Enum(EspecialidadEnum), nullable=False)
    cedula_profesional = Column(String(20), unique=True, nullable=False)

    # Campos ahora OBLIGATORIOS
    consultorio = Column(String(200), nullable=False)
    direccion_consultorio = Column(Text, nullable=False)
    ciudad = Column(String(100), nullable=False)
    estado = Column(String(100), nullable=False)
    codigo_postal = Column(String(10), nullable=False)
    anos_experiencia = Column(Integer, nullable=False)

    # Coordenadas para búsqueda por ubicación (opcionales por ahora)
    latitud = Column(Float)
    longitud = Column(Float)

    # Costos y duración (ahora obligatorios)
    costo_consulta = Column(Float, nullable=False)
    duracion_cita_minutos = Column(Integer, default=30, nullable=False)

    # Información adicional (opcional)
    universidad = Column(String(200))
    biografia = Column(Text)
    foto_url = Column(String(500))

    # Modalidades de atención
    acepta_seguro = Column(Boolean, default=False)
    atiende_domicilio = Column(Boolean, default=False)
    atiende_videollamada = Column(Boolean, default=False)

    # Valoraciones
    calificacion_promedio = Column(Float, default=0.0)
    total_valoraciones = Column(Integer, default=0)
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Índices para búsquedas
    __table_args__ = (
        Index("idx_doctor_especialidad", "especialidad"),
        Index("idx_doctor_ubicacion", "ciudad", "estado"),
        Index("idx_doctor_calificacion", "calificacion_promedio"),
    )

    # Relaciones
    usuario = relationship("Usuario", back_populates="doctor")
    citas = relationship("Cita", back_populates="doctor", foreign_keys="Cita.doctor_id")
    horarios = relationship(
        "HorarioDoctor", back_populates="doctor", cascade="all, delete-orphan"
    )
    valoraciones = relationship("ValoracionDoctor", back_populates="doctor")
    dias_no_laborales = relationship(
        "DiaNoLaboral", back_populates="doctor", cascade="all, delete-orphan"
    )
    expedientes = relationship("ExpedienteMedico", back_populates="doctor")
    favoritos = relationship("DoctorFavorito", back_populates="doctor")
