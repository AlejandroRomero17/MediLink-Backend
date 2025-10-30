from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import TipoUsuarioEnum


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
