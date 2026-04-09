from pydantic_settings import BaseSettings, SettingsConfigDict

# Esta clase lee automáticamente las variables del archivo .env
# y las hace disponibles en toda la aplicación como settings.nombre_variable.
# Si falta alguna variable obligatoria en .env, la app lanza un error al arrancar.
class Settings(BaseSettings):
    # Datos de conexión a la base de datos PostgreSQL
    database_hostname: str
    database_port: str
    database_name: str
    database_username: str
    database_password: str

    # Configuración para los tokens JWT (autenticación)
    secret_key: str               # clave secreta para firmar los tokens
    algorithm: str                # algoritmo de firma (normalmente "HS256")
    access_token_expire_minutes: int  # minutos que dura un token antes de expirar

    # Token de acceso a la API de TMDB (base de datos de películas)
    tmdb_token: str

    # Le decimos a pydantic que lea las variables desde el archivo .env
    model_config = SettingsConfigDict(env_file=".env")

# Instancia global con todos los ajustes ya cargados.
# Se importa en otros archivos como: from .config import settings
settings = Settings()