import discord
from discord.ext import commands


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.theme_color = discord.Color.purple()

    @commands.command(name="info", help="Display bot information")
    async def info(self, ctx: commands.Context):
        ping = int(self.bot.latency * 1000)
        guild_count = str(len(self.bot.guilds))
        total_member_count = 0

        for guild in self.bot.guilds:
            total_member_count += guild.member_count

        info_embed = discord.Embed(title="Sparta Bot Information", color=self.theme_color)
        info_embed.set_thumbnail(url=self.bot.user.avatar_url)

        info_embed.add_field(name="Latency/Ping", value=f"{ping}ms", inline=False)
        info_embed.add_field(name="Server Count", value=guild_count, inline=False)
        info_embed.add_field(name="Total Member Count", value=str(total_member_count), inline=False)

        await ctx.send(embed=info_embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
