from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional


class PeliculaCache(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None

class PuntuacionCreate(BaseModel):
    puntuacion: int = Field(..., ge=1, le=10)

class EntradaDiarioCreate(BaseModel):
    fecha_visionado: date
    resena: Optional[str] = None

class EntradaDiarioUpdate(BaseModel):
    fecha_visionado: Optional[date] = None
    resena: Optional[str] = None

class EntradaDiarioOut(BaseModel):
    id: int
    id_usuario: int
    id_pelicula: int
    fecha_visionado: date
    resena: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class VistaOut(BaseModel):
    id: int
    id_usuario: int
    id_pelicula: int
    puntuacion: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class EstadoUsuarioPelicula(BaseModel):
    vista: bool = False
    puntuacion: Optional[int] = None
    me_gusta: bool = False
    en_watchlist: bool = False

class PeliculaDetalle(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    descripcion: Optional[str] = None
    generos: list[str] = []
    duracion: Optional[int] = None
    puntuacion: Optional[float] = None
    reparto: list[dict] = []
    estado_usuario: Optional[EstadoUsuarioPelicula] = None