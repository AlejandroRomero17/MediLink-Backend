from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base para modelos
Base = declarative_base()

# --- Crear engine principal usando la URL de Railway ---
try:
    # Usar la URL de la configuración (Railway proporciona DATABASE_URL completa)
    engine = create_engine(
        settings.sqlalchemy_database_url,  # Usar la propiedad que definimos
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        echo=False,  # Desactivar en producción para mejor rendimiento
        connect_args={"connect_timeout": 30},
    )

    logger.info(f"✅ Engine de base de datos creado exitosamente")

    # Probar la conexión
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos verificada")

except Exception as e:
    logger.error(f"❌ Error conectando a la base de datos: {str(e)}")
    logger.info(f"URL usada: {settings.sqlalchemy_database_url}")
    raise

# --- Crear sesión de base de datos ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Dependencia para obtener sesión en FastAPI ---
def get_db():
    """
    Dependencia para obtener sesión de base de datos.
    Usar en endpoints de FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
