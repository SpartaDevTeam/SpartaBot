"""added moderator_id field

Revision ID: 24933d669517
Revises: 81217e467554
Create Date: 2022-04-14 19:01:57.155489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "24933d669517"
down_revision = "81217e467554"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "infractions",
        sa.Column("moderator_id", sa.BigInteger(), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("infractions", "moderator_id")
    # ### end Alembic commands ###