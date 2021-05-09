import datetime
import json
from re import search

import discord
from discord.ext import commands

from bot import MyBot
from bot.data import Data


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = "Commands to setup Auto-Mod in Sparta"
        self.theme_color = discord.Color.purple()
        self.url_regex = (
            r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.]"
            r"[a-z]{2,4}/)("
            r"?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<"
            r">]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^"
            r"\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        )

    @commands.command(
        name="automod", help="Allows you to enable/disable automod features"
    )
    @commands.has_guild_permissions(administrator=True)
    async def automod(self, ctx):
        Data.check_guild_entry(ctx.guild)

        available_features = ["links", "images", "spam"]

        Data.c.execute(
            "SELECT activated_automod FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        activated_features = json.loads(Data.c.fetchone()[0])

        def check(message: discord.Message):
            return (
                message.channel == ctx.channel
                and message.author == ctx.message.author
            )

        def save():
            Data.c.execute(
                "UPDATE guilds SET activated_automod = :new_features WHERE id = :guild_id",
                {
                    "new_features": json.dumps(activated_features),
                    "guild_id": ctx.guild.id,
                },
            )
            Data.conn.commit()

        mod_embed = discord.Embed(
            title="Auto-Mod",
            description=(
                "Allow Sparta to administrate on its own. "
                "Reply with a particular feature."
            ),
            color=self.theme_color,
        )
        mod_embed.add_field(
            name="`links`",
            value="Bans links from being sent to this server",
            inline=False,
        )
        mod_embed.add_field(
            name="`images`",
            value="Bans attachments from being sent to this server",
            inline=False,
        )
        mod_embed.add_field(
            name="`spam`",
            value="Temporarily mutes users who are spamming mentions in this server",
            inline=False,
        )
        mod_embed.set_footer(
            text=(
                "Reply with stop if you want to stop "
                "adding auto-mod features and save your changes"
            )
        )
        await ctx.send(embed=mod_embed)

        while True:
            msg = await self.bot.wait_for("message", check=check)
            msg = str(msg.content)

            if msg.lower() in available_features:
                if msg.lower() in activated_features:
                    await ctx.send(f"Removed `{msg}`!")
                    activated_features.remove(msg)
                else:
                    await ctx.send(f"Added `{msg}`!")
                    activated_features.append(msg)

                if len(activated_features) == len(available_features):
                    await ctx.send(
                        "You have activated all the features. Changes "
                        "have been saved!"
                    )
                    save()
                    break

            elif msg == "stop":
                await ctx.send("The changes have been saved!")
                save()
                break

            else:
                await ctx.send("Not a valid response!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        def spam_check(msg):
            return (
                (msg.author == message.author)
                and len(msg.mentions)
                and (
                    (datetime.datetime.utcnow() - msg.created_at).seconds < 20
                )
            )

        Data.check_guild_entry(message.guild)

        Data.c.execute(
            "SELECT activated_automod FROM guilds WHERE id = :guild_id",
            {"guild_id": message.guild.id},
        )
        activated_features = json.loads(Data.c.fetchone()[0])

        # if channel id's data contains "links":
        if "links" in activated_features:
            if search(self.url_regex, message.content):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, You cannot send links "
                    "in this channel!",
                    delete_after=3,
                )

        # if channel id's data contains "images"
        if "images" in activated_features:
            if any([hasattr(a, "width") for a in message.attachments]):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, You cannot send images "
                    "in this channel!",
                    delete_after=3,
                )

        # if channel id's data contains "spam":
        if "spam" in activated_features:
            if (
                len(
                    list(
                        filter(
                            lambda m: spam_check(m), self.bot.cached_messages
                        )
                    )
                )
                >= 5
            ):
                await message.channel.send(
                    f"{message.author.mention}, Do not spam mentions "
                    "in this channel!",
                    delete_after=3,
                )


def setup(bot):
    bot.add_cog(AutoMod(bot))
