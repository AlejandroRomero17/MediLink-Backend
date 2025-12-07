# app/routers/metrics.py - VERSIÓN CORREGIDA
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text  # <-- AGREGAR text aquí
from datetime import datetime, timedelta
import psutil
import os
import time  # <-- AGREGAR para medir tiempo

from app.core.database import get_db
from app.models.cita import Cita
from app.models.usuario import Usuario
from app.models.doctor import Doctor
from app.models.paciente import Paciente

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
                "pid": process.pid,
            },
        }
    except Exception as e:
        return {
            "error": f"Error obteniendo métricas del sistema: {str(e)[:100]}",
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
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # Citas por día (si existe la tabla)
        appointments_by_day = []
        total_appointments = 0
        try:
            appointments_by_day = (
                db.query(
                    func.date(Cita.fecha_hora).label("date"),
                    func.count(Cita.id).label("count"),
                )
                .filter(Cita.fecha_hora >= cutoff_date)
                .group_by(func.date(Cita.fecha_hora))
                .order_by(func.date(Cita.fecha_hora))
                .all()
            )
            total_appointments = sum(r.count for r in appointments_by_day)
        except:
            appointments_by_day = []
            total_appointments = 0

        # Usuarios nuevos por día (si existe la tabla)
        new_users_by_day = []
        total_new_users = 0
        try:
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
            total_new_users = sum(r.count for r in new_users_by_day)
        except:
            new_users_by_day = []
            total_new_users = 0

        # Doctores más solicitados
        top_doctors = []
        try:
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
                .group_by(
                    Doctor.id, Usuario.nombre, Usuario.apellido, Doctor.especialidad
                )
                .order_by(desc("appointment_count"))
                .limit(10)
                .all()
            )
        except:
            top_doctors = []

        # Totales
        total_doctors = 0
        total_patients = 0
        try:
            total_doctors = db.query(Doctor).count()
        except:
            pass

        try:
            total_patients = db.query(Paciente).count()
        except:
            pass

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
                "total": total_appointments,
                "by_day": [
                    {"date": str(r.date), "count": r.count} for r in appointments_by_day
                ],
            },
            "users": {
                "total": total_new_users,
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
        }
    except Exception as e:
        return {
            "period_days": days,
            "timestamp": datetime.now().isoformat(),
            "error": f"Error obteniendo métricas de uso: {str(e)[:100]}",
            "totals": {
                "appointments": 0,
                "new_users": 0,
                "total_doctors": 0,
                "total_patients": 0,
            },
            "appointments": {"total": 0, "by_day": []},
            "users": {"total": 0, "by_day": []},
            "top_doctors": [],
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
        # Test de conexión a BD CON text()
        db_response_time = None
        db_status = "unknown"
        db_health = "unknown"

        try:
            start_time = time.time()
            db.execute(text("SELECT 1"))  # <-- CORREGIDO: Usar text()
            end_time = time.time()
            db_response_time = round((end_time - start_time) * 1000, 2)
            db_status = "connected"
            db_health = "healthy" if db_response_time < 100 else "slow"
        except Exception as db_error:
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
                "response_time_avg_ms": 150,
                "error_rate_percent": 0.5,
                "requests_per_minute": 50,
            },
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": f"Error obteniendo métricas de rendimiento: {str(e)[:100]}",
            "api_status": "unhealthy",
            "database": {
                "status": "error",
                "health": "error",
                "response_time_ms": None,
            },
            "application": {
                "memory_mb": 0,
                "cpu_percent": 0,
                "threads": 0,
                "uptime_seconds": 0,
            },
            "estimated_metrics": {
                "response_time_avg_ms": 0,
                "error_rate_percent": 0,
                "requests_per_minute": 0,
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
        # Verificar conexión primero
        db.execute(text("SELECT 1"))  # <-- CORREGIDO: Usar text()

        # Contar registros en cada tabla principal (con try/except por si no existen)
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "status": "connected",
            "tables": {},
        }

        try:
            total_usuarios = db.query(Usuario).count()
            metrics["tables"]["usuarios"] = total_usuarios
        except:
            metrics["tables"]["usuarios"] = "table_not_found"

        try:
            total_doctores = db.query(Doctor).count()
            metrics["tables"]["doctores"] = total_doctores
        except:
            metrics["tables"]["doctores"] = "table_not_found"

        try:
            total_pacientes = db.query(Paciente).count()
            metrics["tables"]["pacientes"] = total_pacientes
        except:
            metrics["tables"]["pacientes"] = "table_not_found"

        try:
            total_citas = db.query(Cita).count()
            metrics["tables"]["citas"] = {"total": total_citas}
        except:
            metrics["tables"]["citas"] = {"total": "table_not_found"}

        return metrics

    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)[:100],
            "tables": {},
        }
