from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NotificacionBase(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = None
    url: Optional[str] = None


class NotificacionCreate(NotificacionBase):
    usuario_id: int


class NotificacionResponse(NotificacionBase):
    id: int
    usuario_id: int
    leida: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
