from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from ..database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

class Pelicula(Base):
    __tablename__ = "peliculas"
    id = Column(Integer, primary_key=True, nullable=False)
    tmdb_id = Column(Integer, nullable=False, unique=True)
    titulo = Column(String(255), nullable=True)
    poster_url = Column(String(500), nullable=True)
    anio_estreno = Column(Integer, nullable=True)

class Vista(Base):
    __tablename__ = "vistas"
    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    puntuacion = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")

    __table_args__ = (
        CheckConstraint("puntuacion >= 1 AND puntuacion <= 10", name="check_puntuacion"),
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_vista"), 
    )

class EntradaDiario(Base):
    __tablename__ = "entradas_diario"
    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    fecha_visionado = Column(Date, nullable=False)
    resena = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

class MeGusta(Base):
    __tablename__ = "me_gusta"
    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_mg"),)

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_wl"),)

class PeliculaFavorita(Base):
    __tablename__ = "peliculas_favoritas"
    id = Column(Integer, primary_key=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    id_pelicula = Column(Integer, ForeignKey("peliculas.id", ondelete="CASCADE"), nullable=False)
    orden = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    pelicula = relationship("Pelicula")
    
    __table_args__ = (
        CheckConstraint("orden >= 1 AND orden <= 4", name="check_orden"),
        UniqueConstraint("id_usuario", "id_pelicula", name="unique_usuario_pelicula_fav"),
        UniqueConstraint("id_usuario", "orden", name="unique_usuario_orden_fav"), 
    )