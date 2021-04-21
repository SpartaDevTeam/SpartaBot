import os
import urbanpython
import discord
from discord.ext import commands


class InternetStuff(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.theme_color = discord.Color.purple()
        self.description = (
            "Commands to surf the interwebs without leaving Discord"
        )
        self.urban = urbanpython.Urban(os.environ["SPARTA_URBAN_API_KEY"])


def setup(bot):
    bot.add_cog(InternetStuff(bot))
