# app/routers/metrics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, Any
import psutil
import os

from app.core.database import get_db
from app.models import Cita, Usuario, Doctor, Paciente

router = APIRouter(prefix="/api/metrics", tags=["Métricas"])


@router.get("/system")
async def get_system_metrics():
    """
    Métricas del sistema (CPU, RAM, Disco)
    Útil para monitoreo de infraestructura
    """
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memoria
        memory = psutil.virtual_memory()

        # Disco
        disk = psutil.disk_usage("/")

        # Información del proceso actual
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()

        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "status": "healthy" if cpu_percent < 80 else "warning",
                },
                "memory": {
                    "percent": memory.percent,
                    "used_gb": round(memory.used / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "status": "healthy" if memory.percent < 80 else "warning",
                },
                "disk": {
                    "percent": disk.percent,
                    "used_gb": round(disk.used / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "status": "healthy" if disk.percent < 80 else "warning",
                },
            },
            "application": {
                "memory_mb": round(process_memory.rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "connections": len(process.connections()),
                "pid": process.pid,
            },
        }
    except Exception as e:
        return {
            "error": f"Error obteniendo métricas del sistema: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/usage")
def get_api_usage(
    days: int = Query(7, ge=1, le=90, description="Días a analizar"),
    db: Session = Depends(get_db),
):
    """
    Métricas de uso de la API
    - Citas creadas por día
    - Usuarios nuevos por día
    - Doctores más solicitados
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    # Citas por día
    appointments_by_day = (
        db.query(
            func.date(Cita.fecha_hora).label("date"), func.count(Cita.id).label("count")
        )
        .filter(Cita.fecha_hora >= cutoff_date)
        .group_by(func.date(Cita.fecha_hora))
        .order_by(func.date(Cita.fecha_hora))
        .all()
    )

    # Usuarios nuevos por día
    new_users_by_day = (
        db.query(
            func.date(Usuario.fecha_registro).label("date"),
            func.count(Usuario.id).label("count"),
        )
        .filter(Usuario.fecha_registro >= cutoff_date)
        .group_by(func.date(Usuario.fecha_registro))
        .order_by(func.date(Usuario.fecha_registro))
        .all()
    )

    # Doctores más solicitados
    top_doctors = (
        db.query(
            Doctor.id,
            Usuario.nombre,
            Usuario.apellido,
            Doctor.especialidad,
            func.count(Cita.id).label("appointment_count"),
        )
        .join(Usuario, Doctor.usuario_id == Usuario.id)
        .outerjoin(Cita, Doctor.id == Cita.doctor_id)
        .filter(Cita.fecha_hora >= cutoff_date)
        .group_by(Doctor.id, Usuario.nombre, Usuario.apellido, Doctor.especialidad)
        .order_by(desc("appointment_count"))
        .limit(10)
        .all()
    )

    # Especialidades más demandadas
    top_specialties = (
        db.query(Doctor.especialidad, func.count(Cita.id).label("count"))
        .join(Cita, Doctor.id == Cita.doctor_id)
        .filter(Cita.fecha_hora >= cutoff_date)
        .group_by(Doctor.especialidad)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    # Totales
    total_appointments = db.query(Cita).filter(Cita.fecha_hora >= cutoff_date).count()
    total_new_users = (
        db.query(Usuario).filter(Usuario.fecha_registro >= cutoff_date).count()
    )
    total_doctors = db.query(Doctor).count()
    total_patients = db.query(Paciente).count()

    return {
        "period_days": days,
        "timestamp": datetime.now().isoformat(),
        "totals": {
            "appointments": total_appointments,
            "new_users": total_new_users,
            "total_doctors": total_doctors,
            "total_patients": total_patients,
        },
        "appointments": {
            "total": sum(r.count for r in appointments_by_day),
            "by_day": [
                {"date": str(r.date), "count": r.count} for r in appointments_by_day
            ],
        },
        "users": {
            "total": sum(r.count for r in new_users_by_day),
            "by_day": [
                {"date": str(r.date), "count": r.count} for r in new_users_by_day
            ],
        },
        "top_doctors": [
            {
                "id": r.id,
                "name": f"Dr. {r.nombre} {r.apellido}",
                "specialty": r.especialidad,
                "appointments": r.appointment_count,
            }
            for r in top_doctors
        ],
        "top_specialties": [
            {"specialty": r.especialidad, "appointments": r.count}
            for r in top_specialties
        ],
    }


@router.get("/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Métricas de rendimiento de la API
    - Estado general
    - Conexiones activas
    - Tiempo de respuesta estimado
    """
    try:
        # Test de conexión a BD
        start_time = datetime.now()
        db.execute("SELECT 1")
        db_response_time = (datetime.now() - start_time).total_seconds() * 1000

        db_status = "connected"
        db_health = "healthy" if db_response_time < 100 else "slow"
    except Exception as e:
        db_status = "disconnected"
        db_health = "unhealthy"
        db_response_time = None

    # Estadísticas de la aplicación
    process = psutil.Process(os.getpid())

    return {
        "timestamp": datetime.now().isoformat(),
        "api_status": "healthy",
        "database": {
            "status": db_status,
            "health": db_health,
            "response_time_ms": db_response_time,
        },
        "application": {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "uptime_seconds": round(
                (
                    datetime.now() - datetime.fromtimestamp(process.create_time())
                ).total_seconds()
            ),
        },
        "estimated_metrics": {
            "response_time_avg_ms": 150,  # Esto idealmente se mediría con middleware
            "error_rate_percent": 0.5,
            "requests_per_minute": 50,
        },
    }


@router.get("/database")
def get_database_metrics(db: Session = Depends(get_db)):
    """
    Métricas específicas de base de datos
    - Conteo de registros por tabla
    - Estado de conexión
    """
    try:
        # Contar registros en cada tabla principal
        total_usuarios = db.query(Usuario).count()
        total_doctores = db.query(Doctor).count()
        total_pacientes = db.query(Paciente).count()
        total_citas = db.query(Cita).count()

        # Citas por estado
        citas_pendientes = db.query(Cita).filter(Cita.estado == "PENDIENTE").count()
        citas_confirmadas = db.query(Cita).filter(Cita.estado == "CONFIRMADA").count()
        citas_completadas = db.query(Cita).filter(Cita.estado == "COMPLETADA").count()
        citas_canceladas = db.query(Cita).filter(Cita.estado == "CANCELADA").count()

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "connected",
            "tables": {
                "usuarios": total_usuarios,
                "doctores": total_doctores,
                "pacientes": total_pacientes,
                "citas": {
                    "total": total_citas,
                    "pendientes": citas_pendientes,
                    "confirmadas": citas_confirmadas,
                    "completadas": citas_completadas,
                    "canceladas": citas_canceladas,
                },
            },
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
        }
