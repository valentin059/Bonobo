"""añadir logros

Revision ID: 7274d676df0b
Revises: bc8c354484a5
Create Date: 2026-04-20 16:07:29.955477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7274d676df0b'
down_revision: Union[str, Sequence[str], None] = 'bc8c354484a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Crear tabla logros
    op.create_table(
        'logros',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo')
    )

    # Crear tabla usuario_logros
    op.create_table(
        'usuario_logros',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=True),
        sa.Column('id_logro', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['id_logro'], ['logros.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_usuario', 'id_logro')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('usuario_logros')
    op.drop_table('logros')