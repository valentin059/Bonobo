from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .. import database, models, schemas, oauth2
from typing import Optional

# Todas las rutas de este router empiezan por /api/usuarios
router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)


# ─── MI PERFIL ────────────────────────────────────────────────────────────

# GET /api/usuarios/me
# Devuelve el perfil del usuario autenticado con sus estadísticas.
@router.get("/me", response_model=schemas.UserProfile)
def get_mi_perfil(db: Session = Depends(database.get_db),
                  current_user: models.Usuario = Depends(oauth2.get_current_user)):

    # Contamos las películas vistas, seguidores y seguidos con queries individuales
    total_vistas = db.execute(
        select(func.count(models.Vista.id)).where(models.Vista.id_usuario == current_user.id)
    ).scalar()

    seguidores = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguido == current_user.id)
    ).scalar()

    seguidos = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguidor == current_user.id)
    ).scalar()

    return schemas.UserProfile(
        id=current_user.id,
        username=current_user.username,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        total_vistas=total_vistas,
        seguidores=seguidores,
        seguidos=seguidos,
        yo_sigo=None   # no tiene sentido "si me sigo a mí mismo"
    )


# PUT /api/usuarios/me
# Actualiza la bio o el avatar del usuario autenticado.
@router.put("/me", response_model=schemas.UserOut)
def editar_perfil(usuario_data: schemas.UserUpdate,
                  db: Session = Depends(database.get_db),
                  current_user: models.Usuario = Depends(oauth2.get_current_user)):

    # Solo actualizamos los campos que se envíen (los que no sean None)
    if usuario_data.bio is not None:
        current_user.bio = usuario_data.bio
    if usuario_data.avatar_url is not None:
        current_user.avatar_url = usuario_data.avatar_url

    db.commit()
    db.refresh(current_user)

    return current_user


# ─── BUSCAR USUARIOS ──────────────────────────────────────────────────────

# GET /api/usuarios/buscar?q=texto
# Busca usuarios por nombre de usuario (búsqueda parcial, sin distinción de mayúsculas).
@router.get("/buscar")
def buscar_usuarios(q: str, skip: int = 0, limit: int = 20,
                    db: Session = Depends(database.get_db)):

    # ilike = LIKE sin distinción de mayúsculas/minúsculas
    usuarios = db.execute(
        select(models.Usuario)
        .where(models.Usuario.username.ilike(f"%{q}%"))
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "avatar_url": u.avatar_url
        }
        for u in usuarios
    ]


# ─── PERFIL DE OTRO USUARIO ───────────────────────────────────────────────

# GET /api/usuarios/{id}
# Devuelve el perfil público de un usuario.
# Si el usuario autenticado lo consulta, incluye si ya lo sigue.
@router.get("/{id}", response_model=schemas.UserProfile)
def get_perfil(id: int,
               db: Session = Depends(database.get_db),
               current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

    total_vistas = db.execute(
        select(func.count(models.Vista.id)).where(models.Vista.id_usuario == id)
    ).scalar()

    seguidores = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguido == id)
    ).scalar()

    seguidos = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguidor == id)
    ).scalar()

    # Comprobamos si el usuario autenticado ya sigue a este usuario
    yo_sigo = None
    if current_user and current_user.id != id:
        yo_sigo = db.execute(
            select(models.Seguidor).where(
                models.Seguidor.id_seguidor == current_user.id,
                models.Seguidor.id_seguido == id
            )
        ).scalar_one_or_none() is not None

    return schemas.UserProfile(
        id=usuario.id,
        username=usuario.username,
        bio=usuario.bio,
        avatar_url=usuario.avatar_url,
        total_vistas=total_vistas,
        seguidores=seguidores,
        seguidos=seguidos,
        yo_sigo=yo_sigo
    )


# ─── DATOS DEL USUARIO ────────────────────────────────────────────────────

