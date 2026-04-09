from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional


# Datos básicos de una película tal como los guardamos en nuestra BD (caché de TMDB)
class PeliculaCache(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None


# Datos para puntuar una película (del 1 al 10)
class PuntuacionCreate(BaseModel):
    puntuacion: int = Field(..., ge=1, le=10)   # ge=1 (mayor o igual a 1), le=10 (menor o igual a 10)


# Datos para crear una nueva entrada en el diario
class EntradaDiarioCreate(BaseModel):
    fecha_visionado: date             # fecha en que se vio la película
    resena: Optional[str] = None      # texto de la reseña (opcional)


# Datos para editar una entrada existente del diario (todos los campos son opcionales)
class EntradaDiarioUpdate(BaseModel):
    fecha_visionado: Optional[date] = None
    resena: Optional[str] = None


# Datos de una entrada de diario que devuelve la API
class EntradaDiarioOut(BaseModel):
    id: int
    id_usuario: int
    id_pelicula: int
    fecha_visionado: date
    resena: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# Datos de una vista que devuelve la API
class VistaOut(BaseModel):
    id: int
    id_usuario: int
    id_pelicula: int
    puntuacion: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# Estado de una película para el usuario autenticado.
# Indica si la tiene vista, puntuada, con me gusta o en watchlist.
class EstadoUsuarioPelicula(BaseModel):
    vista: bool = False
    puntuacion: Optional[int] = None
    me_gusta: bool = False
    en_watchlist: bool = False


# Datos de una persona del reparto de una película
class PersonaCast(BaseModel):
    nombre: Optional[str] = None
    personaje: Optional[str] = None   # personaje que interpreta
    foto: Optional[str] = None        # URL de la foto del actor


# Resumen de una película para mostrar en listados
class PeliculaResumen(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    descripcion: Optional[str] = None


# Película en cartelera (añade la puntuación de TMDB)
class PeliculaCartelera(PeliculaResumen):
    puntuacion: Optional[float] = None   # valoración media en TMDB


# Próximo estreno (añade la fecha exacta de estreno)
class PeliculaEstreno(PeliculaResumen):
    fecha_exacta: Optional[str] = None   # formato "YYYY-MM-DD"


# Respuesta paginada para búsquedas de películas
class PaginadoPeliculas(BaseModel):
    results: list[PeliculaResumen]
    total: int    # total de resultados en TMDB (no solo los de esta página)
    page: int     # página actual


# Respuesta paginada para la cartelera
class PaginadoCartelera(BaseModel):
    results: list[PeliculaCartelera]
    total: int
    page: int


# Respuesta paginada para próximos estrenos
class PaginadoEstrenos(BaseModel):
    results: list[PeliculaEstreno]
    total: int
    page: int


# Datos para crear una lista de películas
class ListaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    es_publica: bool = True    # por defecto la lista es pública


# Datos para editar una lista (todos opcionales, solo se actualiza lo que se envíe)
class ListaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    es_publica: Optional[bool] = None


# Resumen de una lista para mostrar en listados
class ListaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    es_publica: bool
    total_peliculas: int = 0   # número de películas que contiene
    created_at: datetime


# Detalle completo de una lista, incluyendo las películas que contiene
class ListaDetalle(BaseModel):
    id: int
    id_usuario: int
    username: str           # nombre del creador de la lista
    nombre: str
    descripcion: Optional[str] = None
    es_publica: bool
    peliculas: list[PeliculaCache]   # las películas de la lista
    total_peliculas: int = 0


# Datos para crear un comentario en una reseña
class ComentarioCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=1000)


# Datos de un comentario que devuelve la API
class ComentarioOut(BaseModel):
    id: int
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    texto: str
    created_at: datetime


# Reseña de un amigo (usuario seguido) para una película concreta
class ResenaAmigo(BaseModel):
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    puntuacion: Optional[int] = None
    ultima_resena: Optional[str] = None      # primeros 200 caracteres de su última reseña
    ultima_entrada_id: Optional[int] = None  # id de esa entrada de diario
    total_entradas: int = 0                  # cuántas veces ha visto esta película


# Reseña de cualquier usuario de la comunidad (para la sección de reseñas generales)
class ResenaGeneral(BaseModel):
    id: int                         # id de la entrada de diario
    id_usuario: int
    username: str
    avatar_url: Optional[str] = None
    fecha_visionado: date
    resena: Optional[str] = None
    puntuacion: Optional[int] = None
    total_likes: int = 0
    total_comentarios: int = 0
    yo_di_like: Optional[bool] = None   # si el usuario autenticado ya le dio like (None si no hay sesión)


# Detalle de una entrada de diario con sus contadores sociales
class EntradaDiarioDetalle(BaseModel):
    id: int
    fecha_visionado: date
    resena: Optional[str] = None
    created_at: datetime
    total_likes: int = 0
    total_comentarios: int = 0


# Detalle completo de una película obtenida de TMDB
class PeliculaDetalle(BaseModel):
    tmdb_id: int
    titulo: Optional[str] = None
    poster_url: Optional[str] = None
    anio_estreno: Optional[int] = None
    descripcion: Optional[str] = None
    generos: list[str] = []                              # lista de géneros ("Acción", "Drama"...)
    duracion: Optional[int] = None                       # duración en minutos
    puntuacion: Optional[float] = None                   # valoración media en TMDB
    reparto: list[PersonaCast] = []                      # primeros 10 actores
    estado_usuario: Optional[EstadoUsuarioPelicula] = None  # None si el usuario no está logueado
