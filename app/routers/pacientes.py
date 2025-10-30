from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

# Importaciones actualizadas
from app.models import Paciente, Usuario, TipoUsuarioEnum
from app.schemas import PacienteCreate, PacienteResponse, PacienteCompleto, PacienteBase
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/api/pacientes", tags=["Pacientes"])


@router.post("", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def crear_perfil_paciente(
    paciente: PacienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea el perfil de un paciente"""

    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == paciente.usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    # Verificar que sea tipo paciente
    if usuario.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no es de tipo paciente",
        )

    # Verificar que no tenga ya un perfil de paciente
    paciente_existente = (
        db.query(Paciente).filter(Paciente.usuario_id == paciente.usuario_id).first()
    )

    if paciente_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un perfil de paciente",
        )

    # Crear perfil de paciente
    nuevo_paciente = Paciente(**paciente.model_dump())

    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)

    return nuevo_paciente


@router.get("", response_model=List[PacienteCompleto])
def obtener_pacientes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene la lista de pacientes"""

    pacientes = db.query(Paciente).offset(skip).limit(limit).all()
    return pacientes


@router.get("/{paciente_id}", response_model=PacienteCompleto)
def obtener_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene un paciente específico con su información completa"""

    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    return paciente


@router.get("/usuario/{usuario_id}", response_model=PacienteCompleto)
def obtener_paciente_por_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el perfil de paciente asociado a un usuario"""

    paciente = db.query(Paciente).filter(Paciente.usuario_id == usuario_id).first()

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de paciente no encontrado para este usuario",
        )

    return paciente


@router.put("/{paciente_id}", response_model=PacienteResponse)
def actualizar_paciente(
    paciente_id: int,
    paciente_data: PacienteBase,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza la información de un paciente"""

    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
        )

    # Verificar que el usuario actual sea el dueño del perfil o sea admin
    if (
        paciente.usuario_id != current_user.id
        and current_user.tipo_usuario != TipoUsuarioEnum.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este paciente",
        )

    # Actualizar campos
    for campo, valor in paciente_data.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    return paciente
