"""empty message

Revision ID: fde79d794d29
Revises: 16a0c63a8c5a
Create Date: 2021-01-09 18:05:21.752410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fde79d794d29'
down_revision = '16a0c63a8c5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tourneycollabs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tourney_id', sa.Integer(), nullable=False),
    sa.Column('coach_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ),
    sa.ForeignKeyConstraint(['tourney_id'], ['tourneys.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tourney_id', 'coach_id', name='tc_constraint')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tourneycollabs')
    # ### end Alembic commands ###