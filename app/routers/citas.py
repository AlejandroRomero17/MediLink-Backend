from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.cita import Cita
from app.models.doctor import Doctor
from app.models.paciente import Paciente
from app.models.horario_doctor import HorarioDoctor
from app.models.enums import EstadoCitaEnum, TipoUsuarioEnum
from app.schemas.cita import (
    CitaCreate,
    CitaUpdate,
    CitaCancelar,
    CitaCompletarConsulta,
    CitaConPaciente,
    CitaConDoctor,
    CitaPacienteListItem,
    CitaDoctorListItem,
    CitasEstadisticas,
    CitaFiltros,
    CitaDoctorInfo,
    CitaPacienteInfo,
)

router = APIRouter(prefix="/api/citas", tags=["Citas"])


# ==================== HELPERS ====================


def validar_disponibilidad_doctor(
    db: Session,
    doctor_id: int,
    fecha_hora: datetime,
    duracion_minutos: int,
    excluir_cita_id: Optional[int] = None,
) -> bool:
    """Valida si el doctor está disponible en la fecha/hora indicada"""

    # 1. Verificar que la fecha no sea en el pasado
    if fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=400, detail="No se pueden agendar citas en fechas pasadas"
        )

    # 2. Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # 3. Verificar que la fecha sea en horario laboral del doctor
    dia_semana = fecha_hora.strftime("%A").upper()
    dia_map = {
        "MONDAY": "LUNES",
        "TUESDAY": "MARTES",
        "WEDNESDAY": "MIERCOLES",
        "THURSDAY": "JUEVES",
        "FRIDAY": "VIERNES",
        "SATURDAY": "SABADO",
        "SUNDAY": "DOMINGO",
    }
    dia_semana_es = dia_map.get(dia_semana)

    horario = (
        db.query(HorarioDoctor)
        .filter(
            HorarioDoctor.doctor_id == doctor_id,
            HorarioDoctor.dia_semana == dia_semana_es,
            HorarioDoctor.activo == True,
        )
        .first()
    )

    if not horario:
        raise HTTPException(
            status_code=400, detail=f"El doctor no atiende los días {dia_semana_es}"
        )

    # Verificar hora dentro del rango
    hora_cita = fecha_hora.time()
    if not (horario.hora_inicio <= hora_cita < horario.hora_fin):
        raise HTTPException(
            status_code=400,
            detail=f"La hora debe estar entre {horario.hora_inicio} y {horario.hora_fin}",
        )

    # 4. Verificar que no haya otra cita en ese horario (VERSIÓN SIMPLIFICADA)
    fecha_fin = fecha_hora + timedelta(minutes=duracion_minutos)

    # Obtener todas las citas del doctor que podrían superponerse
    citas_existentes = db.query(Cita).filter(
        Cita.doctor_id == doctor_id,
        Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
    )

    if excluir_cita_id:
        citas_existentes = citas_existentes.filter(Cita.id != excluir_cita_id)

    citas_existentes = citas_existentes.all()

    # Verificar superposición manualmente
    for cita_existente in citas_existentes:
        fecha_fin_existente = cita_existente.fecha_hora + timedelta(
            minutes=cita_existente.duracion_minutos
        )

        # Verificar si hay superposición
        if fecha_hora < fecha_fin_existente and fecha_fin > cita_existente.fecha_hora:
            raise HTTPException(
                status_code=400,
                detail=f"El doctor ya tiene una cita programada a las {cita_existente.fecha_hora.strftime('%H:%M')}",
            )

    return True


def handle_db_operation(db: Session, operation: callable):
    """Maneja operaciones de base de datos con manejo de errores"""
    try:
        return operation()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Error al procesar la solicitud en la base de datos"
        )


def crear_doctor_info_manual(doctor_completo):
    """Crea manualmente la info del doctor para evitar errores de mapeo"""
    return CitaDoctorInfo(
        id=doctor_completo.id,
        nombre=doctor_completo.usuario.nombre,
        apellido=doctor_completo.usuario.apellido,
        especialidad=doctor_completo.especialidad,
        consultorio=doctor_completo.consultorio,
        telefono=doctor_completo.usuario.telefono,
    )


