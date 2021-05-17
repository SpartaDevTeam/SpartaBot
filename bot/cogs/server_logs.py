import discord
import datetime
from discord.ext import commands


class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = "Shows when the bot joins or leaves a guild"
        self.theme_color = discord.Color.purple()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        inv = await guild.text_channels[0].create_invite()
        embed = discord.Embed(
            title="I Have Joined A New Guild!",
            description=f"[{guild.name}]({inv})",
            timestamp=datetime.datetime.now(),
            color=self.theme_color,
        )
        embed.add_field(
            name=f"This Guild Has {guild.member_count} Members!",
            value=f"Yay Another Server! We Are Now At {len(self.bot.guilds)} Guilds!",
        )
        await self.bot.get_guild(733224197827854377).get_channel(
            843726111360024586
        ).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(
            title="I Have Left A Guild!",
            description=f"{guild.name}",
            timestamp=datetime.datetime.now(),
            color=self.theme_color,
        )
        embed.add_field(
            name=f";-; We Are Now At {len(self.bot.guilds)} Guilds!"
        )
        await self.bot.get_guild(733224197827854377).get_channel(
            843726111360024586
        ).send(embed=embed)


def setup(bot):
    bot.add_cog(ServerLogs(bot))
