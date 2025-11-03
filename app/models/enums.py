from enum import Enum


class TipoUsuarioEnum(str, Enum):
    """Tipos de usuario en el sistema"""

    PACIENTE = "paciente"
    DOCTOR = "doctor"
    ADMIN = "admin"


class GeneroEnum(str, Enum):
    """Géneros disponibles"""

    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"


class TipoSangreEnum(str, Enum):
    """Tipos de sangre"""

    A_POSITIVO = "A+"
    A_NEGATIVO = "A-"
    B_POSITIVO = "B+"
    B_NEGATIVO = "B-"
    AB_POSITIVO = "AB+"
    AB_NEGATIVO = "AB-"
    O_POSITIVO = "O+"
    O_NEGATIVO = "O-"


class EspecialidadEnum(str, Enum):
    """Especialidades médicas disponibles"""

    MEDICINA_GENERAL = "medicina_general"
    CARDIOLOGIA = "cardiologia"
    DERMATOLOGIA = "dermatologia"
    GINECOLOGIA = "ginecologia"
    NEUROLOGIA = "neurologia"
    OFTALMOLOGIA = "oftalmologia"
    PEDIATRIA = "pediatria"
    TRAUMATOLOGIA = "traumatologia"
    PSIQUIATRIA = "psiquiatria"
    UROLOGIA = "urologia"
    ONCOLOGIA = "oncologia"
    ENDOCRINOLOGIA = "endocrinologia"


class DiaSemanaEnum(str, Enum):
    """Días de la semana - IMPORTANTE: usar strings en lugar de enteros"""

    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"


class EstadoCitaEnum(str, Enum):
    """Estados posibles de una cita"""

    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA_PACIENTE = "cancelada_paciente"
    CANCELADA_DOCTOR = "cancelada_doctor"
    NO_ASISTIO = "no_asistio"


class TipoNotificacionEnum(str, Enum):
    """Tipos de notificaciones"""

    NUEVA_CITA = "nueva_cita"
    CONFIRMACION_CITA = "confirmacion_cita"
    RECORDATORIO_CITA = "recordatorio_cita"
    CANCELACION_CITA = "cancelacion_cita"
    MENSAJE = "mensaje"
    ALERTA = "alerta"
