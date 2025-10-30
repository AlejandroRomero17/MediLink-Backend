from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

# Importaciones actualizadas
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioLogin, UsuarioResponse, UsuarioBase, Token
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


@router.post(
    "/registro",
    response_model=Token,  # Ahora devuelve Token en lugar de UsuarioResponse
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema y devuelve un token JWT
    """
    # Verificar si el email ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # Crear nuevo usuario con contraseña encriptada
    nuevo_usuario = Usuario(
        email=usuario.email,
        password_hash=hash_password(usuario.password),
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        telefono=usuario.telefono,
        tipo_usuario=usuario.tipo_usuario,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Crear token JWT para el nuevo usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": nuevo_usuario.id,
            "email": nuevo_usuario.email,
            "tipo_usuario": nuevo_usuario.tipo_usuario.value,
        },
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": nuevo_usuario,  # Incluimos los datos del usuario
    }


@router.post("/login", response_model=Token)
def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión y devuelve un token JWT
    """
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == credenciales.email).first()

    if not usuario or not verify_password(credenciales.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": usuario.id,
            "email": usuario.email,
            "tipo_usuario": usuario.tipo_usuario.value,
        },
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario,  # Incluimos los datos del usuario
    }


@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene la información del usuario autenticado actual
    """
    return current_user


@router.get("", response_model=List[UsuarioResponse])
def obtener_usuarios(
    skip: int = 0,
    limit: int = 100,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # Requiere autenticación
):
    """
    Obtiene la lista de usuarios registrados (requiere autenticación)
    """
    query = db.query(Usuario)

    # Filtrar por tipo de usuario si se proporciona
    if tipo:
        query = query.filter(Usuario.tipo_usuario == tipo)

    usuarios = query.offset(skip).limit(limit).all()
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # Requiere autenticación
):
    """
    Obtiene un usuario específico por ID (requiere autenticación)
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioBase,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Actualiza la información de un usuario
    Solo el propio usuario puede actualizar su información
    """
    # Verificar que el usuario solo pueda actualizar su propia información
    if current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    # Actualizar campos
    for campo, valor in usuario_update.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)

    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Desactiva un usuario (soft delete)
    Solo el propio usuario puede desactivar su cuenta
    """
    # Verificar que el usuario solo pueda desactivar su propia cuenta
    if current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para desactivar este usuario",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    usuario.activo = False
    db.commit()

    return None
