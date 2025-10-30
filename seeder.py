"""
Seeder para la base de datos de MediLink
Limpia y llena la BD con datos de prueba
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date

from app.core.database import SessionLocal, engine
from models import Base, Usuario, Paciente, Doctor, Cita
from models import TipoUsuarioEnum, EstadoCitaEnum, EspecialidadEnum, GeneroEnum
from app.core.auth import (
    hash_password,
)  # Importar la función de hash del sistema de autenticación


def limpiar_base_datos():
    """Elimina todas las tablas y las vuelve a crear"""
    print("🗑️  Limpiando base de datos...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos limpia y tablas creadas")


def crear_usuarios(db: Session):
    """Crea usuarios de prueba"""
    print("\n👥 Creando usuarios...")

    usuarios = [
        # Administrador
        Usuario(
            email="admin@medilink.com",
            password_hash=hash_password("admin123"),
            nombre="Admin",
            apellido="Sistema",
            telefono="5550000000",
            tipo_usuario=TipoUsuarioEnum.ADMIN,
            activo=True,
        ),
        # Doctores
        Usuario(
            email="maria.gonzalez@medilink.com",
            password_hash=hash_password("doctor123"),
            nombre="María",
            apellido="González",
            telefono="5551234567",
            tipo_usuario=TipoUsuarioEnum.DOCTOR,
            activo=True,
        ),
        Usuario(
            email="carlos.rodriguez@medilink.com",
            password_hash=hash_password("doctor123"),
            nombre="Carlos",
            apellido="Rodríguez",
            telefono="5551234568",
            tipo_usuario=TipoUsuarioEnum.DOCTOR,
            activo=True,
        ),
        Usuario(
            email="ana.martinez@medilink.com",
            password_hash=hash_password("doctor123"),
            nombre="Ana",
            apellido="Martínez",
            telefono="5551234569",
            tipo_usuario=TipoUsuarioEnum.DOCTOR,
            activo=True,
        ),
        Usuario(
            email="luis.lopez@medilink.com",
            password_hash=hash_password("doctor123"),
            nombre="Luis",
            apellido="López",
            telefono="5551234570",
            tipo_usuario=TipoUsuarioEnum.DOCTOR,
            activo=True,
        ),
        # Pacientes
        Usuario(
            email="juan.perez@email.com",
            password_hash=hash_password("paciente123"),
            nombre="Juan",
            apellido="Pérez",
            telefono="5559876543",
            tipo_usuario=TipoUsuarioEnum.PACIENTE,
            activo=True,
        ),
        Usuario(
            email="laura.sanchez@email.com",
            password_hash=hash_password("paciente123"),
            nombre="Laura",
            apellido="Sánchez",
            telefono="5559876544",
            tipo_usuario=TipoUsuarioEnum.PACIENTE,
            activo=True,
        ),
        Usuario(
            email="pedro.ramirez@email.com",
            password_hash=hash_password("paciente123"),
            nombre="Pedro",
            apellido="Ramírez",
            telefono="5559876545",
            tipo_usuario=TipoUsuarioEnum.PACIENTE,
            activo=True,
        ),
        Usuario(
            email="sofia.torres@email.com",
            password_hash=hash_password("paciente123"),
            nombre="Sofía",
            apellido="Torres",
            telefono="5559876546",
            tipo_usuario=TipoUsuarioEnum.PACIENTE,
            activo=True,
        ),
        Usuario(
            email="miguel.flores@email.com",
            password_hash=hash_password("paciente123"),
            nombre="Miguel",
            apellido="Flores",
            telefono="5559876547",
            tipo_usuario=TipoUsuarioEnum.PACIENTE,
            activo=True,
        ),
    ]

    db.add_all(usuarios)
    db.commit()

    print(f"✅ {len(usuarios)} usuarios creados")
    return usuarios


def crear_doctores(db: Session, usuarios: list):
    """Crea perfiles de doctores"""
    print("\n👨‍⚕️ Creando perfiles de doctores...")

    # Filtrar solo usuarios tipo doctor (IDs 2-5)
    doctores = [
        Doctor(
            usuario_id=2,
            especialidad=EspecialidadEnum.CARDIOLOGIA,
            cedula_profesional="CARD123456",
            consultorio="Hospital General, Torre A, Consultorio 301",
            horario_atencion="Lunes a Viernes 9:00-17:00",
            costo_consulta=1200.00,
        ),
        Doctor(
            usuario_id=3,
            especialidad=EspecialidadEnum.PEDIATRIA,
            cedula_profesional="PEDI789012",
            consultorio="Centro Médico Infantil, Piso 2",
            horario_atencion="Lunes a Viernes 10:00-18:00",
            costo_consulta=900.00,
        ),
        Doctor(
            usuario_id=4,
            especialidad=EspecialidadEnum.DERMATOLOGIA,
            cedula_profesional="DERM345678",
            consultorio="Clínica Dermatológica Especializada",
            horario_atencion="Martes a Sábado 8:00-14:00",
            costo_consulta=1100.00,
        ),
        Doctor(
            usuario_id=5,
            especialidad=EspecialidadEnum.MEDICINA_GENERAL,
            cedula_profesional="MEDI901234",
            consultorio="Consultorio Médico Familiar, Consultorio 5",
            horario_atencion="Lunes a Sábado 7:00-15:00",
            costo_consulta=700.00,
        ),
    ]

    db.add_all(doctores)
    db.commit()

    print(f"✅ {len(doctores)} doctores creados")
    return doctores


def crear_pacientes(db: Session, usuarios: list):
    """Crea perfiles de pacientes"""
    print("\n🏥 Creando perfiles de pacientes...")

    # Filtrar solo usuarios tipo paciente (IDs 6-10)
    pacientes = [
        Paciente(
            usuario_id=6,
            fecha_nacimiento=date(1990, 5, 15),
            genero=GeneroEnum.MASCULINO,
            direccion="Av. Insurgentes Sur 123, Col. Del Valle, CDMX",
            numero_seguro="NSS1234567890",
            alergias="Penicilina, Aspirina",
            tipo_sangre="O+",
        ),
        Paciente(
            usuario_id=7,
            fecha_nacimiento=date(1985, 8, 22),
            genero=GeneroEnum.FEMENINO,
            direccion="Paseo de la Reforma 456, Col. Juárez, CDMX",
            numero_seguro="NSS2345678901",
            alergias="Ninguna conocida",
            tipo_sangre="A+",
        ),
        Paciente(
            usuario_id=8,
            fecha_nacimiento=date(1978, 12, 10),
            genero=GeneroEnum.MASCULINO,
            direccion="Av. México 789, Col. Condesa, CDMX",
            numero_seguro="NSS3456789012",
            alergias="Polen, Ácaros del polvo",
            tipo_sangre="B+",
        ),
        Paciente(
            usuario_id=9,
            fecha_nacimiento=date(1995, 3, 8),
            genero=GeneroEnum.FEMENINO,
            direccion="Calle Durango 321, Col. Roma Norte, CDMX",
            numero_seguro="NSS4567890123",
            alergias="Mariscos, Frutos secos",
            tipo_sangre="AB+",
        ),
        Paciente(
            usuario_id=10,
            fecha_nacimiento=date(2000, 7, 25),
            genero=GeneroEnum.MASCULINO,
            direccion="Av. Presidente Masaryk 654, Col. Polanco, CDMX",
            numero_seguro="NSS5678901234",
            alergias="Ninguna conocida",
            tipo_sangre="O-",
        ),
    ]

    db.add_all(pacientes)
    db.commit()

    print(f"✅ {len(pacientes)} pacientes creados")
    return pacientes


def crear_citas(db: Session):
    """Crea citas de prueba"""
    print("\n📅 Creando citas...")

    hoy = datetime.now()

    citas = [
        # Citas pendientes (futuras)
        Cita(
            paciente_id=1,
            doctor_id=1,
            fecha_hora=hoy + timedelta(days=2, hours=10),
            motivo="Revisión de presión arterial elevada y ajuste de medicación para hipertensión",
            notas="Paciente reporta mareos ocasionales",
            estado=EstadoCitaEnum.PENDIENTE,
        ),
        Cita(
            paciente_id=2,
            doctor_id=2,
            fecha_hora=hoy + timedelta(days=3, hours=11),
            motivo="Consulta pediátrica por fiebre persistente de 39°C en niño de 5 años durante 3 días",
            notas="Madre menciona que el niño no quiere comer",
            estado=EstadoCitaEnum.PENDIENTE,
        ),
        Cita(
            paciente_id=3,
            doctor_id=3,
            fecha_hora=hoy + timedelta(days=5, hours=9),
            motivo="Evaluación de manchas rojizas en la piel del abdomen con comezón intensa",
            notas="Aparecieron hace 2 semanas, no mejoran",
            estado=EstadoCitaEnum.PENDIENTE,
        ),
        # Citas confirmadas
        Cita(
            paciente_id=4,
            doctor_id=4,
            fecha_hora=hoy + timedelta(days=1, hours=14),
            motivo="Chequeo médico general anual preventivo y revisión de análisis de laboratorio",
            notas="Traer estudios de laboratorio recientes (máximo 1 mes)",
            estado=EstadoCitaEnum.CONFIRMADA,
        ),
        Cita(
            paciente_id=5,
            doctor_id=1,
            fecha_hora=hoy + timedelta(days=7, hours=15),
            motivo="Seguimiento post-operatorio de cirugía de bypass coronario realizada hace 3 semanas",
            notas="Revisar herida quirúrgica y resultados de electrocardiograma",
            estado=EstadoCitaEnum.CONFIRMADA,
        ),
        Cita(
            paciente_id=1,
            doctor_id=2,
            fecha_hora=hoy + timedelta(days=10, hours=16),
            motivo="Control de vacunación y revisión de desarrollo físico infantil",
            notas="Aplicación de vacuna pentavalente",
            estado=EstadoCitaEnum.CONFIRMADA,
        ),
        # Citas completadas (pasadas)
        Cita(
            paciente_id=1,
            doctor_id=4,
            fecha_hora=hoy - timedelta(days=10, hours=-10),
            motivo="Consulta por dolor de garganta intenso, fiebre de 38.5°C y malestar general",
            diagnostico="Faringitis viral aguda",
            receta="Paracetamol 500mg cada 8 horas por 5 días, reposo en cama, abundantes líquidos",
            notas="Paciente respondió bien al tratamiento",
            estado=EstadoCitaEnum.COMPLETADA,
        ),
        Cita(
            paciente_id=2,
            doctor_id=3,
            fecha_hora=hoy - timedelta(days=15, hours=-11),
            motivo="Tratamiento dermatológico para acné facial persistente grado moderado",
            diagnostico="Acné vulgar moderado con lesiones inflamatorias",
            receta="Gel de peróxido de benzoilo 5% aplicar en rostro limpio 2 veces al día. Limpiador facial suave",
            notas="Evitar exposición solar excesiva. Cita de seguimiento en 4 semanas",
            estado=EstadoCitaEnum.COMPLETADA,
        ),
        Cita(
            paciente_id=3,
            doctor_id=4,
            fecha_hora=hoy - timedelta(days=20, hours=-14),
            motivo="Dolor abdominal recurrente en cuadrante inferior derecho con náuseas",
            diagnostico="Gastritis leve, probable estrés",
            receta="Omeprazol 20mg en ayunas por 14 días. Dieta blanda sin irritantes",
            notas="Recomendación de reducir estrés y mejorar hábitos alimenticios",
            estado=EstadoCitaEnum.COMPLETADA,
        ),
        # Citas canceladas
        Cita(
            paciente_id=3,
            doctor_id=2,
            fecha_hora=hoy + timedelta(days=4, hours=10),
            motivo="Aplicación de vacunas infantiles del esquema nacional",
            notas="Paciente canceló por viaje familiar imprevisto",
            estado=EstadoCitaEnum.CANCELADA,
        ),
        Cita(
            paciente_id=5,
            doctor_id=3,
            fecha_hora=hoy + timedelta(days=6, hours=12),
            motivo="Revisión de lunares y manchas en la piel por prevención",
            notas="Doctor canceló por conferencia médica. Reagendar",
            estado=EstadoCitaEnum.CANCELADA,
        ),
    ]

    db.add_all(citas)
    db.commit()

    print(f"✅ {len(citas)} citas creadas")
    return citas


def run_seeder():
    """Ejecuta el seeder completo"""
    print("\n" + "=" * 70)
    print("🌱 INICIANDO SEEDER DE MEDILINK".center(70))
    print("=" * 70)

    # Limpiar base de datos
    limpiar_base_datos()

    # Crear sesión
    db = SessionLocal()

    try:
        # Crear datos
        usuarios = crear_usuarios(db)
        doctores = crear_doctores(db, usuarios)
        pacientes = crear_pacientes(db, usuarios)
        citas = crear_citas(db)

        print("\n" + "=" * 70)
        print("✅ SEEDER COMPLETADO EXITOSAMENTE".center(70))
        print("=" * 70)

        print("\n📊 RESUMEN DE DATOS CREADOS:")
        print(f"   {'Usuarios:':<20} {len(usuarios)}")
        print(f"   {'├─ Administradores:':<20} 1")
        print(f"   {'├─ Doctores:':<20} {len(doctores)}")
        print(f"   {'└─ Pacientes:':<20} {len(pacientes)}")
        print(f"   {'Citas totales:':<20} {len(citas)}")
        print(
            f"   {'├─ Pendientes:':<20} {sum(1 for c in citas if c.estado == EstadoCitaEnum.PENDIENTE)}"
        )
        print(
            f"   {'├─ Confirmadas:':<20} {sum(1 for c in citas if c.estado == EstadoCitaEnum.CONFIRMADA)}"
        )
        print(
            f"   {'├─ Completadas:':<20} {sum(1 for c in citas if c.estado == EstadoCitaEnum.COMPLETADA)}"
        )
        print(
            f"   {'└─ Canceladas:':<20} {sum(1 for c in citas if c.estado == EstadoCitaEnum.CANCELADA)}"
        )

        print("\n" + "=" * 70)
        print("🔑 CREDENCIALES DE ACCESO PARA PRUEBAS".center(70))
        print("=" * 70)

        print("\n   👨‍💼 ADMINISTRADOR:")
        print("   " + "─" * 40)
        print("   📧 Email:    admin@medilink.com")
        print("   🔒 Password: admin123")
        print("   🎯 Rol:      Administrador del sistema")

        print("\n   👨‍⚕️ DOCTORES (4 disponibles):")
        print("   " + "─" * 40)
        print("   📧 Email:    maria.gonzalez@medilink.com")
        print("   🔒 Password: doctor123")
        print("   💼 Especialidad: Cardiología")
        print()
        print("   📧 Email:    carlos.rodriguez@medilink.com")
        print("   🔒 Password: doctor123")
        print("   💼 Especialidad: Pediatría")
        print()
        print("   📧 Email:    ana.martinez@medilink.com")
        print("   🔒 Password: doctor123")
        print("   💼 Especialidad: Dermatología")
        print()
        print("   📧 Email:    luis.lopez@medilink.com")
        print("   🔒 Password: doctor123")
        print("   💼 Especialidad: Medicina General")

        print("\n   👤 PACIENTES (5 disponibles):")
        print("   " + "─" * 40)
        print("   📧 Email:    juan.perez@email.com")
        print("   🔒 Password: paciente123")
        print()
        print("   📧 Email:    laura.sanchez@email.com")
        print("   🔒 Password: paciente123")
        print()
        print("   📧 Email:    pedro.ramirez@email.com")
        print("   🔒 Password: paciente123")

        print("\n" + "=" * 70)
        print("💡 SIGUIENTE PASO: Inicia el servidor con 'fastapi dev main.py'")
        print("   Accede a: http://127.0.0.1:8000/docs")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error durante el seeder: {str(e)}")
        print(f"   Tipo de error: {type(e).__name__}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
