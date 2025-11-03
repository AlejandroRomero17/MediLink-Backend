"""
Script para recrear completamente la base de datos
USO: python reset_database.py

⚠️ ADVERTENCIA: Este script ELIMINARÁ TODOS LOS DATOS
Solo usar en desarrollo
"""

import sys
from sqlalchemy import text

# Importar configuración de base de datos
from app.core.database import engine
from app.models import Base


def reset_database():
    """Elimina y recrea todas las tablas"""

    print("=" * 60)
    print("🗑️  RESET DE BASE DE DATOS - MEDILINK")
    print("=" * 60)

    # Confirmar acción
    confirm = input(
        "\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos.\n¿Estás seguro? (escribe 'SI' para continuar): "
    )

    if confirm != "SI":
        print("\n❌ Operación cancelada.")
        sys.exit(0)

    try:
        print("\n📋 Eliminando todas las tablas...")

        # Deshabilitar foreign key checks temporalmente
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()

        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        print("   ✅ Tablas eliminadas correctamente")

        # Rehabilitar foreign key checks
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()

        print("\n📋 Creando nuevas tablas...")

        # Crear todas las tablas de nuevo
        Base.metadata.create_all(bind=engine)
        print("   ✅ Tablas creadas correctamente")

        print("\n" + "=" * 60)
        print("✅ BASE DE DATOS RECREADA EXITOSAMENTE")
        print("=" * 60)

        # Mostrar tablas creadas
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]

            print(f"\n📊 Tablas creadas ({len(tables)}):")
            for table in sorted(tables):
                print(f"   • {table}")

        print("\n✨ La base de datos está lista para usar.")
        print("   Puedes iniciar el servidor con: uvicorn main:app --reload\n")

    except Exception as e:
        print(f"\n❌ ERROR al recrear la base de datos:")
        print(f"   {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    reset_database()
