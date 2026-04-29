from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from .. import database, models, schemas, oauth2, utils
from typing import Optional
from ..services import get_or_create_pelicula
from ..services.logros import comprobar_y_dar_logros

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)


# helper que devuelve total_vistas + seguidores + seguidos en UNA sola query.
# antes lo haciamos con 3 selects separados y era una tonteria.
def _stats_perfil(db: Session, user_id: int):
    return db.execute(
        select(
            select(func.count()).select_from(models.Vista)
                .where(models.Vista.id_usuario == user_id)
                .scalar_subquery().label('total_vistas'),
            select(func.count()).select_from(models.Seguidor)
                .where(models.Seguidor.id_seguido == user_id)
                .scalar_subquery().label('seguidores'),
            select(func.count()).select_from(models.Seguidor)
                .where(models.Seguidor.id_seguidor == user_id)
                .scalar_subquery().label('seguidos'),
        )
    ).one()


@router.get("/me", response_model=schemas.UserProfile)
def get_mi_perfil(db: Session = Depends(database.get_db),
                  current_user: models.Usuario = Depends(oauth2.get_current_user)):

    stats = _stats_perfil(db, current_user.id)

    logros = db.execute(
        select(models.UsuarioLogro, models.Logro)
        .join(models.Logro, models.UsuarioLogro.id_logro == models.Logro.id)
        .where(models.UsuarioLogro.id_usuario == current_user.id)
        .order_by(models.UsuarioLogro.created_at.desc())
    ).all()

    logros_out = [
        schemas.LogroOut(
            codigo=l.codigo,
            nombre=l.nombre,
            descripcion=l.descripcion,
            xp=l.xp,
            xp_reclamado=ul.xp_reclamado,
            desbloqueado_el=ul.created_at
        )
        for ul, l in logros
    ]

    return schemas.UserProfile(
        id=current_user.id,
        username=current_user.username,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        total_vistas=stats.total_vistas,
        seguidores=stats.seguidores,
        seguidos=stats.seguidos,
        yo_sigo=None,
        xp_total=current_user.xp_total,
        nivel=current_user.nivel,
        logros=logros_out,
    )


