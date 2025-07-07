from fastapi.testclient import TestClient
from main import app
import respx
from httpx import Response
import requests
import pytest

client = TestClient(app)

def test_get_productos():
    response = client.get("/productos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_post_producto():
    data = {
        "codigo": "TST123",
        "nombre": "Producto de prueba",
        "marca": "MarcaTest",
        "precio": 9990,
        "stock": 10
    }
    response = client.post("/productos", json=data)
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Producto agregado correctamente"

def test_put_producto():
    data_actualizado = {
        "nombre": "Producto actualizado",
        "marca": "MarcaActualizada",
        "precio": 14990,
        "stock": 20
    }
    response = client.put("/productos/TST123", json=data_actualizado)
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Producto actualizado correctamente"

def test_delete_producto():
    response = client.delete("/productos/TST123")
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Producto eliminado correctamente"


def test_post_solicitud():
    data = {
        "codigo_producto": "TST123",
        "cantidad": 5,
        "sucursal": "Santiago"
    }
    response = client.post("/solicitudes", json=data)
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Solicitud creada correctamente"


RESPUESTA_BANCO_CENTRAL_OK = {
    "Series": {
        "Obs": [{"value": "950.00"}]
    }
}

# Revisa si el Banco Central está disponible
def banco_central_disponible():
    try:
        url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        response = requests.get(url, timeout=3)
        return response.status_code == 200
    except:
        return False
    
# Fixture para omitir pruebas si el Banco Central no está disponible
@pytest.fixture(scope="module")
def skip_si_banco_no_esta_operando():
    if not banco_central_disponible():
        pytest.skip("Banco Central no disponible: se omiten pruebas dependientes")

# USD a CLP
@respx.mock
def test_usd_a_clp(skip_si_banco_no_esta_operando):
    respx.get().mock(return_value=Response(200, json=RESPUESTA_BANCO_CENTRAL_OK))
    response = client.get("/convertir?monto=1&moneda_origen=USD")
    assert response.status_code == 200
    assert response.json()["moneda_destino"] == "CLP"

# CLP a USD
@respx.mock
def test_clp_a_usd(skip_si_banco_no_esta_operando):
    respx.get().mock(return_value=Response(200, json=RESPUESTA_BANCO_CENTRAL_OK))
    response = client.get("/convertir?monto=950&moneda_origen=CLP")
    assert response.status_code == 200
    assert response.json()["moneda_destino"] == "USD"

# Monto ≤ 0
def test_monto_cero():
    response = client.get("/convertir?monto=0&moneda_origen=USD")
    assert response.status_code == 422  # FastAPI valida monto > 0

# Moneda no soportada
def test_moneda_invalida():
    response = client.get("/convertir?monto=100&moneda_origen=EUR")
    assert response.status_code == 422  # Regex valida CLP o USD

# Error del Banco Central (HTTP 500 simulado)
@respx.mock
def test_error_banco_central(skip_si_banco_no_esta_operando):
    respx.get().mock(return_value=Response(500, text="Internal Server Error"))
    response = client.get("/convertir?monto=100&moneda_origen=USD")
    assert response.status_code == 500
    assert "Error al obtener datos" in response.json()["detail"]

# Moneda en minúsculas (usd o clp)
@respx.mock
def test_moneda_minuscula(skip_si_banco_no_esta_operando):
    respx.get().mock(return_value=Response(200, json=RESPUESTA_BANCO_CENTRAL_OK))
    response = client.get("/convertir?monto=1000&moneda_origen=clp")
    assert response.status_code == 200
    assert response.json()["moneda_origen"] == "CLP"