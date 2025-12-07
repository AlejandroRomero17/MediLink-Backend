# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"  # Cambia por tu URL de producción


def test_endpoints():
    print("🔍 Probando endpoints de la API...")

    # 1. Health check
    print("\n1. Health Check:")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # 2. Métricas
    print("\n2. Métricas del sistema:")
    response = requests.get(f"{BASE_URL}/api/metrics/system")
    print(f"   Status: {response.status_code}")

    # 3. Métricas de uso
    print("\n3. Métricas de uso:")
    response = requests.get(f"{BASE_URL}/api/metrics/usage?days=7")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Citas totales: {data['appointments']['total']}")
        print(f"   Usuarios nuevos: {data['users']['total']}")

    # 4. Incidencias stats
    print("\n4. Estadísticas de incidencias:")
    response = requests.get(f"{BASE_URL}/api/incidents/stats")
    print(f"   Status: {response.status_code}")

    # 5. Documentación
    print("\n5. Documentación Swagger:")
    print(f"   Disponible en: {BASE_URL}/docs")

    print("\n✅ Todas las pruebas completadas!")


if __name__ == "__main__":
    test_endpoints()
