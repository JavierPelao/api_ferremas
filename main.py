from fastapi import FastAPI, HTTPException
from db import get_connection
from pydantic import BaseModel

app = FastAPI()

# Definir la entra de los productos
class Producto(BaseModel):
    codigo: str
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
def actualizar_producto(codigo: str, producto: Producto):
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

#-------PAYPAL--------
# Configuración PayPal (reemplaza con tus datos)
paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": "AQJsUqE8-P0orUYjNNMjZ3_3tC-y8Txx47R028AC8_HQdbXJTM0mUrwZVLA-RU89HErsLkKty4VpIs0x",
    "client_secret": "EP4vZM6u1bKYLPBSAeukmJr76UngVhIXZQRF1ecPF9QtusHbB7UpQp60WgebZmTsSBvoEKdBjmLiV9sa"
})

class PagoRequest(BaseModel):
    total: str  # Ej: "10.00"
    currency: str = "USD"  # Por defecto USD
    descripcion: str = "Pago desde FastAPI con PayPal"

@app.post("/crear-pago")
def crear_pago(pago_request: PagoRequest):
    pago = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "http://localhost:8000/pago-exitoso",
            "cancel_url": "http://localhost:8000/pago-cancelado"
        },
        "transactions": [{
            "amount": {
                "total": pago_request.total,
                "currency": pago_request.currency
            },
            "description": pago_request.descripcion
        }]
    })

    if pago.create():
        for link in pago.links:
            if link.rel == "approval_url":
                return {"url_pago": link.href}
    else:
        raise HTTPException(status_code=500, detail=pago.error)

@app.get("/pago-exitoso")
def pago_exitoso(paymentId: str = Query(...), PayerID: str = Query(...)):
    pago = paypalrestsdk.Payment.find(paymentId)

    if pago.execute({"payer_id": PayerID}):
        monto = pago.transactions[0].amount.total
        estado = pago.state  # normalmente "approved"

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO ventas (id_pago, estado, monto) VALUES (%s, %s, %s)",
                    (paymentId, estado, monto)
                )
                conn.commit()
        finally:
            conn.close()

        return {"mensaje": "Pago aprobado y registrado en la tabla ventas"}
    else:
        raise HTTPException(status_code=500, detail=pago.error)
