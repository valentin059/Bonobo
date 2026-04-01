"""Crear tablas nivel 2

Revision ID: b7e2f91a3c05
Revises: 3b1efadd1ec9
Create Date: 2026-04-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2f91a3c05'
down_revision: Union[str, Sequence[str], None] = '3b1efadd1ec9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'seguidores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_seguidor', sa.Integer(), nullable=False),
        sa.Column('id_seguido', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('id_seguidor != id_seguido', name='check_no_autofollow'),
        sa.ForeignKeyConstraint(['id_seguido'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_seguidor'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_seguidor', 'id_seguido', name='unique_seguidor_seguido'),
    )
    op.create_table(
        'listas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('es_publica', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'comentarios_resena',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('id_entrada_diario', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_entrada_diario'], ['entradas_diario.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'likes_resena',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('id_entrada_diario', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_entrada_diario'], ['entradas_diario.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_usuario', 'id_entrada_diario', name='unique_usuario_entrada_like'),
    )
    op.create_table(
        'listas_peliculas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_lista', sa.Integer(), nullable=False),
        sa.Column('id_pelicula', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_lista'], ['listas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_pelicula'], ['peliculas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_lista', 'id_pelicula', name='unique_lista_pelicula'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('listas_peliculas')
    op.drop_table('likes_resena')
    op.drop_table('comentarios_resena')
    op.drop_table('listas')
    op.drop_table('seguidores')
