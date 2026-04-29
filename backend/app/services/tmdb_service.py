from datetime import datetime
import httpx
from ..config import settings
from ..schemas.peliculas import (
    PersonaCast, PersonaCrew, PeliculaResumen, PeliculaCartelera, PeliculaEstreno,
    PaginadoPeliculas, PaginadoCartelera, PaginadoEstrenos, PeliculaDetalle,
    PeliculaPersona, PersonaDetalle,
)

# Roles del crew que mostramos en la ficha de la peli, agrupados por departamento.
# Si TMDB devuelve un rol que no esta aqui, lo ignoramos.
CREW_ROLES = {
    "Directing":         {"Director"},
    "Writing":           {"Screenplay", "Story", "Writer", "Novel", "Characters", "Original Story"},
    "Camera":            {"Director of Photography"},
    "Editing":           {"Editor"},
    "Sound":             {"Original Music Composer"},
    "Production":        {"Producer"},
    "Art":               {"Production Designer"},
    "Costume & Make-Up": {"Costume Designer"},
    "Visual Effects":    {"Visual Effects Supervisor", "VFX Supervisor"},
    "Lighting":          {"Gaffer"},
}

TMDB_BASE_URL          = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL    = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"
TMDB_TIMEOUT           = 10.0

headers = {
    "Authorization": f"Bearer {settings.tmdb_token}",
    "accept": "application/json"
}


