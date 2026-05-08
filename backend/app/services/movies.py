from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from .. import models
from . import obtener_detalle_pelicula


def get_or_create_pelicula(tmdb_id: int, db: Session) -> models.Pelicula:
    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    if pelicula:
        return pelicula

    # no esta en cache, pedimos a TMDB
    try:
        datos = obtener_detalle_pelicula(tmdb_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener los datos de la película"
        )

    pelicula = models.Pelicula(
        tmdb_id=tmdb_id,
        titulo=datos.titulo,
        poster_url=datos.poster_url,
        anio_estreno=datos.anio_estreno
    )
    db.add(pelicula)

    # si dos peticiones simultaneas crean la misma peli salta la UNIQUE de tmdb_id.
    # rollback y volvemos a leer la fila que ya esta
    try:
        db.commit()
        db.refresh(pelicula)
    except IntegrityError:
        db.rollback()
        pelicula = db.execute(
            select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
        ).scalar_one()

    return pelicula
