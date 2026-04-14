from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from .. import database, schemas, models, utils, oauth2

router = APIRouter(
    prefix="/api/auth",
    tags=['Autenticación']
)


# POST /api/auth/registro
@router.post('/registro', status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def crear_usuario(usuario: schemas.UserCreate, db: Session = Depends(database.get_db)):

    usuario_existente = db.execute(select(models.Usuario).where(models.Usuario.email == usuario.email)).scalar_one_or_none()
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ese email ya está registrado")

    hashed_password = utils.hash_password(usuario.password)

    nuevo_usuario = models.Usuario(
        email=usuario.email,
        username=usuario.username,
        password_hash=hashed_password
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


# POST /api/auth/login
# OAuth2PasswordRequestForm espera form-urlencoded con campos "username" y "password"
@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    # el campo "username" de OAuth2 contiene el email en nuestra app
    user = db.execute(select(models.Usuario).where(models.Usuario.email == user_credentials.username)).scalar_one_or_none()

    # mismo error para email y contraseña incorrectos — no revelamos cuál es
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credenciales inválidas")

    if not utils.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credenciales inválidas")

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
