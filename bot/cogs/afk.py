import asyncio
import discord
from discord.ext import commands

from bot import get_prefix, MyBot
from bot.data import Data


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.theme_color = discord.Color.purple()

    async def process_afk(self, message: discord.Message):
        Data.c.execute("SELECT * FROM afks")
        afks = Data.c.fetchall()

        for afk_entry in afks:
            guild_prefixes = get_prefix(self.bot, message)
            guild_prefixes.remove(f"{self.bot.user.mention} ")
            guild_prefixes.remove(f"<@!{self.bot.user.id}> ")
            guild_prefix = guild_prefixes[0]

            if int(
                afk_entry[0]
            ) == message.author.id and not message.content.startswith(
                guild_prefix
            ):
                await message.channel.send(
                    f"{message.author.mention}, you have been un-AFK'd",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                Data.delete_afk_data(message.author)
                continue

            user = await self.bot.fetch_user(int(afk_entry[0]))
            if user in message.mentions:
                afk_reason = afk_entry[1]
                await message.channel.send(
                    f"{message.author.mention}, {user} is currently AFK because:\n*{afk_reason}*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        asyncio.create_task(self.process_afk(message))


def setup(bot):
    # bot.add_cog(AFK(bot))
    pass
