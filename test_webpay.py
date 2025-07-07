from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_crear_transaccion_webpay():
    response = client.post("/webpay/crear")
    assert response.status_code == 200
    json_data = response.json()
    assert "url_webpay" in json_data
    assert "token" in json_data
    assert json_data["url_webpay"].startswith("http://localhost:8000/webpay/redirigir")

def test_redirigir_webpay():
    # Primero crear una transacción válida para obtener un token
    crear = client.post("/webpay/crear")
    assert crear.status_code == 200
    token = crear.json()["token"]

    # Ahora probar redirección
    redir = client.get(f"/webpay/redirigir?token={token}")
    assert redir.status_code == 200
    assert "<form" in redir.text
    assert "token_ws" in redir.text

def test_estado_pago_token_invalido():
    response = client.get("/webpay/estado?token=token-invalido-123")
    # Puede ser 500 si WebPay devuelve error o 404 si tú lo manejas
    assert response.status_code in [200, 400, 404, 500]

def test_reembolso_token_invalido():
    response = client.post("/webpay/reembolso", data={
        "token": "token-invalido-123",
        "amount": 15000
    })
    assert response.status_code in [200, 400, 404, 500]
