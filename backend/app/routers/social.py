from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import database, models, schemas, oauth2

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Social"]
)


# ─── SEGUIR / DEJAR DE SEGUIR ─────────────────────────────────────────────

# POST /api/usuarios/{id}/seguir
@router.post("/{id}/seguir", status_code=status.HTTP_201_CREATED)
def seguir_usuario(id: int,
                   db: Session = Depends(database.get_db),
                   current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No puedes seguirte a ti mismo.")

    objetivo = db.execute(
        select(models.Usuario).where(models.Usuario.id == id)
    ).scalar_one_or_none()

    if not objetivo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    ya_sigue = db.execute(
        select(models.Seguidor).where(
            models.Seguidor.id_seguidor == current_user.id,
            models.Seguidor.id_seguido == id
        )
    ).scalar_one_or_none()

    if ya_sigue:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya sigues a este usuario.")

    db.add(models.Seguidor(id_seguidor=current_user.id, id_seguido=id))
    db.commit()

    return {"detail": f"Ahora sigues a {objetivo.username}."}


# DELETE /api/usuarios/{id}/seguir
@router.delete("/{id}/seguir", status_code=status.HTTP_200_OK)
def dejar_seguir_usuario(id: int,
                         db: Session = Depends(database.get_db),
                         current_user: models.Usuario = Depends(oauth2.get_current_user)):

    seguidor = db.execute(
        select(models.Seguidor).where(
            models.Seguidor.id_seguidor == current_user.id,
            models.Seguidor.id_seguido == id
        )
    ).scalar_one_or_none()

    if not seguidor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sigues a este usuario.")

    db.delete(seguidor)
    db.commit()

    return {"detail": "Has dejado de seguir al usuario."}


# ─── LISTAS DE SEGUIDORES / SEGUIDOS ─────────────────────────────────────

# GET /api/usuarios/{id}/seguidores
@router.get("/{id}/seguidores", response_model=list[schemas.UsuarioResumen])
def get_seguidores(id: int,
                   skip: int = 0,
                   limit: int = Query(20, ge=1, le=100),
                   db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # join para obtener los usuarios que siguen a {id}
    seguidores = db.execute(
        select(models.Usuario)
        .join(models.Seguidor, models.Seguidor.id_seguidor == models.Usuario.id)
        .where(models.Seguidor.id_seguido == id)
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return seguidores


# GET /api/usuarios/{id}/seguidos
@router.get("/{id}/seguidos", response_model=list[schemas.UsuarioResumen])
def get_seguidos(id: int,
                 skip: int = 0,
                 limit: int = Query(20, ge=1, le=100),
                 db: Session = Depends(database.get_db)):

    if not db.execute(select(models.Usuario).where(models.Usuario.id == id)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # join para obtener los usuarios a los que sigue {id}
    seguidos = db.execute(
        select(models.Usuario)
        .join(models.Seguidor, models.Seguidor.id_seguido == models.Usuario.id)
        .where(models.Seguidor.id_seguidor == id)
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return seguidos
