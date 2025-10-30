from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Importar modelos para crear las tablas
from database import engine, Base
import models

# Importar routers
from routers import usuarios, pacientes, doctores, citas

# Cargar variables de entorno
load_dotenv()

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="MediLink API",
    description="Sistema de gestión de citas médicas",
    version="1.0.0",
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

# Incluir routers
app.include_router(usuarios.router)
app.include_router(pacientes.router)
app.include_router(doctores.router)
app.include_router(citas.router)


# Ruta raíz
@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a MediLink API",
        "version": "1.0.0",
        "status": "activo",
        "documentacion": "/docs",
    }


# Ruta de health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Ejecutar servidor
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True  # Auto-reload en desarrollo
    )
