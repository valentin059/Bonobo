from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# Construimos la URL de conexión a la base de datos PostgreSQL
# con los datos del archivo .env (usuario, contraseña, host, puerto, nombre de la BD)
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}:{settings.database_port}"
    f"/{settings.database_name}"
)

# El engine es el objeto que gestiona la conexión real con la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal es la fábrica de sesiones.
# Cada vez que queremos hacer una consulta, creamos una sesión nueva.
# autocommit=False: los cambios no se guardan automáticamente, hay que hacer db.commit()
# autoflush=False: no envía cambios a la BD antes de cada consulta
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredan todos los modelos (tablas de la BD)
Base = declarative_base()

# Función que nos da una sesión de base de datos.
# Se usa como dependencia en los endpoints con Depends(get_db).
# El yield asegura que la sesión se cierra siempre, aunque haya un error.
def get_db():
    db = SessionLocal()
    try:
        yield db       # entrega la sesión al endpoint
    finally:
        db.close()     # siempre cierra la sesión al terminar