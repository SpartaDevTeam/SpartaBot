import discord
from discord.ext import commands

from bot.data import Data


class SlashAFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.theme_color = discord.Color.purple()

    async def process_afk(self, message: discord.Message):
        Data.c.execute("SELECT * FROM afks")
        afks = Data.c.fetchall()

        for afk_entry in afks:
            if int(afk_entry[0]) == message.author.id:
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
        if message.author != self.bot.user:
            await self.process_afk(message)


def setup(bot):
    # TODO: Enable when removing prefix commands
    # bot.add_cog(SlashAFK(bot))
    pass
