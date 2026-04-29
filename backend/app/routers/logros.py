from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import database, models, oauth2

router = APIRouter(
    prefix="/api/logros",
    tags=["Logros"]
)


# devuelve los logros que tiene el user, con flag de si ya reclamó la XP
@router.get("/mis-logros")
def get_mis_logros(db: Session = Depends(database.get_db),
                   current_user: models.Usuario = Depends(oauth2.get_current_user)):

    rows = db.execute(
        select(models.UsuarioLogro, models.Logro)
        .join(models.Logro, models.UsuarioLogro.id_logro == models.Logro.id)
        .where(models.UsuarioLogro.id_usuario == current_user.id)
        .order_by(models.UsuarioLogro.created_at.desc())
    ).all()

    return [
        {
            "id_usuario_logro": ul.id,
            "codigo": l.codigo,
            "nombre": l.nombre,
            "descripcion": l.descripcion,
            "xp": l.xp,
            "xp_reclamado": ul.xp_reclamado,
            "desbloqueado_el": ul.created_at
        }
        for ul, l in rows
    ]


# devuelve TODOS los logros del catalogo y marca cuales tiene el user
@router.get("/todos")
def get_todos_logros(db: Session = Depends(database.get_db),
                     current_user: models.Usuario = Depends(oauth2.get_current_user)):

    todos = db.execute(
        select(models.Logro).order_by(models.Logro.id)
    ).scalars().all()

    # mapa id_logro -> UsuarioLogro para los que ya tiene el user
    desbloqueados = {
        ul.id_logro: ul
        for ul in db.execute(
            select(models.UsuarioLogro).where(
                models.UsuarioLogro.id_usuario == current_user.id
            )
        ).scalars().all()
    }

    return [
        {
            "codigo": l.codigo,
            "nombre": l.nombre,
            "descripcion": l.descripcion,
            "xp": l.xp,
            "desbloqueado": l.id in desbloqueados,
            "xp_reclamado": desbloqueados[l.id].xp_reclamado if l.id in desbloqueados else None,
            "desbloqueado_el": desbloqueados[l.id].created_at if l.id in desbloqueados else None,
        }
        for l in todos
    ]


# reclama la XP de un logro desbloqueado y recalcula el nivel.
# formula del nivel: (xp_total // 100) + 1
@router.post("/{id_usuario_logro}/reclamar")
def reclamar_xp(id_usuario_logro: int,
                db: Session = Depends(database.get_db),
                current_user: models.Usuario = Depends(oauth2.get_current_user)):

    usuario_logro = db.execute(
        select(models.UsuarioLogro).where(
            models.UsuarioLogro.id == id_usuario_logro,
            models.UsuarioLogro.id_usuario == current_user.id
        )
    ).scalar_one_or_none()

    if not usuario_logro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Logro no encontrado.")

    if usuario_logro.xp_reclamado:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ya reclamaste la XP de este logro.")

    logro = db.execute(
        select(models.Logro).where(models.Logro.id == usuario_logro.id_logro)
    ).scalar_one()

    usuario_logro.xp_reclamado = True

    # sumamos XP y recalculamos nivel con la formula del documento maestro
    current_user.xp_total += logro.xp
    current_user.nivel = (current_user.xp_total // 100) + 1

    db.commit()

    return {
        "detail": f"¡+{logro.xp} XP reclamados!",
        "xp_total": current_user.xp_total,
        "nivel": current_user.nivel
    }
