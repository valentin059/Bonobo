from sqlalchemy import Boolean, Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from ..database import Base

# Cada clase aquí representa una tabla en la base de datos.
# SQLAlchemy se encarga de traducir estas clases a SQL.


# ── Tabla: usuarios ────────────────────────────────────────────────────────
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String(255), nullable=False, unique=True)         # email único por usuario
    username = Column(String(50), nullable=False, unique=True)       # nombre de usuario único
    password_hash = Column(String(255), nullable=False)              # contraseña cifrada (nunca en texto plano)
    bio = Column(Text, nullable=True)                                # descripción del perfil (opcional)
    avatar_url = Column(String(500), nullable=True)                  # URL de la foto de perfil (opcional)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))  # fecha de registro


# ── Tabla: peliculas ───────────────────────────────────────────────────────
# Caché local de películas. No guardamos toda la info de TMDB, solo lo esencial
# para poder relacionar las acciones del usuario con una película concreta.
class Pelicula(Base):
    __tablename__ = "peliculas"

    id = Column(Integer, primary_key=True, nullable=False)
    tmdb_id = Column(Integer, nullable=False, unique=True)       # ID de la película en TMDB
    titulo = Column(String(255), nullable=True)
    poster_url = Column(String(500), nullable=True)
    anio_estreno = Column(Integer, nullable=True)


# ── Tabla: vistas ──────────────────────────────────────────────────────────
# Registra qué películas ha marcado como vistas cada usuario, y su puntuación.
class Vista(Base):
    __tablename__ = "vistas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    puntuacion = Column(Integer, nullable=True)   # del 1 al 10, puede ser nula si no ha puntuado
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relación para acceder a los datos de la película desde una vista
    pelicula = relationship("Pelicula")

    __table_args__ = (
        # La puntuación solo puede ser entre 1 y 10
        CheckConstraint("puntuacion >= 1 AND puntuacion <= 10", name="check_puntuacion"),
        # Un usuario no puede marcar la misma película como vista dos veces
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_vista"),
    )


# ── Tabla: entradas_diario ─────────────────────────────────────────────────
# Cada entrada es un registro de cuándo vio el usuario una película y su reseña.
# Un usuario puede tener varias entradas para la misma película (visionados múltiples).
class EntradaDiario(Base):
    __tablename__ = "entradas_diario"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    fecha_visionado = Column(Date, nullable=False)      # fecha en que vio la película
    resena = Column(Text, nullable=True)                # texto de la reseña (opcional)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))


# ── Tabla: me_gusta ────────────────────────────────────────────────────────
# Registra los "me gusta" de los usuarios en películas.
class MeGusta(Base):
    __tablename__ = "me_gusta"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Un usuario solo puede dar me gusta una vez a cada película
    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_mg"),)


# ── Tabla: watchlist ───────────────────────────────────────────────────────
# Lista de películas que el usuario quiere ver en el futuro.
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Una película no puede estar dos veces en la watchlist del mismo usuario
    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_wl"),)


# ── Tabla: peliculas_favoritas ─────────────────────────────────────────────
# Máximo 4 películas favoritas por usuario, con un orden (1-4) para mostrarlas en el perfil.
class PeliculaFavorita(Base):
    __tablename__ = "peliculas_favoritas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    orden = Column(Integer, nullable=False)   # posición en el perfil (1, 2, 3 o 4)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    __table_args__ = (
        CheckConstraint("orden >= 1 AND orden <= 4", name="check_orden"),           # solo posiciones 1-4
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_fav"),  # no duplicar película
        UniqueConstraint("id_usuario", "orden", name="unique_usuario_orden_fav"),   # no duplicar posición
    )


# ── Nivel 2 ────────────────────────────────────────────────────────────────

# ── Tabla: seguidores ──────────────────────────────────────────────────────
# Relación de seguimiento entre usuarios (quién sigue a quién).
class Seguidor(Base):
    __tablename__ = "seguidores"

    id = Column(Integer, primary_key=True, nullable=False)
    id_seguidor = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)  # el que sigue
    id_seguido = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)   # el que es seguido
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        # No se puede seguir dos veces a la misma persona
        UniqueConstraint("id_seguidor", "id_seguido", name="unique_seguidor_seguido"),
        # No se puede seguir a uno mismo
        CheckConstraint("id_seguidor != id_seguido", name="check_no_autofollow"),
    )


# ── Tabla: comentarios_resena ──────────────────────────────────────────────
# Comentarios que los usuarios dejan en las entradas de diario de otros usuarios.
class ComentarioResena(Base):
    __tablename__ = "comentarios_resena"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_entrada_diario = Column(Integer, ForeignKey("entradas_diario.id", ondelete="CASCADE"), nullable=False)
    texto = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relación para acceder fácilmente al usuario que escribió el comentario
    usuario = relationship("Usuario")


# ── Tabla: likes_resena ────────────────────────────────────────────────────
# Likes que los usuarios dan a entradas del diario de otros.
class LikeResena(Base):
    __tablename__ = "likes_resena"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_entrada_diario = Column(Integer, ForeignKey("entradas_diario.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Un usuario solo puede dar like una vez a cada entrada de diario
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_entrada_diario", name="unique_usuario_entrada_like"),
    )


# ── Tabla: listas ──────────────────────────────────────────────────────────
# Listas de películas creadas por los usuarios (públicas o privadas).
class Lista(Base):
    __tablename__ = "listas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    es_publica = Column(Boolean, nullable=False, server_default=text("true"))  # por defecto pública
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))


# ── Tabla: listas_peliculas ────────────────────────────────────────────────
# Tabla intermedia que asocia películas con listas (relación muchos a muchos).
class ListaPelicula(Base):
    __tablename__ = "listas_peliculas"

    id = Column(Integer, primary_key=True, nullable=False)
    id_lista = Column(Integer, ForeignKey("listas.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    # Una película no puede aparecer dos veces en la misma lista
    __table_args__ = (
        UniqueConstraint("id_lista", "id_pelicula", name="unique_lista_pelicula"),
    )
