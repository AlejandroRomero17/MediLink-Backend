from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Importar modelos para crear las tablas
from app.core.database import engine
from app.models import Base

# Importar routers
from app.routers import (
    usuarios,
    pacientes,
    doctores,
    citas,
    disponibilidad,
    registro,
    busqueda,
    horarios,  # ← NUEVO: Router de horarios
)

# Cargar variables de entorno
load_dotenv()

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="MediLink API",
    description="Sistema de gestión de citas médicas",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers (todos ya tienen su prefix definido)
app.include_router(registro.router)  # /api/registro
app.include_router(usuarios.router)  # /api/usuarios
app.include_router(pacientes.router)  # /api/pacientes
app.include_router(doctores.router)  # /api/doctores
app.include_router(citas.router)  # /api/citas
app.include_router(disponibilidad.router)  # /api/disponibilidad
app.include_router(busqueda.router)  # /api/busqueda
app.include_router(horarios.router)  # /api/horarios ← NUEVO


# Ruta raíz
@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a MediLink API v2.0",
        "version": "2.0.0",
        "status": "activo",
        "documentacion": "/docs",
        "features": [
            "Registro combinado (usuario + perfil)",
            "Sistema de horarios flexible por día",  # ← ACTUALIZADO
            "Autenticación JWT",
            "Geolocalización de doctores",
            "Valoraciones y reseñas",
        ],
    }


# Ruta de health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "version": "2.0.0"}


# Ejecutar servidor
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True  # Auto-reload en desarrollo
    )
