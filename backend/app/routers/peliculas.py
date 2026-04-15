from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from collections import defaultdict
import httpx
from typing import Optional
from .. import services, schemas, models, database, oauth2

# Todas las rutas de este router empiezan por /api/peliculas
# y están relacionadas con consultar información de películas
router = APIRouter(
    prefix="/api/peliculas",
    tags=["Películas"]
)


# GET /api/peliculas/buscar?q=texto
# Busca películas en TMDB por texto. Devuelve una lista paginada.
@router.get("/buscar", response_model=schemas.PaginadoPeliculas)
def buscar_peliculas(q: str, skip: int = 0, limit: int = Query(20, ge=1, le=100)):
    try:
        return services.buscar_peliculas(q, skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener resultados de TMDB. Inténtalo de nuevo."
        )


# GET /api/peliculas/cartelera
# Devuelve las películas que están actualmente en cines (España).
@router.get("/cartelera", response_model=schemas.PaginadoCartelera)
def obtener_cartelera(skip: int = 0, limit: int = Query(20, ge=1, le=100)):
    try:
        return services.obtener_cartelera(skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo obtener la cartelera. Inténtalo de nuevo."
        )


# GET /api/peliculas/estrenos
# Devuelve las películas próximas a estrenarse.
@router.get("/estrenos", response_model=schemas.PaginadoEstrenos)
def obtener_estrenos(skip: int = 0, limit: int = Query(20, ge=1, le=100)):
    try:
        return services.obtener_estrenos(skip, limit)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron obtener los estrenos. Inténtalo de nuevo."
        )


# GET /api/peliculas/persona/{person_id}
# Devuelve el perfil de una persona (actor, director…) con su filmografía.
@router.get("/persona/{person_id}", response_model=schemas.PersonaDetalle)
def obtener_persona(person_id: int):
    try:
        return services.obtener_persona(person_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Persona no encontrada.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="No se pudo obtener la información.")


# GET /api/peliculas/{tmdb_id}
# Devuelve el detalle completo de una película.
# Si el usuario está autenticado, incluye también su estado personal
# (si la ha visto, puntuado, dado me gusta o añadido a watchlist).
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
        # Buscamos la película en nuestra BD para poder consultar las acciones del usuario
        pelicula = db.execute(select(models.Pelicula).where(
            models.Pelicula.tmdb_id == tmdb_id
        )).scalar_one_or_none()

        if pelicula:
            # Consultamos si el usuario tiene la película vista, con me gusta o en watchlist
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
            # La película no está en nuestra BD (nadie la ha interaccionado aún)
            estado = schemas.EstadoUsuarioPelicula()

    # model_copy(update=...) devuelve una copia del schema con el campo estado_usuario actualizado
    return datos.model_copy(update={"estado_usuario": estado})


