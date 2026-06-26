from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base
 
class Producto(Base):
    __tablename__ = 'productos'
 
    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String(120), nullable=False, index=True)
    precio    = Column(Float, nullable=False)
    stock     = Column(Integer, default=0)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
