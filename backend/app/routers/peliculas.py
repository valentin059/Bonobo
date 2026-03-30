from fastapi import APIRouter, HTTPException, status
import httpx
from .. import services

router = APIRouter(
    prefix="/api/peliculas",
    tags=["Películas"]
)


@router.get("/buscar")
def buscar_peliculas(q: str, skip: int = 0, limit: int = 20):
    try:
        return services.buscar_peliculas(q, skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener resultados de TMDB. Inténtalo de nuevo."
        )


@router.get("/cartelera")
def obtener_cartelera(skip: int = 0, limit: int = 20):
    try:
        return services.obtener_cartelera(skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo obtener la cartelera. Inténtalo de nuevo."
        )


@router.get("/estrenos")
def obtener_estrenos(skip: int = 0, limit: int = 20):
    try:
        return services.obtener_estrenos(skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener los estrenos. Inténtalo de nuevo."
        )


@router.get("/{tmdb_id}")
def obtener_detalle(tmdb_id: int):
    try:
        return services.obtener_detalle_pelicula(tmdb_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Película no encontrada."
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo obtener el detalle de la película."
        )