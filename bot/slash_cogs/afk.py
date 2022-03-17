import discord
from discord.ext import commands

from bot.data import Data


class SlashAFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def process_afk(self, message: discord.Message):
        Data.c.execute("SELECT * FROM afks")
        afks = Data.c.fetchall()

        for afk_entry in afks:
            user = await self.bot.fetch_user(int(afk_entry[0]))
            if user in message.mentions:
                afk_reason = afk_entry[1]
                await message.channel.send(
                    f"{message.author.mention}, {user} is currently AFK because:\n*{afk_reason}*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            await self.process_afk(message)


def setup(bot):
    bot.add_cog(SlashAFK(bot))
