# models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Text,
    Float,
    Boolean,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


# ============= ENUMS =============
class TipoUsuarioEnum(str, enum.Enum):
    PACIENTE = "paciente"
    DOCTOR = "doctor"
    ADMIN = "admin"


class EstadoCitaEnum(str, enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"


class EspecialidadEnum(str, enum.Enum):
    MEDICINA_GENERAL = "medicina_general"
    CARDIOLOGIA = "cardiologia"
    DERMATOLOGIA = "dermatologia"
    PEDIATRIA = "pediatria"
    GINECOLOGIA = "ginecologia"
    TRAUMATOLOGIA = "traumatologia"
    OFTALMOLOGIA = "oftalmologia"
    NEUROLOGIA = "neurologia"


class GeneroEnum(str, enum.Enum):
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"


# ============= MODELOS =============
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

    # Relaciones
    paciente = relationship("Paciente", back_populates="usuario", uselist=False)
    doctor = relationship("Doctor", back_populates="usuario", uselist=False)


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(Enum(GeneroEnum), nullable=False)
    direccion = Column(Text)
    numero_seguro = Column(String(50))
    alergias = Column(Text)
    tipo_sangre = Column(String(5))
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Relaciones
    usuario = relationship("Usuario", back_populates="paciente")
    citas = relationship(
        "Cita", back_populates="paciente", foreign_keys="Cita.paciente_id"
    )


class Doctor(Base):
    __tablename__ = "doctores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    especialidad = Column(Enum(EspecialidadEnum), nullable=False)
    cedula_profesional = Column(String(20), unique=True, nullable=False)
    consultorio = Column(String(200))
    horario_atencion = Column(Text)
    costo_consulta = Column(Float)
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Relaciones
    usuario = relationship("Usuario", back_populates="doctor")
    citas = relationship("Cita", back_populates="doctor", foreign_keys="Cita.doctor_id")


class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctores.id"), nullable=False)
    fecha_hora = Column(DateTime, nullable=False, index=True)
    motivo = Column(Text, nullable=False)
    notas = Column(Text)
    diagnostico = Column(Text)
    receta = Column(Text)
    estado = Column(Enum(EstadoCitaEnum), default=EstadoCitaEnum.PENDIENTE)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    paciente = relationship(
        "Paciente", back_populates="citas", foreign_keys=[paciente_id]
    )
    doctor = relationship("Doctor", back_populates="citas", foreign_keys=[doctor_id])
