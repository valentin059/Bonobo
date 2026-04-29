from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import database, models, schemas, oauth2
from typing import Optional
from ..services.logros import verificar_logros, otorgar_logros

# dos routers porque las rutas de comentarios tienen prefijos distintos:
# router_diario      -> /api/diario/{id}/*
# router_comentarios -> /api/comentarios/{id}
router_diario = APIRouter(
    prefix="/api/diario",
    tags=["Diario"]
)

router_comentarios = APIRouter(
    prefix="/api/comentarios",
    tags=["Diario"]
)


# ─── EDITAR ENTRADA ───────────────────────────────────────────────────────

# PUT /api/diario/{id_entrada}
@router_diario.put("/{id_entrada}", response_model=schemas.EntradaDiarioOut)
def editar_entrada_diario(id_entrada: int, entrada_data: schemas.EntradaDiarioUpdate,
                          db: Session = Depends(database.get_db),
                          current_user: models.Usuario = Depends(oauth2.get_current_user)):

    entrada = db.execute(select(models.EntradaDiario).where(
        models.EntradaDiario.id == id_entrada
    )).scalar_one_or_none()

    if not entrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    if entrada.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes editar esta entrada")

    if entrada_data.fecha_visionado:
        entrada.fecha_visionado = entrada_data.fecha_visionado
    if 'resena' in entrada_data.model_fields_set:
        entrada.resena = entrada_data.resena
    if 'puntuacion' in entrada_data.model_fields_set:
        entrada.puntuacion = entrada_data.puntuacion

    db.commit()
    db.refresh(entrada)


    return entrada


# ─── BORRAR ENTRADA ───────────────────────────────────────────────────────

# DELETE /api/diario/{id_entrada}
# Elimina una entrada del diario propia. La película sigue marcada como vista.
@router_diario.delete("/{id_entrada}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_entrada_diario(id_entrada: int,
                          db: Session = Depends(database.get_db),
                          current_user: models.Usuario = Depends(oauth2.get_current_user)):

    entrada = db.execute(
        select(models.EntradaDiario).where(models.EntradaDiario.id == id_entrada)
    ).scalar_one_or_none()

    if not entrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Entrada no encontrada.")

    # Solo el dueño puede borrar su entrada
    if entrada.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes borrar la entrada de otro usuario.")

    db.delete(entrada)
    db.commit()


# ─── COMENTARIOS ──────────────────────────────────────────────────────────

# POST /api/diario/{id_entrada}/comentarios
@router_diario.post("/{id_entrada}/comentarios",
                    response_model=schemas.ComentarioOut,
                    status_code=status.HTTP_201_CREATED)
def crear_comentario(id_entrada: int,
                     comentario_data: schemas.ComentarioCreate,
                     db: Session = Depends(database.get_db),
                     current_user: models.Usuario = Depends(oauth2.get_current_user)):

    entrada = db.execute(
        select(models.EntradaDiario).where(models.EntradaDiario.id == id_entrada)
    ).scalar_one_or_none()

    if not entrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Entrada de diario no encontrada.")

    comentario = models.ComentarioResena(
        id_usuario=current_user.id,
        id_entrada_diario=id_entrada,
        texto=comentario_data.texto
    )
    db.add(comentario)
    db.commit()
    logros = verificar_logros(db, current_user.id)
    otorgar_logros(db, current_user.id, logros)
    db.refresh(comentario)
    

    # construimos la respuesta manualmente para incluir username y avatar
    return schemas.ComentarioOut(
        id=comentario.id,
        id_usuario=current_user.id,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        texto=comentario.texto,
        created_at=comentario.created_at
    )


# GET /api/diario/{id_entrada}/comentarios
@router_diario.get("/{id_entrada}/comentarios",
                   response_model=list[schemas.ComentarioOut])
def get_comentarios(id_entrada: int,
                    skip: int = 0,
                    limit: int = Query(20, ge=1, le=100),
                    db: Session = Depends(database.get_db)):

    if not db.execute(
        select(models.EntradaDiario).where(models.EntradaDiario.id == id_entrada)
    ).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Entrada de diario no encontrada.")

    # join con Usuario para traer username y avatar en la misma query
    rows = db.execute(
        select(models.ComentarioResena, models.Usuario)
        .join(models.Usuario, models.ComentarioResena.id_usuario == models.Usuario.id)
        .where(models.ComentarioResena.id_entrada_diario == id_entrada)
        .order_by(models.ComentarioResena.created_at.asc())
        .offset(skip)
        .limit(limit)
    ).all()

    return [
        schemas.ComentarioOut(
            id=c.id,
            id_usuario=c.id_usuario,
            username=u.username,
            avatar_url=u.avatar_url,
            texto=c.texto,
            created_at=c.created_at
        )
        for c, u in rows
    ]


# DELETE /api/comentarios/{id_comentario}
@router_comentarios.delete("/{id_comentario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comentario(id_comentario: int,
                        db: Session = Depends(database.get_db),
                        current_user: models.Usuario = Depends(oauth2.get_current_user)):

    comentario = db.execute(
        select(models.ComentarioResena).where(models.ComentarioResena.id == id_comentario)
    ).scalar_one_or_none()

    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado.")

    if comentario.id_usuario != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No puedes eliminar el comentario de otro usuario.")

    db.delete(comentario)
    db.commit()


# ─── LIKES ────────────────────────────────────────────────────────────────

# POST /api/diario/{id_entrada}/like
@router_diario.post("/{id_entrada}/like", status_code=status.HTTP_201_CREATED)
def dar_like(id_entrada: int,
             db: Session = Depends(database.get_db),
             current_user: models.Usuario = Depends(oauth2.get_current_user)):

    if not db.execute(
        select(models.EntradaDiario).where(models.EntradaDiario.id == id_entrada)
    ).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Entrada de diario no encontrada.")

    ya_existe = db.execute(
        select(models.LikeResena).where(
            models.LikeResena.id_usuario == current_user.id,
            models.LikeResena.id_entrada_diario == id_entrada
        )
    ).scalar_one_or_none()

    if ya_existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ya le has dado like a esta reseña.")

    db.add(models.LikeResena(id_usuario=current_user.id, id_entrada_diario=id_entrada))
    db.commit()

    return {"detail": "Like añadido."}


# DELETE /api/diario/{id_entrada}/like
@router_diario.delete("/{id_entrada}/like", status_code=status.HTTP_200_OK)
def quitar_like(id_entrada: int,
                db: Session = Depends(database.get_db),
                current_user: models.Usuario = Depends(oauth2.get_current_user)):

    like = db.execute(
        select(models.LikeResena).where(
            models.LikeResena.id_usuario == current_user.id,
            models.LikeResena.id_entrada_diario == id_entrada
        )
    ).scalar_one_or_none()

    if not like:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No le has dado like a esta reseña.")

    db.delete(like)
    db.commit()

    return {"detail": "Like eliminado."}