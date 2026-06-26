from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
 
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./productos.db')
# En producción:  postgresql+psycopg2://user:pass@host:5432/db
 
connect_args = {'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
 
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
 
def get_db():
    """Dependencia FastAPI: una sesión por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
