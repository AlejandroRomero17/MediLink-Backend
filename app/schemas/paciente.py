from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.enums import GeneroEnum
from .usuario import UsuarioResponse


class PacienteBase(BaseModel):
    fecha_nacimiento: date
    genero: GeneroEnum
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    numero_seguro: Optional[str] = None
    alergias: Optional[str] = None
    tipo_sangre: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)[+-]$")
    contacto_emergencia_nombre: Optional[str] = None
    contacto_emergencia_telefono: Optional[str] = None


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
