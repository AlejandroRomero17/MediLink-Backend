# app/schemas/doctor.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import EspecialidadEnum
from .usuario import UsuarioResponse
from .horario import HorarioDoctorResponse


class DoctorBase(BaseModel):
    especialidad: EspecialidadEnum
    cedula_profesional: str = Field(..., min_length=6, max_length=20)

    # Campos ahora OBLIGATORIOS
    consultorio: str = Field(..., min_length=3, max_length=200)
    direccion_consultorio: str = Field(..., min_length=10, max_length=500)
    ciudad: str = Field(..., min_length=2, max_length=100)
    estado: str = Field(..., min_length=2, max_length=100)
    codigo_postal: str = Field(..., min_length=4, max_length=10)
    anos_experiencia: int = Field(..., ge=0, le=60)

    # Coordenadas (opcionales por ahora)
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)

    # Costos y duración (ahora obligatorios)
    costo_consulta: float = Field(..., ge=0)
    duracion_cita_minutos: int = Field(30, ge=15, le=120)

    # Información adicional (opcional)
    universidad: Optional[str] = None
    biografia: Optional[str] = None
    foto_url: Optional[str] = None

    # Modalidades de atención
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
    horarios: List[HorarioDoctorResponse] = []  # Lista de horarios del doctor

    model_config = ConfigDict(from_attributes=True)


class DoctorBusqueda(BaseModel):
    """Resultado simplificado para búsquedas"""

    id: int
    nombre_completo: str
    especialidad: str
    ciudad: str  # ← Ahora obligatorio
    calificacion_promedio: float
    total_valoraciones: int
    costo_consulta: float  # ← Ahora obligatorio
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
