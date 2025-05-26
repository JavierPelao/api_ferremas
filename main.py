from datetime import date
from fastapi import FastAPI, HTTPException, Query
from db import get_connection
from pydantic import BaseModel
import requests

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

#Conversion de divisas CLP a USD y viceversa
USER = "fr.manriquezf@duocuc.cl"
PASS = "Hola123"
SERIE = "F073.TCO.PRE.Z.D"  # Tipo de cambio dólar observado

def obtener_valor_dolar_observado():
    hoy = date.today().strftime("%Y-%m-%d")
    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        f"?user={USER}&pass={PASS}&firstdate={hoy}&lastdate={hoy}"
        f"&timeseries={SERIE}&function=GetSeries"
    )

    resp = requests.get(url)
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
def convertir(monto: float = Query(..., gt=0), moneda_origen: str = Query(..., pattern="^(CLP|USD)$")):
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