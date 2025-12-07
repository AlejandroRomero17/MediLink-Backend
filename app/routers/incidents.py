# app/routers/incidents.py (actualizado)
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.incident import Incident
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    IncidentStatus,
)

router = APIRouter(prefix="/api/incidents", tags=["Incidencias"])


@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Obtiene incidencias con paginación"""

    query = db.query(Incident)

    if status:
        query = query.filter(Incident.status == status)

    if severity:
        query = query.filter(Incident.severity == severity)

    total = query.count()
    incidents = (
        query.order_by(desc(Incident.created_at)).offset(offset).limit(limit).all()
    )

    return {"total": total, "offset": offset, "limit": limit, "incidents": incidents}


@router.post("/", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Reporta una nueva incidencia (público - sin auth)"""

    db_incident = Incident(
        title=incident.title,
        description=incident.description,
        endpoint=incident.endpoint,
        error_message=incident.error_message,
        stack_trace=incident.stack_trace,
        severity=incident.severity or "medium",
        reported_by=incident.reported_by or "anonymous",
        status="open",
        created_at=datetime.now(),
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Aquí podrías enviar notificación (email, Slack, etc.)

    return db_incident


@router.get("/stats")
def get_incident_stats(days: int = 30, db: Session = Depends(get_db)):
    """Estadísticas de incidencias"""

    cutoff_date = datetime.now() - timedelta(days=days)

    total = db.query(Incident).filter(Incident.created_at >= cutoff_date).count()
    open_count = (
        db.query(Incident)
        .filter(Incident.created_at >= cutoff_date, Incident.status == "open")
        .count()
    )

    in_progress = (
        db.query(Incident)
        .filter(Incident.created_at >= cutoff_date, Incident.status == "in_progress")
        .count()
    )

    resolved = (
        db.query(Incident)
        .filter(Incident.created_at >= cutoff_date, Incident.status == "resolved")
        .count()
    )

    # Por severidad
    by_severity = (
        db.query(Incident.severity, func.count(Incident.id).label("count"))
        .filter(Incident.created_at >= cutoff_date)
        .group_by(Incident.severity)
        .all()
    )

    # Tiempo promedio de resolución
    resolved_incidents = (
        db.query(Incident)
        .filter(
            Incident.status == "resolved",
            Incident.created_at >= cutoff_date,
            Incident.resolved_at.isnot(None),
        )
        .all()
    )

    avg_resolution_hours = None
    if resolved_incidents:
        total_hours = sum(
            (inc.resolved_at - inc.created_at).total_seconds() / 3600
            for inc in resolved_incidents
        )
        avg_resolution_hours = round(total_hours / len(resolved_incidents), 2)

    return {
        "period_days": days,
        "total": total,
        "by_status": {
            "open": open_count,
            "in_progress": in_progress,
            "resolved": resolved,
        },
        "by_severity": {r.severity: r.count for r in by_severity},
        "avg_resolution_hours": avg_resolution_hours,
        "resolution_rate": round((resolved / total * 100) if total > 0 else 0, 2),
    }
