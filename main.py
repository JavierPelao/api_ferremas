from datetime import date
from fastapi.responses import HTMLResponse


from fastapi import Form
import uuid
from fastapi import FastAPI, HTTPException, Query


from db import get_connection
from pydantic import BaseModel
import httpx


app = FastAPI()

# Definir la entra de los productos
class Producto(BaseModel):
    codigo: str
    nombre: str
    marca: str
    precio: float
    stock: int

class ProductoUpdate(BaseModel):
    nombre: str
    marca: str
    precio: float
    stock: int


# Get para listar los productos
@app.get("/productos")
def get_productos():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos")
            data = cursor.fetchall()
            return data
    finally:
        conn.close()

# Post para agregar los productos
@app.post("/productos")
def crear_productos(producto: Producto):
    conn = get_connection()
    try: 
        with conn.cursor() as cursor:
            #validar si existe el producto
            cursor.execute("SELECT * FROM productos WHERE codigo = %s", (producto.codigo,))
            existe = cursor.fetchone()
            if existe:
                raise HTTPException(status_code=400, detail="Producto ya existente")

            cursor.execute(
                "INSERT INTO productos (codigo, nombre, marca, precio, stock) VALUES (%s, %s, %s, %s, %s)",
                (producto.codigo, producto.nombre, producto.marca, producto.precio, producto.stock ))
            
            conn.commit()
            return {"mensaje": "Producto agregado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

#actualizar los productos
@app.put("/productos/{codigo}")
def actualizar_producto(codigo: str, producto: ProductoUpdate):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado")

            cursor.execute("""
                UPDATE productos SET nombre = %s, marca = %s, precio = %s, stock = %s
                WHERE codigo = %s
            """, (producto.nombre, producto.marca, producto.precio, producto.stock, codigo))
            conn.commit()
            return {"mensaje": "Producto actualizado correctamente"}
    finally:
        conn.close()


#Eliminar producto por código
@app.delete("/productos/{codigo}")
def eliminar_producto(codigo: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado")

            cursor.execute("DELETE FROM productos WHERE codigo = %s", (codigo,))
            conn.commit()
            return {"mensaje": "Producto eliminado correctamente"}
    finally:
        conn.close()


class SolicitudProducto(BaseModel):
    codigo_producto: str
    cantidad: int
    sucursal: str

@app.post("/solicitudes")
def crear_solicitud(solicitud: SolicitudProducto):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO solicitudes (codigo_producto, cantidad, sucursal) 
                VALUES (%s, %s, %s)
            """, (solicitud.codigo_producto, solicitud.cantidad, solicitud.sucursal))
            conn.commit()
            return {"mensaje": "Solicitud creada correctamente"}
    finally:
        conn.close()


#Conversion de divisas CLP a USD y viceversa
USER = "fr.manriquezf@duocuc.cl"
PASS = "Hola123"
SERIE = "F073.TCO.PRE.Z.D"  # Tipo de cambio dólar observado

def obtener_valor_dolar_observado():
    hoy = date.today()
    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        f"?user={USER}&pass={PASS}&firstdate={hoy}&lastdate={hoy}"
        f"&timeseries={SERIE}&function=GetSeries"
    )

    resp = httpx.get(url)
    print(f"Status: {resp.status_code}")
    print(f"Contenido:\n{resp.text}")

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al obtener datos del Banco Central")

    try:
        data = resp.json()
        obs_list = data.get("Series", {}).get("Obs", [])
        if not obs_list:
            raise HTTPException(status_code=404, detail="No hay valor disponible para hoy")
        valor = float(obs_list[0]["value"])
        return valor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando datos: {e}")

@app.get("/convertir")
def convertir(monto: float = Query(..., gt=0), moneda_origen: str = Query(..., pattern="^(CLP|USD|clp|usd)$")):
    tasa = obtener_valor_dolar_observado()

    if moneda_origen.upper() == "CLP":
        convertido = monto / tasa
        moneda_destino = "USD"
    else:
        convertido = monto * tasa
        moneda_destino = "CLP"

    return {
        "monto_original": monto,
        "moneda_origen": moneda_origen.upper(),
        "monto_convertido": round(convertido, 2),
        "moneda_destino": moneda_destino,
        "tasa_actual": tasa
    }

#------------------------------------
# Configuración PayPal

TBK_API_KEY_ID = '597055555532'
TBK_API_KEY_SECRET = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
WEBPAY_BASE_URL = 'https://webpay3gint.transbank.cl'  # Testing

import httpx  # en vez de requests

def webpay_request(data: dict, method: str, endpoint: str):
    headers = {
        'Tbk-Api-Key-Id': TBK_API_KEY_ID,
        'Tbk-Api-Key-Secret': TBK_API_KEY_SECRET,
        'Content-Type': 'application/json'
    }

    url = f"{WEBPAY_BASE_URL}{endpoint}"

    with httpx.Client() as client:
        response = client.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None
        )

    # Validación de código HTTP
    if not response.status_code // 100 == 2:  # si no es 2xx
        raise HTTPException(status_code=response.status_code, detail=f"Error de WebPay: {response.text}")

    try:
        return response.json()
    except:
        raise HTTPException(status_code=500, detail="Respuesta inválida de WebPay")

# Endpoint para iniciar la transacción
@app.post("/webpay/crear")
def crear_transaccion():
    buy_order = str(uuid.uuid4())[:12]
    session_id = str(uuid.uuid4())[:12]
    amount = 15000
    return_url = "http://localhost:8000/webpay/confirmar"

    data = {
        "buy_order": buy_order,
        "session_id": session_id,
        "amount": amount,
        "return_url": return_url
    }

    result = webpay_request(data, "POST", "/rswebpaytransaction/api/webpay/v1.0/transactions")

    if "token" in result and "url" in result:
        redireccion_url = f"http://localhost:8000/webpay/redirigir?token={result['token']}"
        return {
            "url_webpay": redireccion_url,
            "token": result["token"]
        }
    else:
        raise HTTPException(status_code=500, detail="Error al crear la transacción WebPay")

# Endpoint para confirmar el pago (WebPay redirige aquí con POST)
@app.post("/webpay/confirmar")
def confirmar_pago(token_ws: str = Form(...)):
    result = webpay_request(None, "PUT", f"/rswebpaytransaction/api/webpay/v1.0/transactions/{token_ws}")

    if result.get("status") == "AUTHORIZED":
        return {
            "mensaje": "Pago autorizado correctamente",
            "detalle": result
        }
    else:
        return {
            "mensaje": "Pago rechazado o con error",
            "detalle": result
        }

# Endpoint para obtener el estado de la transacción
@app.get("/webpay/estado")
def estado_pago(token: str):
    result = webpay_request(None, "GET", f"/rswebpaytransaction/api/webpay/v1.0/transactions/{token}")
    return result

# Endpoint para realizar un reembolso
@app.post("/webpay/reembolso")
def reembolso(token: str = Form(...), amount: int = Form(...)):
    data = {
        "amount": amount
    }

    result = webpay_request(data, "POST", f"/rswebpaytransaction/api/webpay/v1.0/transactions/{token}/refunds")

    if "type" in result and result["type"] == "NULLIFIED":
        return {"mensaje": "Reembolso exitoso", "detalle": result}
    else:
        return {"mensaje": "No se pudo procesar el reembolso", "detalle": result}
    

@app.get("/webpay/redirigir")
def redirigir_webpay(token: str):
    html_content = f"""
    <html>
        <body onload="document.forms[0].submit()">
            <form action="https://webpay3gint.transbank.cl/webpayserver/initTransaction" method="POST">
                <input type="hidden" name="token_ws" value="{token}">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)