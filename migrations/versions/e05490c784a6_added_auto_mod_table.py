"""added auto_mod table

Revision ID: e05490c784a6
Revises: c534a7e185b6
Create Date: 2022-04-06 17:53:35.163875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e05490c784a6"
down_revision = "c534a7e185b6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "auto_mod",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("links", sa.Boolean(), nullable=False),
        sa.Column("images", sa.Boolean(), nullable=False),
        sa.Column("ping_spam", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("guild_id"),
    )
    op.drop_column("guilds", "activated_automod")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "guilds",
        sa.Column(
            "activated_automod",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_table("auto_mod")
    # ### end Alembic commands ###
