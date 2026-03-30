from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from typing import Optional
from .peliculas import PeliculaCache, EntradaDiarioOut

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

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

class UserProfile(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    total_vistas: int
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class VistaConPelicula(BaseModel):
    id: int
    puntuacion: Optional[int] = None
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)

class FavoritaOut(BaseModel):
    orden: int
    pelicula: PeliculaCache
    model_config = ConfigDict(from_attributes=True)