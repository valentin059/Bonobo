from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .. import database, models, schemas, oauth2
from typing import Optional

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)


# --- MI PERFIL ---

@router.get("/me", response_model=schemas.UserProfile)
def get_mi_perfil(db: Session = Depends(database.get_db),
                  current_user: models.Usuario = Depends(oauth2.get_current_user)):

    total_vistas = db.execute(
        select(func.count(models.Vista.id)).where(models.Vista.id_usuario == current_user.id)
    ).scalar()

    seguidores = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguido == current_user.id)
    ).scalar()

    seguidos = db.execute(
        select(func.count(models.Seguidor.id)).where(models.Seguidor.id_seguidor == current_user.id)
    ).scalar()

    return {
        "id": current_user.id,
        "username": current_user.username,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "total_vistas": total_vistas,
        "seguidores": seguidores,
        "seguidos": seguidos,
        "yo_sigo": None
    }


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


# --- BUSCAR USUARIOS ---

@router.get("/buscar")
def buscar_usuarios(q: str, skip: int = 0, limit: int = 20,
                    db: Session = Depends(database.get_db)):

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


# --- PERFIL DE OTRO USUARIO ---

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

    yo_sigo = None
    if current_user and current_user.id != id:
        yo_sigo = db.execute(
            select(models.Seguidor).where(
                models.Seguidor.id_seguidor == current_user.id,
                models.Seguidor.id_seguido == id
            )
        ).scalar_one_or_none() is not None

    return {
        "id": usuario.id,
        "username": usuario.username,
        "bio": usuario.bio,
        "avatar_url": usuario.avatar_url,
        "total_vistas": total_vistas,
        "seguidores": seguidores,
        "seguidos": seguidos,
        "yo_sigo": yo_sigo
    }


# --- LISTAS DEL USUARIO ---

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


@router.get("/{id}/watchlist")
def get_watchlist(id: int, skip: int = 0, limit: int = 20,
                  db: Session = Depends(database.get_db)):

    usuario = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado")

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
                        db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado.")

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
    ).scalars().all()

    result = []
    for entrada in entradas:
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
        result.append(schemas.EntradaDiarioDetalle(
            id=entrada.id,
            fecha_visionado=entrada.fecha_visionado,
            resena=entrada.resena,
            created_at=entrada.created_at,
            total_likes=total_likes,
            total_comentarios=total_comentarios
        ))

    return result


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
        query = query.where(models.Lista.es_publica == True)
    query = query.order_by(models.Lista.created_at.desc())

    listas = db.execute(query).scalars().all()

    from sqlalchemy import func as _func
    result = []
    for lista in listas:
        total = db.execute(
            select(_func.count(models.ListaPelicula.id)).where(
                models.ListaPelicula.id_lista == lista.id
            )
        ).scalar()
        result.append(schemas.ListaOut(
            id=lista.id,
            nombre=lista.nombre,
            descripcion=lista.descripcion,
            es_publica=lista.es_publica,
            total_peliculas=total,
            created_at=lista.created_at
        ))

    return result


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
        .order_by(models.PeliculaFavorita.orden)
    ).scalars().all()

    return favoritas