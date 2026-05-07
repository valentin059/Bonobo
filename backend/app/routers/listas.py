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


# si la lista es privada, solo el dueño la ve. tira 403 si intentas mirar
# la lista de otro user. Se añadió para crear lista compartidas
def comprobar_permisos_lista(lista: models.Lista, current_user: Optional[models.Usuario], db: Session) -> None:
    if not lista.es_publica:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Esta lista es privada.")
        if current_user.id == lista.id_usuario:
            return
        es_colaborador = db.execute(select(models.ListaColaborador).where(
            models.ListaColaborador.id_lista == lista.id,
            models.ListaColaborador.id_usuario == current_user.id
        )).scalar_one_or_none()
        if not es_colaborador:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Esta lista es privada.")


def _es_dueno_o_colaborador(lista: models.Lista, current_user: models.Usuario, db: Session) -> bool:
    if lista.id_usuario == current_user.id:
        return True
    return db.execute(select(models.ListaColaborador).where(
        models.ListaColaborador.id_lista == lista.id,
        models.ListaColaborador.id_usuario == current_user.id
    )).scalar_one_or_none() is not None


# arma el schema ListaOut con el total de peliculas (lo necesitamos en POST y PUT)
def armar_lista_out(lista: models.Lista, db: Session) -> schemas.ListaOut:
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

    return armar_lista_out(lista, db)

# GET /api/listas/colaborando
# Listas en las que el usuario es colaborador (no dueño)
@router.get("/colaborando", response_model=list[schemas.ListaOut])
def get_listas_colaborando(db: Session = Depends(database.get_db),
                            current_user: models.Usuario = Depends(oauth2.get_current_user)):

    rows = db.execute(
        select(models.Lista)
        .join(models.ListaColaborador, models.ListaColaborador.id_lista == models.Lista.id)
        .where(models.ListaColaborador.id_usuario == current_user.id)
        .order_by(models.Lista.created_at.desc())
    ).scalars().all()

    if not rows:
        return []

    lista_ids = [l.id for l in rows]
    counts = dict(db.execute(
        select(models.ListaPelicula.id_lista, func.count(models.ListaPelicula.id))
        .where(models.ListaPelicula.id_lista.in_(lista_ids))
        .group_by(models.ListaPelicula.id_lista)
    ).all())

    return [
        schemas.ListaOut(
            id=l.id,
            nombre=l.nombre,
            descripcion=l.descripcion,
            es_publica=l.es_publica,
            total_peliculas=counts.get(l.id, 0),
            created_at=l.created_at
        )
        for l in rows
    ]

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

    comprobar_permisos_lista(lista, current_user, db)

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

    # total general independiente del skip/limit
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

    # solo tocamos lo que ha mandado el cliente
    if lista_data.nombre is not None:
        lista.nombre = lista_data.nombre
    if lista_data.descripcion is not None:
        lista.descripcion = lista_data.descripcion
    if lista_data.es_publica is not None:
        lista.es_publica = lista_data.es_publica

    db.commit()
    db.refresh(lista)

    return armar_lista_out(lista, db)


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

    if not _es_dueno_o_colaborador(lista, current_user, db):
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

    if not _es_dueno_o_colaborador(lista, current_user, db):
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


# POST /api/listas/{id_lista}/colaboradores/{id_usuario}
# Invitar a un colaborador (solo el dueño, y solo si hay seguimiento mutuo)
@router.post("/{id_lista}/colaboradores/{id_usuario}", status_code=status.HTTP_201_CREATED)
def añadir_colaborador(id_lista: int, id_usuario: int,
                       db: Session = Depends(database.get_db),
                       current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(select(models.Lista).where(models.Lista.id == id_lista)).scalar_one_or_none()
    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada.")
    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el dueño puede invitar colaboradores.")

    usuario = db.execute(select(models.Usuario).where(models.Usuario.id == id_usuario)).scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    yo_sigo = db.execute(select(models.Seguidor).where(
        models.Seguidor.id_seguidor == current_user.id,
        models.Seguidor.id_seguido == id_usuario
    )).scalar_one_or_none()

    me_sigue = db.execute(select(models.Seguidor).where(
        models.Seguidor.id_seguidor == id_usuario,
        models.Seguidor.id_seguido == current_user.id
    )).scalar_one_or_none()

    if not yo_sigo or not me_sigue:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo puedes invitar a usuarios con seguimiento mutuo.")

    ya_existe = db.execute(select(models.ListaColaborador).where(
        models.ListaColaborador.id_lista == id_lista,
        models.ListaColaborador.id_usuario == id_usuario
    )).scalar_one_or_none()

    if ya_existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya es colaborador de esta lista.")

    db.add(models.ListaColaborador(id_lista=id_lista, id_usuario=id_usuario))
    db.commit()

    return {"detail": "Colaborador añadido"}


# DELETE /api/listas/{id_lista}/colaboradores/{id_usuario}
# Eliminar colaborador (solo el dueño)
@router.delete("/{id_lista}/colaboradores/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_colaborador(id_lista: int, id_usuario: int,
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(select(models.Lista).where(models.Lista.id == id_lista)).scalar_one_or_none()
    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada.")
    if lista.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el dueño puede eliminar colaboradores.")

    colaborador = db.execute(select(models.ListaColaborador).where(
        models.ListaColaborador.id_lista == id_lista,
        models.ListaColaborador.id_usuario == id_usuario
    )).scalar_one_or_none()

    if not colaborador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No es colaborador de esta lista.")

    db.delete(colaborador)
    db.commit()


# GET /api/listas/{id_lista}/colaboradores
# Ver colaboradores de una lista
@router.get("/{id_lista}/colaboradores", response_model=list[schemas.UsuarioResumen])
def get_colaboradores(id_lista: int,
                      db: Session = Depends(database.get_db),
                      current_user: models.Usuario = Depends(oauth2.get_current_user)):

    lista = db.execute(select(models.Lista).where(models.Lista.id == id_lista)).scalar_one_or_none()
    if not lista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada.")

    if not _es_dueno_o_colaborador(lista, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta lista.")

    colaboradores = db.execute(
        select(models.Usuario)
        .join(models.ListaColaborador, models.ListaColaborador.id_usuario == models.Usuario.id)
        .where(models.ListaColaborador.id_lista == id_lista)
    ).scalars().all()

    return colaboradores

