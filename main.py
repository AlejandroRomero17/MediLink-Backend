# main.py (EN LA RAÍZ) - VERSIÓN CORREGIDA PARA RENDER
import os
import sys

# 🔥 CRÍTICO: Esto arregla el problema de Render
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    # Intentar importar base de datos (puede fallar si no hay conexión)
    from app.core.database import engine
    from app.models.base import Base

    # Crear tablas solo si estamos en desarrollo
    if os.getenv("ENVIRONMENT", "development") != "production":
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tablas de base de datos verificadas")
        except Exception as e:
            print(f"⚠️  Nota al crear tablas: {e}")
except ImportError as e:
    print(f"⚠️  Error importando módulos de base de datos: {e}")
    print("⚠️  Continuando sin inicialización de BD...")

# Importar routers con manejo de errores
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
    )

    routers_loaded = True
except ImportError as e:
    print(f"❌ Error cargando routers: {e}")
    routers_loaded = False

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
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

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

# Incluir routers si se cargaron correctamente
if routers_loaded:
    app.include_router(registro.router, prefix="/api", tags=["registro"])
    app.include_router(usuarios.router, prefix="/api", tags=["usuarios"])
    app.include_router(pacientes.router, prefix="/api", tags=["pacientes"])
    app.include_router(doctores.router, prefix="/api", tags=["doctores"])
    app.include_router(citas.router, prefix="/api", tags=["citas"])
    app.include_router(disponibilidad.router, prefix="/api", tags=["disponibilidad"])
    app.include_router(busqueda.router, prefix="/api", tags=["busqueda"])
    app.include_router(horarios.router, prefix="/api", tags=["horarios"])
else:

    @app.get("/api/error")
    async def router_error():
        return {"error": "Routers no cargados correctamente"}


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


# Ruta de health check mejorada
@app.get("/health")
async def health_check():
    try:
        from app.core.database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# Ruta para debug de imports
@app.get("/debug/imports")
async def debug_imports():
    import_paths = sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Verificar si podemos importar módulos
    modules_status = {}
    try:
        from app.core import config

        modules_status["app.core.config"] = "✅ OK"
    except ImportError as e:
        modules_status["app.core.config"] = f"❌ {str(e)}"

    try:
        from app.core import database

        modules_status["app.core.database"] = "✅ OK"
    except ImportError as e:
        modules_status["app.core.database"] = f"❌ {str(e)}"

    return {
        "current_directory": current_dir,
        "python_path": import_paths,
        "modules": modules_status,
    }


# Ejecutar servidor
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
