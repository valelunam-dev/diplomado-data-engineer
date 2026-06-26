from fastapi import FastAPI
from fastapi import Query
from modulo5.apis.schemas import ProductoCreate, ProductoOut, ProductoUpdate
from datetime import datetime
from typing import List
from fastapi import HTTPException
from pydantic import BaseModel, field_validator

app = FastAPI(
    title='API de Productos USACH',
    version='0.1.0',
    description='API didáctica del Módulo 5'
)

PRODUCTOS = []  
_id = 0

@app.get('/')
def root():
    return {'status': 'ok', 'modulo': 5}

@app.get('/saludo/{nombre}')
def saludo(nombre: str):
    return {'mensaje': f'Hola, {nombre}'}

@app.post('/productos')
def crear_producto(p: ProductoCreate):
    global _id
    _id += 1
    nuevo = {**p.model_dump(), 'id': _id, 'creado_en': datetime.utcnow()}
    PRODUCTOS.append(nuevo)
    return nuevo

@app.get('/productos', response_model=List[ProductoOut])
def listar():
    return PRODUCTOS

@app.get('/productos/{pid}', response_model=ProductoOut)
def obtener(pid: int):
    for p in PRODUCTOS:
        if p['id'] == pid:
            return p
    raise HTTPException(404, detail='Producto no encontrado')

@app.patch('/productos/{pid}', response_model=ProductoOut)
def actualizar(pid: int, datos: ProductoUpdate):
    for p in PRODUCTOS:
        if p['id'] == pid:
            cambios = datos.model_dump(exclude_unset=True)
            p.update(cambios)
            return p
    raise HTTPException(404, 'Producto no encontrado')


@app.delete('/productos/{pid}', status_code=204)
def borrar(pid: int):
    global PRODUCTOS
    antes = len(PRODUCTOS)
    PRODUCTOS = [p for p in PRODUCTOS if p['id'] != pid]
    if len(PRODUCTOS) == antes:
        raise HTTPException(404, 'Producto no encontrado')


@app.get('/buscar')
def buscar(
    q: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    activos: bool = True #(true, 1, yes, True)
):
    return {
        'busqueda': q,
        'limite': limit,
        'offset': offset,
        'activos': activos,
    }

class ProductoCreate(BaseModel):
    nombre: str
    precio: float
    stock: int
 
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Nombre muy corto')
        return v
