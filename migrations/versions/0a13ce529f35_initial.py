"""initial

Revision ID: 0a13ce529f35
Revises:
Create Date: 2022-04-05 14:27:50.687033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0a13ce529f35"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "afks",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "auto_responses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("activation", sa.String(), nullable=False),
        sa.Column("response", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "guilds",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("infractions", sa.JSON(), nullable=False),
        sa.Column("mute_role", sa.BigInteger(), nullable=True),
        sa.Column("activated_automod", sa.JSON(), nullable=False),
        sa.Column("welcome_message", sa.String(), nullable=True),
        sa.Column("leave_message", sa.String(), nullable=True),
        sa.Column("welcome_channel", sa.BigInteger(), nullable=True),
        sa.Column("leave_channel", sa.BigInteger(), nullable=True),
        sa.Column("auto_role", sa.BigInteger(), nullable=True),
        sa.Column("prefix", sa.String(), nullable=False),
        sa.Column("clear_cap", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reaction_roles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("emoji", sa.String(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reminders",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("due", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "webhooks",
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("webhook_url", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("channel_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("webhooks")
    op.drop_table("reminders")
    op.drop_table("reaction_roles")
    op.drop_table("guilds")
    op.drop_table("auto_responses")
    op.drop_table("afks")
    # ### end Alembic commands ###
