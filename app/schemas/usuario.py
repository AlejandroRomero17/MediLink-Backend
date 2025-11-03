from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import TipoUsuarioEnum


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=10, max_length=15)


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)
    tipo_usuario: Optional[TipoUsuarioEnum] = (
        None  # ← OPCIONAL: Se asigna en el endpoint
    )

    # Nota: En el endpoint de registro combinado (/api/registro/doctor o /paciente)
    # el tipo_usuario se fuerza automáticamente, por lo que no es necesario enviarlo


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, min_length=10, max_length=15)


class UsuarioResponse(UsuarioBase):
    id: int
    tipo_usuario: TipoUsuarioEnum
    activo: bool
    fecha_registro: datetime  # ← Cambiado de fecha_creacion
    fecha_actualizacion: Optional[datetime] = None  # ← Cambiado de fecha_modificacion

    model_config = ConfigDict(from_attributes=True)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str
