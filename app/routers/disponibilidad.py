"""
Router de disponibilidad de doctores
Maneja horarios disponibles para agendar citas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, time

# Importaciones actualizadas
from app.models import Doctor, Cita, Usuario, EstadoCitaEnum, TipoUsuarioEnum
from app.schemas import (
    DisponibilidadResponse,
    ProximosHorariosResponse,
    EstadisticasDoctor,
)
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_doctor

router = APIRouter(prefix="/api/disponibilidad", tags=["Disponibilidad"])

# Configuración de horarios (puedes moverlo a .env después)
HORA_INICIO = 8  # 8 AM
HORA_FIN = 18  # 6 PM
DURACION_CITA = 30  # minutos
DIAS_LABORALES = [0, 1, 2, 3, 4]  # Lunes a Viernes


def generar_horarios_del_dia(fecha: datetime) -> List[datetime]:
    """Genera todos los posibles horarios para un día"""
    horarios = []
    hora_actual = HORA_INICIO
    minuto_actual = 0

    while hora_actual < HORA_FIN:
        horario = fecha.replace(
            hour=hora_actual, minute=minuto_actual, second=0, microsecond=0
        )
        horarios.append(horario)

        minuto_actual += DURACION_CITA
        if minuto_actual >= 60:
            hora_actual += 1
            minuto_actual = 0

    return horarios


@router.get("/doctor/{doctor_id}", response_model=DisponibilidadResponse)
def obtener_disponibilidad_doctor(
    doctor_id: int,
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Obtiene los horarios disponibles de un doctor para una fecha específica
    Retorna slots de 30 minutos entre 8 AM y 6 PM que no estén ocupados
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Parsear y validar la fecha
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD",
        )

    # Verificar que la fecha sea futura o hoy
    fecha_actual = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if fecha_obj < fecha_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden consultar fechas pasadas",
        )

    # Verificar que sea día laboral
    if fecha_obj.weekday() not in DIAS_LABORALES:
        return DisponibilidadResponse(
            doctor_id=doctor_id,
            fecha=fecha,
            horarios_disponibles=[],
            mensaje="No hay atención los fines de semana",
        )

    # Generar todos los horarios posibles del día
    todos_horarios = generar_horarios_del_dia(fecha_obj)

    # Si es hoy, filtrar horarios que ya pasaron (+ 1 hora de anticipación)
    ahora = datetime.now()
    hora_minima = ahora + timedelta(hours=1)

    if fecha_obj.date() == ahora.date():
        todos_horarios = [h for h in todos_horarios if h > hora_minima]

    # Obtener citas ocupadas del doctor para ese día
    inicio_dia = fecha_obj.replace(hour=0, minute=0, second=0)
    fin_dia = fecha_obj.replace(hour=23, minute=59, second=59)

    citas_ocupadas = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.fecha_hora >= inicio_dia,
            Cita.fecha_hora <= fin_dia,
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .all()
    )

    # Crear set de horarios ocupados
    horarios_ocupados = {cita.fecha_hora for cita in citas_ocupadas}

    # Filtrar horarios disponibles
    horarios_disponibles = [
        h.strftime("%H:%M") for h in todos_horarios if h not in horarios_ocupados
    ]

    return DisponibilidadResponse(
        doctor_id=doctor_id,
        fecha=fecha,
        horarios_disponibles=horarios_disponibles,
        mensaje=f"Se encontraron {len(horarios_disponibles)} horarios disponibles",
    )


@router.get("/doctor/{doctor_id}/proximos-disponibles")
def obtener_proximos_horarios_disponibles(
    doctor_id: int,
    cantidad: int = Query(10, ge=1, le=50, description="Cantidad de horarios"),
    db: Session = Depends(get_db),
):
    """
    Obtiene los próximos horarios disponibles de un doctor
    Útil para mostrar opciones rápidas al paciente
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    horarios_disponibles = []
    fecha_actual = datetime.now().date()
    dias_buscados = 0
    max_dias = 30  # Buscar hasta 30 días adelante

    while len(horarios_disponibles) < cantidad and dias_buscados < max_dias:
        fecha_busqueda = fecha_actual + timedelta(days=dias_buscados)

        # Saltar fines de semana
        if fecha_busqueda.weekday() not in DIAS_LABORALES:
            dias_buscados += 1
            continue

        # Obtener citas del día
        inicio_dia = datetime.combine(fecha_busqueda, time.min)
        fin_dia = datetime.combine(fecha_busqueda, time.max)

        citas_dia = (
            db.query(Cita)
            .filter(
                Cita.doctor_id == doctor_id,
                Cita.fecha_hora >= inicio_dia,
                Cita.fecha_hora <= fin_dia,
                Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
            )
            .all()
        )

        # Generar horarios del día
        horarios_dia = generar_horarios_del_dia(
            datetime.combine(fecha_busqueda, time.min)
        )
        horarios_ocupados = {cita.fecha_hora for cita in citas_dia}

        # Agregar horarios disponibles
        for horario in horarios_dia:
            if len(horarios_disponibles) >= cantidad:
                break

            # Solo si es en el futuro y no está ocupado
            if horario > datetime.now() and horario not in horarios_ocupados:
                horarios_disponibles.append(
                    {
                        "fecha": horario.strftime("%Y-%m-%d"),
                        "hora": horario.strftime("%H:%M"),
                        "fecha_hora_completa": horario.isoformat(),
                    }
                )

        dias_buscados += 1

    return ProximosHorariosResponse(
        doctor_id=doctor_id,
        cantidad_encontrados=len(horarios_disponibles),
        horarios=horarios_disponibles,
    )


