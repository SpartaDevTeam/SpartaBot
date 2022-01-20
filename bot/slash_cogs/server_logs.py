import discord
import datetime
from discord.ext import commands

from bot import THEME


class SlashServerLogs(commands.Cog):
    """
    Shows when the bot joins or leaves a guild
    """

    logs_channel = 843726111360024586

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(
            title="I Have Joined A New Guild!",
            description=guild.name,
            timestamp=datetime.datetime.now(),
            color=THEME,
        )
        embed.add_field(
            name=f"This Guild Has {guild.member_count} Members!",
            value=f"Yay Another Server! We Are Now At {len(self.bot.guilds)} Guilds!",
        )
        await self.bot.get_channel(self.logs_channel).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(
            title="I Have Left A Guild!",
            description=f"{guild.name}",
            timestamp=datetime.datetime.now(),
            color=THEME,
        )
        embed.add_field(
            name=f"We Are Now At {len(self.bot.guilds)} Guilds!", value="T-T"
        )
        await self.bot.get_channel(self.logs_channel).send(embed=embed)


# TODO: Enable when removing prefix commands
# def setup(bot):
#     bot.add_cog(SlashServerLogs(bot))
