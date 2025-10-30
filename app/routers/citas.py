from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

# Importaciones actualizadas
from app.models import Cita, Paciente, Doctor, Usuario, EstadoCitaEnum, TipoUsuarioEnum
from app.schemas import CitaCreate, CitaResponse, CitaCompleta, CitaUpdate
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/api/citas", tags=["Citas"])

# Configuración de citas
DURACION_CITA_MINUTOS = 30
HORA_INICIO_LABORAL = 8  # 8 AM
HORA_FIN_LABORAL = 18  # 6 PM


def verificar_horario_laboral(fecha_hora: datetime) -> None:
    """Verifica que la fecha/hora esté dentro del horario laboral"""
    hora = fecha_hora.hour
    dia_semana = fecha_hora.weekday()  # 0=Lunes, 6=Domingo

    if hora < HORA_INICIO_LABORAL or hora >= HORA_FIN_LABORAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Las citas solo pueden agendarse entre {HORA_INICIO_LABORAL}:00 y {HORA_FIN_LABORAL}:00",
        )

    if dia_semana >= 5:  # Sábado o Domingo
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden agendar citas los fines de semana",
        )


def verificar_conflicto_horario(
    db: Session, doctor_id: int, fecha_hora: datetime, cita_id: int = None
) -> None:
    """Verifica que no haya conflictos de horario con otras citas del doctor"""
    duracion = timedelta(minutes=DURACION_CITA_MINUTOS)
    inicio_nueva = fecha_hora
    fin_nueva = inicio_nueva + duracion

    # Obtener todas las citas activas del doctor
    query = db.query(Cita).filter(
        Cita.doctor_id == doctor_id,
        Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
    )

    # Si es una actualización, excluir la cita actual
    if cita_id:
        query = query.filter(Cita.id != cita_id)

    citas_doctor = query.all()

    # Verificar solapamiento con cada cita
    for cita_existente in citas_doctor:
        inicio_existente = cita_existente.fecha_hora
        fin_existente = inicio_existente + duracion

        # Hay conflicto si los rangos se solapan
        if inicio_nueva < fin_existente and fin_nueva > inicio_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hay un conflicto de horario. El doctor tiene otra cita entre {inicio_existente.strftime('%H:%M')} y {fin_existente.strftime('%H:%M')}",
            )


def verificar_permisos_cita(cita: Cita, usuario: Usuario) -> None:
    """Verifica que el usuario tenga permisos para acceder a la cita"""
    if usuario.tipo_usuario == TipoUsuarioEnum.ADMIN:
        return  # Admin tiene acceso total

    if usuario.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        if cita.paciente.usuario_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta cita",
            )
    elif usuario.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        if cita.doctor.usuario_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta cita",
            )


