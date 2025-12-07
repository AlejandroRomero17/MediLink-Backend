# main.py - VERSIÓN FINAL PARA RENDER
import os
import sys

# 🔥 SOLUCIÓN DEFINITIVA PARA RENDER
# Obtener el directorio del archivo actual
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)

# Agregar múltiples paths para asegurar
paths_to_add = [
    current_dir,  # Directorio actual
    os.path.join(current_dir, "app"),  # Directorio app
    os.path.join(current_dir, "app/core"),  # Directorio core
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"✅ Path agregado: {path}")

print(f"✅ Python path configurado: {sys.path}")

# Intentar importar config primero
try:
    from app.core.config import settings

    print("✅ Configuración cargada exitosamente")
    print(f"   DB_HOST: {settings.DB_HOST}")
    print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
except ImportError as e:
    print(f"❌ Error cargando configuración: {e}")
    print("⚠️  Creando configuración por defecto...")

    # Configuración por defecto para emergencia
    class DefaultSettings:
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "3306")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_NAME = os.getenv("DB_NAME", "medilink")
        SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")
        CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

        @property
        def sqlalchemy_database_url(self):
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    settings = DefaultSettings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear aplicación FastAPI
app = FastAPI(
    title="MediLink API",
    description="Sistema de gestión de citas médicas - Render Deployment",
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

# Intentar cargar routers
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
    ]
    print("✅ Todos los routers cargados")
except ImportError as e:
    print(f"⚠️  Algunos routers no se cargaron: {e}")

# Incluir routers si se cargaron
for name, router in routers:
    try:
        app.include_router(router, prefix="/api", tags=[name])
        print(f"✅ Router {name} incluido")
    except Exception as e:
        print(f"❌ Error incluyendo router {name}: {e}")


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
            if path in ["/", "/health", "/api/registro/", "/api/usuarios/login"]:
                continue
            if method in ["post", "get", "put", "delete"]:
                openapi_schema["paths"][path][method]["security"] = [{"Bearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Ruta raíz mejorada
@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a MediLink API v2.0",
        "version": "2.0.0",
        "status": "activo",
        "deployment": "Render.com",
        "url": "https://medilink-backend-7ivn.onrender.com",
        "documentacion": "/docs",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api_base": "/api",
            "debug": "/debug/paths",
        },
        "database": {
            "host": settings.DB_HOST,
            "status": "configurada" if settings.DB_HOST != "localhost" else "local",
        },
    }


# Ruta de health check mejorada
@app.get("/health")
async def health_check():
    try:
        # Intentar conexión a BD si tenemos los módulos
        from app.core.database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"config_error: {str(e)[:100]}"

    return {
        "status": "healthy",
        "service": "MediLink API",
        "deployment": "Render.com",
        "database": db_status,
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "cors_origins": origins,
        "available_routers": [name for name, _ in routers],
    }


# Ruta de debug para ver paths
@app.get("/debug/paths")
async def debug_paths():
    return {
        "current_file": os.path.abspath(__file__),
        "current_dir": os.path.dirname(os.path.abspath(__file__)),
        "sys_path": sys.path,
        "working_dir": os.getcwd(),
        "environment_vars": {
            "DB_HOST": os.getenv("DB_HOST", "not_set"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "not_set"),
            "RENDER": os.getenv("RENDER", "not_set"),
        },
    }


# Ruta de prueba de API
@app.get("/api/test")
async def api_test():
    return {
        "message": "API funcionando",
        "status": "ok",
        "timestamp": "2025-01-30T10:00:00Z",
    }


# Ejecutar servidor
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Iniciando servidor en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
