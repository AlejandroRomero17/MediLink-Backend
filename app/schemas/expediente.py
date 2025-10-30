from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date


class ExpedienteMedicoBase(BaseModel):
    fecha: date
    tipo: str
    titulo: str
    descripcion: Optional[str] = None
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    archivo_url: Optional[str] = None


class ExpedienteMedicoCreate(ExpedienteMedicoBase):
    paciente_id: int
    cita_id: Optional[int] = None
    doctor_id: Optional[int] = None


class ExpedienteMedicoResponse(ExpedienteMedicoBase):
    id: int
    paciente_id: int
    cita_id: Optional[int]
    doctor_id: Optional[int]
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