@router.post("", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
def crear_cita(
    cita: CitaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea una nueva cita médica"""

    # Verificar que el paciente existe
    paciente = db.query(Paciente).filter(Paciente.id == cita.paciente_id).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    # Verificar permisos: un paciente solo puede crear citas para sí mismo
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        if paciente.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes crear citas para ti mismo",
            )

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == cita.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Verificar que la fecha sea futura (al menos 1 hora de anticipación)
    hora_minima = datetime.now() + timedelta(hours=1)
    if cita.fecha_hora <= hora_minima:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cita debe agendarse con al menos 1 hora de anticipación",
        )

    # Verificar horario laboral
    verificar_horario_laboral(cita.fecha_hora)

    # Verificar conflictos de horario
    verificar_conflicto_horario(db, cita.doctor_id, cita.fecha_hora)

    # Crear nueva cita
    nueva_cita = Cita(**cita.model_dump())
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    return nueva_cita


@router.get("", response_model=List[CitaResponse])
def obtener_citas(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene citas filtradas según el rol del usuario"""

    query = db.query(Cita)

    # Filtrar según el rol
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        # Pacientes solo ven sus propias citas
        paciente = (
            db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        )
        if paciente:
            query = query.filter(Cita.paciente_id == paciente.id)
        else:
            return []

    elif current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        # Doctores solo ven sus propias citas
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        if doctor:
            query = query.filter(Cita.doctor_id == doctor.id)
        else:
            return []

    # Admin ve todas las citas

    # Filtrar por estado si se especifica
    if estado:
        query = query.filter(Cita.estado == estado)

    # Ordenar por fecha (más recientes primero)
    query = query.order_by(Cita.fecha_hora.desc())

    citas = query.offset(skip).limit(limit).all()
    return citas


@router.get("/{cita_id}", response_model=CitaCompleta)
def obtener_cita(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene una cita específica con información completa"""

    cita = db.query(Cita).filter(Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Verificar permisos
    verificar_permisos_cita(cita, current_user)

    return cita


@router.get("/paciente/{paciente_id}", response_model=List[CitaResponse])
def obtener_citas_paciente(
    paciente_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene todas las citas de un paciente específico"""

    # Verificar que el paciente existe
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    # Verificar permisos
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        if paciente.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver estas citas",
            )

    citas = (
        db.query(Cita)
        .filter(Cita.paciente_id == paciente_id)
        .order_by(Cita.fecha_hora.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return citas


@router.get("/doctor/{doctor_id}", response_model=List[CitaResponse])
def obtener_citas_doctor(
    doctor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene todas las citas de un doctor específico"""

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
                detail="No tienes permiso para ver estas citas",
            )

    citas = (
        db.query(Cita)
        .filter(Cita.doctor_id == doctor_id)
        .order_by(Cita.fecha_hora.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return citas


@router.patch("/{cita_id}", response_model=CitaResponse)
def actualizar_cita(
    cita_id: int,
    cita_update: CitaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza información de una cita existente"""

    cita = db.query(Cita).filter(Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Verificar permisos
    verificar_permisos_cita(cita, current_user)

    # No se puede modificar una cita completada o cancelada
    if cita.estado in [
        EstadoCitaEnum.COMPLETADA,
        EstadoCitaEnum.CANCELADA,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar una cita completada o cancelada",
        )

    # Actualizar solo los campos proporcionados
    update_data = cita_update.model_dump(exclude_unset=True)

    # Si se actualiza la fecha, hacer validaciones
    if "fecha_hora" in update_data and update_data["fecha_hora"]:
        nueva_fecha = update_data["fecha_hora"]

        # Verificar que sea futura
        hora_minima = datetime.now() + timedelta(hours=1)
        if nueva_fecha <= hora_minima:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cita debe reagendarse con al menos 1 hora de anticipación",
            )

        # Verificar horario laboral
        verificar_horario_laboral(nueva_fecha)

        # Verificar conflictos de horario
        verificar_conflicto_horario(db, cita.doctor_id, nueva_fecha, cita_id)

    # Aplicar actualizaciones
    for campo, valor in update_data.items():
        setattr(cita, campo, valor)

    db.commit()
    db.refresh(cita)

    return cita


@router.delete("/{cita_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_cita(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cancela una cita (cambia su estado a cancelada)"""

    cita = db.query(Cita).filter(Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Verificar permisos
    verificar_permisos_cita(cita, current_user)

    # No se puede cancelar una cita ya completada o cancelada
    if cita.estado in [
        EstadoCitaEnum.COMPLETADA,
        EstadoCitaEnum.CANCELADA,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar una cita completada o ya cancelada",
        )

    # Cambiar estado a cancelada
    cita.estado = EstadoCitaEnum.CANCELADA
    db.commit()

    return None


@router.post("/{cita_id}/confirmar", response_model=CitaResponse)
def confirmar_cita(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Confirma una cita pendiente (solo doctores o admin)"""

    cita = db.query(Cita).filter(Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Solo doctores o admin pueden confirmar citas
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para confirmar citas",
        )

    # Verificar permisos para doctores
    if current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        if not doctor or cita.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes confirmar tus propias citas",
            )

    if cita.estado != EstadoCitaEnum.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden confirmar citas pendientes",
        )

    cita.estado = EstadoCitaEnum.CONFIRMADA
    db.commit()
    db.refresh(cita)

    return cita


@router.post("/{cita_id}/completar", response_model=CitaResponse)
def completar_cita(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marca una cita como completada (solo doctores o admin)"""

    cita = db.query(Cita).filter(Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Solo doctores o admin pueden completar citas
    if current_user.tipo_usuario == TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para completar citas",
        )

    # Verificar permisos para doctores
    if current_user.tipo_usuario == TipoUsuarioEnum.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()
        if not doctor or cita.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes completar tus propias citas",
            )

    if cita.estado == EstadoCitaEnum.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede completar una cita cancelada",
        )

    if cita.estado == EstadoCitaEnum.COMPLETADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="La cita ya está completada"
        )

    cita.estado = EstadoCitaEnum.COMPLETADA
    db.commit()
    db.refresh(cita)

    return cita
