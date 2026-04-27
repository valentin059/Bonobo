from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from .. import database, models, schemas, oauth2
from ..services import get_or_create_pelicula

router = APIRouter(
    prefix="/api/listas",
    tags=["Listas"]
)


def _check_acceso_lista(lista: models.Lista, current_user: Optional[models.Usuario]) -> None:
    if not lista.es_publica:
        if not current_user or current_user.id != lista.id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Esta lista es privada.")


def _lista_out(lista: models.Lista, db: Session) -> schemas.ListaOut:
    total = db.execute(
        select(func.count(models.ListaPelicula.id)).where(
            models.ListaPelicula.id_lista == lista.id
        )
    ).scalar()
    return schemas.ListaOut(
        id=lista.id,
        nombre=lista.nombre,
        descripcion=lista.descripcion,
        es_publica=lista.es_publica,
        total_peliculas=total,
        created_at=lista.created_at
    )


@router.post("", response_model=schemas.ListaOut, status_code=status.HTTP_201_CREATED)
def crear_lista(lista_data: schemas.ListaCreate,
                db: Session = Depends(database.get_db),
                current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = models.Lista(
        id_usuario=current_user.id,
        nombre=lista_data.nombre,
        descripcion=lista_data.descripcion,
        es_publica=lista_data.es_publica
    )
    db.add(lista)
    db.commit()
    db.refresh(lista)

    return _lista_out(lista, db)


@router.get("/{id_lista}", response_model=schemas.ListaDetalle)
def get_lista(id_lista: int,
              skip: int = 0,
              limit: int = Query(20, ge=1, le=100),
              db: Session = Depends(database.get_db),
              current_user: Optional[models.Usuario] = Depends(oauth2.get_optional_user)):

    lista = db.execute(
        select(models.Lista).where(models.Lista.id == id_lista)
    ).scalar_one_or_none()

    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lista no encontrada.")

    _check_acceso_lista(lista, current_user)

    dueno = db.execute(
        select(models.Usuario).where(models.Usuario.id == lista.id_usuario)
    ).scalar_one_or_none()

    rows = db.execute(
        select(models.ListaPelicula, models.Pelicula)
        .join(models.Pelicula, models.ListaPelicula.id_pelicula == models.Pelicula.id)
        .where(models.ListaPelicula.id_lista == id_lista)
        .order_by(models.ListaPelicula.created_at.asc())
        .offset(skip)
        .limit(limit)
    ).all()

    peliculas = [
        schemas.PeliculaCache(
            tmdb_id=row.Pelicula.tmdb_id,
            titulo=row.Pelicula.titulo,
            poster_url=row.Pelicula.poster_url,
            anio_estreno=row.Pelicula.anio_estreno
        )
        for row in rows
    ]

    # total independiente de la paginación
    total = db.execute(
        select(func.count(models.ListaPelicula.id)).where(
            models.ListaPelicula.id_lista == id_lista
        )
    ).scalar()

    return schemas.ListaDetalle(
        id=lista.id,
        id_usuario=lista.id_usuario,
        username=dueno.username,
        nombre=lista.nombre,
        descripcion=lista.descripcion,
        es_publica=lista.es_publica,
        peliculas=peliculas,
        total_peliculas=total
    )


@router.put("/{id_lista}", response_model=schemas.ListaOut)
def editar_lista(id_lista: int,
                 lista_data: schemas.ListaUpdate,
                 db: Session = Depends(database.get_db),
                 current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(
        select(models.Lista).where(models.Lista.id == id_lista)
    ).scalar_one_or_none()

    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lista no encontrada.")

    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes editar esta lista.")

    # solo actualizamos los campos que se envíen
    if lista_data.nombre is not None:
        lista.nombre = lista_data.nombre
    if lista_data.descripcion is not None:
        lista.descripcion = lista_data.descripcion
    if lista_data.es_publica is not None:
        lista.es_publica = lista_data.es_publica

    db.commit()
    db.refresh(lista)

    return _lista_out(lista, db)


@router.delete("/{id_lista}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_lista(id_lista: int,
                   db: Session = Depends(database.get_db),
                   current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(
        select(models.Lista).where(models.Lista.id == id_lista)
    ).scalar_one_or_none()

    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lista no encontrada.")

    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes eliminar esta lista.")

    db.delete(lista)
    db.commit()


@router.get("/mis-listas-con-pelicula/{tmdb_id}", response_model=list[int])
def mis_listas_con_pelicula(tmdb_id: int,
                             db: Session = Depends(database.get_db),
                             current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    if not pelicula:
        return []

    rows = db.execute(
        select(models.ListaPelicula.id_lista)
        .join(models.Lista, models.Lista.id == models.ListaPelicula.id_lista)
        .where(
            models.Lista.id_usuario == current_user.id,
            models.ListaPelicula.id_pelicula == pelicula.id
        )
    ).scalars().all()

    return list(rows)


@router.post("/{id_lista}/peliculas/{tmdb_id}", status_code=status.HTTP_201_CREATED)
def añadir_pelicula_lista(id_lista: int,
                          tmdb_id: int,
                          db: Session = Depends(database.get_db),
                          current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(
        select(models.Lista).where(models.Lista.id == id_lista)
    ).scalar_one_or_none()

    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lista no encontrada.")

    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes modificar esta lista.")

    pelicula = get_or_create_pelicula(tmdb_id, db)

    ya_existe = db.execute(
        select(models.ListaPelicula).where(
            models.ListaPelicula.id_lista == id_lista,
            models.ListaPelicula.id_pelicula == pelicula.id
        )
    ).scalar_one_or_none()

    if ya_existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="La película ya está en esta lista.")

    db.add(models.ListaPelicula(id_lista=id_lista, id_pelicula=pelicula.id))
    db.commit()

    return {"detail": "Película añadida a la lista."}


@router.delete("/{id_lista}/peliculas/{tmdb_id}", status_code=status.HTTP_200_OK)
def quitar_pelicula_lista(id_lista: int,
                          tmdb_id: int,
                          db: Session = Depends(database.get_db),
                          current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(
        select(models.Lista).where(models.Lista.id == id_lista)
    ).scalar_one_or_none()

    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lista no encontrada.")

    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes modificar esta lista.")

    pelicula = db.execute(
        select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)
    ).scalar_one_or_none()

    if not pelicula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Película no encontrada.")

    entrada = db.execute(
        select(models.ListaPelicula).where(
            models.ListaPelicula.id_lista == id_lista,
            models.ListaPelicula.id_pelicula == pelicula.id
        )
    ).scalar_one_or_none()

    if not entrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="La película no está en esta lista.")

    db.delete(entrada)
    db.commit()

    return {"detail": "Película eliminada de la lista."}
