# seeder.py - Actualizado con Xicotepec, Puebla
import sys
import os
from datetime import datetime, time, date, timedelta
import random

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import SessionLocal, engine
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.doctor import Doctor
from app.models.horario_doctor import HorarioDoctor
from app.models.cita import Cita
from app.models.base import Base
from app.models.enums import (
    TipoUsuarioEnum,
    GeneroEnum,
    EspecialidadEnum,
    DiaSemanaEnum,
    EstadoCitaEnum,
    TipoSangreEnum,
)
from app.core.security import hash_password

# Importar el modelo de Incident
from app.routers.incidents import Incident


def create_all_tables():
    """Crear todas las tablas incluyendo incidents"""
    print("🔨 Creando todas las tablas en la base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Todas las tablas creadas/verificadas exitosamente")

        # Mostrar tablas creadas
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Tablas en la base de datos: {', '.join(tables)}")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        raise


def clear_database():
    """Limpiar todas las tablas de la base de datos"""
    print("🧹 Limpiando base de datos...")
    db = SessionLocal()
    try:
        # Eliminar en orden para respetar las foreign keys
        db.query(Cita).delete()
        db.query(HorarioDoctor).delete()
        db.query(Incident).delete()
        db.query(Paciente).delete()
        db.query(Doctor).delete()
        db.query(Usuario).delete()
        db.commit()
        print("✅ Base de datos limpiada exitosamente")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al limpiar base de datos: {e}")
    finally:
        db.close()


