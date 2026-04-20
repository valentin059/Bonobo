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


class UsuarioResumen(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    total_vistas: int
    seguidores: int = 0
    seguidos: int = 0
    yo_sigo: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=250)
    avatar_url: Optional[str] = None

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
