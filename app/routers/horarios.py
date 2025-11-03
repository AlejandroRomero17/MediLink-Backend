"""
Router para gestionar horarios de doctores
Permite crear, obtener, actualizar y eliminar horarios
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import HorarioDoctor, Doctor
from app.schemas import (
    HorarioDoctorBase,
    HorarioDoctorCreate,
    HorarioDoctorResponse,
)
from app.core.database import get_db

router = APIRouter(prefix="/api/horarios", tags=["Horarios Doctor"])


@router.post(
    "", response_model=HorarioDoctorResponse, status_code=status.HTTP_201_CREATED
)
def crear_horario(horario: HorarioDoctorCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo horario de atención para un doctor

    Valida:
    - Que el doctor exista
    - Que hora_inicio < hora_fin
    - Que no exista el mismo horario (unicidad)
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == horario.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Validar horario
    if horario.hora_inicio >= horario.hora_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora de inicio debe ser menor a la hora de fin",
        )

    # Verificar que no exista un horario duplicado
    horario_existente = (
        db.query(HorarioDoctor)
        .filter(
            HorarioDoctor.doctor_id == horario.doctor_id,
            HorarioDoctor.dia_semana == horario.dia_semana,
            HorarioDoctor.hora_inicio == horario.hora_inicio,
        )
        .first()
    )

    if horario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un horario con estos datos",
        )

    # Crear horario
    nuevo_horario = HorarioDoctor(**horario.model_dump())
    db.add(nuevo_horario)
    db.commit()
    db.refresh(nuevo_horario)

    return nuevo_horario


@router.get("/doctor/{doctor_id}", response_model=List[HorarioDoctorResponse])
def obtener_horarios_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los horarios de un doctor específico
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    horarios = (
        db.query(HorarioDoctor)
        .filter(HorarioDoctor.doctor_id == doctor_id)
        .order_by(HorarioDoctor.dia_semana, HorarioDoctor.hora_inicio)
        .all()
    )

    return horarios


@router.get("/{horario_id}", response_model=HorarioDoctorResponse)
def obtener_horario(horario_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un horario específico por su ID
    """

    horario = db.query(HorarioDoctor).filter(HorarioDoctor.id == horario_id).first()

    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado"
        )

    return horario


@router.put("/{horario_id}", response_model=HorarioDoctorResponse)
def actualizar_horario(
    horario_id: int, horario_data: HorarioDoctorBase, db: Session = Depends(get_db)
):
    """
    Actualiza un horario existente
    """

    horario = db.query(HorarioDoctor).filter(HorarioDoctor.id == horario_id).first()

    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado"
        )

    # Validar nuevo horario si se actualiza
    if horario_data.hora_inicio >= horario_data.hora_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora de inicio debe ser menor a la hora de fin",
        )

    # Actualizar campos
    for campo, valor in horario_data.model_dump().items():
        setattr(horario, campo, valor)

    db.commit()
    db.refresh(horario)

    return horario


@router.delete("/{horario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_horario(horario_id: int, db: Session = Depends(get_db)):
    """
    Elimina un horario de atención
    """

    horario = db.query(HorarioDoctor).filter(HorarioDoctor.id == horario_id).first()

    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado"
        )

    db.delete(horario)
    db.commit()

    return None


@router.patch("/{horario_id}/toggle", response_model=HorarioDoctorResponse)
def toggle_horario(horario_id: int, db: Session = Depends(get_db)):
    """
    Activa o desactiva un horario (toggle del campo activo)
    """

    horario = db.query(HorarioDoctor).filter(HorarioDoctor.id == horario_id).first()

    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado"
        )

    horario.activo = not horario.activo
    db.commit()
    db.refresh(horario)

    return horario


@router.post("/doctor/{doctor_id}/bulk", response_model=List[HorarioDoctorResponse])
def crear_horarios_bulk(
    doctor_id: int, horarios: List[HorarioDoctorBase], db: Session = Depends(get_db)
):
    """
    Crea múltiples horarios para un doctor en una sola operación
    Útil para configuración inicial o actualización masiva
    """

    # Verificar que el doctor existe
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    if not horarios or len(horarios) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un horario",
        )

    # Validar todos los horarios
    for horario in horarios:
        if horario.hora_inicio >= horario.hora_fin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Horario inválido para {horario.dia_semana}",
            )

    try:
        # Crear todos los horarios
        nuevos_horarios = []
        for horario_data in horarios:
            nuevo_horario = HorarioDoctor(
                doctor_id=doctor_id, **horario_data.model_dump()
            )
            db.add(nuevo_horario)
            nuevos_horarios.append(nuevo_horario)

        db.commit()

        # Refrescar todos
        for horario in nuevos_horarios:
            db.refresh(horario)

        return nuevos_horarios

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear horarios: {str(e)}",
        )
