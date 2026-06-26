from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas
 
def crear(db: Session, p: schemas.ProductoCreate) -> models.Producto:
    obj = models.Producto(**p.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)   # trae id y creado_en generados por la BD
    return obj
 
def listar(db: Session, skip: int = 0, limit: int = 100):
    return (db.query(models.Producto)
              .order_by(models.Producto.id)
              .offset(skip).limit(limit).all())
 
def obtener(db: Session, pid: int):
    return db.query(models.Producto).filter(models.Producto.id == pid).first()
 
def buscar(db: Session, q: str):
    pat = f'%{q}%'
    return db.query(models.Producto).filter(
        models.Producto.nombre.ilike(pat)
    ).all()
 
def actualizar(db: Session, pid: int, datos: schemas.ProductoUpdate):
    obj = obtener(db, pid)
    if not obj:
        return None
    for k, v in datos.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
 
def borrar(db: Session, pid: int) -> bool:
    obj = obtener(db, pid)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
