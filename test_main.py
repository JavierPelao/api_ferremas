from fastapi.testclient import TestClient
from main import app

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
