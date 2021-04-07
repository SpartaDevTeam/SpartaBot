import os
import sqlite3


class Data:
    data_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(data_dir, "db.sqlite3")
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    @classmethod
    def create_tables(cls):
        cls.c.execute(
            """CREATE TABLE IF NOT EXISTS "guilds" (
            "id"	INTEGER,
            "infractions"	TEXT DEFAULT '[]',
            "mute_role"	INTEGER DEFAULT NULL,
            "activated_automod"	TEXT DEFAULT '[]',
            "welcome_message"	TEXT DEFAULT NULL,
            "leave_message"	TEXT DEFAULT NULL,
            "welcome_channel"	TEXT DEFAULT NULL,
            "leave_channel"	TEXT DEFAULT NULL,
            "auto_role"	TEXT DEFAULT NULL,
            "prefix"	TEXT DEFAULT 'sb!'
        )"""
        )
        # TODO: change prefix to "s!" after rewrite

        cls.c.execute(
            """CREATE TABLE IF NOT EXISTS "webhooks" (
            "channel_id"	INTEGER,
            "webhook_url"	TEXT
        )"""
        )

        cls.c.execute(
            """CREATE TABLE IF NOT EXISTS "afks" (
            "user_id"	INTEGER,
            "afk_reason"	TEXT
        )"""
        )

        cls.conn.commit()

    # Guild Data
    @classmethod
    def create_new_guild_data(cls, guild):
        # TODO: change prefix to "s!" after rewrite
        cls.c.execute(
            """INSERT INTO guilds VALUES
            (:guild_id, '[]', NULL, '[]', NULL, NULL, NULL, NULL, NULL, 'sb!')
            """,
            {"guild_id": guild.id},
        )
        cls.conn.commit()
        print(f"Created data entry for guild {guild.name}")

    @classmethod
    def check_guild_entry(cls, guild):
        cls.c.execute(
            "SELECT * FROM guilds WHERE id = :guild_id", {"guild_id": guild.id}
        )
        guild_data = cls.c.fetchone()

        if guild_data is None:
            cls.create_new_guild_data(guild)

    # Webhook Data
    @classmethod
    def create_new_webhook_data(cls, channel, webhook_url):
        cls.c.execute(
            "INSERT INTO webhooks VALUES (:channel_id, :webhook_url)",
            {"channel_id": channel.id, "webhook_url": webhook_url},
        )
        cls.conn.commit()
        print(f"Created webhook entry for channel with ID {channel.id}")

    @classmethod
    def webhook_entry_exists(cls, channel) -> str or bool:
        cls.c.execute(
            "SELECT webhook_url FROM webhooks WHERE channel_id = :channel_id",
            {"channel_id": channel.id},
        )
        webhook_data = cls.c.fetchone()

        if webhook_data:
            return webhook_data[0]

        return False

    # AFK Data
    @classmethod
    def create_new_afk_data(cls, user, afk_reason):
        cls.c.execute(
            "INSERT INTO afks VALUES (:user_id, :afk_reason)",
            {"user_id": user.id, "afk_reason": afk_reason},
        )
        cls.conn.commit()
        print(f"Created AFK entry for user {user}")

    @classmethod
    def delete_afk_data(cls, user):
        cls.c.execute(
            "DELETE FROM afks WHERE user_id = :user_id", {"user_id": user.id}
        )
        cls.conn.commit()
        print(f"Deleted AFK entry for user {user}")

    @classmethod
    def afk_entry_exists(cls, user) -> bool:
        cls.c.execute(
            "SELECT afk_reason FROM afks WHERE user_id = :user_id",
            {"user_id": user.id},
        )
        afk_data = cls.c.fetchone()
        return afk_data is not None
