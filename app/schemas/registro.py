from pydantic import BaseModel
from .usuario import UsuarioCreate
from .paciente import PacienteBase
from .doctor import DoctorBase


class PacienteRegistroCompleto(BaseModel):
    """Para registrar usuario + paciente en una sola petición"""

    usuario: UsuarioCreate
    paciente: PacienteBase


class DoctorRegistroCompleto(BaseModel):
    """Para registrar usuario + doctor en una sola petición"""

    usuario: UsuarioCreate
    doctor: DoctorBase
