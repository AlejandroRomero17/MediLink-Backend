from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime, time
from app.models.enums import DiaSemanaEnum


class HorarioDoctorBase(BaseModel):
    dia_semana: DiaSemanaEnum
    hora_inicio: time
    hora_fin: time
    activo: bool = True


class HorarioDoctorCreate(HorarioDoctorBase):
    doctor_id: int


class HorarioDoctorResponse(HorarioDoctorBase):
    id: int
    doctor_id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class DiaNoLaboralBase(BaseModel):
    fecha: date
    motivo: Optional[str] = None


class DiaNoLaboralCreate(DiaNoLaboralBase):
    doctor_id: int


class DiaNoLaboralResponse(DiaNoLaboralBase):
    id: int
    doctor_id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
