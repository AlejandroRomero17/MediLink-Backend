# app/core/health.py
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import os

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check completo del sistema"""

    # Verificar base de datos
    db_healthy = False
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        db_error = str(e)

    # Métricas del sistema
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Uptime
    uptime_seconds = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)

    # Conexiones de red
    connections = psutil.net_connections()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "error": db_error if not db_healthy else None,
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "uptime_days": uptime.days,
            "uptime_hours": uptime.seconds // 3600,
            "network_connections": len(connections),
        },
        "services": {
            "api": "running",
            "database": "running" if db_healthy else "stopped",
            "authentication": "running",
        },
    }
