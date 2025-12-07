# app/routers/incidents.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db

router = APIRouter(prefix="/api/incidents", tags=["Incidencias"])


# Schemas (inline porque no tienes el modelo aún)
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    endpoint: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    severity: str = Field("medium", pattern="^(low|medium|high|critical)$")
    reported_by: Optional[str] = "anonymous"


class IncidentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    resolution_notes: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    endpoint: Optional[str]
    error_message: Optional[str]
    severity: str
    status: str
    reported_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True


# Modelo SQLAlchemy (inline)
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    endpoint = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    severity = Column(String(20), default="medium")
    status = Column(String(20), default="open")
    reported_by = Column(String(100), default="anonymous")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)


@router.get("/", response_model=dict)
def get_incidents(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Obtiene lista de incidencias con filtros y paginación"""

    query = db.query(Incident)

    if status:
        query = query.filter(Incident.status == status)

    if severity:
        query = query.filter(Incident.severity == severity)

    total = query.count()
    incidents = (
        query.order_by(desc(Incident.created_at)).offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "incidents": [
            {
                "id": inc.id,
                "title": inc.title,
                "description": inc.description,
                "endpoint": inc.endpoint,
                "error_message": inc.error_message,
                "severity": inc.severity,
                "status": inc.status,
                "reported_by": inc.reported_by,
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc in incidents
        ],
    }


@router.post("/", response_model=IncidentResponse, status_code=201)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Reporta una nueva incidencia (público - sin autenticación)"""

    db_incident = Incident(
        title=incident.title,
        description=incident.description,
        endpoint=incident.endpoint,
        error_message=incident.error_message,
        stack_trace=incident.stack_trace,
        severity=incident.severity,
        reported_by=incident.reported_by,
        status="open",
        created_at=datetime.now(),
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return db_incident


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Obtiene una incidencia específica"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int, update: IncidentUpdate, db: Session = Depends(get_db)
):
    """Actualiza el estado de una incidencia"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    if update.status:
        incident.status = update.status
        incident.updated_at = datetime.now()

        # Si se marca como resuelta, guardar fecha
        if update.status in ["resolved", "closed"]:
            incident.resolved_at = datetime.now()

    if update.resolution_notes:
        incident.resolution_notes = update.resolution_notes

    db.commit()
    db.refresh(incident)

    return incident


@router.get("/stats/summary", response_model=dict)
def get_incident_stats(
    days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)
):
    """Estadísticas de incidencias del periodo"""

    cutoff_date = datetime.now() - timedelta(days=days)

    # Total de incidencias
    total = db.query(Incident).filter(Incident.created_at >= cutoff_date).count()

    # Por estado
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
        .filter(
            Incident.created_at >= cutoff_date,
            Incident.status.in_(["resolved", "closed"]),
        )
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
            Incident.status.in_(["resolved", "closed"]),
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
            if inc.resolved_at
        )
        avg_resolution_hours = round(total_hours / len(resolved_incidents), 2)

    # Top endpoints con más incidencias
    top_endpoints = (
        db.query(Incident.endpoint, func.count(Incident.id).label("count"))
        .filter(Incident.created_at >= cutoff_date, Incident.endpoint.isnot(None))
        .group_by(Incident.endpoint)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

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
        "top_error_endpoints": [
            {"endpoint": r.endpoint, "count": r.count} for r in top_endpoints
        ],
    }
