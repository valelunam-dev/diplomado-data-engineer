# schemas.py
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Literal
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    precio: float = Field(..., gt=0, description='Precio en CLP')
    stock:  int   = Field(0, ge=0)

class ProductoCreate(BaseModel):
    nombre: str
    precio: float
    stock: int
 
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        v = v.strip() # "  Iván   " -> "Iván"
        if len(v) < 2:
            raise ValueError('Nombre muy corto')
        return v
    
 


class ProductoUpdate(BaseModel):
    nombre: Optional[str]   = None
    precio: Optional[float] = Field(None, gt=0)
    stock:  Optional[int]   = Field(None, ge=0)


class ProductoOut(ProductoBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


