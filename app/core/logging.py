# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
import sys
import json
from datetime import datetime


def setup_logging():
    # Configurar logging
    logger = logging.getLogger("medilink")
    logger.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Handler para archivo (rotativo)
    file_handler = RotatingFileHandler(
        "logs/medilink.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Middleware para log de requests
async def log_requests(request, call_next):
    logger = logging.getLogger("medilink")

    # Datos de la request
    request_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    logger.info(f"Request: {json.dumps(request_data)}")

    response = await call_next(request)

    # Datos de la response
    response_data = {
        "timestamp": datetime.now().isoformat(),
        "status_code": response.status_code,
        "elapsed_ms": None,  # Podrías calcular el tiempo
    }

    logger.info(f"Response: {json.dumps(response_data)}")

    return response