# GET /api/usuarios/{id}/vistas
# Devuelve las películas que ha marcado como vistas un usuario.
@router.get("/{id}/vistas", response_model=list[schemas.VistaConPelicula])
def get_vistas(id: int, skip: int = 0, limit: int = 20,
               db: Session = Depends(database.get_db)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

    vistas = db.execute(
        select(models.Vista)
        .where(models.Vista.id_usuario == id)
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return vistas


# GET /api/usuarios/{id}/diario
# Devuelve las entradas del diario de un usuario, ordenadas por fecha descendente.
@router.get("/{id}/diario", response_model=list[schemas.EntradaDiarioOut])
def get_diario(id: int, skip: int = 0, limit: int = 20,
               db: Session = Depends(database.get_db)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

    entradas = db.execute(
        select(models.EntradaDiario)
        .where(models.EntradaDiario.id_usuario == id)
        .order_by(models.EntradaDiario.fecha_visionado.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return entradas


# GET /api/usuarios/{id}/watchlist
# Devuelve la watchlist de un usuario con los datos de cada película.
@router.get("/{id}/watchlist")
def get_watchlist(id: int, skip: int = 0, limit: int = 20,
                  db: Session = Depends(database.get_db)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

    # Hacemos un join para traer los datos de la película en la misma query
    watchlist = db.execute(
        select(models.Watchlist, models.Pelicula)
        .join(models.Pelicula, models.Watchlist.id_pelicula == models.Pelicula.id)
        .where(models.Watchlist.id_usuario == id)
        .offset(skip)
        .limit(limit)
    ).all()

    return [
        {
            "id": w.Watchlist.id,
            "pelicula": {
                "tmdb_id": w.Pelicula.tmdb_id,
                "titulo": w.Pelicula.titulo,
                "poster_url": w.Pelicula.poster_url,
                "anio_estreno": w.Pelicula.anio_estreno
            }
        }
        for w in watchlist
    ]


# GET /api/usuarios/{id}/diario/pelicula/{tmdb_id}
# Devuelve todas las entradas del diario de un usuario para una película concreta.
# Incluye el número de likes y comentarios de cada entrada.
@router.get("/{id}/diario/pelicula/{tmdb_id}", response_model=list[schemas.EntradaDiarioDetalle])
def get_diario_pelicula(id: int, tmdb_id: int,
                        skip: int = 0,
                        limit: int = Query(20, ge=1, le=100),
                        db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado.")

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    # Si la película no está en nuestra BD, el usuario no puede tener entradas para ella
    if not pelicula:
        return []

    entradas = db.execute(
        select(models.EntradaDiario)
        .where(
            models.EntradaDiario.id_usuario == id,
            models.EntradaDiario.id_pelicula == pelicula.id
        )
        .order_by(models.EntradaDiario.fecha_visionado.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    if not entradas:
        return []

    entrada_ids = [e.id for e in entradas]

    # Contamos los likes de todas las entradas en una sola query (eficiente)
    likes_counts = dict(db.execute(
        select(models.LikeResena.id_entrada_diario, func.count(models.LikeResena.id))
        .where(models.LikeResena.id_entrada_diario.in_(entrada_ids))
        .group_by(models.LikeResena.id_entrada_diario)
    ).all())

    # Contamos los comentarios de todas las entradas en una sola query
    comments_counts = dict(db.execute(
        select(models.ComentarioResena.id_entrada_diario, func.count(models.ComentarioResena.id))
        .where(models.ComentarioResena.id_entrada_diario.in_(entrada_ids))
        .group_by(models.ComentarioResena.id_entrada_diario)
    ).all())

    return [
        schemas.EntradaDiarioDetalle(
            id=entrada.id,
            fecha_visionado=entrada.fecha_visionado,
            resena=entrada.resena,
            created_at=entrada.created_at,
            total_likes=likes_counts.get(entrada.id, 0),
            total_comentarios=comments_counts.get(entrada.id, 0)
        )
        for entrada in entradas
    ]


# GET /api/usuarios/{id}/listas
# Devuelve las listas de un usuario.
# Si quien consulta es el propio usuario, ve también sus listas privadas.
# Si es otro usuario (o nadie), solo ve las listas públicas.
@router.get("/{id}/listas", response_model=list[schemas.ListaOut])
def get_listas_usuario(id: int,
                       db: Session = Depends(database.get_db),
                       current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado.")

    es_propio = current_user and current_user.id == id

    query = select(models.Lista).where(models.Lista.id_usuario == id)
    if not es_propio:
        # Si no es el propietario, filtramos para mostrar solo las listas públicas
        query = query.where(models.Lista.es_publica == True)
    query = query.order_by(models.Lista.created_at.desc())

    listas = db.execute(query).scalars().all()

    if not listas:
        return []

    # Contamos las películas de cada lista en una sola query (eficiente)
    lista_ids = [l.id for l in listas]
    counts = dict(db.execute(
        select(models.ListaPelicula.id_lista, func.count(models.ListaPelicula.id))
        .where(models.ListaPelicula.id_lista.in_(lista_ids))
        .group_by(models.ListaPelicula.id_lista)
    ).all())

    return [
        schemas.ListaOut(
            id=lista.id,
            nombre=lista.nombre,
            descripcion=lista.descripcion,
            es_publica=lista.es_publica,
            total_peliculas=counts.get(lista.id, 0),
            created_at=lista.created_at
        )
        for lista in listas
    ]


# GET /api/usuarios/{id}/favoritas
# Devuelve las películas favoritas de un usuario, ordenadas por posición (1-4).
@router.get("/{id}/favoritas", response_model=list[schemas.FavoritaOut])
def get_favoritas(id: int, db: Session = Depends(database.get_db)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

    favoritas = db.execute(
        select(models.PeliculaFavorita)
        .where(models.PeliculaFavorita.id_usuario == id)
        .order_by(models.PeliculaFavorita.orden)   # ordenamos por posición en el perfil
    ).scalars().all()

    return favoritas
