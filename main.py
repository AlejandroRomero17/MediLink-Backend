# main.py - VERSIÓN CON MÉTRICAS E INCIDENCIAS CORREGIDA
import os
import sys

# Configuración de paths
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)

paths_to_add = [
    current_dir,
    os.path.join(current_dir, "app"),
    os.path.join(current_dir, "app/core"),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

print(f"✅ Python path configurado")

# Importar configuración
try:
    from app.core.config import settings

    print("✅ Configuración cargada")
except ImportError as e:
    print(f"⚠️  Error cargando configuración: {e}")

    class DefaultSettings:
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "3306")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_NAME = os.getenv("DB_NAME", "medilink")
        SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
        ALGORITHM = "HS256"
        CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

        @property
        def sqlalchemy_database_url(self):
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    settings = DefaultSettings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Crear aplicación
app = FastAPI(
    title="MediLink API",
    description="Sistema de gestión de citas médicas con métricas e incidencias",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,https://medilink-backend-7ivn.onrender.com"
)
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar routers
routers = []
try:
    from app.routers import (
        usuarios,
        pacientes,
        doctores,
        citas,
        disponibilidad,
        registro,
        busqueda,
        horarios,
        metrics,  # ← NUEVO
        incidents,  # ← NUEVO
    )

    routers = [
        ("registro", registro.router),
        ("usuarios", usuarios.router),
        ("pacientes", pacientes.router),
        ("doctores", doctores.router),
        ("citas", citas.router),
        ("disponibilidad", disponibilidad.router),
        ("busqueda", busqueda.router),
        ("horarios", horarios.router),
        ("metrics", metrics.router),  # ← NUEVO
        ("incidents", incidents.router),  # ← NUEVO
    ]
    print("✅ Todos los routers cargados (incluyendo metrics e incidents)")
except ImportError as e:
    print(f"⚠️  Error cargando routers: {e}")

# Incluir routers
for name, router in routers:
    try:
        app.include_router(router)
        print(f"✅ Router {name} incluido")
    except Exception as e:
        print(f"❌ Error incluyendo router {name}: {e}")


@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "app": "MediLink API",
        "version": "2.0.0",
        "status": "activo",
        "deployment": "Render.com",
        "documentacion": "/docs",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api_base": "/api",
            "metrics": "/api/metrics",
            "incidents": "/api/incidents",
        },
        "features": [
            "Gestión de citas médicas",
            "Búsqueda avanzada de doctores",
            "Sistema de autenticación JWT",
            "Métricas del sistema",
            "Registro de incidencias",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check completo del sistema"""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text  # <-- IMPORTANTE: Agregar este import

        db = SessionLocal()
        db.execute(text("SELECT 1"))  # <-- CORREGIDO: Usar text()
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    return {
        "status": "healthy",
        "service": "MediLink API",
        "version": "2.0.0",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "features": {
            "metrics": "enabled",
            "incidents": "enabled",
            "authentication": "enabled",
        },
    }


@app.get("/api/test")
async def api_test():
    """Endpoint de prueba"""
    from datetime import datetime

    return {
        "message": "API funcionando correctamente",
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Iniciando servidor en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
