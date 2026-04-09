from datetime import datetime
import httpx
from ..config import settings
from ..schemas.peliculas import (
    PersonaCast, PeliculaResumen, PeliculaCartelera, PeliculaEstreno,
    PaginadoPeliculas, PaginadoCartelera, PaginadoEstrenos, PeliculaDetalle
)

# URL base de la API de TMDB y de sus imágenes
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"   # w500 = ancho de 500px
TMDB_TIMEOUT = 10.0   # segundos máximos de espera para cada petición a TMDB

# Cabeceras que enviamos en cada petición a TMDB (autenticación con token Bearer)
headers = {
    "Authorization": f"Bearer {settings.tmdb_token}",
    "accept": "application/json"
}


# Construye la URL completa de un poster a partir del path que devuelve TMDB.
# TMDB devuelve solo el path (ej: "/abc123.jpg"), nosotros añadimos la base.
def build_poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


# Extrae el año de una fecha en formato "YYYY-MM-DD".
# Devuelve None si la fecha es vacía o tiene un formato incorrecto.
def _parse_anio(release_date: str | None) -> int | None:
    if not release_date or len(release_date) < 4:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


# Busca películas en TMDB por texto libre.
# skip y limit permiten paginar los resultados.
def buscar_peliculas(query: str, skip: int = 0, limit: int = 20) -> PaginadoPeliculas:
    # TMDB trabaja con páginas de 20 resultados; calculamos qué página pedir
    page = (skip // 20) + 1
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        response = client.get(
            f"{TMDB_BASE_URL}/search/movie",
            headers=headers,
            params={"query": query, "language": "es-ES", "page": page}
        )
        response.raise_for_status()   # lanza excepción si TMDB devuelve error (4xx, 5xx)
        data = response.json()

    # Construimos la lista de resultados descartando películas sin id
    resultados = [
        PeliculaResumen(
            tmdb_id=movie["id"],
            titulo=movie.get("title"),
            poster_url=build_poster_url(movie.get("poster_path")),
            anio_estreno=_parse_anio(movie.get("release_date")),
            descripcion=movie.get("overview")
        )
        for movie in data.get("results", [])[:limit]
        if movie.get("id")
    ]

    return PaginadoPeliculas(
        results=resultados,
        total=data.get("total_results", 0),
        page=page
    )


# Obtiene las películas que están actualmente en cines (cartelera española).
# Las ordena de mayor a menor puntuación antes de devolverlas.
def obtener_cartelera(skip: int = 0, limit: int = 20) -> PaginadoCartelera:
    page = (skip // 20) + 1
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        response = client.get(
            f"{TMDB_BASE_URL}/movie/now_playing",
            headers=headers,
            params={"language": "es-ES", "page": page, "region": "ES"}
        )
        response.raise_for_status()
        data = response.json()

    resultados = [
        PeliculaCartelera(
            tmdb_id=movie["id"],
            titulo=movie.get("title"),
            poster_url=build_poster_url(movie.get("poster_path")),
            anio_estreno=_parse_anio(movie.get("release_date")),
            descripcion=movie.get("overview"),
            puntuacion=movie.get("vote_average")
        )
        for movie in data.get("results", [])
        if movie.get("id")
    ]

    # Ordenamos por puntuación descendente (las mejores primero)
    resultados.sort(key=lambda x: x.puntuacion or 0, reverse=True)

    return PaginadoCartelera(
        results=resultados[:limit],
        total=data.get("total_results", 0),
        page=page
    )


# Obtiene las películas próximas a estrenarse.
# Filtra las que tengan fecha de estreno igual o posterior a hoy,
# y las ordena por fecha de estreno (las más próximas primero).
def obtener_estrenos(skip: int = 0, limit: int = 20) -> PaginadoEstrenos:
    page = (skip // 20) + 1
    hoy = datetime.now().date()

    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        response = client.get(
            f"{TMDB_BASE_URL}/movie/upcoming",
            headers=headers,
            params={"language": "es-ES", "page": page, "region": "ES"}
        )
        response.raise_for_status()
        data = response.json()

    resultados = []
    for movie in data.get("results", []):
        if not movie.get("id"):
            continue
        fecha_str = movie.get("release_date")
        if not fecha_str:
            continue
        try:
            fecha_peli = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        # Solo incluimos películas que se estrenan hoy o en el futuro
        if fecha_peli >= hoy:
            resultados.append(PeliculaEstreno(
                tmdb_id=movie["id"],
                titulo=movie.get("title"),
                poster_url=build_poster_url(movie.get("poster_path")),
                anio_estreno=fecha_peli.year,
                descripcion=movie.get("overview"),
                fecha_exacta=fecha_str
            ))

    # Ordenamos por fecha de estreno (primero las más próximas)
    resultados.sort(key=lambda x: x.fecha_exacta or "")

    return PaginadoEstrenos(
        results=resultados[:limit],
        total=len(resultados),
        page=page
    )


# Obtiene el detalle completo de una película: info, géneros, duración y reparto.
# Hace dos peticiones a TMDB: una para los datos de la película y otra para los créditos.
def obtener_detalle_pelicula(tmdb_id: int) -> PeliculaDetalle:
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        # Primera petición: datos generales de la película
        detalle = client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            headers=headers,
            params={"language": "es-ES"}
        )
        detalle.raise_for_status()

        # Segunda petición: reparto y equipo técnico
        creditos = client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            headers=headers,
            params={"language": "es-ES"}
        )
        creditos.raise_for_status()

    movie = detalle.json()
    cast = creditos.json().get("cast", [])[:10]   # solo los 10 primeros actores

    return PeliculaDetalle(
        tmdb_id=movie["id"],
        titulo=movie.get("title"),
        poster_url=build_poster_url(movie.get("poster_path")),
        anio_estreno=_parse_anio(movie.get("release_date")),
        descripcion=movie.get("overview"),
        generos=[g["name"] for g in movie.get("genres", []) if g.get("name")],
        duracion=movie.get("runtime"),
        puntuacion=movie.get("vote_average"),
        reparto=[
            PersonaCast(
                nombre=p.get("name"),
                personaje=p.get("character"),
                foto=build_poster_url(p.get("profile_path"))
            )
            for p in cast
        ]
    )
