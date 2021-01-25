"""empty message

Revision ID: 7a8f5250ad17
Revises: d0586e09a329
Create Date: 2021-01-18 19:45:08.914992

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7a8f5250ad17'
down_revision = 'd0586e09a329'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tourneys', 'info')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tourneys', sa.Column('info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False))
    # ### end Alembic commands ###