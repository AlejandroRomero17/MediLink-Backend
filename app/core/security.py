from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.models import Usuario, Doctor, Paciente, TipoUsuarioEnum
from app.core.database import get_db
from app.core.config import settings

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/usuarios/login")

# Constante para el tiempo de expiración del token
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """
    Encripta la contraseña usando bcrypt

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash de la contraseña
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña coincide con el hash

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña

    Returns:
        True si coinciden, False si no
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT con los datos proporcionados

    Args:
        data: Diccionario con los datos a incluir en el token
        expires_delta: Tiempo de expiración del token

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT

    Args:
        token: Token JWT a decodificar

    Returns:
        Diccionario con los datos del token

    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Usuario:
    """
    Obtiene el usuario actual desde el token JWT

    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

    if usuario is None:
        raise credentials_exception

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    return usuario


def get_current_active_doctor(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Doctor:
    """
    Obtiene el perfil de doctor del usuario actual

    Args:
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Perfil de doctor

    Raises:
        HTTPException: Si el usuario no es doctor o no tiene perfil
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no es un doctor"
        )

    doctor = db.query(Doctor).filter(Doctor.usuario_id == current_user.id).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de doctor no encontrado",
        )

    return doctor


def get_current_active_patient(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paciente:
    """
    Obtiene el perfil de paciente del usuario actual

    Args:
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Perfil de paciente

    Raises:
        HTTPException: Si el usuario no es paciente o no tiene perfil
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.PACIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no es un paciente"
        )

    paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de paciente no encontrado",
        )

    return paciente


def get_current_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Verifica que el usuario actual sea administrador

    Args:
        current_user: Usuario autenticado

    Returns:
        Usuario administrador

    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.tipo_usuario != TipoUsuarioEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder a este recurso",
        )

    return current_user
