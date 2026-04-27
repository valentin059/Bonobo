from sqlalchemy import func, extract, select
from .. import models


def verificar_logros(db, usuario_id: int) -> list[str]:
    """Devuelve los códigos de logro que el usuario tiene que recibir (sin filtrar ya obtenidos)."""
    logros = []

    # vistas
    total_vistas = db.execute(
        select(func.count()).select_from(models.Vista)
        .where(models.Vista.id_usuario == usuario_id)
    ).scalar()

    if total_vistas >= 1:
        logros.append("PRIMERA_FUNCION")
    if total_vistas >= 10:
        logros.append("CINEFILO")
    if total_vistas >= 20:
        logros.append("CINEFILO_PROGRESO")
    if total_vistas >= 100:
        logros.append("MAESTRO_CINEFILO")

    # entradas de diario (= reseñas)
    total_resenas = db.execute(
        select(func.count()).select_from(models.EntradaDiario)
        .where(models.EntradaDiario.id_usuario == usuario_id)
    ).scalar()

    if total_resenas >= 1:
        logros.append("CRITICO_PROCESO")
    if total_resenas >= 3:
        logros.append("PERIODISTA")
    if total_resenas >= 50:
        logros.append("PLUMA_DE_ORO")

    # favoritas
    total_favs = db.execute(
        select(func.count()).select_from(models.PeliculaFavorita)
        .where(models.PeliculaFavorita.id_usuario == usuario_id)
    ).scalar()

    if total_favs >= 4:
        logros.append("CON_CRITERIO")

    # watchlist
    total_watchlist = db.execute(
        select(func.count()).select_from(models.Watchlist)
        .where(models.Watchlist.id_usuario == usuario_id)
    ).scalar()

    if total_watchlist >= 5:
        logros.append("PLANIFICADOR")

    # maratón: 10 vistas en el mismo mes
    maraton = db.execute(
        select(
            extract("year", models.Vista.created_at).label("anio"),
            extract("month", models.Vista.created_at).label("mes"),
            func.count(models.Vista.id).label("total")
        )
        .where(models.Vista.id_usuario == usuario_id)
        .group_by(
            extract("year", models.Vista.created_at),
            extract("month", models.Vista.created_at)
        )
        .having(func.count(models.Vista.id) >= 10)
    ).first()

    if maraton:
        logros.append("MARATONISTA")

    # sociales: seguidos
    total_seguidos = db.execute(
        select(func.count()).select_from(models.Seguidor)
        .where(models.Seguidor.id_seguidor == usuario_id)
    ).scalar()

    if total_seguidos >= 1:
        logros.append("SOCIABLE")

    # mutualidades: usuarios que se siguen mutuamente
    mutuos = db.execute(
        select(func.count()).select_from(models.Seguidor).where(
            models.Seguidor.id_seguidor == usuario_id,
            models.Seguidor.id_seguido.in_(
                select(models.Seguidor.id_seguidor).where(
                    models.Seguidor.id_seguido == usuario_id
                )
            )
        )
    ).scalar()

    if mutuos >= 10:
        logros.append("CONEXION_MUTUA")

    # seguidores
    total_seguidores = db.execute(
        select(func.count()).select_from(models.Seguidor)
        .where(models.Seguidor.id_seguido == usuario_id)
    ).scalar()

    if total_seguidores >= 300:
        logros.append("INFLUENCER")

    # comentarios en reseñas de otros
    total_comentarios = db.execute(
        select(func.count()).select_from(models.ComentarioResena)
        .where(models.ComentarioResena.id_usuario == usuario_id)
    ).scalar()

    if total_comentarios >= 1:
        logros.append("CONVERSADOR")

    # nostálgico: 5 películas anteriores a 1980
    peliculas_antiguas = db.execute(
        select(func.count()).select_from(models.Vista)
        .join(models.Pelicula, models.Vista.id_pelicula == models.Pelicula.id)
        .where(
            models.Vista.id_usuario == usuario_id,
            models.Pelicula.anio_estreno < 1980
        )
    ).scalar()

    if peliculas_antiguas >= 5:
        logros.append("NOSTALGICO")

    # trasnochador: entrada de diario creada entre las 2:00 y las 5:00
    trasnochador = db.execute(
        select(func.count()).select_from(models.EntradaDiario)
        .where(
            models.EntradaDiario.id_usuario == usuario_id,
            func.extract("hour", models.EntradaDiario.created_at) >= 2,
            func.extract("hour", models.EntradaDiario.created_at) < 5
        )
    ).scalar()

    if trasnochador >= 1:
        logros.append("TRASNOCHADOR")

    # doble función: 2 o más entradas de diario el mismo día
    doble_funcion = db.execute(
        select(func.count()).select_from(
            select(models.EntradaDiario.fecha_visionado)
            .where(models.EntradaDiario.id_usuario == usuario_id)
            .group_by(models.EntradaDiario.fecha_visionado)
            .having(func.count(models.EntradaDiario.id) >= 2)
            .subquery()
        )
    ).scalar()

    if doble_funcion >= 1:
        logros.append("DOBLE_FUNCION")

    # hater profesional: reseña con puntuación <= 1
    hater = db.execute(
        select(func.count()).select_from(models.EntradaDiario)
        .where(
            models.EntradaDiario.id_usuario == usuario_id,
            models.EntradaDiario.resena.isnot(None),
            models.EntradaDiario.puntuacion <= 1
        )
    ).scalar()

    if hater >= 1:
        logros.append("HATER_PROFESIONAL")

    return logros


def otorgar_logros(db, usuario_id: int, codigos: list[str]) -> None:
    """Crea las filas en usuario_logros para los logros que el usuario aún no tiene."""
    for codigo in codigos:
        logro = db.execute(
            select(models.Logro).where(models.Logro.codigo == codigo)
        ).scalar_one_or_none()

        if not logro:
            continue

        ya_tiene = db.execute(
            select(models.UsuarioLogro).where(
                models.UsuarioLogro.id_usuario == usuario_id,
                models.UsuarioLogro.id_logro == logro.id
            )
        ).scalar_one_or_none()

        if ya_tiene:
            continue

        db.add(models.UsuarioLogro(id_usuario=usuario_id, id_logro=logro.id))

    db.commit()
