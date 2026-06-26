from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductoCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    active: bool = True


class ProductoOut(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None
    active: bool
    creado_en: datetime


class ProductoUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    active: Optional[bool] = None