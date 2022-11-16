"""Made playlist_id primary key as well

Revision ID: ef4c153dc7d7
Revises: 1b6128ae5a4b
Create Date: 2022-11-16 09:21:40.000057

"""
from alembic import op

# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ef4c153dc7d7"
down_revision = "1b6128ae5a4b"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("playlist_songs_pkey", "playlist_songs")
    op.create_primary_key(
        "playlist_songs_pkey", "playlist_songs", ["uri", "playlist_id"]
    )


def downgrade():
    op.drop_constraint("playlist_songs_pkey", "playlist_songs")
    op.create_primary_key("playlist_songs_pkey", "playlist_songs", ["uri"])