def create_usuarios(db):
    """Crear usuarios de prueba"""
    print("👥 Creando usuarios...")

    usuarios_data = [
        # Doctores
        {
            "email": "ana.garcia@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Ana",
            "apellido": "García",
            "telefono": "776-101-2345",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "jaime.martinez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Jaime",
            "apellido": "Martínez",
            "telefono": "776-102-2345",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "martin.lopez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Martín",
            "apellido": "López",
            "telefono": "776-103-2345",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "alejandro.rodriguez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Alejandro",
            "apellido": "Rodríguez",
            "telefono": "776-104-2345",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        # Pacientes
        {
            "email": "maria.perez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "María",
            "apellido": "Pérez",
            "telefono": "776-201-2345",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "juan.hernandez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Juan",
            "apellido": "Hernández",
            "telefono": "776-202-2345",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "laura.gonzalez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Laura",
            "apellido": "González",
            "telefono": "776-203-2345",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "carlos.ramirez@utxicotepec.edu.mx",
            "password": "password123",
            "nombre": "Carlos",
            "apellido": "Ramírez",
            "telefono": "776-204-2345",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        # Admin
        {
            "email": "admin@utxicotepec.edu.mx",
            "password": "admin123",
            "nombre": "Admin",
            "apellido": "Sistema",
            "telefono": "776-001-2345",
            "tipo_usuario": TipoUsuarioEnum.ADMIN,
        },
    ]

    usuarios = []
    for user_data in usuarios_data:
        usuario = Usuario(
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            nombre=user_data["nombre"],
            apellido=user_data["apellido"],
            telefono=user_data["telefono"],
            tipo_usuario=user_data["tipo_usuario"],
            fecha_registro=datetime.now(),
        )
        db.add(usuario)
        usuarios.append(usuario)

    db.commit()

    # Refrescar para obtener los IDs
    for usuario in usuarios:
        db.refresh(usuario)

    print(f"✅ {len(usuarios)} usuarios creados")
    return usuarios


def create_doctores(db, usuarios):
    """Crear doctores de prueba"""
    print("👨‍⚕️ Creando doctores...")

    doctores_usuarios = [
        u for u in usuarios if u.tipo_usuario == TipoUsuarioEnum.DOCTOR
    ]

    doctores_data = [
        {
            "usuario": doctores_usuarios[0],
            "especialidad": EspecialidadEnum.CARDIOLOGIA,
            "cedula_profesional": "CED-PUE-001",
            "consultorio": "Consultorio Cardiológico de Xicotepec",
            "direccion_consultorio": "Av. 20 de Noviembre 45, Centro",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "anos_experiencia": 12,
            "costo_consulta": 450.00,
            "duracion_cita_minutos": 45,
            "universidad": "Universidad Autónoma de Puebla",
            "biografia": "Cardióloga con más de 10 años de experiencia en intervenciones cardíacas y prevención.",
            "acepta_seguro": True,
            "atiende_domicilio": False,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[1],
            "especialidad": EspecialidadEnum.PEDIATRIA,
            "cedula_profesional": "CED-PUE-002",
            "consultorio": "Clínica Pediátrica Infantil Xicotepec",
            "direccion_consultorio": "Calle Hidalgo 123, Col. Centro",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "anos_experiencia": 8,
            "costo_consulta": 350.00,
            "duracion_cita_minutos": 30,
            "universidad": "Universidad Popular Autónoma del Estado de Puebla",
            "biografia": "Especialista en cuidado infantil y desarrollo pediátrico integral.",
            "acepta_seguro": True,
            "atiende_domicilio": True,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[2],
            "especialidad": EspecialidadEnum.DERMATOLOGIA,
            "cedula_profesional": "CED-PUE-003",
            "consultorio": "Centro Dermatológico Sierra Norte",
            "direccion_consultorio": "Av. Juárez 234, Col. Reforma",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "anos_experiencia": 15,
            "costo_consulta": 400.00,
            "duracion_cita_minutos": 40,
            "universidad": "Benemérita Universidad Autónoma de Puebla",
            "biografia": "Experto en tratamientos dermatológicos y cuidado de la piel.",
            "acepta_seguro": False,
            "atiende_domicilio": False,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[3],
            "especialidad": EspecialidadEnum.MEDICINA_GENERAL,
            "cedula_profesional": "CED-PUE-004",
            "consultorio": "Consultorio Médico General Xicotepec",
            "direccion_consultorio": "Calle Morelos 89, Centro",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "anos_experiencia": 10,
            "costo_consulta": 300.00,
            "duracion_cita_minutos": 30,
            "universidad": "Universidad Autónoma de Puebla",
            "biografia": "Médico general con amplia experiencia en diagnóstico y tratamiento integral.",
            "acepta_seguro": True,
            "atiende_domicilio": True,
            "atiende_videollamada": True,
        },
    ]

    doctores = []
    for doc_data in doctores_data:
        doctor = Doctor(
            usuario_id=doc_data["usuario"].id,
            especialidad=doc_data["especialidad"],
            cedula_profesional=doc_data["cedula_profesional"],
            consultorio=doc_data["consultorio"],
            direccion_consultorio=doc_data["direccion_consultorio"],
            ciudad=doc_data["ciudad"],
            estado=doc_data["estado"],
            codigo_postal=doc_data["codigo_postal"],
            anos_experiencia=doc_data["anos_experiencia"],
            costo_consulta=doc_data["costo_consulta"],
            duracion_cita_minutos=doc_data["duracion_cita_minutos"],
            universidad=doc_data.get("universidad"),
            biografia=doc_data.get("biografia"),
            acepta_seguro=doc_data["acepta_seguro"],
            atiende_domicilio=doc_data["atiende_domicilio"],
            atiende_videollamada=doc_data["atiende_videollamada"],
            calificacion_promedio=round(random.uniform(4.0, 5.0), 1),
            total_valoraciones=random.randint(10, 50),
        )
        db.add(doctor)
        doctores.append(doctor)

    db.commit()

    for doctor in doctores:
        db.refresh(doctor)

    print(f"✅ {len(doctores)} doctores creados")
    return doctores


def create_pacientes(db, usuarios):
    """Crear pacientes de prueba"""
    print("👤 Creando pacientes...")

    pacientes_usuarios = [
        u for u in usuarios if u.tipo_usuario == TipoUsuarioEnum.PACIENTE
    ]

    pacientes_data = [
        {
            "usuario": pacientes_usuarios[0],
            "fecha_nacimiento": date(1985, 5, 15),
            "genero": GeneroEnum.FEMENINO,
            "direccion": "Calle Allende 67, Col. Centro",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "numero_seguro": "SEG-PUE-001234",
            "alergias": "Penicilina, Mariscos",
            "tipo_sangre": TipoSangreEnum.A_POSITIVO,
            "contacto_emergencia_nombre": "José Pérez",
            "contacto_emergencia_telefono": "776-111-2345",
        },
        {
            "usuario": pacientes_usuarios[1],
            "fecha_nacimiento": date(1990, 8, 22),
            "genero": GeneroEnum.MASCULINO,
            "direccion": "Av. Independencia 234, Col. Reforma",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "numero_seguro": "SEG-PUE-005678",
            "alergias": "Ninguna",
            "tipo_sangre": TipoSangreEnum.O_POSITIVO,
            "contacto_emergencia_nombre": "María Hernández",
            "contacto_emergencia_telefono": "776-222-2345",
        },
        {
            "usuario": pacientes_usuarios[2],
            "fecha_nacimiento": date(1992, 3, 10),
            "genero": GeneroEnum.FEMENINO,
            "direccion": "Calle 5 de Mayo 156, Centro",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "numero_seguro": "SEG-PUE-009876",
            "alergias": "Polvo, Ácaros",
            "tipo_sangre": TipoSangreEnum.B_NEGATIVO,
            "contacto_emergencia_nombre": "Carlos González",
            "contacto_emergencia_telefono": "776-333-2345",
        },
        {
            "usuario": pacientes_usuarios[3],
            "fecha_nacimiento": date(1988, 11, 30),
            "genero": GeneroEnum.MASCULINO,
            "direccion": "Av. Juárez 345, Col. Revolución",
            "ciudad": "Xicotepec de Juárez",
            "estado": "Puebla",
            "codigo_postal": "73080",
            "numero_seguro": "SEG-PUE-003456",
            "alergias": "Aspirina",
            "tipo_sangre": TipoSangreEnum.AB_POSITIVO,
            "contacto_emergencia_nombre": "Ana Ramírez",
            "contacto_emergencia_telefono": "776-444-2345",
        },
    ]

    pacientes = []
    for pac_data in pacientes_data:
        paciente = Paciente(
            usuario_id=pac_data["usuario"].id,
            fecha_nacimiento=pac_data["fecha_nacimiento"],
            genero=pac_data["genero"],
            direccion=pac_data["direccion"],
            ciudad=pac_data["ciudad"],
            estado=pac_data["estado"],
            codigo_postal=pac_data["codigo_postal"],
            numero_seguro=pac_data["numero_seguro"],
            alergias=pac_data["alergias"],
            tipo_sangre=pac_data["tipo_sangre"],
            contacto_emergencia_nombre=pac_data["contacto_emergencia_nombre"],
            contacto_emergencia_telefono=pac_data["contacto_emergencia_telefono"],
        )
        db.add(paciente)
        pacientes.append(paciente)

    db.commit()

    for paciente in pacientes:
        db.refresh(paciente)

    print(f"✅ {len(pacientes)} pacientes creados")
    return pacientes


def create_horarios(db, doctores):
    """Crear horarios para los doctores"""
    print("🕐 Creando horarios...")

    horarios = []

    for doctor in doctores:
        # Horario de lunes a viernes para todos los doctores
        dias_semana = [
            DiaSemanaEnum.LUNES,
            DiaSemanaEnum.MARTES,
            DiaSemanaEnum.MIERCOLES,
            DiaSemanaEnum.JUEVES,
            DiaSemanaEnum.VIERNES,
        ]

        for dia in dias_semana:
            # Horario de mañana
            horario_manana = HorarioDoctor(
                doctor_id=doctor.id,
                dia_semana=dia,
                hora_inicio=time(9, 0),  # 9:00 AM
                hora_fin=time(13, 0),  # 1:00 PM
                activo=True,
            )
            db.add(horario_manana)
            horarios.append(horario_manana)

            # Horario de tarde
            horario_tarde = HorarioDoctor(
                doctor_id=doctor.id,
                dia_semana=dia,
                hora_inicio=time(15, 0),  # 3:00 PM
                hora_fin=time(18, 0),  # 6:00 PM
                activo=True,
            )
            db.add(horario_tarde)
            horarios.append(horario_tarde)

    db.commit()
    print(f"✅ {len(horarios)} horarios creados")
    return horarios


def create_citas(db, doctores, pacientes):
    """Crear citas de prueba"""
    print("📅 Creando citas...")

    citas = []
    estados = [
        EstadoCitaEnum.PENDIENTE,
        EstadoCitaEnum.CONFIRMADA,
        EstadoCitaEnum.COMPLETADA,
        EstadoCitaEnum.EN_CURSO,
    ]

    motivos = [
        "Consulta de rutina",
        "Chequeo general",
        "Seguimiento de tratamiento",
        "Dolor persistente",
        "Revisión de resultados",
        "Consulta por síntomas nuevos",
    ]

    sintomas = [
        "Dolor de cabeza, fiebre",
        "Tos persistente, congestión nasal",
        "Dolor abdominal, náuseas",
        "Cansancio extremo, mareos",
        "Dolor en las articulaciones",
        "Problemas digestivos",
    ]

    for i, paciente in enumerate(pacientes):
        # Asignar diferentes doctores a diferentes pacientes
        doctor = doctores[i % len(doctores)]

        # Crear 3-4 citas por paciente
        for j in range(random.randint(3, 4)):
            # Fechas en el futuro (próximos 15 días)
            dias_futuro = random.randint(1, 15)
            fecha_cita = datetime.now() + timedelta(days=dias_futuro)

            # Ajustar hora entre 9 AM y 5 PM
            hora_cita = random.randint(9, 16)
            fecha_cita = fecha_cita.replace(
                hour=hora_cita, minute=0, second=0, microsecond=0
            )

            estado = random.choice(estados)
            es_videollamada = random.choice([True, False])

            cita = Cita(
                paciente_id=paciente.id,
                doctor_id=doctor.id,
                fecha_hora=fecha_cita,
                duracion_minutos=doctor.duracion_cita_minutos,
                motivo=random.choice(motivos),
                sintomas=random.choice(sintomas),
                notas_paciente=f"Paciente refiere {random.choice(sintomas)}",
                es_videollamada=es_videollamada,
                url_videollamada=es_videollamada
                and f"https://meet.medilink.com/cita-{i}-{j}"
                or None,
                estado=estado,
                costo=doctor.costo_consulta,
                recordatorio_enviado=random.choice([True, False]),
            )

            # Si la cita está completada, agregar notas del doctor
            if estado == EstadoCitaEnum.COMPLETADA:
                cita.notas_doctor = "Paciente evaluado, tratamiento prescrito"
                cita.diagnostico = "Diagnóstico preliminar basado en síntomas"
                cita.tratamiento = "Medicamento recetado y recomendaciones"

            db.add(cita)
            citas.append(cita)

    db.commit()
    print(f"✅ {len(citas)} citas creadas")
    return citas


def create_incidents(db):
    """Crear incidencias de ejemplo"""
    print("🚨 Creando incidencias...")

    incidents_data = [
        {
            "title": "Error 500 en búsqueda de doctores por especialidad",
            "description": "La API retornaba error 500 al buscar doctores cuando la especialidad se enviaba en mayúsculas (CARDIOLOGIA en lugar de cardiologia)",
            "endpoint": "/api/busqueda/doctores",
            "error_message": "Input should be 'medicina_general', 'cardiologia', etc.",
            "severity": "high",
            "status": "resolved",
            "reported_by": "frontend_team",
            "created_at": datetime.now() - timedelta(days=5),
            "resolved_at": datetime.now() - timedelta(days=4),
            "resolution_notes": "Normalizado valores a minúsculas en frontend y agregada validación en backend",
        },
        {
            "title": "Timeout en conexión a base de datos",
            "description": "Timeouts intermitentes en Railway después de 15 minutos de inactividad. Primera consulta toma 3-5 segundos.",
            "endpoint": "/api/doctores",
            "error_message": "Database connection timeout after 15min inactivity",
            "severity": "medium",
            "status": "resolved",
            "reported_by": "monitoring_system",
            "created_at": datetime.now() - timedelta(days=3),
            "resolved_at": datetime.now() - timedelta(days=2),
            "resolution_notes": "Implementado pool_pre_ping=True y pool_recycle=3600 en engine de SQLAlchemy",
        },
        {
            "title": "CORS bloqueando requests desde Vercel",
            "description": "Frontend desplegado en Vercel no puede hacer requests a la API. Origen bloqueado por política CORS.",
            "endpoint": "/api/citas",
            "error_message": "CORS policy: No 'Access-Control-Allow-Origin' header",
            "severity": "critical",
            "status": "resolved",
            "reported_by": "production_monitoring",
            "created_at": datetime.now() - timedelta(days=2),
            "resolved_at": datetime.now() - timedelta(days=1),
            "resolution_notes": "Agregado dominio de Vercel a CORS_ORIGINS en variables de entorno",
        },
        {
            "title": "Lentitud en listado de citas con muchos registros",
            "description": "Endpoint de listado de citas se vuelve muy lento cuando hay más de 1000 registros",
            "endpoint": "/api/citas",
            "error_message": None,
            "severity": "medium",
            "status": "in_progress",
            "reported_by": "performance_test",
            "created_at": datetime.now() - timedelta(days=1),
            "resolution_notes": "Implementando paginación y optimización de queries",
        },
        {
            "title": "Error al crear cita con horario fuera de disponibilidad",
            "description": "Sistema permite crear citas en horarios donde el doctor no está disponible",
            "endpoint": "/api/citas",
            "error_message": "Appointment created outside doctor's available hours",
            "severity": "high",
            "status": "open",
            "reported_by": "qa_testing",
            "created_at": datetime.now(),
        },
    ]

    incidents = []
    for inc_data in incidents_data:
        incident = Incident(
            title=inc_data["title"],
            description=inc_data["description"],
            endpoint=inc_data["endpoint"],
            error_message=inc_data.get("error_message"),
            severity=inc_data["severity"],
            status=inc_data["status"],
            reported_by=inc_data["reported_by"],
            created_at=inc_data.get("created_at", datetime.now()),
            resolved_at=inc_data.get("resolved_at"),
            resolution_notes=inc_data.get("resolution_notes"),
        )
        db.add(incident)
        incidents.append(incident)

    db.commit()
    print(f"✅ {len(incidents)} incidencias creadas")
    return incidents


def main():
    """Función principal del seeder"""
    print("🚀 Iniciando seeder de MediLink - Xicotepec, Puebla...")
    print("=" * 60)

    # Crear todas las tablas primero
    create_all_tables()
    print("=" * 60)

    db = SessionLocal()
    try:
        # Limpiar base de datos
        clear_database()
        print("=" * 60)

        # Crear datos
        usuarios = create_usuarios(db)
        doctores = create_doctores(db, usuarios)
        pacientes = create_pacientes(db, usuarios)
        horarios = create_horarios(db, doctores)
        citas = create_citas(db, doctores, pacientes)
        incidents = create_incidents(db)

        print("\n" + "=" * 60)
        print("🎉 Seeder completado exitosamente!")
        print("=" * 60)
        print(f"📊 Resumen:")
        print(f"   👥 Usuarios: {len(usuarios)}")
        print(f"   👨‍⚕️ Doctores: {len(doctores)}")
        print(f"   👤 Pacientes: {len(pacientes)}")
        print(f"   🕐 Horarios: {len(horarios)}")
        print(f"   📅 Citas: {len(citas)}")
        print(f"   🚨 Incidencias: {len(incidents)}")

        print("\n" + "=" * 60)
        print("🔑 Credenciales de prueba:")
        print("=" * 60)
        print("   Doctores:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.DOCTOR:
                print(f"   📧 {usuario.email} / password123")

        print("\n   Pacientes:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.PACIENTE:
                print(f"   📧 {usuario.email} / password123")

        print("\n   Admin:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.ADMIN:
                print(f"   📧 {usuario.email} / admin123")

        print("\n" + "=" * 60)
        print("🌐 Endpoints para probar:")
        print("=" * 60)
        print("   GET  /api/doctores")
        print("   GET  /api/busqueda/doctores")
        print("   GET  /api/citas")
        print("   GET  /api/metrics/system")
        print("   GET  /api/metrics/usage")
        print("   GET  /api/incidents/")
        print("   GET  /api/incidents/stats/summary")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Error en el seeder: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
