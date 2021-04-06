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

        cls.conn.commit()

    # Guild Data
    @classmethod
    def create_new_guild_data(cls, guild):
        # TODO: change prefix to "s!" after rewrite
        cls.c.execute(
            "INSERT INTO guilds VALUES (:guild_id, '[]', NULL, '[]', NULL, NULL, NULL, NULL, NULL, 'sb!')",
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
    def webhook_entry_exists(cls, channel):
        cls.c.execute(
            "SELECT webhook_url FROM webhooks WHERE channel_id = :channel_id",
            {"channel_id": channel.id},
        )
        webhook_data = cls.c.fetchone()

        if webhook_data:
            return webhook_data[0]

        return False
