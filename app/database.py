

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {
    "pool_pre_ping": True,   
    "pool_recycle": 300,     
}

if DATABASE_URL.startswith("sqlite"):
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        **engine_kwargs,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        **engine_kwargs,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