# GET /api/peliculas/{tmdb_id}/resenas/amigos
# Devuelve las reseñas de los usuarios que sigue el usuario autenticado para esta película.
# Requiere estar autenticado.
@router.get("/{tmdb_id}/resenas/amigos", response_model=list[schemas.ResenaAmigo])
def get_resenas_amigos(tmdb_id: int,
                       db: Session = Depends(database.get_db),
                       current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    # Si la película no está en nuestra BD, nadie la ha interaccionado -> sin reseñas
    if not pelicula:
        return []

    # Obtenemos los ids de los usuarios que sigue el usuario autenticado
    seguidos_ids = db.execute(
        select(models.Seguidor.id_seguido).where(models.Seguidor.id_seguidor == current_user.id)
    ).scalars().all()

    if not seguidos_ids:
        return []

    # Una sola query: vistas de amigos para esta película, con datos del usuario
    rows_vistas = db.execute(
        select(models.Vista, models.Usuario)
        .join(models.Usuario, models.Vista.id_usuario == models.Usuario.id)
        .where(
            models.Vista.id_usuario.in_(seguidos_ids),
            models.Vista.id_pelicula == pelicula.id
        )
    ).all()

    if not rows_vistas:
        return []

    user_ids_con_vista = [row.Vista.id_usuario for row in rows_vistas]

    # Una sola query: todas las entradas de diario de estos amigos para esta película
    todas_entradas = db.execute(
        select(models.EntradaDiario)
        .where(
            models.EntradaDiario.id_usuario.in_(user_ids_con_vista),
            models.EntradaDiario.id_pelicula == pelicula.id
        )
        .order_by(models.EntradaDiario.fecha_visionado.desc())
    ).scalars().all()

    # Agrupamos las entradas por id de usuario para acceder a ellas rápidamente
    entradas_por_usuario = defaultdict(list)
    for e in todas_entradas:
        entradas_por_usuario[e.id_usuario].append(e)

    result = []
    for row in rows_vistas:
        vista = row.Vista
        usuario = row.Usuario
        entradas = entradas_por_usuario.get(vista.id_usuario, [])

        # Buscamos la última reseña con texto (puede que haya entradas sin reseña)
        ultima_resena = None
        ultima_entrada_id = None
        for entrada in entradas:
            if entrada.resena:
                ultima_resena = entrada.resena[:200]   # máximo 200 caracteres en el resumen
                ultima_entrada_id = entrada.id
                break

        result.append(schemas.ResenaAmigo(
            id_usuario=vista.id_usuario,
            username=usuario.username,
            avatar_url=usuario.avatar_url,
            puntuacion=vista.puntuacion or (entradas[0].puntuacion if entradas else None),
            ultima_resena=ultima_resena,
            ultima_entrada_id=ultima_entrada_id,
            total_entradas=len(entradas)
        ))

    return result


# GET /api/peliculas/{tmdb_id}/resenas
# Devuelve las reseñas de todos los usuarios para esta película (comunidad).
# Si el usuario está autenticado, incluye si ya dio like a cada reseña.
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

    # Subconsulta: cuenta los likes de cada entrada de diario
    likes_sub = (
        select(func.count(models.LikeResena.id))
        .where(models.LikeResena.id_entrada_diario == models.EntradaDiario.id)
        .correlate(models.EntradaDiario)
        .scalar_subquery()
        .label("total_likes")
    )

    # Subconsulta: cuenta los comentarios de cada entrada de diario
    comments_sub = (
        select(func.count(models.ComentarioResena.id))
        .where(models.ComentarioResena.id_entrada_diario == models.EntradaDiario.id)
        .correlate(models.EntradaDiario)
        .scalar_subquery()
        .label("total_comentarios")
    )

    # Query principal: entradas de diario con reseña, con datos del usuario y contadores
    rows = db.execute(
        select(
            models.EntradaDiario,
            models.Usuario.username,
            models.Usuario.avatar_url,
            models.Vista.puntuacion,
            likes_sub,
            comments_sub
        )
        .join(models.Usuario, models.EntradaDiario.id_usuario == models.Usuario.id)
        .outerjoin(models.Vista, and_(   # outerjoin porque puede no tener puntuación
            models.Vista.id_usuario == models.EntradaDiario.id_usuario,
            models.Vista.id_pelicula == pelicula.id
        ))
        .where(
            models.EntradaDiario.id_pelicula == pelicula.id,
            models.EntradaDiario.resena.isnot(None)   # solo entradas que tengan reseña
        )
        .order_by(models.EntradaDiario.created_at.desc())   # las más recientes primero
        .offset(skip)
        .limit(limit)
    ).all()

    # Si el usuario está autenticado, obtenemos de una sola query todos sus likes
    # (más eficiente que consultar uno a uno)
    mis_likes = set()
    if current_user and rows:
        entrada_ids = [row.EntradaDiario.id for row in rows]
        mis_likes = set(db.execute(
            select(models.LikeResena.id_entrada_diario)
            .where(
                models.LikeResena.id_usuario == current_user.id,
                models.LikeResena.id_entrada_diario.in_(entrada_ids)
            )
        ).scalars().all())

    return [
        schemas.ResenaGeneral(
            id=row.EntradaDiario.id,
            id_usuario=row.EntradaDiario.id_usuario,
            username=row.username,
            avatar_url=row.avatar_url,
            fecha_visionado=row.EntradaDiario.fecha_visionado,
            resena=row.EntradaDiario.resena,
            puntuacion=row.EntradaDiario.puntuacion or row.puntuacion,
            total_likes=row.total_likes,
            total_comentarios=row.total_comentarios,
            yo_di_like=row.EntradaDiario.id in mis_likes if current_user else None
        )
        for row in rows
    ]
