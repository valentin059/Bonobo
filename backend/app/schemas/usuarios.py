from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from .peliculas import PeliculaCache, EntradaDiarioOut


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


# nunca incluimos el password_hash en la respuesta
class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


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
    total_vistas: int
    seguidores: int = 0
    seguidos: int = 0
    yo_sigo: Optional[bool] = None
    xp_total: int = 0
    nivel: int = 1
    logros: list[LogroOut] = []
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=250)
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    password_actual: str
    password_nueva: str = Field(..., min_length=8)

    @field_validator('avatar_url')
    @classmethod
    def validar_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('La URL del avatar debe empezar por http:// o https://')
        return v


class VistaConPelicula(BaseModel):
    id: int
    id_pelicula: int
    puntuacion: Optional[int] = None
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)


class FavoritaOut(BaseModel):
    orden: int
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)
