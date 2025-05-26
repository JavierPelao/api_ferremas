# FERREMAS API

API REST para la ferretería **FERREMAS**, desarrollada en **FastAPI + MySQL**.
RECUERDEN DESCARGAR POSTMAN Y MYSQL Y MYSQL WORKBENCH 
## ✅ Integraciones ya realizadas

1. **Catálogo de productos disponibles en bodega** (`GET /productos`)
2. **Agregar, actualizar y eliminar productos** (`POST`, `PUT`, `DELETE /productos/{codigo}`)

## 🧠 Integraciones que faltan (por completar)

- [ ] **Sistema de pago para una venta** (puede ser simulado o integrar WebPay)
- [ ] **Conversión de divisas (CLP <-> USD)** usando la API del **Banco Central**

## 🚀 Cómo levantar el proyecto
"Recuerden instalar esto en un entorno virtual" = env\Scripts\activate 
Ponen el entorno virtual y luego ejecutan este pip
pip install -r requirements.txt 

Para ejecutar el proyecto en la terminal se inicia asi = uvicorn main:app --reload(todo esto dentro del entorno virtual)


### 1. Clonar este repositorio

```bash 
git clone https://github.com/JavierPelao/api_ferremas.git
cd api_ferremas
```

## 💱 API de Conversión de Moneda (CLP/USD)

(PARA UTILIZARLO CAMBIARLO A LA RAMA (branch) "Conversion de Divisas")

Esta API permite convertir montos entre pesos chilenos (CLP) y dólares estadounidenses (USD), utilizando la API del Banco Central de Chile

Despues de utilizar el comando "uvicorn main:app --reload" hay que abrir el postman poner:

Convertir de CLP a USD
(GET http://127.0.0.1:8000/convertir?monto=10000&moneda_origen=CLP)

Convertir de USD a CLP
(GET http://127.0.0.1:8000/convertir?monto=10&moneda_origen=USD)