def url_poster(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


def url_backdrop(backdrop_path: str | None) -> str | None:
    if not backdrop_path:
        return None
    return f"{TMDB_BACKDROP_BASE_URL}{backdrop_path}"


def parsear_anio(release_date: str | None) -> int | None:
    # release_date viene como "YYYY-MM-DD". Si no esta o no se puede parsear, None.
    if not release_date or len(release_date) < 4:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


def buscar_peliculas(query: str, skip: int = 0, limit: int = 20) -> PaginadoPeliculas:
    page = (skip // 20) + 1
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        response = client.get(
            f"{TMDB_BASE_URL}/search/movie",
            headers=headers,
            params={"query": query, "language": "es-ES", "page": page}
        )
        response.raise_for_status()
        data = response.json()

    resultados = [
        PeliculaResumen(
            tmdb_id=movie["id"],
            titulo=movie.get("title"),
            poster_url=url_poster(movie.get("poster_path")),
            anio_estreno=parsear_anio(movie.get("release_date")),
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
            poster_url=url_poster(movie.get("poster_path")),
            anio_estreno=parsear_anio(movie.get("release_date")),
            descripcion=movie.get("overview"),
            puntuacion=movie.get("vote_average")
        )
        for movie in data.get("results", [])
        if movie.get("id")
    ]

    resultados.sort(key=lambda x: x.puntuacion or 0, reverse=True)

    return PaginadoCartelera(
        results=resultados[:limit],
        total=data.get("total_results", 0),
        page=page
    )


def _parsear_fecha_estreno(fecha_str: str | None):
    # convierte "YYYY-MM-DD" a date, o None si no parsea
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return None


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

    # filtramos las que tengan id, fecha valida y sean futuras (hoy o despues).
    # comprehension en vez de un for-with-continues para que sea mas declarativo.
    resultados = [
        PeliculaEstreno(
            tmdb_id=movie["id"],
            titulo=movie.get("title"),
            poster_url=url_poster(movie.get("poster_path")),
            anio_estreno=_parsear_fecha_estreno(movie.get("release_date")).year,
            descripcion=movie.get("overview"),
            fecha_exacta=movie.get("release_date")
        )
        for movie in data.get("results", [])
        if movie.get("id")
        and _parsear_fecha_estreno(movie.get("release_date")) is not None
        and _parsear_fecha_estreno(movie.get("release_date")) >= hoy
    ]

    resultados.sort(key=lambda x: x.fecha_exacta or "")

    return PaginadoEstrenos(
        results=resultados[:limit],
        total=len(resultados),
        page=page
    )


def obtener_detalle_pelicula(tmdb_id: int) -> PeliculaDetalle:
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
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

    movie         = detalle.json()
    creditos_data = creditos.json()
    cast_raw      = creditos_data.get("cast", [])[:15]
    crew_raw      = creditos_data.get("crew", [])

    reparto = [
        PersonaCast(
            nombre=p.get("name"),
            personaje=p.get("character"),
            foto=url_poster(p.get("profile_path")),
            person_id=p.get("id")
        )
        for p in cast_raw
    ]

    # crew filtrado por CREW_ROLES y deduplicado por (id, job).
    # un solo if compuesto, sin continues en el bucle interno.
    vistos = set()
    crew = []
    for dept, roles_permitidos in CREW_ROLES.items():
        for p in crew_raw:
            clave = (p.get("id"), p.get("job"))
            if (
                p.get("department") == dept
                and p.get("job") in roles_permitidos
                and clave not in vistos
            ):
                vistos.add(clave)
                crew.append(PersonaCrew(
                    nombre=p.get("name"),
                    rol=p.get("job"),
                    departamento=dept,
                    foto=url_poster(p.get("profile_path")),
                    person_id=p.get("id")
                ))

    return PeliculaDetalle(
        tmdb_id=movie["id"],
        titulo=movie.get("title"),
        titulo_original=movie.get("original_title"),
        poster_url=url_poster(movie.get("poster_path")),
        backdrop_url=url_backdrop(movie.get("backdrop_path")),
        anio_estreno=parsear_anio(movie.get("release_date")),
        descripcion=movie.get("overview"),
        generos=[g["name"] for g in movie.get("genres", []) if g.get("name")],
        duracion=movie.get("runtime"),
        puntuacion=movie.get("vote_average"),
        reparto=reparto,
        crew=crew,
        productoras=[c["name"] for c in movie.get("production_companies", []) if c.get("name")],
        paises=[c["name"] for c in movie.get("production_countries", []) if c.get("name")],
        idioma_original=movie.get("original_language"),
        presupuesto=movie.get("budget") or None,
        recaudacion=movie.get("revenue") or None,
    )


def obtener_persona(person_id: int) -> PersonaDetalle:
    with httpx.Client(timeout=TMDB_TIMEOUT) as client:
        persona_res = client.get(
            f"{TMDB_BASE_URL}/person/{person_id}",
            headers=headers,
            params={"language": "es-ES"}
        )
        persona_res.raise_for_status()

        creditos_res = client.get(
            f"{TMDB_BASE_URL}/person/{person_id}/movie_credits",
            headers=headers,
            params={"language": "es-ES"}
        )
        creditos_res.raise_for_status()

    persona  = persona_res.json()
    creditos = creditos_res.json()

    # combinamos cast y crew dedupeando por tmdb_id (cast manda).
    # primero metemos cast en el dict, luego crew solo si no esta ya.
    pelis: dict[int, PeliculaPersona] = {
        movie["id"]: PeliculaPersona(
            tmdb_id=movie["id"],
            titulo=movie.get("title"),
            poster_url=url_poster(movie.get("poster_path")),
            anio_estreno=parsear_anio(movie.get("release_date")),
            personaje=movie.get("character") or None,
        )
        for movie in creditos.get("cast", [])
        if movie.get("id")
    }

    for movie in creditos.get("crew", []):
        tid = movie.get("id")
        if tid and tid not in pelis:
            pelis[tid] = PeliculaPersona(
                tmdb_id=tid,
                titulo=movie.get("title"),
                poster_url=url_poster(movie.get("poster_path")),
                anio_estreno=parsear_anio(movie.get("release_date")),
                rol=movie.get("job") or None,
            )

    filmografia = sorted(
        [p for p in pelis.values() if p.anio_estreno],
        key=lambda x: x.anio_estreno or 0,
        reverse=True
    )[:60]

    return PersonaDetalle(
        person_id=persona["id"],
        nombre=persona.get("name", ""),
        foto_url=url_poster(persona.get("profile_path")),
        biografia=persona.get("biography") or None,
        conocido_por=persona.get("known_for_department") or None,
        fecha_nacimiento=persona.get("birthday") or None,
        lugar_nacimiento=persona.get("place_of_birth") or None,
        filmografia=filmografia,
    )
