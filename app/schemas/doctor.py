from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import EspecialidadEnum
from .usuario import UsuarioResponse


class DoctorBase(BaseModel):
    especialidad: EspecialidadEnum
    cedula_profesional: str = Field(..., min_length=6, max_length=20)
    consultorio: Optional[str] = Field(None, max_length=200)
    direccion_consultorio: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)
    horario_atencion: Optional[str] = None
    costo_consulta: Optional[float] = Field(None, ge=0)
    duracion_cita_minutos: Optional[int] = Field(30, ge=15, le=120)
    anos_experiencia: Optional[int] = Field(None, ge=0)
    universidad: Optional[str] = None
    biografia: Optional[str] = None
    foto_url: Optional[str] = None
    acepta_seguro: bool = False
    atiende_domicilio: bool = False
    atiende_videollamada: bool = False


class DoctorCreate(DoctorBase):
    usuario_id: int


class DoctorResponse(DoctorBase):
    id: int
    usuario_id: int
    calificacion_promedio: float
    total_valoraciones: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorCompleto(DoctorResponse):
    usuario: UsuarioResponse

    model_config = ConfigDict(from_attributes=True)


class DoctorBusqueda(BaseModel):
    """Resultado simplificado para búsquedas"""

    id: int
    nombre_completo: str
    especialidad: str
    ciudad: Optional[str]
    calificacion_promedio: float
    total_valoraciones: int
    costo_consulta: Optional[float]
    foto_url: Optional[str]
    acepta_seguro: bool
    atiende_videollamada: bool
    distancia_km: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorCercano(BaseModel):
    """Doctor con información de distancia"""

    doctor: DoctorCompleto
    distancia_km: float
    tiempo_estimado_minutos: int
