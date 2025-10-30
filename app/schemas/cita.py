from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import EstadoCitaEnum
from .paciente import PacienteCompleto
from .doctor import DoctorCompleto


class CitaBase(BaseModel):
    fecha_hora: datetime
    duracion_minutos: int = 30
    motivo: str = Field(..., min_length=10, max_length=500)
    sintomas: Optional[str] = None
    notas_paciente: Optional[str] = None
    es_videollamada: bool = False


class CitaCreate(CitaBase):
    paciente_id: int
    doctor_id: int


class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    motivo: Optional[str] = Field(None, min_length=10, max_length=500)
    sintomas: Optional[str] = None
    notas_paciente: Optional[str] = None
    notas_doctor: Optional[str] = None
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    receta: Optional[str] = None
    estado: Optional[EstadoCitaEnum] = None


class CitaResponse(CitaBase):
    id: int
    paciente_id: int
    doctor_id: int
    notas_doctor: Optional[str]
    diagnostico: Optional[str]
    tratamiento: Optional[str]
    receta: Optional[str]
    estado: EstadoCitaEnum
    costo: Optional[float]
    url_videollamada: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)


class CitaCompleta(CitaResponse):
    paciente: PacienteCompleto
    doctor: DoctorCompleto

    model_config = ConfigDict(from_attributes=True)
