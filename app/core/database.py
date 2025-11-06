from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# --- Crear la base de datos si no existe ---
# Crear conexión temporal (sin especificar DB)
temp_engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}",
    pool_pre_ping=True,
)

# Crear la base de datos si no existe
with temp_engine.connect() as conn:
    conn.execute(
        text(
            f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
    )
    print(f"✅ Base de datos '{settings.DB_NAME}' verificada o creada con éxito.")

# --- Crear engine principal apuntando a la base de datos ---
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=True,  # Muestra consultas SQL (desactivar en producción)
)

# --- Crear sesión de base de datos ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Dependencia para obtener sesión en FastAPI ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
