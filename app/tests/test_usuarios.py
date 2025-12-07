# app/tests/test_usuarios.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Configurar app de prueba
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crear tablas antes de tests y eliminarlas después"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Tests para usuarios
def test_crear_usuario():
    response = client.post(
        "/api/usuarios/registro",
        json={
            "nombre": "Test",
            "apellido": "User",
            "email": "test@example.com",
            "telefono": "1234567890",
            "password": "testpass123",
            "tipo_usuario": "PACIENTE",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"


def test_login_usuario():
    response = client.post(
        "/api/usuarios/login",
        data={"username": "test@example.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_obtener_usuario_autenticado():
    # Primero login
    login_response = client.post(
        "/api/usuarios/login",
        data={"username": "test@example.com", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    # Luego obtener usuario
    response = client.get(
        "/api/usuarios/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


# Tests para citas
def test_crear_cita():
    # Primero crear doctor
    doctor_response = client.post(
        "/api/doctores/",
        json={
            "usuario_id": 1,
            "especialidad": "CARDIOLOGIA",
            "cedula_profesional": "TEST123",
            "consultorio": "Consultorio Test",
            "direccion_consultorio": "Calle Test 123",
            "ciudad": "Test City",
            "estado": "Test State",
            "codigo_postal": "12345",
            "costo_consulta": 500.0,
            "duracion_cita_minutos": 30,
            "acepta_seguro": True,
            "atiende_domicilio": False,
            "atiende_videollamada": True,
            "calificacion_promedio": 4.5,
            "total_valoraciones": 10,
        },
    )

    # Crear cita
    response = client.post(
        "/api/citas/",
        json={
            "doctor_id": 1,
            "fecha_hora": "2024-01-15T10:00:00",
            "motivo": "Consulta general",
            "es_videollamada": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["motivo"] == "Consulta general"


# Ejecutar tests: pytest app/tests/ -v
