# routers/citas.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/citas", tags=["Citas"])


@router.post(
    "", response_model=schemas.CitaResponse, status_code=status.HTTP_201_CREATED
)
def crear_cita(cita: schemas.CitaCreate, db: Session = Depends(get_db)):
    """Crea una nueva cita médica"""

    # Verificar que el paciente existe
    paciente = (
        db.query(models.Paciente).filter(models.Paciente.id == cita.paciente_id).first()
    )
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    # Verificar que el doctor existe
    doctor = db.query(models.Doctor).filter(models.Doctor.id == cita.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Verificar que la fecha sea futura
    if cita.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de la cita debe ser futura",
        )

    # Verificar disponibilidad del doctor (no debe tener otra cita a la misma hora)
    cita_existente = (
        db.query(models.Cita)
        .filter(
            models.Cita.doctor_id == cita.doctor_id,
            models.Cita.fecha_hora == cita.fecha_hora,
            models.Cita.estado.in_(
                [models.EstadoCitaEnum.PENDIENTE, models.EstadoCitaEnum.CONFIRMADA]
            ),
        )
        .first()
    )

    if cita_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El doctor ya tiene una cita agendada en ese horario",
        )

    # Crear nueva cita
    nueva_cita = models.Cita(**cita.model_dump())

    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    return nueva_cita


@router.get("", response_model=List[schemas.CitaResponse])
def obtener_citas(
    skip: int = 0, limit: int = 100, estado: str = None, db: Session = Depends(get_db)
):
    """Obtiene todas las citas, opcionalmente filtradas por estado"""

    query = db.query(models.Cita)

    if estado:
        query = query.filter(models.Cita.estado == estado)

    citas = query.offset(skip).limit(limit).all()
    return citas


@router.get("/{cita_id}", response_model=schemas.CitaCompleta)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    """Obtiene una cita específica con información completa"""

    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    return cita


@router.get("/paciente/{paciente_id}", response_model=List[schemas.CitaResponse])
def obtener_citas_paciente(
    paciente_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Obtiene todas las citas de un paciente específico"""

    # Verificar que el paciente existe
    paciente = (
        db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    )
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    citas = (
        db.query(models.Cita)
        .filter(models.Cita.paciente_id == paciente_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return citas


@router.get("/doctor/{doctor_id}", response_model=List[schemas.CitaResponse])
def obtener_citas_doctor(
    doctor_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Obtiene todas las citas de un doctor específico"""

    # Verificar que el doctor existe
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    citas = (
        db.query(models.Cita)
        .filter(models.Cita.doctor_id == doctor_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return citas


@router.patch("/{cita_id}", response_model=schemas.CitaResponse)
def actualizar_cita(
    cita_id: int, cita_update: schemas.CitaUpdate, db: Session = Depends(get_db)
):
    """Actualiza información de una cita existente"""

    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Actualizar solo los campos proporcionados
    update_data = cita_update.model_dump(exclude_unset=True)

    # Si se actualiza la fecha, verificar disponibilidad
    if "fecha_hora" in update_data and update_data["fecha_hora"]:
        if update_data["fecha_hora"] <= datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de la cita debe ser futura",
            )

        # Verificar que no haya conflicto con otra cita del doctor
        cita_conflicto = (
            db.query(models.Cita)
            .filter(
                models.Cita.doctor_id == cita.doctor_id,
                models.Cita.fecha_hora == update_data["fecha_hora"],
                models.Cita.id != cita_id,
                models.Cita.estado.in_(
                    [models.EstadoCitaEnum.PENDIENTE, models.EstadoCitaEnum.CONFIRMADA]
                ),
            )
            .first()
        )

        if cita_conflicto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El doctor ya tiene una cita agendada en ese horario",
            )

    # Aplicar actualizaciones
    for campo, valor in update_data.items():
        setattr(cita, campo, valor)

    db.commit()
    db.refresh(cita)

    return cita


@router.delete("/{cita_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    """Cancela una cita (cambia su estado a cancelada)"""

    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    # Cambiar estado a cancelada en lugar de eliminar
    cita.estado = models.EstadoCitaEnum.CANCELADA
    db.commit()

    return None


@router.post("/{cita_id}/confirmar", response_model=schemas.CitaResponse)
def confirmar_cita(cita_id: int, db: Session = Depends(get_db)):
    """Confirma una cita pendiente"""

    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    if cita.estado != models.EstadoCitaEnum.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden confirmar citas pendientes",
        )

    cita.estado = models.EstadoCitaEnum.CONFIRMADA
    db.commit()
    db.refresh(cita)

    return cita


@router.post("/{cita_id}/completar", response_model=schemas.CitaResponse)
def completar_cita(cita_id: int, db: Session = Depends(get_db)):
    """Marca una cita como completada"""

    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()

    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    if cita.estado == models.EstadoCitaEnum.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede completar una cita cancelada",
        )

    cita.estado = models.EstadoCitaEnum.COMPLETADA
    db.commit()
    db.refresh(cita)

    return cita