@router.get("/mis-horarios")
def obtener_mis_horarios(
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    current_doctor: Doctor = Depends(get_current_active_doctor),
    db: Session = Depends(get_db),
):
    """
    Obtiene los horarios del doctor autenticado para una fecha
    Muestra qué está ocupado y qué está disponible
    """

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de fecha inválido"
        )

    # Obtener citas del día
    inicio_dia = fecha_obj.replace(hour=0, minute=0, second=0)
    fin_dia = fecha_obj.replace(hour=23, minute=59, second=59)

    citas = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == current_doctor.id,
            Cita.fecha_hora >= inicio_dia,
            Cita.fecha_hora <= fin_dia,
        )
        .all()
    )

    return {
        "doctor_id": current_doctor.id,
        "fecha": fecha,
        "total_citas": len(citas),
        "citas": [
            {
                "id": cita.id,
                "hora": cita.fecha_hora.strftime("%H:%M"),
                "paciente_id": cita.paciente_id,
                "motivo": cita.motivo,
                "estado": cita.estado.value,
            }
            for cita in citas
        ],
    }


@router.get("/estadisticas/doctor/{doctor_id}", response_model=EstadisticasDoctor)
def obtener_estadisticas_doctor(
    doctor_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene estadísticas de citas de un doctor
    Solo accesible por el doctor mismo o admin
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Verificar permisos
    if current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        if doctor.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver estas estadísticas",
            )
    elif current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los pacientes no pueden ver estadísticas de doctores",
        )

    # Contar citas por estado
    total_citas = db.query(Cita).filter(Cita.doctor_id == doctor_id).count()

    citas_pendientes = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.estado == EstadoCitaEnum.PENDIENTE,
        )
        .count()
    )

    citas_confirmadas = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.estado == EstadoCitaEnum.CONFIRMADA,
        )
        .count()
    )

    citas_completadas = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.estado == EstadoCitaEnum.COMPLETADA,
        )
        .count()
    )

    citas_canceladas = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.estado == EstadoCitaEnum.CANCELADA,
        )
        .count()
    )

    # Citas de hoy
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=59)

    citas_hoy = (
        db.query(Cita)
        .filter(
            Cita.doctor_id == doctor_id,
            Cita.fecha_hora >= hoy_inicio,
            Cita.fecha_hora <= hoy_fin,
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .count()
    )

    return EstadisticasDoctor(
        doctor_id=doctor_id,
        total_citas=total_citas,
        citas_pendientes=citas_pendientes,
        citas_confirmadas=citas_confirmadas,
        citas_completadas=citas_completadas,
        citas_canceladas=citas_canceladas,
        citas_hoy=citas_hoy,
    )
