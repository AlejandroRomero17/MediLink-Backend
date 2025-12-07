# app/routers/busqueda.py
"""
Router de búsqueda avanzada de doctores
Permite buscar por múltiples criterios: especialidad, ubicación, precio, calificación
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from math import radians, cos, sin, asin, sqrt

# Importaciones actualizadas
from app.models import Doctor, Usuario, Cita, EspecialidadEnum, EstadoCitaEnum
from app.schemas import DoctorCompleto
from app.core.database import get_db

router = APIRouter(prefix="/api/busqueda", tags=["Búsqueda de Doctores"])


def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos
    usando la fórmula de Haversine

    Args:
        lat1, lon1: Coordenadas del punto 1 (usuario)
        lat2, lon2: Coordenadas del punto 2 (doctor)

    Returns:
        Distancia en kilómetros
    """
    # Convertir grados a radianes
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Fórmula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    # Radio de la Tierra en kilómetros
    r = 6371

    return c * r


@router.get("/doctores", response_model=List[DoctorCompleto])
def buscar_doctores(
    # Filtros de texto
    nombre: Optional[str] = Query(None, description="Nombre del doctor"),
    especialidad: Optional[EspecialidadEnum] = Query(
        None, description="Especialidad médica"
    ),
    # Filtros de ubicación
    ciudad: Optional[str] = Query(None, description="Ciudad"),
    estado: Optional[str] = Query(None, description="Estado"),
    latitud: Optional[float] = Query(None, description="Latitud del usuario"),
    longitud: Optional[float] = Query(None, description="Longitud del usuario"),
    radio_km: Optional[float] = Query(None, description="Radio de búsqueda en km"),
    # Filtros de precio y calificación
    precio_min: Optional[float] = Query(
        None, ge=0, description="Precio mínimo de consulta"
    ),
    precio_max: Optional[float] = Query(
        None, ge=0, description="Precio máximo de consulta"
    ),
    calificacion_min: Optional[float] = Query(
        None, ge=0, le=5, description="Calificación mínima"
    ),
    # Filtros de servicios
    acepta_seguro: Optional[bool] = Query(None, description="Acepta seguro médico"),
    atiende_videollamada: Optional[bool] = Query(
        None, description="Atiende por videollamada"
    ),
    atiende_domicilio: Optional[bool] = Query(None, description="Atiende a domicilio"),
    # Ordenamiento
    ordenar_por: Optional[str] = Query(
        "calificacion",
        description="Campo para ordenar: 'calificacion', 'precio', 'distancia', 'nombre'",
    ),
    orden: Optional[str] = Query("desc", description="Orden: 'asc' o 'desc'"),
    # Paginación
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Búsqueda avanzada de doctores con múltiples filtros

    Ejemplos de uso:
    - Buscar por especialidad: ?especialidad=cardiologia
    - Buscar cerca de mí: ?latitud=20.1797&longitud=-98.0517&radio_km=10
    - Buscar por precio: ?precio_min=500&precio_max=1000
    - Buscar por calificación: ?calificacion_min=4.5
    - Combinar filtros: ?especialidad=pediatria&ciudad=Huauchinango&acepta_seguro=true
    """

    # ========== CONSTRUCCIÓN DE LA QUERY BASE ==========
    query = db.query(Doctor).join(Usuario)

    # Solo doctores activos
    query = query.filter(Usuario.activo == True)

    # ========== FILTROS DE TEXTO ==========
    if nombre:
        # Buscar en nombre o apellido
        query = query.filter(
            or_(
                Usuario.nombre.ilike(f"%{nombre}%"),
                Usuario.apellido.ilike(f"%{nombre}%"),
            )
        )

    if especialidad:
        query = query.filter(Doctor.especialidad == especialidad)

    # ========== FILTROS DE UBICACIÓN ==========
    if ciudad:
        query = query.filter(Doctor.ciudad.ilike(f"%{ciudad}%"))

    if estado:
        query = query.filter(Doctor.estado.ilike(f"%{estado}%"))

    # ========== FILTROS DE PRECIO ==========
    if precio_min is not None:
        query = query.filter(Doctor.costo_consulta >= precio_min)

    if precio_max is not None:
        query = query.filter(Doctor.costo_consulta <= precio_max)

    # ========== FILTROS DE CALIFICACIÓN ==========
    if calificacion_min is not None:
        query = query.filter(Doctor.calificacion_promedio >= calificacion_min)

    # ========== FILTROS DE SERVICIOS ==========
    if acepta_seguro is not None:
        query = query.filter(Doctor.acepta_seguro == acepta_seguro)

    if atiende_videollamada is not None:
        query = query.filter(Doctor.atiende_videollamada == atiende_videollamada)

    if atiende_domicilio is not None:
        query = query.filter(Doctor.atiende_domicilio == atiende_domicilio)

    # ========== FILTRO DE DISTANCIA ==========
    if latitud is not None and longitud is not None and radio_km is not None:
        # Solo doctores con coordenadas
        query = query.filter(
            and_(Doctor.latitud.isnot(None), Doctor.longitud.isnot(None))
        )

    # ========== ORDENAMIENTO ==========
    if ordenar_por == "calificacion":
        if orden == "desc":
            query = query.order_by(Doctor.calificacion_promedio.desc())
        else:
            query = query.order_by(Doctor.calificacion_promedio.asc())

    elif ordenar_por == "precio":
        if orden == "desc":
            query = query.order_by(Doctor.costo_consulta.desc())
        else:
            query = query.order_by(Doctor.costo_consulta.asc())

    elif ordenar_por == "nombre":
        if orden == "desc":
            query = query.order_by(Usuario.nombre.desc())
        else:
            query = query.order_by(Usuario.nombre.asc())

    # ========== EJECUTAR QUERY ==========
    doctores = query.offset(skip).limit(limit).all()

    # ========== CALCULAR DISTANCIAS (si se proporcionó ubicación) ==========
    if latitud is not None and longitud is not None:
        doctores_con_distancia = []

        for doctor in doctores:
            if doctor.latitud and doctor.longitud:
                distancia = calcular_distancia(
                    latitud, longitud, doctor.latitud, doctor.longitud
                )

                # Filtrar por radio si se especificó
                if radio_km is None or distancia <= radio_km:
                    doctores_con_distancia.append((doctor, distancia))

        # Ordenar por distancia si se solicitó
        if ordenar_por == "distancia":
            doctores_con_distancia.sort(key=lambda x: x[1], reverse=(orden == "desc"))

        # Extraer solo los doctores (sin la distancia)
        doctores = [d[0] for d in doctores_con_distancia]

    return doctores


@router.get("/doctores/cercanos", response_model=List[dict])
def buscar_doctores_cercanos(
    latitud: float = Query(..., description="Latitud del usuario"),
    longitud: float = Query(..., description="Longitud del usuario"),
    radio_km: float = Query(10, ge=0.1, le=100, description="Radio de búsqueda en km"),
    especialidad: Optional[EspecialidadEnum] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Busca doctores cercanos a una ubicación específica
    Devuelve la lista ordenada por distancia con información de la distancia

    Ejemplo: ?latitud=20.1797&longitud=-98.0517&radio_km=5
    """

    # Query base
    query = (
        db.query(Doctor)
        .join(Usuario)
        .filter(
            Usuario.activo == True,
            Doctor.latitud.isnot(None),
            Doctor.longitud.isnot(None),
        )
    )

    # Filtrar por especialidad si se proporciona
    if especialidad:
        query = query.filter(Doctor.especialidad == especialidad)

    doctores = query.all()

    # Calcular distancias y filtrar por radio
    doctores_con_distancia = []

    for doctor in doctores:
        distancia = calcular_distancia(
            latitud, longitud, doctor.latitud, doctor.longitud
        )

        if distancia <= radio_km:
            doctores_con_distancia.append(
                {
                    "doctor": doctor,
                    "distancia_km": round(distancia, 2),
                    "tiempo_estimado_minutos": round(distancia * 3),  # ~3 min por km
                }
            )

    # Ordenar por distancia
    doctores_con_distancia.sort(key=lambda x: x["distancia_km"])

    # Limitar resultados
    doctores_con_distancia = doctores_con_distancia[:limit]

    # Formatear respuesta
    resultados = []
    for item in doctores_con_distancia:
        doctor = item["doctor"]
        resultados.append(
            {
                "id": doctor.id,
                "nombre_completo": f"{doctor.usuario.nombre} {doctor.usuario.apellido}",
                "especialidad": doctor.especialidad.value,
                "consultorio": doctor.consultorio,
                "direccion": doctor.direccion_consultorio,
                "ciudad": doctor.ciudad,
                "telefono": doctor.usuario.telefono,
                "costo_consulta": doctor.costo_consulta,
                "calificacion_promedio": doctor.calificacion_promedio,
                "total_valoraciones": doctor.total_valoraciones,
                "acepta_seguro": doctor.acepta_seguro,
                "atiende_videollamada": doctor.atiende_videollamada,
                "distancia_km": item["distancia_km"],
                "tiempo_estimado_minutos": item["tiempo_estimado_minutos"],
            }
        )

    return resultados


@router.get("/especialidades/populares")
def obtener_especialidades_populares(
    limit: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)
):
    """
    Obtiene las especialidades más populares (con más doctores)
    Útil para mostrar en la página principal
    """

    resultados = (
        db.query(
            Doctor.especialidad,
            func.count(Doctor.id).label("cantidad_doctores"),
        )
        .group_by(Doctor.especialidad)
        .order_by(func.count(Doctor.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "especialidad": r.especialidad.value,
            "nombre_display": r.especialidad.value.replace("_", " ").title(),
            "cantidad_doctores": r.cantidad_doctores,
        }
        for r in resultados
    ]


@router.get("/doctores/mejor-valorados", response_model=List[DoctorCompleto])
def obtener_doctores_mejor_valorados(
    especialidad: Optional[EspecialidadEnum] = Query(None),
    calificacion_min: float = Query(4.0, ge=0, le=5),
    valoraciones_min: int = Query(
        5, ge=1, description="Mínimo de valoraciones requeridas"
    ),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Obtiene los doctores mejor valorados
    Requiere un mínimo de valoraciones para evitar sesgos

    Ejemplo: ?calificacion_min=4.5&valoraciones_min=10
    """

    query = (
        db.query(Doctor)
        .join(Usuario)
        .filter(
            Usuario.activo == True,
            Doctor.calificacion_promedio >= calificacion_min,
            Doctor.total_valoraciones >= valoraciones_min,
        )
    )

    if especialidad:
        query = query.filter(Doctor.especialidad == especialidad)

    doctores = (
        query.order_by(
            Doctor.calificacion_promedio.desc(),
            Doctor.total_valoraciones.desc(),
        )
        .limit(limit)
        .all()
    )

    return doctores


@router.get("/doctores/disponibles-hoy")
def obtener_doctores_disponibles_hoy(
    especialidad: Optional[EspecialidadEnum] = Query(None),
    hora_minima: Optional[str] = Query(
        None, description="Hora mínima en formato HH:MM"
    ),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Obtiene doctores que tienen disponibilidad HOY
    Verifica que tengan al menos un horario libre

    Ejemplo: ?especialidad=medicina_general&hora_minima=15:00
    """
    from datetime import datetime, time

    # Query base
    query = db.query(Doctor).join(Usuario).filter(Usuario.activo == True)

    if especialidad:
        query = query.filter(Doctor.especialidad == especialidad)

    doctores = query.limit(limit * 2).all()  # Traemos más para filtrar

    # Obtener la fecha y hora actual
    ahora = datetime.now()
    hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=59)

    # Hora mínima de búsqueda
    if hora_minima:
        try:
            h, m = map(int, hora_minima.split(":"))
            hora_minima_dt = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
        except:
            hora_minima_dt = ahora
    else:
        hora_minima_dt = ahora

    doctores_disponibles = []

    for doctor in doctores:
        # Contar citas del doctor hoy después de hora_minima
        citas_hoy = (
            db.query(Cita)
            .filter(
                Cita.doctor_id == doctor.id,
                Cita.fecha_hora >= hora_minima_dt,
                Cita.fecha_hora <= hoy_fin,
                Cita.estado.in_([EstadoCitaEnum.PENDIENTE, EstadoCitaEnum.CONFIRMADA]),
            )
            .count()
        )

        # Asumimos horario de 8 AM a 6 PM con citas de 30 min = 20 slots
        slots_totales = 20

        # Si tiene menos de 20 citas, tiene disponibilidad
        if citas_hoy < slots_totales:
            doctores_disponibles.append(
                {
                    "id": doctor.id,
                    "nombre_completo": f"{doctor.usuario.nombre} {doctor.usuario.apellido}",
                    "especialidad": doctor.especialidad.value,
                    "consultorio": doctor.consultorio,
                    "telefono": doctor.usuario.telefono,
                    "costo_consulta": doctor.costo_consulta,
                    "calificacion_promedio": doctor.calificacion_promedio,
                    "slots_disponibles": slots_totales - citas_hoy,
                    "atiende_videollamada": doctor.atiende_videollamada,
                }
            )

        if len(doctores_disponibles) >= limit:
            break

    return doctores_disponibles
