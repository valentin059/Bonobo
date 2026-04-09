from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from .. import database, models, schemas, oauth2, services

# Todas las rutas de este router empiezan por /api/peliculas
# y agrupan las acciones del usuario sobre películas (vista, watchlist, me gusta, favoritas)
router = APIRouter(
    prefix="/api/peliculas",
    tags=["Acciones"]
)


# Busca una película en nuestra BD por su tmdb_id.
# Si no existe todavía, la pide a TMDB y la guarda (caché local).
# Así no tenemos que guardar todas las películas de TMDB de antemano.
def get_or_create_pelicula(tmdb_id: int, db: Session):
    pelicula = db.execute(select(models.Pelicula).where(models.Pelicula.tmdb_id == tmdb_id)).scalar_one_or_none()
    if not pelicula:
        try:
            datos = services.obtener_detalle_pelicula(tmdb_id)
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
        db.commit()
        db.refresh(pelicula)
    return pelicula


# Elimina una película de la watchlist del usuario si estaba en ella.
# Se llama automáticamente al marcar como vista o puntuar una película.
def eliminar_de_watchlist(id_usuario: int, id_pelicula: int, db: Session):
    wl = db.execute(select(models.Watchlist).where(
        models.Watchlist.id_usuario == id_usuario,
        models.Watchlist.id_pelicula == id_pelicula
    )).scalar_one_or_none()
    if wl:
        db.delete(wl)
        db.commit()


# ─── VISTA ────────────────────────────────────────────────────────────────

