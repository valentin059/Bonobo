from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from .peliculas import PeliculaCache, EntradaDiarioOut

# Los schemas de Pydantic definen la forma de los datos que entran y salen de la API.
# "Create" = datos que recibe la API del cliente.
# "Out" = datos que devuelve la API al cliente.


# Datos necesarios para registrar un nuevo usuario
class UserCreate(BaseModel):
    email: EmailStr                          # valida automáticamente que sea un email real
    username: str = Field(..., min_length=3) # mínimo 3 caracteres
    password: str = Field(..., min_length=8) # mínimo 8 caracteres


# Datos del usuario que devuelve la API tras registrarse o consultarse.
# Nunca incluimos el password_hash aquí.
class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)  # permite convertir objetos SQLAlchemy a este schema


# Datos para el login (no se usa directamente, el login usa OAuth2PasswordRequestForm)
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Respuesta que devuelve el endpoint de login con el token JWT
class Token(BaseModel):
    access_token: str   # el token JWT que el cliente debe guardar y enviar en cada petición
    token_type: str     # siempre "bearer"


# Datos internos que guardamos dentro del token JWT
class TokenData(BaseModel):
    id: Optional[int] = None   # id del usuario autenticado

    # Logro desbloqueado para mostrar en el perfil
class LogroOut(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    xp: int
    xp_reclamado: bool
    desbloqueado_el: datetime
    model_config = ConfigDict(from_attributes=True)


# Resumen mínimo de un usuario para mostrar en listas (seguidores, buscador...)
class UsuarioResumen(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    xp_total: int = 0   
    nivel: int = 1  
    model_config = ConfigDict(from_attributes=True)


# Perfil completo de un usuario para la página de perfil
class UserProfile(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    total_vistas: int              # cuántas películas ha marcado como vistas
    seguidores: int = 0
    seguidos: int = 0
    yo_sigo: Optional[bool] = None  # si el usuario autenticado sigue a este (None si no hay sesión)
    xp_total: int = 0          # Para mostrar en el perfil
    nivel: int = 1             # 
    logros: list[LogroOut] = [] # 
    model_config = ConfigDict(from_attributes=True)


# Datos que puede editar el usuario en su perfil
class UserUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=250)
    avatar_url: Optional[str] = None

    @field_validator('avatar_url')
    @classmethod
    def validar_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('La URL del avatar debe empezar por http:// o https://')
        return v


# Vista de una película con sus datos de película adjuntos (para mostrar en el perfil)
class VistaConPelicula(BaseModel):
    id: int
    id_pelicula: int             # id interno de la película en nuestra BD (necesario para cruzar con el diario)
    puntuacion: Optional[int] = None
    pelicula: PeliculaCache      # datos básicos de la película (tmdb_id, título, poster...)
    model_config = ConfigDict(from_attributes=True)


# Una película favorita con su posición en el perfil
class FavoritaOut(BaseModel):
    orden: int           # posición (1-4)
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)
