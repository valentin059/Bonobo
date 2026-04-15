from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from .. import database, models, schemas, oauth2
from ..services import get_or_create_pelicula

# Todas las rutas de este router empiezan por /api/listas
# y gestionan las listas de películas creadas por los usuarios
router = APIRouter(
    prefix="/api/listas",
    tags=["Listas"]
)


# Comprueba si el usuario tiene permiso para ver una lista privada.
# Si la lista es privada y el usuario no es el dueño, lanza un error 403.
def _check_acceso_lista(lista: models.Lista,
                        current_user: Optional[models.Usuario]) -> None:
    if not lista.es_publica:
        if not current_user or current_user.id != lista.id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Esta lista es privada.")


# Construye el schema ListaOut para una lista, calculando el número de películas que contiene.
# Es una función auxiliar para no repetir este código en varios endpoints.
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


# ─── CRUD DE LISTAS ───────────────────────────────────────────────────────

# POST /api/listas
# Crea una nueva lista para el usuario autenticado.
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


# GET /api/listas/{id_lista}
# Devuelve el detalle completo de una lista, incluyendo sus películas.
# Si la lista es privada, solo puede verla su dueño.
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

    # Verificamos que el usuario puede ver esta lista
    _check_acceso_lista(lista, current_user)

    # Obtenemos los datos del usuario dueño de la lista
    dueno = db.execute(
        select(models.Usuario).where(models.Usuario.id == lista.id_usuario)
    ).scalar_one_or_none()

    # Obtenemos las películas de la lista con un join (por orden de creación)
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

    # Contamos el total de películas (independiente de la paginación)
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


# PUT /api/listas/{id_lista}
# Edita el nombre, descripción o visibilidad de una lista. Solo puede hacerlo su dueño.
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

    # Solo actualizamos los campos que se envíen
    if lista_data.nombre is not None:
        lista.nombre = lista_data.nombre
    if lista_data.descripcion is not None:
        lista.descripcion = lista_data.descripcion
    if lista_data.es_publica is not None:
        lista.es_publica = lista_data.es_publica

    db.commit()
    db.refresh(lista)

    return _lista_out(lista, db)


# DELETE /api/listas/{id_lista}
# Elimina una lista y todas sus películas (CASCADE en la BD). Solo puede hacerlo su dueño.
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


# GET /api/listas/mis-listas-con-pelicula/{tmdb_id}
# Devuelve los IDs de las listas del usuario que ya contienen esta película.
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


# ─── PELÍCULAS EN LISTA ───────────────────────────────────────────────────

# POST /api/listas/{id_lista}/peliculas/{tmdb_id}
# Añade una película a una lista. Solo puede hacerlo el dueño de la lista.
# Si la película no existe en nuestra BD, se crea automáticamente (caché de TMDB).
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

    # Buscamos la película en nuestra BD o la creamos si no existe
    pelicula = get_or_create_pelicula(tmdb_id, db)

    # Comprobamos que la película no esté ya en la lista
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


# DELETE /api/listas/{id_lista}/peliculas/{tmdb_id}
# Elimina una película de una lista. Solo puede hacerlo el dueño de la lista.
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

    # Buscamos la entrada en la tabla intermedia listas_peliculas
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
