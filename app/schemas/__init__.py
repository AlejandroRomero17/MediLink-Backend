# Importar todos los schemas para facilitar el acceso
from .usuario import *
from .paciente import *
from .doctor import *
from .cita import *
from .horario import *
from .valoracion import *
from .notificacion import *
from .expediente import *
from .auth import *
from .disponibilidad import *
from .registro import *  # <-- AÑADIR ESTA LÍNEA

__all__ = [
    # Usuario
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioResponse",
    "UsuarioLogin",
    # Paciente
    "PacienteBase",
    "PacienteCreate",
    "PacienteResponse",
    "PacienteCompleto",
    # Doctor
    "DoctorBase",
    "DoctorCreate",
    "DoctorResponse",
    "DoctorCompleto",
    "DoctorBusqueda",
    "DoctorCercano",
    # Cita
    "CitaBase",
    "CitaCreate",
    "CitaUpdate",
    "CitaResponse",
    "CitaCompleta",
    # Horario
    "HorarioDoctorBase",
    "HorarioDoctorCreate",
    "HorarioDoctorResponse",
    "DiaNoLaboralBase",
    "DiaNoLaboralCreate",
    "DiaNoLaboralResponse",
    # Valoración
    "ValoracionDoctorBase",
    "ValoracionDoctorCreate",
    "ValoracionDoctorResponse",
    # Notificación
    "NotificacionBase",
    "NotificacionCreate",
    "NotificacionResponse",
    # Expediente
    "ExpedienteMedicoBase",
    "ExpedienteMedicoCreate",
    "ExpedienteMedicoResponse",
    # Auth
    "Token",
    "TokenData",
    # Disponibilidad
    "DisponibilidadResponse",
    "ProximosHorariosResponse",
    # Estadísticas
    "EstadisticasDoctor",
    # Registro
    "PacienteRegistroCompleto",
    "DoctorRegistroCompleto",  # <-- Estos vienen de registro.py
]
