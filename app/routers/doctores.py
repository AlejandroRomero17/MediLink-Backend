# app/routers/doctores.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importaciones actualizadas
from app.models import Doctor, Usuario, HorarioDoctor, TipoUsuarioEnum, EspecialidadEnum
from app.schemas import DoctorCreate, DoctorResponse, DoctorCompleto, DoctorBase
from app.core.database import get_db

router = APIRouter(prefix="/api/doctores", tags=["Doctores"])


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def crear_perfil_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    """Crea el perfil profesional de un doctor"""

    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == doctor.usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    # Verificar que sea tipo doctor
    if usuario.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no es de tipo doctor",
        )

    # Verificar que no tenga ya un perfil de doctor
    doctor_existente = (
        db.query(Doctor).filter(Doctor.usuario_id == doctor.usuario_id).first()
    )

    if doctor_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un perfil de doctor",
        )

    # Verificar que la cédula sea única
    cedula_existente = (
        db.query(Doctor)
        .filter(Doctor.cedula_profesional == doctor.cedula_profesional)
        .first()
    )

    if cedula_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula profesional ya está registrada",
        )

    # Crear perfil de doctor
    nuevo_doctor = Doctor(**doctor.model_dump())

    db.add(nuevo_doctor)
    db.commit()
    db.refresh(nuevo_doctor)

    return nuevo_doctor


@router.get("", response_model=List[DoctorCompleto])
def obtener_doctores(
    skip: int = 0,
    limit: int = 100,
    especialidad: str = None,
    db: Session = Depends(get_db),
):
    """Obtiene la lista de doctores, opcionalmente filtrados por especialidad"""

    query = db.query(Doctor)

    # Filtrar por especialidad si se proporciona
    if especialidad:
        query = query.filter(Doctor.especialidad == especialidad)

    doctores = query.offset(skip).limit(limit).all()
    return doctores


@router.get("/{doctor_id}", response_model=DoctorCompleto)
def obtener_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un doctor específico con su información completa
    Incluye ahora sus horarios de atención
    """

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    return doctor


@router.get("/usuario/{usuario_id}", response_model=DoctorCompleto)
def obtener_doctor_por_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el perfil de doctor asociado a un usuario
    Incluye sus horarios de atención
    """

    doctor = db.query(Doctor).filter(Doctor.usuario_id == usuario_id).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de doctor no encontrado para este usuario",
        )

    return doctor


@router.get("/especialidad/{especialidad}", response_model=List[DoctorCompleto])
def obtener_doctores_por_especialidad(
    especialidad: EspecialidadEnum, db: Session = Depends(get_db)
):
    """Obtiene todos los doctores de una especialidad específica"""

    doctores = db.query(Doctor).filter(Doctor.especialidad == especialidad).all()

    return doctores


@router.put("/{doctor_id}", response_model=DoctorResponse)
def actualizar_doctor(
    doctor_id: int, doctor_data: DoctorBase, db: Session = Depends(get_db)
):
    """Actualiza la información de un doctor"""

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado"
        )

    # Si se actualiza la cédula, verificar que sea única
    if (
        doctor_data.cedula_profesional
        and doctor_data.cedula_profesional != doctor.cedula_profesional
    ):
        cedula_existente = (
            db.query(Doctor)
            .filter(Doctor.cedula_profesional == doctor_data.cedula_profesional)
            .first()
        )

        if cedula_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cédula profesional ya está registrada",
            )

    # Actualizar campos
    for campo, valor in doctor_data.model_dump(exclude_unset=True).items():
        setattr(doctor, campo, valor)

    db.commit()
    db.refresh(doctor)

    return doctor
