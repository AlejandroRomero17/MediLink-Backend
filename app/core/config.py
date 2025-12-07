import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Para Render + Railway MySQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Variables de MySQL desde Railway
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "medilink")

    # Configuración API
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL para SQLAlchemy - compatible con Render y Railway"""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("mysql://"):
                return self.DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
            return self.DATABASE_URL

        # Construir URL para Railway MySQL
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()

# Validar en producción
if settings.is_production:
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY es requerida en producción")
    if not settings.DB_HOST or settings.DB_HOST == "localhost":
        raise ValueError("DB_HOST debe apuntar a Railway en producción")
