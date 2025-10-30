from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear motor de base de datos
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=3600,  # Recicla conexiones cada hora
    echo=True,  # Muestra las consultas SQL (quitar en producción)
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