# POST /api/peliculas/{tmdb_id}/vista
# Marca una película como vista para el usuario autenticado.
# Si estaba en su watchlist, la elimina automáticamente.
@router.post("/{tmdb_id}/vista", status_code=status.HTTP_201_CREATED)
def marcar_vista(tmdb_id: int, db: Session = Depends(database.get_db),
                 current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

    # Comprobamos que no la tenga ya marcada como vista
    vista_existente = db.execute(select(models.Vista).where(
        models.Vista.id_usuario == current_user.id,
        models.Vista.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if vista_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La película ya está marcada como vista")

    nueva_vista = models.Vista(id_usuario=current_user.id, id_pelicula=pelicula.id)
    db.add(nueva_vista)
    db.commit()

    # Si estaba en la watchlist, la quitamos (ya no hace falta verla)
    eliminar_de_watchlist(current_user.id, pelicula.id, db)

    return {"detail": "Película marcada como vista"}


# DELETE /api/peliculas/{tmdb_id}/vista
# Desmarca una película como vista.
# No se permite si tiene puntuación, entradas de diario o me gusta asociados.
@router.delete("/{tmdb_id}/vista", status_code=status.HTTP_204_NO_CONTENT)
def desmarcar_vista(tmdb_id: int, db: Session = Depends(database.get_db),
                    current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(select(models.Pelicula).where(
        models.Pelicula.tmdb_id == tmdb_id
    )).scalar_one_or_none()

    if not pelicula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Película no encontrada")

    vista = db.execute(select(models.Vista).where(
        models.Vista.id_usuario == current_user.id,
        models.Vista.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if not vista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La película no está marcada como vista")

    # Comprobamos si tiene datos asociados que se perderían al desmarcar
    tiene_diario = db.execute(select(models.EntradaDiario).where(
        models.EntradaDiario.id_usuario == current_user.id,
        models.EntradaDiario.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    tiene_me_gusta = db.execute(select(models.MeGusta).where(
        models.MeGusta.id_usuario == current_user.id,
        models.MeGusta.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if vista.puntuacion or tiene_diario or tiene_me_gusta:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No puedes desmarcar una película con puntuación, entradas de diario o me gusta")

    db.delete(vista)
    db.commit()


# ─── PUNTUACIÓN ───────────────────────────────────────────────────────────

# PUT /api/peliculas/{tmdb_id}/puntuacion
# Guarda o actualiza la puntuación del usuario para una película.
# Si el usuario no la tenía marcada como vista, la marca automáticamente.
@router.put("/{tmdb_id}/puntuacion")
def puntuar(tmdb_id: int, puntuacion_data: schemas.PuntuacionCreate,
            db: Session = Depends(database.get_db),
            current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

    vista = db.execute(select(models.Vista).where(
        models.Vista.id_usuario == current_user.id,
        models.Vista.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if vista:
        # Si ya la tenía vista, solo actualizamos la puntuación
        vista.puntuacion = puntuacion_data.puntuacion
        db.commit()
        db.refresh(vista)
    else:
        # Si no la tenía vista, creamos la vista con puntuación y la quitamos de watchlist
        vista = models.Vista(
            id_usuario=current_user.id,
            id_pelicula=pelicula.id,
            puntuacion=puntuacion_data.puntuacion
        )
        db.add(vista)
        db.commit()
        db.refresh(vista)
        eliminar_de_watchlist(current_user.id, pelicula.id, db)

    return {"detail": "Puntuación guardada", "puntuacion": vista.puntuacion}


# DELETE /api/peliculas/{tmdb_id}/puntuacion
# Elimina la puntuación del usuario para una película (la pone a null).
@router.delete("/{tmdb_id}/puntuacion")
def eliminar_puntuacion(tmdb_id: int, db: Session = Depends(database.get_db),
                        current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(select(models.Pelicula).where(
        models.Pelicula.tmdb_id == tmdb_id
    )).scalar_one_or_none()

    if not pelicula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Película no encontrada")

    vista = db.execute(select(models.Vista).where(
        models.Vista.id_usuario == current_user.id,
        models.Vista.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if not vista:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No has visto esta película")

    vista.puntuacion = None
    db.commit()

    return {"detail": "Puntuación eliminada"}


# ─── DIARIO ───────────────────────────────────────────────────────────────

# POST /api/peliculas/{tmdb_id}/diario
# Crea una nueva entrada en el diario para una película.
# Si no estaba marcada como vista, la marca automáticamente.
@router.post("/{tmdb_id}/diario", status_code=status.HTTP_201_CREATED, response_model=schemas.EntradaDiarioOut)
def crear_entrada_diario(tmdb_id: int, entrada_data: schemas.EntradaDiarioCreate,
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

    # Si no tiene la película como vista, la marcamos automáticamente
    vista = db.execute(select(models.Vista).where(
        models.Vista.id_usuario == current_user.id,
        models.Vista.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if not vista:
        vista = models.Vista(id_usuario=current_user.id, id_pelicula=pelicula.id)
        db.add(vista)
        db.commit()
        eliminar_de_watchlist(current_user.id, pelicula.id, db)

    nueva_entrada = models.EntradaDiario(
        id_usuario=current_user.id,
        id_pelicula=pelicula.id,
        fecha_visionado=entrada_data.fecha_visionado,
        resena=entrada_data.resena
    )
    db.add(nueva_entrada)
    db.commit()
    db.refresh(nueva_entrada)

    return nueva_entrada


# PUT /api/peliculas/diario/{id_entrada}
# Edita una entrada existente del diario. Solo puede editarla su autor.
@router.put("/diario/{id_entrada}", response_model=schemas.EntradaDiarioOut)
def editar_entrada_diario(id_entrada: int, entrada_data: schemas.EntradaDiarioUpdate,
                          db: Session = Depends(database.get_db),
                          current_user: models.Usuario = Depends(oauth2.get_current_user)):

    entrada = db.execute(select(models.EntradaDiario).where(
        models.EntradaDiario.id == id_entrada
    )).scalar_one_or_none()

    if not entrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    # Verificamos que la entrada pertenece al usuario autenticado
    if entrada.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes editar esta entrada")

    # Solo actualizamos los campos que se envíen (los que no sean None)
    if entrada_data.fecha_visionado:
        entrada.fecha_visionado = entrada_data.fecha_visionado
    if entrada_data.resena is not None:
        entrada.resena = entrada_data.resena

    db.commit()
    db.refresh(entrada)

    return entrada


# ─── ME GUSTA ─────────────────────────────────────────────────────────────

# POST /api/peliculas/{tmdb_id}/me-gusta
# Da me gusta a una película.
@router.post("/{tmdb_id}/me-gusta", status_code=status.HTTP_201_CREATED)
def dar_me_gusta(tmdb_id: int, db: Session = Depends(database.get_db),
                 current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

    existente = db.execute(select(models.MeGusta).where(
        models.MeGusta.id_usuario == current_user.id,
        models.MeGusta.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya le has dado me gusta")

    me_gusta = models.MeGusta(id_usuario=current_user.id, id_pelicula=pelicula.id)
    db.add(me_gusta)
    db.commit()

    return {"detail": "Me gusta añadido"}


# DELETE /api/peliculas/{tmdb_id}/me-gusta
# Quita el me gusta de una película.
@router.delete("/{tmdb_id}/me-gusta")
def quitar_me_gusta(tmdb_id: int, db: Session = Depends(database.get_db),
                    current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(select(models.Pelicula).where(
        models.Pelicula.tmdb_id == tmdb_id
    )).scalar_one_or_none()

    if not pelicula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Película no encontrada")

    me_gusta = db.execute(select(models.MeGusta).where(
        models.MeGusta.id_usuario == current_user.id,
        models.MeGusta.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if not me_gusta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No le has dado me gusta")

    db.delete(me_gusta)
    db.commit()

    return {"detail": "Me gusta eliminado"}


# ─── WATCHLIST ────────────────────────────────────────────────────────────

# POST /api/peliculas/{tmdb_id}/watchlist
# Añade una película a la watchlist del usuario.
@router.post("/{tmdb_id}/watchlist", status_code=status.HTTP_201_CREATED)
def añadir_watchlist(tmdb_id: int, db: Session = Depends(database.get_db),
                     current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

    existente = db.execute(select(models.Watchlist).where(
        models.Watchlist.id_usuario == current_user.id,
        models.Watchlist.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La película ya está en tu watchlist")

    watchlist = models.Watchlist(id_usuario=current_user.id, id_pelicula=pelicula.id)
    db.add(watchlist)
    db.commit()

    return {"detail": "Película añadida a la watchlist"}


# DELETE /api/peliculas/{tmdb_id}/watchlist
# Elimina una película de la watchlist del usuario.
@router.delete("/{tmdb_id}/watchlist")
def quitar_watchlist(tmdb_id: int, db: Session = Depends(database.get_db),
                     current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = db.execute(select(models.Pelicula).where(
        models.Pelicula.tmdb_id == tmdb_id
    )).scalar_one_or_none()

    if not pelicula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Película no encontrada")

    watchlist = db.execute(select(models.Watchlist).where(
        models.Watchlist.id_usuario == current_user.id,
        models.Watchlist.id_pelicula == pelicula.id
    )).scalar_one_or_none()

    if not watchlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La película no está en tu watchlist")

    db.delete(watchlist)
    db.commit()

    return {"detail": "Película eliminada de la watchlist"}


# ─── FAVORITAS ────────────────────────────────────────────────────────────

# PUT /api/peliculas/favoritas
# Reemplaza todas las favoritas del usuario con la nueva lista.
# Se envía una lista de hasta 4 tmdb_ids en el orden deseado.
@router.put("/favoritas")
def configurar_favoritas(tmdb_ids: list[int],
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if len(tmdb_ids) > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 4 películas favoritas")

    # Eliminamos todas las favoritas actuales del usuario
    db.execute(delete(models.PeliculaFavorita).where(models.PeliculaFavorita.id_usuario == current_user.id))
    db.commit()

    # Insertamos las nuevas favoritas en el orden indicado (enumerate empieza en 1)
    for orden, tmdb_id in enumerate(tmdb_ids, start=1):
        pelicula = get_or_create_pelicula(tmdb_id, db)
        favorita = models.PeliculaFavorita(
            id_usuario=current_user.id,
            id_pelicula=pelicula.id,
            orden=orden
        )
        db.add(favorita)

    db.commit()

    return {"detail": "Favoritas actualizadas"}
