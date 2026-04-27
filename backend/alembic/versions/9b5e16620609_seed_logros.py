"""seed logros

Revision ID: 9b5e16620609
Revises: 308bd5664c9d
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '9b5e16620609'
down_revision: Union[str, Sequence[str], None] = '308bd5664c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LOGROS = [
    # vistas
    ("PRIMERA_FUNCION",   "Primera función",        "Marca tu primera película como vista.",              10),
    ("CINEFILO",          "Cinéfilo",               "Marca 10 películas como vistas.",                    25),
    ("CINEFILO_PROGRESO", "Cinéfilo en progreso",   "Marca 20 películas como vistas.",                   50),
    ("MAESTRO_CINEFILO",  "Maestro cinéfilo",       "Marca 100 películas como vistas.",                 100),
    # diario
    ("CRITICO_PROCESO",   "Crítico en proceso",     "Escribe tu primera reseña en el diario.",            10),
    ("PERIODISTA",        "Periodista",             "Escribe 3 reseñas en el diario.",                    25),
    ("PLUMA_DE_ORO",      "Pluma de oro",           "Escribe 50 reseñas en el diario.",                 100),
    # perfil
    ("CON_CRITERIO",      "Con criterio",           "Pon 4 películas favoritas en tu perfil.",            25),
    ("PLANIFICADOR",      "Planificador",           "Añade 5 películas a tu watchlist.",                  15),
    # especiales
    ("MARATONISTA",       "Maratonista",            "Marca 10 películas vistas en el mismo mes.",         50),
    ("DOBLE_FUNCION",     "Doble función",          "Registra 2 películas vistas el mismo día.",          25),
    ("TRASNOCHADOR",      "Trasnochador",           "Escribe una reseña entre las 2:00 y las 5:00.",      25),
    ("NOSTALGICO",        "Nostálgico",             "Marca 5 películas anteriores a 1980 como vistas.",   50),
    ("HATER_PROFESIONAL", "Hater profesional",      "Escribe una reseña con puntuación de 1.",            15),
    # sociales
    ("SOCIABLE",          "Sociable",               "Sigue a tu primer usuario.",                         10),
    ("CONVERSADOR",       "Conversador",            "Deja un comentario en una reseña.",                  10),
    ("CONEXION_MUTUA",    "Conexión mutua",         "Ten 10 seguidores mutuos.",                          75),
    ("INFLUENCER",        "Influencer",             "Consigue 300 seguidores.",                          100),
]


def upgrade() -> None:
    op.execute(
        sa.text("""
            INSERT INTO logros (codigo, nombre, descripcion, xp) VALUES
            """ + ",\n            ".join(
            f"(:c{i}, :n{i}, :d{i}, :x{i})" for i in range(len(LOGROS))
        )).bindparams(
            **{f"c{i}": logro[0] for i, logro in enumerate(LOGROS)},
            **{f"n{i}": logro[1] for i, logro in enumerate(LOGROS)},
            **{f"d{i}": logro[2] for i, logro in enumerate(LOGROS)},
            **{f"x{i}": logro[3] for i, logro in enumerate(LOGROS)},
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM logros"))