def crear_paciente_info_manual(paciente_completo):
    """Crea manualmente la info del paciente para evitar errores de mapeo"""
    return CitaPacienteInfo(
        id=paciente_completo.id,
        nombre=paciente_completo.usuario.nombre,
        apellido=paciente_completo.usuario.apellido,
        telefono=paciente_completo.usuario.telefono,
    )


# ==================== ENDPOINTS PACIENTE ====================


@router.post("/", response_model=CitaConDoctor, status_code=status.HTTP_201_CREATED)
def crear_cita(
    cita_data: CitaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Crear una nueva cita (solo pacientes)
    """
    # Verificar que el usuario es paciente
    if current_user.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes pueden crear citas",
        )

    # Obtener el paciente
    paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Perfil de paciente no encontrado")

    # Obtener el doctor para verificar el costo
    doctor = db.query(Doctor).filter(Doctor.id == cita_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Validar disponibilidad
    duracion = doctor.duracion_cita_minutos or 30
    validar_disponibilidad_doctor(
        db, cita_data.doctor_id, cita_data.fecha_hora, duracion
    )

    # Crear la cita
    nueva_cita = Cita(
        paciente_id=paciente.id,
        doctor_id=cita_data.doctor_id,
        fecha_hora=cita_data.fecha_hora,
        duracion_minutos=duracion,
        motivo=cita_data.motivo,
        sintomas=cita_data.sintomas,
        notas_paciente=cita_data.notas_paciente,
        es_videollamada=cita_data.es_videollamada,
        estado=EstadoCitaEnum.PENDIENTE,
        costo=doctor.costo_consulta,
    )

    def create_operation():
        db.add(nueva_cita)
        db.commit()
        db.refresh(nueva_cita)
        return nueva_cita

    nueva_cita = handle_db_operation(db, create_operation)

    # Cargar el doctor con su usuario
    doctor_completo = (
        db.query(Doctor)
        .options(joinedload(Doctor.usuario))
        .filter(Doctor.id == nueva_cita.doctor_id)
        .first()
    )

    # Crear la info del doctor manualmente
    doctor_info = crear_doctor_info_manual(doctor_completo)

    # Crear la respuesta manualmente
    response = CitaConDoctor(
        # Campos básicos de la cita
        id=nueva_cita.id,
        paciente_id=nueva_cita.paciente_id,
        doctor_id=nueva_cita.doctor_id,
        fecha_hora=nueva_cita.fecha_hora,
        duracion_minutos=nueva_cita.duracion_minutos,
        motivo=nueva_cita.motivo,
        sintomas=nueva_cita.sintomas,
        notas_paciente=nueva_cita.notas_paciente,
        es_videollamada=nueva_cita.es_videollamada,
        url_videollamada=nueva_cita.url_videollamada,
        estado=nueva_cita.estado,
        costo=nueva_cita.costo,
        fecha_creacion=nueva_cita.fecha_creacion,
        fecha_actualizacion=nueva_cita.fecha_actualizacion,
        # Campos médicos (pueden ser None)
        notas_doctor=nueva_cita.notas_doctor,
        diagnostico=nueva_cita.diagnostico,
        tratamiento=nueva_cita.tratamiento,
        receta=nueva_cita.receta,
        # Campos de cancelación (pueden ser None)
        motivo_cancelacion=nueva_cita.motivo_cancelacion,
        fecha_cancelacion=nueva_cita.fecha_cancelacion,
        cancelado_por_usuario_id=nueva_cita.cancelado_por_usuario_id,
        # Información del doctor
        doctor=doctor_info,
    )

    return response


@router.get("/mis-citas", response_model=List[CitaDoctorListItem])
def obtener_mis_citas_paciente(
    estado: Optional[EstadoCitaEnum] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtener todas las citas del paciente actual (con filtros opcionales)
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes pueden acceder a sus citas",
        )

    paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Perfil de paciente no encontrado")

    query = db.query(Cita).filter(Cita.paciente_id == paciente.id)

    # Aplicar filtros
    if estado:
        query = query.filter(Cita.estado == estado)
    if fecha_inicio:
        query = query.filter(Cita.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Cita.fecha_hora <= fecha_fin)

    # Obtener citas con relaciones
    citas_db = (
        query.options(joinedload(Cita.doctor).joinedload(Doctor.usuario))
        .order_by(Cita.fecha_hora.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Crear respuesta manualmente para cada cita
    citas_response = []
    for cita in citas_db:
        doctor_info = crear_doctor_info_manual(cita.doctor)

        cita_response = CitaDoctorListItem(
            id=cita.id,
            fecha_hora=cita.fecha_hora,
            motivo=cita.motivo,
            estado=cita.estado,
            es_videollamada=cita.es_videollamada,
            duracion_minutos=cita.duracion_minutos,
            doctor=doctor_info,
        )
        citas_response.append(cita_response)

    return citas_response


@router.get("/proximas", response_model=List[CitaDoctorListItem])
def obtener_citas_proximas_paciente(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtener las próximas citas del paciente
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(status_code=403, detail="Solo pacientes")

    paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()

    citas_db = (
        db.query(Cita)
        .options(joinedload(Cita.doctor).joinedload(Doctor.usuario))
        .filter(
            Cita.paciente_id == paciente.id,
            Cita.fecha_hora >= datetime.now(),
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .order_by(Cita.fecha_hora.asc())
        .limit(limit)
        .all()
    )

    # Crear respuesta manualmente
    citas_response = []
    for cita in citas_db:
        doctor_info = crear_doctor_info_manual(cita.doctor)

        cita_response = CitaDoctorListItem(
            id=cita.id,
            fecha_hora=cita.fecha_hora,
            motivo=cita.motivo,
            estado=cita.estado,
            es_videollamada=cita.es_videollamada,
            duracion_minutos=cita.duracion_minutos,
            doctor=doctor_info,
        )
        citas_response.append(cita_response)

    return citas_response


# ==================== ENDPOINTS DOCTOR ====================


@router.get("/doctor/mis-citas", response_model=List[CitaPacienteListItem])
def obtener_mis_citas_doctor(
    estado: Optional[EstadoCitaEnum] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtener todas las citas del doctor actual
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los doctores pueden acceder a sus citas",
        )

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Perfil de doctor no encontrado")

    query = db.query(Cita).filter(Cita.doctor_id == doctor.id)

    if estado:
        query = query.filter(Cita.estado == estado)
    if fecha_inicio:
        query = query.filter(Cita.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Cita.fecha_hora <= fecha_fin)

    # Obtener citas con relaciones
    citas_db = (
        query.options(joinedload(Cita.paciente).joinedload(Paciente.usuario))
        .order_by(Cita.fecha_hora.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Crear respuesta manualmente para cada cita
    citas_response = []
    for cita in citas_db:
        paciente_info = crear_paciente_info_manual(cita.paciente)

        cita_response = CitaPacienteListItem(
            id=cita.id,
            fecha_hora=cita.fecha_hora,
            motivo=cita.motivo,
            estado=cita.estado,
            es_videollamada=cita.es_videollamada,
            duracion_minutos=cita.duracion_minutos,
            paciente=paciente_info,
        )
        citas_response.append(cita_response)

    return citas_response


@router.get("/doctor/proximas", response_model=List[CitaPacienteListItem])
def obtener_citas_proximas_doctor(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtener las próximas citas del doctor
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Solo doctores")

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()

    citas_db = (
        db.query(Cita)
        .options(joinedload(Cita.paciente).joinedload(Paciente.usuario))
        .filter(
            Cita.doctor_id == doctor.id,
            Cita.fecha_hora >= datetime.now(),
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .order_by(Cita.fecha_hora.asc())
        .limit(limit)
        .all()
    )

    # Crear respuesta manualmente
    citas_response = []
    for cita in citas_db:
        paciente_info = crear_paciente_info_manual(cita.paciente)

        cita_response = CitaPacienteListItem(
            id=cita.id,
            fecha_hora=cita.fecha_hora,
            motivo=cita.motivo,
            estado=cita.estado,
            es_videollamada=cita.es_videollamada,
            duracion_minutos=cita.duracion_minutos,
            paciente=paciente_info,
        )
        citas_response.append(cita_response)

    return citas_response


@router.get("/doctor/hoy", response_model=List[CitaPacienteListItem])
def obtener_citas_hoy_doctor(
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener las citas del doctor para hoy
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Solo doctores")

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()

    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = hoy_inicio + timedelta(days=1)

    citas_db = (
        db.query(Cita)
        .options(joinedload(Cita.paciente).joinedload(Paciente.usuario))
        .filter(
            Cita.doctor_id == doctor.id,
            Cita.fecha_hora >= hoy_inicio,
            Cita.fecha_hora < hoy_fin,
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .order_by(Cita.fecha_hora.asc())
        .all()
    )

    # Crear respuesta manualmente
    citas_response = []
    for cita in citas_db:
        paciente_info = crear_paciente_info_manual(cita.paciente)

        cita_response = CitaPacienteListItem(
            id=cita.id,
            fecha_hora=cita.fecha_hora,
            motivo=cita.motivo,
            estado=cita.estado,
            es_videollamada=cita.es_videollamada,
            duracion_minutos=cita.duracion_minutos,
            paciente=paciente_info,
        )
        citas_response.append(cita_response)

    return citas_response


# ==================== ENDPOINTS COMUNES ====================


@router.get("/{cita_id}", response_model=CitaConDoctor)
def obtener_cita_detalle(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtener detalle completo de una cita
    """
    # Cargar cita con todas las relaciones
    cita = (
        db.query(Cita)
        .options(
            joinedload(Cita.doctor).joinedload(Doctor.usuario),
            joinedload(Cita.paciente).joinedload(Paciente.usuario),
        )
        .filter(Cita.id == cita_id)
        .first()
    )

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Verificar permisos
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        paciente = (
            db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        )
        if cita.paciente_id != paciente.id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para ver esta cita"
            )
    elif current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        if cita.doctor_id != doctor.id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para ver esta cita"
            )

    # Crear respuesta manualmente
    doctor_info = crear_doctor_info_manual(cita.doctor)

    response = CitaConDoctor(
        id=cita.id,
        paciente_id=cita.paciente_id,
        doctor_id=cita.doctor_id,
        fecha_hora=cita.fecha_hora,
        duracion_minutos=cita.duracion_minutos,
        motivo=cita.motivo,
        sintomas=cita.sintomas,
        notas_paciente=cita.notas_paciente,
        es_videollamada=cita.es_videollamada,
        url_videollamada=cita.url_videollamada,
        estado=cita.estado,
        costo=cita.costo,
        fecha_creacion=cita.fecha_creacion,
        fecha_actualizacion=cita.fecha_actualizacion,
        notas_doctor=cita.notas_doctor,
        diagnostico=cita.diagnostico,
        tratamiento=cita.tratamiento,
        receta=cita.receta,
        motivo_cancelacion=cita.motivo_cancelacion,
        fecha_cancelacion=cita.fecha_cancelacion,
        cancelado_por_usuario_id=cita.cancelado_por_usuario_id,
        doctor=doctor_info,
    )

    return response


