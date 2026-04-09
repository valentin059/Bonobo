from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from .. import database, schemas, models, utils, oauth2

# Todas las rutas de este router empiezan por /api/auth
# y aparecen agrupadas como "Autenticación" en /docs
router = APIRouter(
    prefix="/api/auth",
    tags=['Autenticación']
)


# POST /api/auth/registro
# Crea un nuevo usuario. Devuelve los datos del usuario (sin contraseña).
@router.post('/registro', status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def crear_usuario(usuario: schemas.UserCreate, db: Session = Depends(database.get_db)):

    # Comprobamos que el email no esté ya registrado
    usuario_existente = db.execute(select(models.Usuario).where(models.Usuario.email == usuario.email)).scalar_one_or_none()
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ese email ya está registrado")

    # Ciframos la contraseña antes de guardarla (nunca se guarda en texto plano)
    hashed_password = utils.hash_password(usuario.password)

    nuevo_usuario = models.Usuario(
        email=usuario.email,
        username=usuario.username,
        password_hash=hashed_password
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)   # recarga el objeto con los datos generados por la BD (como el id)

    return nuevo_usuario


# POST /api/auth/login
# Comprueba las credenciales y devuelve un token JWT si son correctas.
# Usa OAuth2PasswordRequestForm: espera un formulario con campos "username" y "password".
# En nuestro caso el campo "username" contiene el email.
@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    # Buscamos al usuario por email (OAuth2PasswordRequestForm llama "username" al email)
    user = db.execute(select(models.Usuario).where(models.Usuario.email == user_credentials.username)).scalar_one_or_none()

    # Si el email no existe, devolvemos error 403 (mismo error que contraseña incorrecta,
    # para no dar pistas sobre qué emails están registrados)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credenciales inválidas"
        )

    # Verificamos que la contraseña introducida coincide con el hash guardado
    if not utils.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credenciales inválidas"
        )

    # Creamos el token JWT con el id del usuario dentro
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
