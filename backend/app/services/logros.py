from sqlalchemy import func, extract, select
from .. import models


# ───────────────────────────────
# CALCULAR LOGROS
# ───────────────────────────────
def verificar_logros(db, usuario_id: int):
    logros = []

    # ─── VISTAS ───────────────────
    total_vistas = db.query(models.Vista).filter(
        models.Vista.id_usuario == usuario_id
    ).count()

    if total_vistas >= 1:
        logros.append("PRIMERA_FUNCION")
    if total_vistas >= 10:
        logros.append("CINEFILO")
    if total_vistas >= 20:
        logros.append("CINEFILO_PROGRESO")
    if total_vistas >= 100:
        logros.append("MAESTRO_CINEFILO")

    # ─── RESEÑAS ──────────────────
    total_resenas = db.query(models.EntradaDiario).filter(
        models.EntradaDiario.id_usuario == usuario_id
    ).count()

    if total_resenas >= 1:
        logros.append("CRITICO_PROCESO")
    if total_resenas >= 3:
        logros.append("PERIODISTA")
    if total_resenas >= 50:
        logros.append("PLUMA_DE_ORO")

    # ─── FAVORITAS ────────────────
    total_favs = db.query(models.PeliculaFavorita).filter(
        models.PeliculaFavorita.id_usuario == usuario_id
    ).count()

    if total_favs >= 4:
        logros.append("CON_CRITERIO")

    # ─── WATCHLIST ────────────────
    total_watchlist = db.query(models.Watchlist).filter(
        models.Watchlist.id_usuario == usuario_id
    ).count()

    if total_watchlist >= 5:
        logros.append("PLANIFICADOR")

    # ─── MARATÓN (10 en un mes) ───
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

    # ─── SOCIALES ─────────────────
    total_seguidos = db.query(models.Seguidor).filter(
        models.Seguidor.id_seguidor == usuario_id
    ).count()

    if total_seguidos >= 1:
        logros.append("SOCIABLE")

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

    total_seguidores = db.query(models.Seguidor).filter(
        models.Seguidor.id_seguido == usuario_id
    ).count()

    if total_seguidores >= 300:
        logros.append("INFLUENCER")

            # ─── CONVERSADOR ──────────────
    total_comentarios = db.query(models.ComentarioResena).filter(
        models.ComentarioResena.id_usuario == usuario_id
    ).count()

    if total_comentarios >= 1:
        logros.append("CONVERSADOR")

            # ─── NOSTÁLGICO (5 películas antes de 1980) ───
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

    # ─── TRASNOCHADOR (entre 2:00 y 5:00 AM) ───
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

    # ─── DOBLE FUNCIÓN (2 películas en el mismo día) ───
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

    # ─── HATER PROFESIONAL (reseña con puntuación <= 1) ───
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


# ───────────────────────────────
# OTORGAR LOGROS
# ───────────────────────────────
def otorgar_logros(db, usuario_id: int, codigos: list[str]):

    for codigo in codigos:
        logro = db.query(models.Logro).filter(
            models.Logro.codigo == codigo
        ).first()

        if not logro:
            continue

        ya_tiene = db.query(models.UsuarioLogro).filter(
            models.UsuarioLogro.id_usuario == usuario_id,
            models.UsuarioLogro.id_logro == logro.id
        ).first()

        if ya_tiene:
            continue

        db.add(models.UsuarioLogro(
            id_usuario=usuario_id,
            id_logro=logro.id
        ))

    db.commit()