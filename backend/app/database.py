from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}"
    f"/{settings.database_name}"
)

# pool_pre_ping=True hace un SELECT 1 antes de cada checkout para evitar
# que supabase nos pase una conexion ya cerrada (pasa cuando la app
# esta inactiva un rato).
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
