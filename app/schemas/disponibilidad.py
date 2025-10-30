from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class DisponibilidadResponse(BaseModel):
    doctor_id: int
    fecha: str
    horarios_disponibles: List[str]
    mensaje: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProximosHorariosResponse(BaseModel):
    doctor_id: int
    cantidad_encontrados: int
    horarios: List[dict]


class EstadisticasDoctor(BaseModel):
    doctor_id: int
    total_citas: int
    citas_pendientes: int
    citas_confirmadas: int
    citas_completadas: int
    citas_canceladas: int
    citas_hoy: int

    model_config = ConfigDict(from_attributes=True)
