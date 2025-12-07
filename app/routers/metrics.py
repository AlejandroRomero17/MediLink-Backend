# app/routers/metrics.py (actualizado)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import psutil
import os

from app.core.database import get_db
from app.models import Cita, Usuario, Doctor, Paciente

router = APIRouter(prefix="/api/metrics", tags=["Métricas"])


@router.get("/system")
async def get_system_metrics():
    """Métricas del sistema"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Información de la aplicación
    process = psutil.Process(os.getpid())

    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
            "disk": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
            },
        },
        "application": {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "connections": len(process.connections()),
        },
    }


@router.get("/usage")
def get_api_usage(days: int = 7, db: Session = Depends(get_db)):
    """Métricas de uso de la API"""
    # Aquí normalmente usarías una tabla de logs
    # Por ahora, métricas básicas de datos

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
        .join(Cita, Doctor.id == Cita.doctor_id)
        .filter(Cita.fecha_hora >= cutoff_date)
        .group_by(Doctor.id, Usuario.nombre, Usuario.apellido, Doctor.especialidad)
        .order_by(desc("appointment_count"))
        .limit(10)
        .all()
    )

    return {
        "period_days": days,
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
                "name": f"{r.nombre} {r.apellido}",
                "specialty": r.especialidad,
                "appointments": r.appointment_count,
            }
            for r in top_doctors
        ],
    }


@router.get("/performance")
def get_performance_metrics():
    """Métricas de rendimiento"""
    # Aquí podrías integrar con herramientas como Prometheus
    # Por ahora, métricas básicas

    return {
        "timestamp": datetime.now().isoformat(),
        "api_status": "healthy",
        "database_status": "connected",
        "response_time_avg_ms": 150,  # Esto sería medido realmente
        "error_rate_percent": 0.5,  # Esto sería medido realmente
        "active_connections": 10,  # Esto sería medido realmente
        "requests_per_minute": 50,  # Esto sería medido realmente
    }
