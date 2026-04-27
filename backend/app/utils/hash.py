import bcrypt

# Convierte una contraseña en texto plano a su versión cifrada (hash).
# Nunca guardamos contraseñas en texto plano en la base de datos.
# bcrypt añade automáticamente un "salt" (dato aleatorio) para que
# dos contraseñas iguales generen hashes distintos.
def hash_password(password: str):
    pwd_bytes = password.encode('utf-8')   # bcrypt necesita bytes, no string
    salt = bcrypt.gensalt()                # genera un salt aleatorio
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8') # devolvemos string para guardarlo en la BD

# Comprueba si una contraseña en texto plano coincide con su hash guardado.
# Se usa en el login: compara lo que escribe el usuario con lo almacenado en la BD.
def verify_password(plain_password: str, hashed_password: str):
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)  # devuelve True si coinciden