"""

Revision ID: 715f226ad393
Revises: ac17ab860b85
Create Date: 2023-03-20 21:40:36.647629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '715f226ad393'
down_revision = 'ac17ab860b85'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scanning_users',
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('is_scanning', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('tg_id')
    )
    op.drop_table('szsdfglkjcanning_users')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('szsdfglkjcanning_users',
    sa.Column('tg_id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('is_scanning', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('tg_id', name='szsdfglkjcanning_users_pkey')
    )
    op.drop_table('scanning_users')
    # ### end Alembic commands ###
