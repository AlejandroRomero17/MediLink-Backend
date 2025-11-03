from pydantic import BaseModel
from typing import List
from .usuario import UsuarioCreate
from .paciente import PacienteBase
from .doctor import DoctorBase
from .horario import HorarioDoctorBase


class PacienteRegistroCompleto(BaseModel):
    """Para registrar usuario + paciente en una sola petición"""

    usuario: UsuarioCreate
    paciente: PacienteBase


class DoctorRegistroCompleto(BaseModel):
    """Para registrar usuario + doctor en una sola petición"""

    usuario: UsuarioCreate
    doctor: DoctorBase
    horarios: List[HorarioDoctorBase] = []  # Lista de horarios


class DoctorRegistroCompletoResponse(BaseModel):
    """Respuesta del registro de doctor"""

    access_token: str
    token_type: str
    usuario: dict
    doctor: dict
    horarios_creados: int  # Cantidad de horarios creados
