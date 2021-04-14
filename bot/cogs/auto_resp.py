import discord
from discord.ext import commands

from bot.data import Data


class AutoResponse(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Commands to setup Sparta Bot to automatically reply to certain phrases"
        self.theme_color = discord.Color.purple()

    @commands.command(
        name="addautoresponse",
        aliases=["addauto"],
        help="Add an auto response phrase",
    )
    async def add_auto_response_phrase(
        self, ctx: commands.Context, options: str
    ):
        options_split = options.split(",", maxsplit=1)
        activation_phrase = options_split[0].strip()
        response = options_split[1].strip()

        # TODO: add auto response


def setup(bot):
    bot.add_cog(AutoResponse(bot))
