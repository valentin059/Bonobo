from sqlalchemy import func, extract, select
from .. import models


# Mira que logros le faltan al user, comprueba si los cumple y los guarda.
# Solo evaluamos los logros que NO tiene aun para no lanzar queries de mas.
def comprobar_y_dar_logros(db, usuario_id: int) -> None:
    # codigos de logros que ya tiene desbloqueados
    ya_obtenidos = set(db.execute(
        select(models.Logro.codigo)
        .join(models.UsuarioLogro, models.UsuarioLogro.id_logro == models.Logro.id)
        .where(models.UsuarioLogro.id_usuario == usuario_id)
    ).scalars().all())

    pendientes = []  # codigos que vamos a desbloquear ahora

    def falta(codigo: str) -> bool:
        return codigo not in ya_obtenidos

    # vistas — solo cuenta la query si me falta alguno de estos
    LOGROS_VISTAS = ("PRIMERA_FUNCION", "CINEFILO", "CINEFILO_PROGRESO", "MAESTRO_CINEFILO")
    if any(falta(c) for c in LOGROS_VISTAS):
        total_vistas = db.execute(
            select(func.count()).select_from(models.Vista)
            .where(models.Vista.id_usuario == usuario_id)
        ).scalar()

        if falta("PRIMERA_FUNCION") and total_vistas >= 1:
            pendientes.append("PRIMERA_FUNCION")
        if falta("CINEFILO") and total_vistas >= 10:
            pendientes.append("CINEFILO")
        if falta("CINEFILO_PROGRESO") and total_vistas >= 20:
            pendientes.append("CINEFILO_PROGRESO")
        if falta("MAESTRO_CINEFILO") and total_vistas >= 100:
            pendientes.append("MAESTRO_CINEFILO")

    # entradas de diario (= reseñas)
    LOGROS_RESENAS = ("CRITICO_PROCESO", "PERIODISTA", "PLUMA_DE_ORO")
    if any(falta(c) for c in LOGROS_RESENAS):
        total_resenas = db.execute(
            select(func.count()).select_from(models.EntradaDiario)
            .where(models.EntradaDiario.id_usuario == usuario_id)
        ).scalar()

        if falta("CRITICO_PROCESO") and total_resenas >= 1:
            pendientes.append("CRITICO_PROCESO")
        if falta("PERIODISTA") and total_resenas >= 3:
            pendientes.append("PERIODISTA")
        if falta("PLUMA_DE_ORO") and total_resenas >= 50:
            pendientes.append("PLUMA_DE_ORO")

    # 4 favoritas configuradas
    if falta("CON_CRITERIO"):
        total_favs = db.execute(
            select(func.count()).select_from(models.PeliculaFavorita)
            .where(models.PeliculaFavorita.id_usuario == usuario_id)
        ).scalar()
        if total_favs >= 4:
            pendientes.append("CON_CRITERIO")

    # watchlist
    if falta("PLANIFICADOR"):
        total_watchlist = db.execute(
            select(func.count()).select_from(models.Watchlist)
            .where(models.Watchlist.id_usuario == usuario_id)
        ).scalar()
        if total_watchlist >= 5:
            pendientes.append("PLANIFICADOR")

    # maraton: 10 vistas o mas en un mismo mes
    if falta("MARATONISTA"):
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
            pendientes.append("MARATONISTA")

    # social: ya sigues a alguien
    if falta("SOCIABLE"):
        total_seguidos = db.execute(
            select(func.count()).select_from(models.Seguidor)
            .where(models.Seguidor.id_seguidor == usuario_id)
        ).scalar()
        if total_seguidos >= 1:
            pendientes.append("SOCIABLE")

    # tio sigues a 10 que tambien te siguen
    if falta("CONEXION_MUTUA"):
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
            pendientes.append("CONEXION_MUTUA")

    # +300 seguidores
    if falta("INFLUENCER"):
        total_seguidores = db.execute(
            select(func.count()).select_from(models.Seguidor)
            .where(models.Seguidor.id_seguido == usuario_id)
        ).scalar()
        if total_seguidores >= 300:
            pendientes.append("INFLUENCER")

    # primer comentario en una reseña ajena
    if falta("CONVERSADOR"):
        total_comentarios = db.execute(
            select(func.count()).select_from(models.ComentarioResena)
            .where(models.ComentarioResena.id_usuario == usuario_id)
        ).scalar()
        if total_comentarios >= 1:
            pendientes.append("CONVERSADOR")

    # 5 pelis vistas anteriores a 1980
    if falta("NOSTALGICO"):
        antiguas = db.execute(
            select(func.count()).select_from(models.Vista)
            .join(models.Pelicula, models.Vista.id_pelicula == models.Pelicula.id)
            .where(
                models.Vista.id_usuario == usuario_id,
                models.Pelicula.anio_estreno < 1980
            )
        ).scalar()
        if antiguas >= 5:
            pendientes.append("NOSTALGICO")

    # entrada de diario creada entre las 02:00 y 05:00
    if falta("TRASNOCHADOR"):
        trasnochador = db.execute(
            select(func.count()).select_from(models.EntradaDiario)
            .where(
                models.EntradaDiario.id_usuario == usuario_id,
                func.extract("hour", models.EntradaDiario.created_at) >= 2,
                func.extract("hour", models.EntradaDiario.created_at) < 5
            )
        ).scalar()
        if trasnochador >= 1:
            pendientes.append("TRASNOCHADOR")

    # 2+ entradas de diario el mismo dia
    if falta("DOBLE_FUNCION"):
        doble = db.execute(
            select(func.count()).select_from(
                select(models.EntradaDiario.fecha_visionado)
                .where(models.EntradaDiario.id_usuario == usuario_id)
                .group_by(models.EntradaDiario.fecha_visionado)
                .having(func.count(models.EntradaDiario.id) >= 2)
                .subquery()
            )
        ).scalar()
        if doble >= 1:
            pendientes.append("DOBLE_FUNCION")

    # reseña con puntuacion <= 1
    if falta("HATER_PROFESIONAL"):
        hater = db.execute(
            select(func.count()).select_from(models.EntradaDiario)
            .where(
                models.EntradaDiario.id_usuario == usuario_id,
                models.EntradaDiario.resena.isnot(None),
                models.EntradaDiario.puntuacion <= 1
            )
        ).scalar()
        if hater >= 1:
            pendientes.append("HATER_PROFESIONAL")

    # si no hay nada nuevo nos vamos sin tocar BD
    if not pendientes:
        return

    # cargamos los logros que vamos a otorgar y los insertamos
    logros_a_dar = db.execute(
        select(models.Logro).where(models.Logro.codigo.in_(pendientes))
    ).scalars().all()

    for logro in logros_a_dar:
        db.add(models.UsuarioLogro(id_usuario=usuario_id, id_logro=logro.id))

    db.commit()
