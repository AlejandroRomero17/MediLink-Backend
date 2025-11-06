from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional
from app.models.enums import EstadoCitaEnum


# ==================== SCHEMAS DE CREACIÓN ====================


class CitaCreate(BaseModel):
    """Schema para crear una cita (usado por el paciente)"""

    doctor_id: int = Field(..., description="ID del doctor")
    fecha_hora: datetime = Field(..., description="Fecha y hora de la cita")
    motivo: str = Field(
        ..., min_length=10, max_length=500, description="Motivo de la consulta"
    )
    sintomas: Optional[str] = Field(
        None, max_length=1000, description="Síntomas del paciente"
    )
    notas_paciente: Optional[str] = Field(
        None, max_length=1000, description="Notas adicionales del paciente"
    )
    es_videollamada: bool = Field(
        default=False, description="¿Es consulta por videollamada?"
    )

    @validator("fecha_hora")
    def validar_fecha_futura(cls, v):
        if v <= datetime.now():
            raise ValueError("La fecha de la cita debe ser en el futuro")
        return v

    @validator("fecha_hora")
    def validar_antelacion_minima(cls, v):
        ahora = datetime.now()
        antelacion_minima = timedelta(hours=24)  # 24 horas mínimas

        if v <= ahora + antelacion_minima:
            raise ValueError(
                "Las citas deben agendarse con al menos 24 horas de antelación"
            )

        # También validar antelación máxima (ej: 3 meses)
        antelacion_maxima = timedelta(days=90)
        if v > ahora + antelacion_maxima:
            raise ValueError(
                "No se pueden agendar citas con más de 3 meses de antelación"
            )

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "doctor_id": 1,
                "fecha_hora": "2025-11-10T10:00:00",
                "motivo": "Consulta general por dolor de cabeza persistente",
                "sintomas": "Dolor de cabeza intenso desde hace 3 días",
                "notas_paciente": "Preferencia por horario matutino",
                "es_videollamada": False,
            }
        }


class CitaUpdate(BaseModel):
    """Schema para actualizar una cita"""

    fecha_hora: Optional[datetime] = None
    motivo: Optional[str] = Field(None, min_length=10, max_length=500)
    sintomas: Optional[str] = Field(None, max_length=1000)
    notas_paciente: Optional[str] = Field(None, max_length=1000)
    es_videollamada: Optional[bool] = None

    @validator("fecha_hora")
    def validar_fecha_futura(cls, v):
        if v and v <= datetime.now():
            raise ValueError("La fecha de la cita debe ser en el futuro")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "fecha_hora": "2025-11-10T15:00:00",
                "motivo": "Consulta de seguimiento",
            }
        }


# ==================== SCHEMAS DE ACCIONES ====================


class CitaCancelar(BaseModel):
    """Schema para cancelar una cita"""

    motivo_cancelacion: str = Field(
        ..., min_length=10, max_length=500, description="Motivo de la cancelación"
    )

    class Config:
        json_schema_extra = {
            "example": {"motivo_cancelacion": "Surgió un compromiso laboral urgente"}
        }


class CitaCompletarConsulta(BaseModel):
    """Schema para que el doctor complete la consulta"""

    notas_doctor: str = Field(..., min_length=10, description="Notas de la consulta")
    diagnostico: str = Field(..., min_length=10, description="Diagnóstico médico")
    tratamiento: Optional[str] = Field(None, description="Tratamiento recomendado")
    receta: Optional[str] = Field(None, description="Receta médica")

    class Config:
        json_schema_extra = {
            "example": {
                "notas_doctor": "Paciente presenta cefalea tensional",
                "diagnostico": "Cefalea tensional tipo 1",
                "tratamiento": "Paracetamol 500mg cada 8 horas por 5 días",
                "receta": "Paracetamol 500mg - 15 tabletas",
            }
        }


# ==================== SCHEMAS DE RESPUESTA ====================


class CitaBase(BaseModel):
    """Schema base con campos comunes"""

    id: int
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
    duracion_minutos: int
    motivo: str
    sintomas: Optional[str]
    notas_paciente: Optional[str]
    es_videollamada: bool
    url_videollamada: Optional[str]
    estado: EstadoCitaEnum
    costo: Optional[float]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class CitaPacienteInfo(BaseModel):
    """Info del paciente para mostrar en citas del doctor"""

    id: int
    nombre: str
    apellido: str
    telefono: str

    class Config:
        from_attributes = True


class CitaDoctorInfo(BaseModel):
    """Info del doctor para mostrar en citas del paciente"""

    id: int
    nombre: str
    apellido: str
    especialidad: str
    consultorio: Optional[str]
    telefono: str

    class Config:
        from_attributes = True


class CitaResponse(CitaBase):
    """Respuesta completa de una cita"""

    notas_doctor: Optional[str]
    diagnostico: Optional[str]
    tratamiento: Optional[str]
    receta: Optional[str]
    motivo_cancelacion: Optional[str]
    fecha_cancelacion: Optional[datetime]
    cancelado_por_usuario_id: Optional[int]

    class Config:
        from_attributes = True


class CitaConPaciente(CitaResponse):
    """Cita con información del paciente (para doctores)"""

    paciente: CitaPacienteInfo


class CitaConDoctor(CitaResponse):
    """Cita con información del doctor (para pacientes)"""

    doctor: CitaDoctorInfo


# ==================== SCHEMAS DE LISTADO ====================


class CitaListItem(BaseModel):
    """Item resumido para listados"""

    id: int
    fecha_hora: datetime
    motivo: str
    estado: EstadoCitaEnum
    es_videollamada: bool
    duracion_minutos: int

    class Config:
        from_attributes = True


class CitaPacienteListItem(CitaListItem):
    """Item de lista con info del paciente"""

    paciente: CitaPacienteInfo


class CitaDoctorListItem(CitaListItem):
    """Item de lista con info del doctor"""

    doctor: CitaDoctorInfo


# ==================== SCHEMAS DE FILTROS ====================


class CitaFiltros(BaseModel):
    """Filtros para búsqueda de citas"""

    estado: Optional[EstadoCitaEnum] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    es_videollamada: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "estado": "pendiente",
                "fecha_inicio": "2025-11-01T00:00:00",
                "fecha_fin": "2025-11-30T23:59:59",
            }
        }


# ==================== SCHEMAS DE ESTADÍSTICAS ====================


class CitasEstadisticas(BaseModel):
    """Estadísticas de citas"""

    total: int
    pendientes: int
    confirmadas: int
    completadas: int
    canceladas: int
    proxima_cita: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 45,
                "pendientes": 5,
                "confirmadas": 8,
                "completadas": 30,
                "canceladas": 2,
                "proxima_cita": "2025-11-06T10:00:00",
            }
        }
