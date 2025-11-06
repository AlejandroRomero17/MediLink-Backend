from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
import os
from dotenv import load_dotenv

# Importar modelos para crear las tablas
from app.core.database import engine
from app.models.base import Base

# Importar routers
from app.routers import (
    usuarios,
    pacientes,
    doctores,
    citas,
    disponibilidad,
    registro,
    busqueda,
    horarios,
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
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
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


# Función personalizada para OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="MediLink API",
        version="2.0.0",
        description="Sistema de gestión de citas médicas",
        routes=app.routes,
    )

    # Configurar esquema de seguridad JWT
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Ingresa el token JWT en el formato: Bearer <token>",
        }
    }

    # Aplicar seguridad globalmente
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            # Excluir endpoints públicos
            if path in ["/", "/health", "/api/registro/", "/api/usuarios/login"]:
                continue
            if method in ["post", "get", "put", "delete"]:
                openapi_schema["paths"][path][method]["security"] = [{"Bearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Incluir routers
app.include_router(registro.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)
app.include_router(doctores.router)
app.include_router(citas.router)
app.include_router(disponibilidad.router)
app.include_router(busqueda.router)
app.include_router(horarios.router)


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
            "Sistema de horarios flexible por día",
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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
