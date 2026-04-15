from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import database, models, schemas, oauth2, services

router = APIRouter(
    prefix="/api/peliculas",
    tags=["Acciones"]
)


# busca la película en BD; si no existe la pide a TMDB y la guarda
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


# quita la película de la watchlist si estaba; se llama al marcar como vista o puntuar
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
@router.post("/{tmdb_id}/vista", status_code=status.HTTP_201_CREATED)
def marcar_vista(tmdb_id: int, db: Session = Depends(database.get_db),
                 current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

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

    eliminar_de_watchlist(current_user.id, pelicula.id, db)

    return {"detail": "Película marcada como vista"}


# DELETE /api/peliculas/{tmdb_id}/vista
# no se permite si tiene puntuación, diario o me gusta asociados
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
# si no la tenía vista, la marca automáticamente
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
        vista.puntuacion = puntuacion_data.puntuacion
        db.commit()
        db.refresh(vista)
    else:
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
# marca como vista si no lo estaba
@router.post("/{tmdb_id}/diario", status_code=status.HTTP_201_CREATED, response_model=schemas.EntradaDiarioOut)
def crear_entrada_diario(tmdb_id: int, entrada_data: schemas.EntradaDiarioCreate,
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    pelicula = get_or_create_pelicula(tmdb_id, db)

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
        resena=entrada_data.resena,
        puntuacion=entrada_data.puntuacion,
    )
    db.add(nueva_entrada)
    db.commit()
    db.refresh(nueva_entrada)

    return nueva_entrada


# ─── ME GUSTA ─────────────────────────────────────────────────────────────

# POST /api/peliculas/{tmdb_id}/me-gusta
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
