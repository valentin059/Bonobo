from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import httpx
from typing import Optional
from .. import services, schemas, models, database, oauth2

router = APIRouter(
    prefix="/api/peliculas",
    tags=["Películas"]
)


@router.get("/buscar", response_model=schemas.PaginadoPeliculas)
def buscar_peliculas(q: str, skip: int = 0, limit: int = Query(20, ge=1, le=100)):
    try:
        return services.buscar_peliculas(q, skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener resultados de TMDB. Inténtalo de nuevo."
        )


@router.get("/cartelera", response_model=schemas.PaginadoCartelera)
def obtener_cartelera(skip: int = 0, limit: int = Query(20, ge=1, le=100)):
    try:
        return services.obtener_cartelera(skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo obtener la cartelera. Inténtalo de nuevo."
        )


@router.get("/estrenos", response_model=schemas.PaginadoEstrenos)
def obtener_estrenos(skip: int = 0, limit: int = Query(20, ge=1, le=100)):
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
                    current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):
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

    return datos.model_copy(update={"estado_usuario": estado})


@router.get("/{tmdb_id}/resenas/amigos", response_model=list[schemas.ResenaAmigo])
def get_resenas_amigos(tmdb_id: int,
                       db: Session = Depends(database.get_db),
                       current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    if not pelicula:
        return []

    seguidos_ids = db.execute(
        select(models.Seguidor.id_seguido).where(models.Seguidor.id_seguidor == current_user.id)
    ).scalars().all()

    if not seguidos_ids:
        return []

    result = []
    for user_id in seguidos_ids:
        vista = db.execute(
            select(models.Vista).where(
                models.Vista.id_usuario == user_id,
                models.Vista.id_pelicula == pelicula.id
            )
        ).scalar_one_or_none()

        if not vista:
            continue

        usuario = db.execute(
            select(models.Usuario).where(models.Usuario.id == user_id)
        ).scalar_one_or_none()

        entradas = db.execute(
            select(models.EntradaDiario)
            .where(
                models.EntradaDiario.id_usuario == user_id,
                models.EntradaDiario.id_pelicula == pelicula.id
            )
            .order_by(models.EntradaDiario.fecha_visionado.desc())
        ).scalars().all()

        ultima_resena = None
        ultima_entrada_id = None
        for entrada in entradas:
            if entrada.resena:
                ultima_resena = entrada.resena[:200]
                ultima_entrada_id = entrada.id
                break

        result.append(schemas.ResenaAmigo(
            id_usuario=user_id,
            username=usuario.username,
            avatar_url=usuario.avatar_url,
            puntuacion=vista.puntuacion,
            ultima_resena=ultima_resena,
            ultima_entrada_id=ultima_entrada_id,
            total_entradas=len(entradas)
        ))

    return result


@router.get("/{tmdb_id}/resenas", response_model=list[schemas.ResenaGeneral])
def get_resenas_generales(tmdb_id: int,
                          skip: int = 0,
                          limit: int = Query(20, ge=1, le=100),
                          db: Session = Depends(database.get_db),
                          current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    if not pelicula:
        return []

    entradas = db.execute(
        select(models.EntradaDiario)
        .where(
            models.EntradaDiario.id_pelicula == pelicula.id,
            models.EntradaDiario.resena.isnot(None)
        )
        .order_by(models.EntradaDiario.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    result = []
    for entrada in entradas:
        usuario = db.execute(
            select(models.Usuario).where(models.Usuario.id == entrada.id_usuario)
        ).scalar_one_or_none()

        vista = db.execute(
            select(models.Vista).where(
                models.Vista.id_usuario == entrada.id_usuario,
                models.Vista.id_pelicula == pelicula.id
            )
        ).scalar_one_or_none()

        total_likes = db.execute(
            select(func.count(models.LikeResena.id)).where(
                models.LikeResena.id_entrada_diario == entrada.id
            )
        ).scalar()

        total_comentarios = db.execute(
            select(func.count(models.ComentarioResena.id)).where(
                models.ComentarioResena.id_entrada_diario == entrada.id
            )
        ).scalar()

        yo_di_like = None
        if current_user:
            yo_di_like = db.execute(
                select(models.LikeResena).where(
                    models.LikeResena.id_usuario == current_user.id,
                    models.LikeResena.id_entrada_diario == entrada.id
                )
            ).scalar_one_or_none() is not None

        result.append(schemas.ResenaGeneral(
            id=entrada.id,
            id_usuario=entrada.id_usuario,
            username=usuario.username,
            avatar_url=usuario.avatar_url,
            fecha_visionado=entrada.fecha_visionado,
            resena=entrada.resena,
            puntuacion=vista.puntuacion if vista else None,
            total_likes=total_likes,
            total_comentarios=total_comentarios,
            yo_di_like=yo_di_like
        ))

    return result