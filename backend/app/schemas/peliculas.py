from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
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
    puntuacion: Optional[int] = Field(None, ge=1, le=10)


class EntradaDiarioUpdate(BaseModel):
    fecha_visionado: Optional[date] = None
    resena: Optional[str] = None
    puntuacion: Optional[int] = Field(None, ge=1, le=10)


class EntradaDiarioOut(BaseModel):
    id: int
    id_usuario: int
    id_pelicula: int
    fecha_visionado: date
    resena: Optional[str] = None
    puntuacion: Optional[int] = None
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


class PersonaCast(BaseModel):
    nombre: Optional[str] = None
    personaje: Optional[str] = None
    foto: Optional[str] = None
    person_id: Optional[int] = None


class PersonaCrew(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    departamento: Optional[str] = None
    foto: Optional[str] = None
    person_id: Optional[int] = None


class PeliculaPersona(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    personaje: Optional[str] = None
    rol: Optional[str] = None


class PersonaDetalle(BaseModel):
    person_id: int
    nombre: str
    foto_url: Optional[str] = None
    biografia: Optional[str] = None
    conocido_por: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    lugar_nacimiento: Optional[str] = None
    filmografia: list[PeliculaPersona] = []


class PeliculaResumen(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    descripcion: Optional[str] = None


class PeliculaCartelera(PeliculaResumen):
    puntuacion: Optional[float] = None


class PeliculaEstreno(PeliculaResumen):
    fecha_exacta: Optional[str] = None


class PaginadoPeliculas(BaseModel):
    results: list[PeliculaResumen]
    total: int
    page: int


class PaginadoCartelera(BaseModel):
    results: list[PeliculaCartelera]
    total: int
    page: int


class PaginadoEstrenos(BaseModel):
    results: list[PeliculaEstreno]
    total: int
    page: int


class ListaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    es_publica: bool = True


class ListaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    es_publica: Optional[bool] = None


class ListaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    es_publica: bool
    total_peliculas: int = 0
    created_at: datetime


class ListaDetalle(BaseModel):
    id: int
    id_usuario: int
    username: str
    nombre: str
    descripcion: Optional[str] = None
    es_publica: bool
    peliculas: list[PeliculaCache]
    total_peliculas: int = 0


class ComentarioCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=1000)


class ComentarioOut(BaseModel):
    id: int
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    texto: str
    created_at: datetime


class ResenaAmigo(BaseModel):
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    puntuacion: Optional[int] = None
    ultima_resena: Optional[str] = None
    ultima_entrada_id: Optional[int] = None
    total_entradas: int = 0


class ResenaGeneral(BaseModel):
    id: int
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    fecha_visionado: date
    resena: Optional[str] = None
    puntuacion: Optional[int] = None
    total_likes: int = 0
    total_comentarios: int = 0
    yo_di_like: Optional[bool] = None


class EntradaDiarioDetalle(BaseModel):
    id: int
    fecha_visionado: date
    resena: Optional[str] = None
    puntuacion: Optional[int] = None
    created_at: datetime
    total_likes: int = 0
    total_comentarios: int = 0


class PeliculaDetalle(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    titulo_original: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    descripcion: Optional[str] = None
    generos: list[str] = []
    duracion: Optional[int] = None
    puntuacion: Optional[float] = None
    reparto: list[PersonaCast] = []
    crew: list[PersonaCrew] = []
    productoras: list[str] = []
    paises: list[str] = []
    idioma_original: Optional[str] = None
    presupuesto: Optional[int] = None
    recaudacion: Optional[int] = None
    estado_usuario: Optional[EstadoUsuarioPelicula] = None
