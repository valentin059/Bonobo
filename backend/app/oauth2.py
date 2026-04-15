from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from .config import settings

# oauth2_scheme extrae el token JWT del header "Authorization: Bearer <token>".
# Si no hay token, lanza un error automáticamente (auto_error=True por defecto).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/auth/login')

# Igual que el anterior pero auto_error=False: si no hay token, devuelve None
# en lugar de lanzar error. Se usa en endpoints donde el login es opcional.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='api/auth/login', auto_error=False)

# Leemos la configuración JWT desde el .env
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


# Crea y devuelve un token JWT firmado con los datos del usuario.
# El token incluye una fecha de expiración.
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})                                       # añadimos la expiración
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)   # firmamos el token
    return encoded_jwt


# Decodifica y valida un token JWT.
# Si el token es inválido o ha expirado, lanza la excepción que se le pase.
def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")   # extraemos el id del usuario del payload
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception
    return token_data


# Dependencia para endpoints donde el usuario puede estar o no logueado.
# Sin token → devuelve None (visitante).
# Token presente pero inválido/caducado → lanza 401 (no tratar como visitante).
def get_optional_user(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(database.get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user = db.execute(
            select(models.Usuario).where(models.Usuario.id == user_id)
        ).scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token caducado o inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Dependencia para endpoints que requieren usuario logueado obligatoriamente.
# Si el token no existe, es inválido o el usuario no existe, devuelve 401 Unauthorized.
# Se usa con: current_user: models.Usuario = Depends(oauth2.get_current_user)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se han podido validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data = verify_access_token(token, credentials_exception)

    # Buscamos el usuario en la BD con el id que venía en el token
    user = db.execute(select(models.Usuario).where(models.Usuario.id == token_data.id)).scalar_one_or_none()

    return user