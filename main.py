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
