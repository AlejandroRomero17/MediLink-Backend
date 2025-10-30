from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ValoracionDoctorBase(BaseModel):
    calificacion: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None
    puntualidad: Optional[int] = Field(None, ge=1, le=5)
    trato: Optional[int] = Field(None, ge=1, le=5)
    instalaciones: Optional[int] = Field(None, ge=1, le=5)


class ValoracionDoctorCreate(ValoracionDoctorBase):
    doctor_id: int
    paciente_id: int
    cita_id: Optional[int] = None


class ValoracionDoctorResponse(ValoracionDoctorBase):
    id: int
    doctor_id: int
    paciente_id: int
    cita_id: Optional[int]
    fecha_valoracion: datetime

    model_config = ConfigDict(from_attributes=True)