@router.put("/{cita_id}", response_model=CitaConDoctor)
def actualizar_cita(
    cita_id: int,
    cita_data: CitaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Actualizar una cita existente (solo paciente dueño de la cita)
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=403, detail="Solo pacientes pueden actualizar citas"
        )

    paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
    cita = (
        db.query(Cita)
        .filter(Cita.id == cita_id, Cita.paciente_id == paciente.id)
        .first()
    )

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Validar que la cita no esté cancelada o completada
    if cita.estado in [EstadoCitaEnum.CANCELADA, EstadoCitaEnum.COMPLETADA]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede actualizar una cita en estado {cita.estado.value}",
        )

    # Si cambia la fecha/hora, validar disponibilidad
    if cita_data.fecha_hora and cita_data.fecha_hora != cita.fecha_hora:
        validar_disponibilidad_doctor(
            db, cita.doctor_id, cita_data.fecha_hora, cita.duracion_minutos, cita_id
        )
        cita.fecha_hora = cita_data.fecha_hora

    # Actualizar otros campos
    update_data = cita_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "fecha_hora":  # Ya manejado arriba
            setattr(cita, field, value)

    def update_operation():
        cita.fecha_actualizacion = datetime.now()
        db.commit()
        db.refresh(cita)
        return cita

    cita_actualizada = handle_db_operation(db, update_operation)

    # Cargar relaciones para la respuesta
    cita_completa = (
        db.query(Cita)
        .options(joinedload(Cita.doctor).joinedload(Doctor.usuario))
        .filter(Cita.id == cita_actualizada.id)
        .first()
    )

    # Crear respuesta manualmente
    doctor_info = crear_doctor_info_manual(cita_completa.doctor)

    response = CitaConDoctor(
        id=cita_completa.id,
        paciente_id=cita_completa.paciente_id,
        doctor_id=cita_completa.doctor_id,
        fecha_hora=cita_completa.fecha_hora,
        duracion_minutos=cita_completa.duracion_minutos,
        motivo=cita_completa.motivo,
        sintomas=cita_completa.sintomas,
        notas_paciente=cita_completa.notas_paciente,
        es_videollamada=cita_completa.es_videollamada,
        url_videollamada=cita_completa.url_videollamada,
        estado=cita_completa.estado,
        costo=cita_completa.costo,
        fecha_creacion=cita_completa.fecha_creacion,
        fecha_actualizacion=cita_completa.fecha_actualizacion,
        notas_doctor=cita_completa.notas_doctor,
        diagnostico=cita_completa.diagnostico,
        tratamiento=cita_completa.tratamiento,
        receta=cita_completa.receta,
        motivo_cancelacion=cita_completa.motivo_cancelacion,
        fecha_cancelacion=cita_completa.fecha_cancelacion,
        cancelado_por_usuario_id=cita_completa.cancelado_por_usuario_id,
        doctor=doctor_info,
    )

    return response


