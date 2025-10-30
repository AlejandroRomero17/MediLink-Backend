from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from models import TipoUsuarioEnum, EstadoCitaEnum, EspecialidadEnum, GeneroEnum


# ============= USUARIOS =============
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    telefono: str = Field(..., min_length=10, max_length=20)
    tipo_usuario: TipoUsuarioEnum


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=100)


class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


# ============= PACIENTES =============
class PacienteBase(BaseModel):
    fecha_nacimiento: date
    genero: GeneroEnum
    direccion: Optional[str] = None
    numero_seguro: Optional[str] = None
    alergias: Optional[str] = None
    tipo_sangre: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)[+-]$")


class PacienteCreate(PacienteBase):
    usuario_id: int


class PacienteResponse(PacienteBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class PacienteCompleto(PacienteResponse):
    usuario: UsuarioResponse

    model_config = ConfigDict(from_attributes=True)


# ============= DOCTORES =============
class DoctorBase(BaseModel):
    especialidad: EspecialidadEnum
    cedula_profesional: str = Field(..., min_length=6, max_length=20)
    consultorio: Optional[str] = Field(None, max_length=200)
    horario_atencion: Optional[str] = None
    costo_consulta: Optional[float] = Field(None, ge=0)


class DoctorCreate(DoctorBase):
    usuario_id: int


class DoctorResponse(DoctorBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorCompleto(DoctorResponse):
    usuario: UsuarioResponse

    model_config = ConfigDict(from_attributes=True)


# ============= CITAS =============
class CitaBase(BaseModel):
    fecha_hora: datetime
    motivo: str = Field(..., min_length=10, max_length=500)
    notas: Optional[str] = None


class CitaCreate(CitaBase):
    paciente_id: int
    doctor_id: int


class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    motivo: Optional[str] = Field(None, min_length=10, max_length=500)
    notas: Optional[str] = None
    diagnostico: Optional[str] = None
    receta: Optional[str] = None
    estado: Optional[EstadoCitaEnum] = None


class CitaResponse(CitaBase):
    id: int
    paciente_id: int
    doctor_id: int
    diagnostico: Optional[str]
    receta: Optional[str]
    estado: EstadoCitaEnum
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)


class CitaCompleta(CitaResponse):
    paciente: PacienteCompleto
    doctor: DoctorCompleto

    model_config = ConfigDict(from_attributes=True)


# ============= TOKEN (para autenticación) =============
class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse  # Agregamos los datos del usuario


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    tipo_usuario: Optional[str] = None
