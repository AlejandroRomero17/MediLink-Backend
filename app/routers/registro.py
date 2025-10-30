"""
Router de registro combinado
Permite crear usuario + perfil (doctor/paciente) en una sola petición
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

# Importaciones actualizadas
from app.models import Usuario, Paciente, Doctor, TipoUsuarioEnum
from app.schemas import (
    PacienteRegistroCompleto,
    DoctorRegistroCompleto,
    UsuarioCreate,
    Token,
)
from app.core.database import get_db
from app.core.security import (
    hash_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/registro", tags=["Registro Combinado"])


@router.post("/paciente", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar_paciente_completo(
    datos: PacienteRegistroCompleto, db: Session = Depends(get_db)
):
    """
    Registra un nuevo paciente con su usuario en una sola petición

    Pasos:
    1. Valida que el email no exista
    2. Crea el usuario con tipo PACIENTE
    3. Crea el perfil de paciente vinculado al usuario
    4. Genera y devuelve un token JWT

    Args:
        datos: Contiene información del usuario y del paciente
        db: Sesión de base de datos

    Returns:
        Token JWT con información del usuario

    Raises:
        HTTPException 400: Si el email ya está registrado
        HTTPException 500: Si hay error en la creación
    """

    # ========== PASO 1: Validar email único ==========
    usuario_existente = (
        db.query(Usuario).filter(Usuario.email == datos.usuario.email).first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    try:
        # ========== PASO 2: Crear usuario ==========
        nuevo_usuario = Usuario(
            email=datos.usuario.email,
            password_hash=hash_password(datos.usuario.password),
            nombre=datos.usuario.nombre,
            apellido=datos.usuario.apellido,
            telefono=datos.usuario.telefono,
            tipo_usuario=TipoUsuarioEnum.PACIENTE,  # Forzamos tipo PACIENTE
        )

        db.add(nuevo_usuario)
        db.flush()  # Obtiene el ID sin hacer commit aún

        # ========== PASO 3: Crear perfil de paciente ==========
        nuevo_paciente = Paciente(
            usuario_id=nuevo_usuario.id,
            fecha_nacimiento=datos.paciente.fecha_nacimiento,
            genero=datos.paciente.genero,
            direccion=datos.paciente.direccion,
            ciudad=datos.paciente.ciudad,
            estado=datos.paciente.estado,
            codigo_postal=datos.paciente.codigo_postal,
            numero_seguro=datos.paciente.numero_seguro,
            alergias=datos.paciente.alergias,
            tipo_sangre=datos.paciente.tipo_sangre,
            contacto_emergencia_nombre=datos.paciente.contacto_emergencia_nombre,
            contacto_emergencia_telefono=datos.paciente.contacto_emergencia_telefono,
        )

        db.add(nuevo_paciente)
        db.commit()  # Commit de ambas inserciones
        db.refresh(nuevo_usuario)
        db.refresh(nuevo_paciente)

        # ========== PASO 4: Generar token JWT ==========
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": nuevo_usuario.id,
                "email": nuevo_usuario.email,
                "tipo_usuario": nuevo_usuario.tipo_usuario.value,
            },
            expires_delta=access_token_expires,
        )

        # ========== PASO 5: Devolver token + info del usuario ==========
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario": nuevo_usuario,
        }

    except Exception as e:
        db.rollback()  # Si algo falla, revertir todo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el paciente: {str(e)}",
        )


@router.post("/doctor", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar_doctor_completo(
    datos: DoctorRegistroCompleto, db: Session = Depends(get_db)
):
    """
    Registra un nuevo doctor con su usuario en una sola petición

    Similar a registrar_paciente_completo pero para doctores
    Incluye validación adicional de cédula profesional única

    Args:
        datos: Contiene información del usuario y del doctor
        db: Sesión de base de datos

    Returns:
        Token JWT con información del usuario

    Raises:
        HTTPException 400: Si el email o cédula ya existen
        HTTPException 500: Si hay error en la creación
    """

    # ========== PASO 1: Validar email único ==========
    usuario_existente = (
        db.query(Usuario).filter(Usuario.email == datos.usuario.email).first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # ========== PASO 1.5: Validar cédula profesional única ==========
    cedula_existente = (
        db.query(Doctor)
        .filter(Doctor.cedula_profesional == datos.doctor.cedula_profesional)
        .first()
    )

    if cedula_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula profesional ya está registrada",
        )

    try:
        # ========== PASO 2: Crear usuario ==========
        nuevo_usuario = Usuario(
            email=datos.usuario.email,
            password_hash=hash_password(datos.usuario.password),
            nombre=datos.usuario.nombre,
            apellido=datos.usuario.apellido,
            telefono=datos.usuario.telefono,
            tipo_usuario=TipoUsuarioEnum.DOCTOR,  # Forzamos tipo DOCTOR
        )

        db.add(nuevo_usuario)
        db.flush()  # Obtiene el ID sin hacer commit

        # ========== PASO 3: Crear perfil de doctor ==========
        nuevo_doctor = Doctor(
            usuario_id=nuevo_usuario.id,
            especialidad=datos.doctor.especialidad,
            cedula_profesional=datos.doctor.cedula_profesional,
            consultorio=datos.doctor.consultorio,
            direccion_consultorio=datos.doctor.direccion_consultorio,
            ciudad=datos.doctor.ciudad,
            estado=datos.doctor.estado,
            codigo_postal=datos.doctor.codigo_postal,
            latitud=datos.doctor.latitud,
            longitud=datos.doctor.longitud,
            horario_atencion=datos.doctor.horario_atencion,
            costo_consulta=datos.doctor.costo_consulta,
            duracion_cita_minutos=datos.doctor.duracion_cita_minutos,
            anos_experiencia=datos.doctor.anos_experiencia,
            universidad=datos.doctor.universidad,
            biografia=datos.doctor.biografia,
            foto_url=datos.doctor.foto_url,
            acepta_seguro=datos.doctor.acepta_seguro,
            atiende_domicilio=datos.doctor.atiende_domicilio,
            atiende_videollamada=datos.doctor.atiende_videollamada,
        )

        db.add(nuevo_doctor)
        db.commit()  # Commit de ambas inserciones
        db.refresh(nuevo_usuario)
        db.refresh(nuevo_doctor)

        # ========== PASO 4: Generar token JWT ==========
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": nuevo_usuario.id,
                "email": nuevo_usuario.email,
                "tipo_usuario": nuevo_usuario.tipo_usuario.value,
            },
            expires_delta=access_token_expires,
        )

        # ========== PASO 5: Devolver token + info del usuario ==========
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario": nuevo_usuario,
        }

    except Exception as e:
        db.rollback()  # Si algo falla, revertir todo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el doctor: {str(e)}",
        )


@router.post("/admin", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar_admin(
    usuario: UsuarioCreate,
    admin_secret: str,  # Clave secreta para crear admins
    db: Session = Depends(get_db),
):
    """
    Registra un nuevo administrador (requiere clave secreta)

    IMPORTANTE: Solo debe usarse con una clave secreta
    En producción, esta clave debe estar en variables de entorno

    Args:
        usuario: Información del usuario admin
        admin_secret: Clave secreta para autorizar creación de admin
        db: Sesión de base de datos

    Returns:
        Token JWT con información del usuario admin

    Raises:
        HTTPException 403: Si la clave secreta es incorrecta
        HTTPException 400: Si el email ya existe
    """

    # ========== Validar clave secreta ==========
    # En producción, esto debe venir de una variable de entorno
    SECRET_ADMIN_KEY = "MEDILINK_ADMIN_2024"  # Cambiar en producción

    if admin_secret != SECRET_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Clave secreta incorrecta"
        )

    # ========== Validar email único ==========
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    try:
        # ========== Crear usuario admin ==========
        nuevo_admin = Usuario(
            email=usuario.email,
            password_hash=hash_password(usuario.password),
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            telefono=usuario.telefono,
            tipo_usuario=TipoUsuarioEnum.ADMIN,  # Forzamos tipo ADMIN
        )

        db.add(nuevo_admin)
        db.commit()
        db.refresh(nuevo_admin)

        # ========== Generar token JWT ==========
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": nuevo_admin.id,
                "email": nuevo_admin.email,
                "tipo_usuario": nuevo_admin.tipo_usuario.value,
            },
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario": nuevo_admin,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el administrador: {str(e)}",
        )