@router.put("/{cita_id}/cancelar")
def cancelar_cita(
    cita_id: int,
    cancelacion: CitaCancelar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cancelar una cita (paciente o doctor)
    """
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Verificar permisos
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        paciente = (
            db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        )
        if cita.paciente_id != paciente.id:
            raise HTTPException(status_code=403, detail="No puedes cancelar esta cita")
    elif current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        if cita.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="No puedes cancelar esta cita")

    # Verificar que la cita no esté ya cancelada o completada
    if cita.estado in [EstadoCitaEnum.CANCELADA, EstadoCitaEnum.COMPLETADA]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar una cita en estado {cita.estado.value}",
        )

    # Actualizar cita
    cita.estado = EstadoCitaEnum.CANCELADA
    cita.motivo_cancelacion = cancelacion.motivo_cancelacion
    cita.cancelado_por_usuario_id = current_user.id
    cita.fecha_cancelacion = datetime.now()

    def cancel_operation():
        db.commit()
        return {"message": "Cita cancelada exitosamente", "cita_id": cita.id}

    return handle_db_operation(db, cancel_operation)


@router.put("/{cita_id}/completar", response_model=CitaConPaciente)
def completar_cita(
    cita_id: int,
    consulta_data: CitaCompletarConsulta,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Marcar cita como completada y agregar notas médicas (solo doctor)
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(
            status_code=403, detail="Solo doctores pueden completar citas"
        )

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
    cita = (
        db.query(Cita).filter(Cita.id == cita_id, Cita.doctor_id == doctor.id).first()
    )

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.estado == EstadoCitaEnum.CANCELADA:
        raise HTTPException(
            status_code=400, detail="No se puede completar una cita cancelada"
        )

    # Actualizar cita
    cita.estado = EstadoCitaEnum.COMPLETADA
    cita.notas_doctor = consulta_data.notas_doctor
    cita.diagnostico = consulta_data.diagnostico
    cita.tratamiento = consulta_data.tratamiento
    cita.receta = consulta_data.receta

    def complete_operation():
        db.commit()
        db.refresh(cita)
        return cita

    cita_completada = handle_db_operation(db, complete_operation)

    # Cargar relaciones para la respuesta
    cita_con_paciente_db = (
        db.query(Cita)
        .options(joinedload(Cita.paciente).joinedload(Paciente.usuario))
        .filter(Cita.id == cita_completada.id)
        .first()
    )

    # Crear respuesta manualmente
    paciente_info = crear_paciente_info_manual(cita_con_paciente_db.paciente)

    response = CitaConPaciente(
        id=cita_con_paciente_db.id,
        paciente_id=cita_con_paciente_db.paciente_id,
        doctor_id=cita_con_paciente_db.doctor_id,
        fecha_hora=cita_con_paciente_db.fecha_hora,
        duracion_minutos=cita_con_paciente_db.duracion_minutos,
        motivo=cita_con_paciente_db.motivo,
        sintomas=cita_con_paciente_db.sintomas,
        notas_paciente=cita_con_paciente_db.notas_paciente,
        es_videollamada=cita_con_paciente_db.es_videollamada,
        url_videollamada=cita_con_paciente_db.url_videollamada,
        estado=cita_con_paciente_db.estado,
        costo=cita_con_paciente_db.costo,
        fecha_creacion=cita_con_paciente_db.fecha_creacion,
        fecha_actualizacion=cita_con_paciente_db.fecha_actualizacion,
        notas_doctor=cita_con_paciente_db.notas_doctor,
        diagnostico=cita_con_paciente_db.diagnostico,
        tratamiento=cita_con_paciente_db.tratamiento,
        receta=cita_con_paciente_db.receta,
        motivo_cancelacion=cita_con_paciente_db.motivo_cancelacion,
        fecha_cancelacion=cita_con_paciente_db.fecha_cancelacion,
        cancelado_por_usuario_id=cita_con_paciente_db.cancelado_por_usuario_id,
        paciente=paciente_info,
    )

    return response


@router.put("/{cita_id}/estado/{estado}")
def cambiar_estado_cita(
    cita_id: int,
    estado: EstadoCitaEnum,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cambiar estado de una cita (solo doctor dueño de la cita)
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(
            status_code=403, detail="Solo doctores pueden cambiar estados"
        )

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
    cita = (
        db.query(Cita).filter(Cita.id == cita_id, Cita.doctor_id == doctor.id).first()
    )

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Validar transiciones de estado
    if estado == EstadoCitaEnum.CANCELADA:
        raise HTTPException(
            status_code=400, detail="Use el endpoint de cancelación para cancelar citas"
        )

    if estado == EstadoCitaEnum.COMPLETADA:
        raise HTTPException(
            status_code=400,
            detail="Use el endpoint de completar consulta para finalizar citas",
        )

    cita.estado = estado
    cita.fecha_actualizacion = datetime.now()

    def change_state_operation():
        db.commit()
        return {
            "message": f"Estado de cita actualizado a {estado.value}",
            "cita_id": cita.id,
        }

    return handle_db_operation(db, change_state_operation)


@router.get("/estadisticas/mis-citas", response_model=CitasEstadisticas)
def obtener_estadisticas_citas(
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas de citas del usuario actual
    """
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        paciente = (
            db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        )
        base_query = db.query(Cita).filter(Cita.paciente_id == paciente.id)
    else:
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        base_query = db.query(Cita).filter(Cita.doctor_id == doctor.id)

    total = base_query.count()
    pendientes = base_query.filter(Cita.estado == EstadoCitaEnum.PENDIENTE).count()
    confirmadas = base_query.filter(Cita.estado == EstadoCitaEnum.CONFIRMADA).count()
    completadas = base_query.filter(Cita.estado == EstadoCitaEnum.COMPLETADA).count()
    canceladas = base_query.filter(Cita.estado == EstadoCitaEnum.CANCELADA).count()

    # Obtener próxima cita
    proxima = (
        base_query.filter(
            Cita.fecha_hora >= datetime.now(),
            Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
        )
        .order_by(Cita.fecha_hora.asc())
        .first()
    )

    return CitasEstadisticas(
        total=total,
        pendientes=pendientes,
        confirmadas=confirmadas,
        completadas=completadas,
        canceladas=canceladas,
        proxima_cita=proxima.fecha_hora if proxima else None,
    )
