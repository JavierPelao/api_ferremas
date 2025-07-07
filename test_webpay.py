from fastapi.testclient import TestClient
from main import app
import respx
from httpx import Response

client = TestClient(app)

@respx.mock
def test_crear_transaccion_webpay():
    mock_token = "fake-token-123"
    mock_url = "https://webpay3gint.transbank.cl/webpayserver/initTransaction"

    respx.post("https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.0/transactions").mock(
        return_value=Response(200, json={"token": mock_token, "url": mock_url})
    )

    response = client.post("/webpay/crear")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["token"] == mock_token
    assert json_data["url_webpay"].startswith("http://localhost:8000/webpay/redirigir")


@respx.mock
def test_redirigir_webpay():
    token = "fake-token-123"
    response = client.get(f"/webpay/redirigir?token={token}")
    assert response.status_code == 200
    assert "<form" in response.text
    assert "token_ws" in response.text


@respx.mock
def test_estado_pago_token_invalido():
    token = "token-invalido-123"

    respx.get(f"https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.0/transactions/{token}").mock(
        return_value=Response(404, json={"error": "Token no encontrado"})
    )

    response = client.get(f"/webpay/estado?token={token}")
    assert response.status_code == 404


@respx.mock
def test_reembolso_token_invalido():
    token = "token-invalido-123"

    respx.post(f"https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.0/transactions/{token}/refunds").mock(
        return_value=Response(400, json={"error": "Reembolso no permitido"})
    )

    response = client.post("/webpay/reembolso", data={
        "token": token,
        "amount": 15000
    })

    assert response.status_code == 400
