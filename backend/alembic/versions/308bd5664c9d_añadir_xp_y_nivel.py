"""añadir xp y nivel

Revision ID: 308bd5664c9d
Revises: 7274d676df0b
Create Date: 2026-04-20 22:42:53.837202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '308bd5664c9d'
down_revision: Union[str, Sequence[str], None] = '7274d676df0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('xp_total', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('usuarios', sa.Column('nivel', sa.Integer(), server_default=sa.text('1'), nullable=False))
    op.add_column('logros', sa.Column('xp', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('usuario_logros', sa.Column('xp_reclamado', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('usuarios', 'xp_total')
    op.drop_column('usuarios', 'nivel')
    op.drop_column('logros', 'xp')
    op.drop_column('usuario_logros', 'xp_reclamado')
