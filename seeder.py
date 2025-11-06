# seeder.py
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
from app.models.enums import (
    TipoUsuarioEnum,
    GeneroEnum,
    EspecialidadEnum,
    DiaSemanaEnum,
    EstadoCitaEnum,
    TipoSangreEnum,
)
from app.core.security import hash_password


def clear_database():
    """Limpiar todas las tablas de la base de datos"""
    print("🧹 Limpiando base de datos...")
    db = SessionLocal()
    try:
        # Eliminar en orden para respetar las foreign keys
        db.query(Cita).delete()
        db.query(HorarioDoctor).delete()
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
            "email": "dr.garcia@medilink.com",
            "password": "password123",
            "nombre": "Carlos",
            "apellido": "García",
            "telefono": "555-0101",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "dra.martinez@medilink.com",
            "password": "password123",
            "nombre": "Ana",
            "apellido": "Martínez",
            "telefono": "555-0102",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "dr.lopez@medilink.com",
            "password": "password123",
            "nombre": "Roberto",
            "apellido": "López",
            "telefono": "555-0103",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        {
            "email": "dra.rodriguez@medilink.com",
            "password": "password123",
            "nombre": "Laura",
            "apellido": "Rodríguez",
            "telefono": "555-0104",
            "tipo_usuario": TipoUsuarioEnum.DOCTOR,
        },
        # Pacientes
        {
            "email": "maria.perez@email.com",
            "password": "password123",
            "nombre": "María",
            "apellido": "Pérez",
            "telefono": "555-0201",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "juan.hernandez@email.com",
            "password": "password123",
            "nombre": "Juan",
            "apellido": "Hernández",
            "telefono": "555-0202",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "laura.gonzalez@email.com",
            "password": "password123",
            "nombre": "Laura",
            "apellido": "González",
            "telefono": "555-0203",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        {
            "email": "carlos.ramirez@email.com",
            "password": "password123",
            "nombre": "Carlos",
            "apellido": "Ramírez",
            "telefono": "555-0204",
            "tipo_usuario": TipoUsuarioEnum.PACIENTE,
        },
        # Admin
        {
            "email": "admin@medilink.com",
            "password": "admin123",
            "nombre": "Admin",
            "apellido": "Sistema",
            "telefono": "555-0001",
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
            "cedula_profesional": "CED-001",
            "consultorio": "Consultorio Cardiológico Central",
            "direccion_consultorio": "Av. Reforma 123, Zona 10",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01010",
            "anos_experiencia": 12,
            "costo_consulta": 350.00,
            "duracion_cita_minutos": 45,
            "universidad": "Universidad de San Carlos",
            "biografia": "Cardiólogo con más de 10 años de experiencia en intervenciones cardíacas.",
            "acepta_seguro": True,
            "atiende_domicilio": False,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[1],
            "especialidad": EspecialidadEnum.PEDIATRIA,
            "cedula_profesional": "CED-002",
            "consultorio": "Clínica Pediátrica Infantil",
            "direccion_consultorio": "Calzada Roosevelt 456, Zona 7",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01007",
            "anos_experiencia": 8,
            "costo_consulta": 250.00,
            "duracion_cita_minutos": 30,
            "universidad": "Universidad Mariano Gálvez",
            "biografia": "Especialista en cuidado infantil y desarrollo pediátrico.",
            "acepta_seguro": True,
            "atiende_domicilio": True,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[2],
            "especialidad": EspecialidadEnum.DERMATOLOGIA,
            "cedula_profesional": "CED-003",
            "consultorio": "Centro Dermatológico Avanzado",
            "direccion_consultorio": "6a Avenida 7-89, Zona 9",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01009",
            "anos_experiencia": 15,
            "costo_consulta": 300.00,
            "duracion_cita_minutos": 40,
            "universidad": "Universidad Rafael Landívar",
            "biografia": "Experto en tratamientos dermatológicos y cuidado de la piel.",
            "acepta_seguro": False,
            "atiende_domicilio": False,
            "atiende_videollamada": True,
        },
        {
            "usuario": doctores_usuarios[3],
            "especialidad": EspecialidadEnum.MEDICINA_GENERAL,
            "cedula_profesional": "CED-004",
            "consultorio": "Consultorio Médico General",
            "direccion_consultorio": "10a Calle 12-34, Zona 1",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01001",
            "anos_experiencia": 10,
            "costo_consulta": 200.00,
            "duracion_cita_minutos": 30,
            "universidad": "Universidad Francisco Marroquín",
            "biografia": "Médico general con amplia experiencia en diagnóstico y tratamiento.",
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
            "direccion": "15 Avenida 8-45, Zona 10",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01010",
            "numero_seguro": "SEG-001234",
            "alergias": "Penicilina, Mariscos",
            "tipo_sangre": TipoSangreEnum.A_POSITIVO,
            "contacto_emergencia_nombre": "José Pérez",
            "contacto_emergencia_telefono": "555-1111",
        },
        {
            "usuario": pacientes_usuarios[1],
            "fecha_nacimiento": date(1990, 8, 22),
            "genero": GeneroEnum.MASCULINO,
            "direccion": "8a Calle 15-67, Zona 13",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01013",
            "numero_seguro": "SEG-005678",
            "alergias": "Ninguna",
            "tipo_sangre": TipoSangreEnum.O_POSITIVO,
            "contacto_emergencia_nombre": "María Hernández",
            "contacto_emergencia_telefono": "555-2222",
        },
        {
            "usuario": pacientes_usuarios[2],
            "fecha_nacimiento": date(1992, 3, 10),
            "genero": GeneroEnum.FEMENINO,
            "direccion": "12 Calle 1-25, Zona 15",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01015",
            "numero_seguro": "SEG-009876",
            "alergias": "Polvo, Ácaros",
            "tipo_sangre": TipoSangreEnum.B_NEGATIVO,
            "contacto_emergencia_nombre": "Carlos González",
            "contacto_emergencia_telefono": "555-3333",
        },
        {
            "usuario": pacientes_usuarios[3],
            "fecha_nacimiento": date(1988, 11, 30),
            "genero": GeneroEnum.MASCULINO,
            "direccion": "5a Avenida 12-89, Zona 9",
            "ciudad": "Ciudad de Guatemala",
            "estado": "Guatemala",
            "codigo_postal": "01009",
            "numero_seguro": "SEG-003456",
            "alergias": "Aspirina",
            "tipo_sangre": TipoSangreEnum.AB_POSITIVO,
            "contacto_emergencia_nombre": "Ana Ramírez",
            "contacto_emergencia_telefono": "555-4444",
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


def main():
    """Función principal del seeder"""
    print("🚀 Iniciando seeder de MediLink...")

    db = SessionLocal()
    try:
        # Limpiar base de datos
        clear_database()

        # Crear datos
        usuarios = create_usuarios(db)
        doctores = create_doctores(db, usuarios)
        pacientes = create_pacientes(db, usuarios)
        horarios = create_horarios(db, doctores)
        citas = create_citas(db, doctores, pacientes)

        print("\n🎉 Seeder completado exitosamente!")
        print(f"📊 Resumen:")
        print(f"   👥 Usuarios: {len(usuarios)}")
        print(f"   👨‍⚕️ Doctores: {len(doctores)}")
        print(f"   👤 Pacientes: {len(pacientes)}")
        print(f"   🕐 Horarios: {len(horarios)}")
        print(f"   📅 Citas: {len(citas)}")

        print("\n🔑 Credenciales de prueba:")
        print("   Doctores:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.DOCTOR:
                print(f"   - {usuario.email} / password123")

        print("\n   Pacientes:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.PACIENTE:
                print(f"   - {usuario.email} / password123")

        print("\n   Admin:")
        for usuario in usuarios:
            if usuario.tipo_usuario == TipoUsuarioEnum.ADMIN:
                print(f"   - {usuario.email} / admin123")

    except Exception as e:
        print(f"❌ Error en el seeder: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
