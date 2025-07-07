# API Ferremas

API REST para la gestión de productos de ferretería, solicitudes, conversión de divisas (CLP/USD) usando la API del Banco Central de Chile, e integración de pagos con WebPay (Transbank). Desarrollada con FastAPI y MySQL.

---

## Tabla de Contenidos

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración de la Base de Datos](#configuración-de-la-base-de-datos)
- [Ejecución](#ejecución)
- [Integraciones y Endpoints](#integraciones-y-endpoints)
  - [Gestión de Productos](#gestión-de-productos)
  - [Solicitudes](#solicitudes)
  - [Conversión de Divisas (Banco Central)](#conversión-de-divisas-banco-central)
  - [Pagos con WebPay (Transbank)](#pagos-con-webpay-transbank)
- [Pruebas con Postman](#pruebas-con-postman)
- [Notas](#notas)

---

## Requisitos

- Python 3.11+
- MySQL Server
- Credenciales válidas para la API del Banco Central de Chile (para conversión de divisas)
- Cuenta de pruebas Transbank (para WebPay)

---

## Instalación

1. **Clona el repositorio:**

   ```sh
   git clone https://github.com/tu_usuario/api_ferremas.git
   cd api_ferremas
   ```

2. **Crea y activa un entorno virtual (opcional):**

   ```sh
   python -m venv env
   env\Scripts\activate
   ```

3. **Instala las dependencias:**

   ```sh
   pip install -r requirements.txt
   ```

---

## Configuración de la Base de Datos

1. **Crea la base de datos y tablas en MySQL:**

   ```sql
   CREATE DATABASE ferremas_db;
   USE ferremas_db;
   
   -- Tabla de creacion de productos
   CREATE TABLE productos (
       codigo VARCHAR(50) PRIMARY KEY,
       nombre VARCHAR(100),
       marca VARCHAR(100),
       precio FLOAT,
       stock INT
   
   
    -- Tabla solicitudes
    CREATE TABLE solicitudes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo_producto VARCHAR(20),
        cantidad INT,
        sucursal VARCHAR(100),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (codigo_producto) REFERENCES productos(codigo)

     -- Insertar producto de prueba
      INSERT INTO productos (codigo, nombre, marca, precio, stock)
      VALUES ('TST123', 'Producto de prueba', 'MarcaTest', 9990, 10)
    );
   ```

2. **Configura la conexión en `db.py`:**

   Asegúrate de que los datos de host, usuario, contraseña y base de datos sean correctos.

---

## Ejecución

1. **Inicia el servidor FastAPI:**

   ```sh
   uvicorn main:app --reload
   ```

2. **Accede a la documentación interactiva:**

   - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Integraciones y Endpoints

### Gestión de Productos

- **GET /productos**  
  Lista todos los productos.

- **POST /productos**  
  Agrega un producto.  
  _Body ejemplo:_
  ```json
  {
    "codigo": "P001",
    "nombre": "Martillo",
    "marca": "Truper",
    "precio": 3500,
    "stock": 20
  }
  ```

- **PUT /productos/{codigo}**  
  Actualiza un producto existente.

- **DELETE /productos/{codigo}**  
  Elimina un producto por código.

---

### Solicitudes

- **POST /solicitudes**  
  Crea una solicitud de producto.  
  _Body ejemplo:_
  ```json
  {
    "codigo_producto": "P001",
    "cantidad": 5,
    "sucursal": "Sucursal Centro"
  }
  ```

---

### Conversión de Divisas (Banco Central)

- **GET /convertir?monto=10000&moneda_origen=CLP**  
  Convierte entre CLP y USD usando el valor del dólar observado del Banco Central de Chile.  
  - `monto`: cantidad a convertir  
  - `moneda_origen`: "CLP" o "USD"  

  _Ejemplo de respuesta:_
  ```json
  {
    "monto_original": 10000,
    "moneda_origen": "CLP",
    "monto_convertido": 10.5,
    "moneda_destino": "USD",
    "tasa_actual": 950.0
  }
  ```

  > **Nota:** Debes tener credenciales válidas del Banco Central configuradas en `main.py`.

---

### Pagos con WebPay (Transbank)

Para la "url_webpay":

💡 Se va actualizando automáticamente cada cierto tiempo, lo cual se tiene que hacer "rapido".

💡 N° tarjeta: 4511 3466 6003 7060

💡 Rut: 11.111.111-1 / clave: 123

- **POST /webpay/crear**  
  Inicia una transacción de pago.  
  _Respuesta:_  
  ```json
  {
    "url_webpay": "http://localhost:8000/webpay/redirigir?token=...",
    "token": "..."
  }
  ```
  Accede a la URL para redirigir al usuario a WebPay.

- **POST /webpay/confirmar**  
  WebPay redirige aquí tras el pago.  
  _Body (form-data):_
  - `token_ws`: token entregado por WebPay

- **GET /webpay/estado?token=...**  
  Consulta el estado de una transacción.

- **POST /webpay/reembolso**  
  Realiza un reembolso.  
  _Body (form-data):_
  - `token`: token de la transacción
  - `amount`: monto a reembolsar

- **GET /webpay/redirigir?token=...**  
  Redirige automáticamente al formulario de pago de WebPay.

---

## Pruebas con Postman

1. Inicia el servidor con `uvicorn main:app --reload`.
2. Usa la URL base `http://127.0.0.1:8000`.
3. Prueba los endpoints desde Postman o desde `/docs`.

