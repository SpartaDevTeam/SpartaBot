import discord
from discord.ext import commands
from discord.mentions import AllowedMentions

from bot import get_prefix, MyBot
from bot.data import Data


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.theme_color = discord.Color.purple()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        Data.c.execute("SELECT * FROM afks")
        afks = Data.c.fetchall()

        for afk in afks:
            guild_prefix = get_prefix(self.bot, message)
            if int(
                afk[0]
            ) == message.author.id and not message.content.startswith(
                guild_prefix
            ):
                await message.channel.send(
                    f"{message.author.mention}, you have been un-AFK'd",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                Data.delete_afk_data(message.author)
                continue

            user = await self.bot.fetch_user(int(afk[0]))
            if user in message.mentions:
                afk_reason = afk[1]
                await message.channel.send(
                    f"{message.author.mention}, {user} is currently AFK because:\n*{afk_reason}*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )


def setup(bot):
    bot.add_cog(AFK(bot))
