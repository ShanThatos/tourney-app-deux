"""empty message

Revision ID: d0586e09a329
Revises: b6e29fbef792
Create Date: 2021-01-18 19:44:10.933151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0586e09a329'
down_revision = 'b6e29fbef792'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'schools', ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'schools', type_='unique')
    # ### end Alembic commands ###