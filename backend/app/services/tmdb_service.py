from datetime import datetime
import httpx
from ..config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

headers = {
    "Authorization": f"Bearer {settings.tmdb_token}",
    "accept": "application/json"
}


def build_poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


def buscar_peliculas(query: str, skip: int = 0, limit: int = 20) -> dict:
    page = (skip // 20) + 1
    with httpx.Client() as client:
        response = client.get(
            f"{TMDB_BASE_URL}/search/movie",
            headers=headers,
            params={"query": query, "language": "es-ES", "page": page}
        )
        response.raise_for_status()
        data = response.json()

    resultados = []
    for movie in data.get("results", [])[:limit]:
        resultados.append({
            "tmdb_id": movie["id"],
            "titulo": movie.get("title"),
            "poster_url": build_poster_url(movie.get("poster_path")),
            "anio_estreno": int(movie["release_date"][:4]) if movie.get("release_date") else None,
            "descripcion": movie.get("overview")
        })

    return {
        "results": resultados,
        "total": data.get("total_results", 0),
        "page": page
    }


def obtener_cartelera(skip: int = 0, limit: int = 20) -> dict:
    page = (skip // 20) + 1
    with httpx.Client() as client:
        response = client.get(
            f"{TMDB_BASE_URL}/movie/now_playing",
            headers=headers,
            params={"language": "es-ES", "page": page, "region": "ES"}
        )
        response.raise_for_status()
        data = response.json()

    resultados = []
    for movie in data.get("results", []):
        resultados.append({
            "tmdb_id": movie["id"],
            "titulo": movie.get("title"),
            "poster_url": build_poster_url(movie.get("poster_path")),
            "anio_estreno": int(movie["release_date"][:4]) if movie.get("release_date") else None,
            "descripcion": movie.get("overview"),
            "puntuacion": movie.get("vote_average")
        })

    resultados.sort(key=lambda x: x["puntuacion"] or 0, reverse=True)

    return {
        "results": resultados[:limit],
        "total": data.get("total_results", 0),
        "page": page
    }


def obtener_estrenos(skip: int = 0, limit: int = 20) -> dict:
    page = (skip // 20) + 1
    hoy = datetime.now().date()

    with httpx.Client() as client:
        response = client.get(
            f"{TMDB_BASE_URL}/movie/upcoming",
            headers=headers,
            params={"language": "es-ES", "page": page, "region": "ES"}
        )
        response.raise_for_status()
        data = response.json()

    resultados = []
    for movie in data.get("results", []):
        fecha_str = movie.get("release_date")
        if fecha_str:
            fecha_peli = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            if fecha_peli >= hoy:
                resultados.append({
                    "tmdb_id": movie["id"],
                    "titulo": movie.get("title"),
                    "poster_url": build_poster_url(movie.get("poster_path")),
                    "anio_estreno": fecha_peli.year,
                    "descripcion": movie.get("overview"),
                    "fecha_exacta": fecha_str
                })

    resultados.sort(key=lambda x: x["fecha_exacta"])

    return {
        "results": resultados[:limit],
        "total": len(resultados),
        "page": page
    }


def obtener_detalle_pelicula(tmdb_id: int) -> dict:
    with httpx.Client() as client:
        detalle = client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            headers=headers,
            params={"language": "es-ES"}
        )
        detalle.raise_for_status()

        creditos = client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            headers=headers,
            params={"language": "es-ES"}
        )
        creditos.raise_for_status()

    movie = detalle.json()
    cast = creditos.json().get("cast", [])[:10]

    return {
        "tmdb_id": movie["id"],
        "titulo": movie.get("title"),
        "poster_url": build_poster_url(movie.get("poster_path")),
        "anio_estreno": int(movie["release_date"][:4]) if movie.get("release_date") else None,
        "descripcion": movie.get("overview"),
        "generos": [g["name"] for g in movie.get("genres", [])],
        "duracion": movie.get("runtime"),
        "puntuacion": movie.get("vote_average"),
        "reparto": [
            {
                "nombre": p.get("name"),
                "personaje": p.get("character"),
                "foto": build_poster_url(p.get("profile_path"))
            }
            for p in cast
        ]
    }