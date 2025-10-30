# app/models/enums.py
"""
Enumeraciones utilizadas en los modelos de la base de datos
"""

import enum


class TipoUsuarioEnum(str, enum.Enum):
    """Tipos de usuario en el sistema"""

    PACIENTE = "paciente"
    DOCTOR = "doctor"
    ADMIN = "admin"


class EstadoCitaEnum(str, enum.Enum):
    """Estados posibles de una cita médica"""

    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"


class EspecialidadEnum(str, enum.Enum):
    """Especialidades médicas disponibles"""

    MEDICINA_GENERAL = "medicina_general"
    CARDIOLOGIA = "cardiologia"
    DERMATOLOGIA = "dermatologia"
    PEDIATRIA = "pediatria"
    GINECOLOGIA = "ginecologia"
    TRAUMATOLOGIA = "traumatologia"
    OFTALMOLOGIA = "oftalmologia"
    NEUROLOGIA = "neurologia"
    PSIQUIATRIA = "psiquiatria"
    ODONTOLOGIA = "odontologia"


class GeneroEnum(str, enum.Enum):
    """Género de la persona"""

    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"


class DiaSemanaEnum(int, enum.Enum):
    """Días de la semana (0 = Lunes, 6 = Domingo)"""

    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6