# reemplaza TODAS las favoritas por la lista nueva (max 4 tmdb_ids).
# primero resolvemos las pelis (esto puede pegarle a TMDB), si peta no
# tocamos las favoritas viejas. solo cuando ya tenemos todas las pelis
# en mano hacemos el delete + insert en la misma transaccion.
@router.put("/me/favoritas")
def configurar_favoritas(tmdb_ids: list[int],
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if len(tmdb_ids) > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 4 películas favoritas")

    # paso 1: resolvemos todas las pelis ANTES de tocar la tabla de favoritas
    peliculas = [get_or_create_pelicula(tid, db) for tid in tmdb_ids]

    # paso 2: borramos las viejas y metemos las nuevas en una transaccion sola
    db.execute(delete(models.PeliculaFavorita).where(
        models.PeliculaFavorita.id_usuario == current_user.id
    ))

    for orden, pelicula in enumerate(peliculas, start=1):
        db.add(models.PeliculaFavorita(
            id_usuario=current_user.id,
            id_pelicula=pelicula.id,
            orden=orden
        ))

    db.commit()

    comprobar_y_dar_logros(db, current_user.id)

    return {"detail": "Favoritas actualizadas"}


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_password(datos: schemas.PasswordChange,
                     db: Session = Depends(database.get_db),
                     current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if not utils.verify_password(datos.password_actual, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no es correcta")

    current_user.password_hash = utils.hash_password(datos.password_nueva)
    db.commit()


@router.put("/me", response_model=schemas.UserOut)
def editar_perfil(usuario_data: schemas.UserUpdate,
                  db: Session = Depends(database.get_db),
                  current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if usuario_data.bio is not None:
        current_user.bio = usuario_data.bio
    if usuario_data.avatar_url is not None:
        current_user.avatar_url = usuario_data.avatar_url

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/buscar", response_model=list[schemas.UsuarioResumen])
def buscar_usuarios(q: str, skip: int = 0, limit: int = 20,
                    db: Session = Depends(database.get_db)):

    # ilike = LIKE pero sin mirar mayus/minus
    usuarios = db.execute(
        select(models.Usuario)
        .where(models.Usuario.username.ilike(f"%{q}%"))
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return usuarios


# si hay sesion devolvemos tambien yo_sigo (si el user actual sigue al perfil)
@router.get("/{id}", response_model=schemas.UserProfile)
def get_perfil(id: int,
               db: Session = Depends(database.get_db),
               current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    stats = _stats_perfil(db, id)

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
        total_vistas=stats.total_vistas,
        seguidores=stats.seguidores,
        seguidos=stats.seguidos,
        yo_sigo=yo_sigo,
    )


@router.get("/{id}/vistas", response_model=list[schemas.VistaConPelicula])
def get_vistas(id: int, skip: int = 0, limit: int = 20,
               db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    vistas = db.execute(
        select(models.Vista)
        .where(models.Vista.id_usuario == id)
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return vistas


@router.get("/{id}/diario", response_model=list[schemas.EntradaDiarioOut])
def get_diario(id: int, skip: int = 0, limit: int = 20,
               db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    entradas = db.execute(
        select(models.EntradaDiario)
        .where(models.EntradaDiario.id_usuario == id)
        .order_by(models.EntradaDiario.fecha_visionado.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return entradas


@router.get("/{id}/watchlist")
def get_watchlist(id: int, skip: int = 0, limit: int = 20,
                  db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # join para sacar los datos de la peli en la misma query (evita N+1)
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


@router.get("/{id}/diario/pelicula/{tmdb_id}", response_model=list[schemas.EntradaDiarioDetalle])
def get_diario_pelicula(id: int, tmdb_id: int,
                        skip: int = 0,
                        limit: int = Query(20, ge=1, le=100),
                        db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

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

    # contamos likes y comentarios de TODAS las entradas a la vez (en vez de un select por entrada)
    likes_counts = dict(db.execute(
        select(models.LikeResena.id_entrada_diario, func.count(models.LikeResena.id))
        .where(models.LikeResena.id_entrada_diario.in_(entrada_ids))
        .group_by(models.LikeResena.id_entrada_diario)
    ).all())

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
            puntuacion=entrada.puntuacion,
            created_at=entrada.created_at,
            total_likes=likes_counts.get(entrada.id, 0),
            total_comentarios=comments_counts.get(entrada.id, 0)
        )
        for entrada in entradas
    ]


# si pides tus listas tu mismo te salen tambien las privadas
@router.get("/{id}/listas", response_model=list[schemas.ListaOut])
def get_listas_usuario(id: int,
                       db: Session = Depends(database.get_db),
                       current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    es_propio = current_user and current_user.id == id

    query = select(models.Lista).where(models.Lista.id_usuario == id)
    if not es_propio:
        query = query.where(models.Lista.es_publica == True)
    query = query.order_by(models.Lista.created_at.desc())

    listas = db.execute(query).scalars().all()

    if not listas:
        return []

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


@router.get("/{id}/favoritas", response_model=list[schemas.FavoritaOut])
def get_favoritas(id: int, db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    favoritas = db.execute(
        select(models.PeliculaFavorita)
        .where(models.PeliculaFavorita.id_usuario == id)
        .order_by(models.PeliculaFavorita.orden)
    ).scalars().all()

    return favoritas


# ranking de los amigos del user actual ordenado por XP
@router.get("/me/ranking-amigos", response_model=list[schemas.UsuarioResumen])
def get_ranking_amigos(db: Session = Depends(database.get_db),
                       current_user: models.Usuario = Depends(oauth2.get_current_user)):

    seguidos_ids = db.execute(
        select(models.Seguidor.id_seguido)
        .where(models.Seguidor.id_seguidor == current_user.id)
    ).scalars().all()

    if not seguidos_ids:
        return []

    usuarios = db.execute(
        select(models.Usuario)
        .where(models.Usuario.id.in_(seguidos_ids))
        .order_by(models.Usuario.xp_total.desc())
    ).scalars().all()

    return usuarios
