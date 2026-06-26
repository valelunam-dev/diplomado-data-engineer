from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import modulo5.apis.models as models, modulo5.apis.schemas as schemas, modulo5.apis.crud as crud
from modulo5.apis.database import engine, get_db
models.Base.metadata.create_all(bind=engine) 
app = FastAPI(title='API Productos M5')
@app.post('/productos', response_model=schemas.ProductoOut, status_code=201)
def crear(p: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return crud.crear(db, p)

@app.get('/productos/{page}', response_model=List[schemas.ProductoOut])
def listar(page: int, limit: int = 20, db: Session = Depends(get_db)):
    skip = 20 * page
    return crud.listar(db, skip, limit)
@app.get('/productos/buscar', response_model=List[schemas.ProductoOut])
def buscar(q: str, db: Session = Depends(get_db)):
    return crud.buscar(db, q)
@app.get('/productos/{pid}', response_model=schemas.ProductoOut)
def obtener(pid: int, db: Session = Depends(get_db)):
    obj = crud.obtener(db, pid)
    if not obj:
        raise HTTPException(404, 'Producto no encontrado')
    return obj
@app.patch('/productos/{pid}', response_model=schemas.ProductoOut)
def actualizar(pid: int, datos: schemas.ProductoUpdate,
               db: Session = Depends(get_db)):
    obj = crud.actualizar(db, pid, datos)
    if not obj:
        raise HTTPException(404, 'Producto no encontrado')
    return obj
@app.delete('/productos/{pid}', status_code=204)
def borrar(pid: int, db: Session = Depends(get_db)):
    if not crud.borrar(db, pid):
        raise HTTPException(404, 'Producto no encontrado')