from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import JWTError, jwt
import httpx
from .. import services, schemas, models, database
from ..config import settings

router = APIRouter(
    prefix="/api/peliculas",
    tags=["Películas"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/auth/login', auto_error=False)


def get_optional_user(token: str = Depends(oauth2_scheme),
                      db: Session = Depends(database.get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        user = db.execute(select(models.Usuario).where(
            models.Usuario.id == user_id
        )).scalar_one_or_none()
        return user
    except JWTError:
        return None


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


@router.get("/{tmdb_id}", response_model=schemas.PeliculaDetalle)
def obtener_detalle(tmdb_id: int,
                    db: Session = Depends(database.get_db),
                    current_user: models.Usuario = Depends(get_optional_user)):
    try:
        datos = services.obtener_detalle_pelicula(tmdb_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Película no encontrada.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="No se pudo obtener el detalle de la película.")

    estado = None
    if current_user:
        pelicula = db.execute(select(models.Pelicula).where(
            models.Pelicula.tmdb_id == tmdb_id
        )).scalar_one_or_none()

        if pelicula:
            vista = db.execute(select(models.Vista).where(
                models.Vista.id_usuario == current_user.id,
                models.Vista.id_pelicula == pelicula.id
            )).scalar_one_or_none()

            me_gusta = db.execute(select(models.MeGusta).where(
                models.MeGusta.id_usuario == current_user.id,
                models.MeGusta.id_pelicula == pelicula.id
            )).scalar_one_or_none()

            watchlist = db.execute(select(models.Watchlist).where(
                models.Watchlist.id_usuario == current_user.id,
                models.Watchlist.id_pelicula == pelicula.id
            )).scalar_one_or_none()

            estado = schemas.EstadoUsuarioPelicula(
                vista=vista is not None,
                puntuacion=vista.puntuacion if vista else None,
                me_gusta=me_gusta is not None,
                en_watchlist=watchlist is not None
            )
        else:
            estado = schemas.EstadoUsuarioPelicula()

    datos["estado_usuario"] = estado
    return datos