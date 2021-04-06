import discord
from discord.ext import commands


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = (
            "Some commands to do general tasks"
        )
        self.theme_color = discord.Color.purple()

    @commands.command(name="info", help="Display bot information")
    async def info(self, ctx: commands.Context):
        ping = int(self.bot.latency * 1000)
        guild_count = str(len(self.bot.guilds))
        total_member_count = 0

        for guild in self.bot.guilds:
            total_member_count += guild.member_count

        info_embed = discord.Embed(
            title="Sparta Bot Information", color=self.theme_color
        )
        info_embed.set_thumbnail(url=self.bot.user.avatar_url)

        info_embed.add_field(
            name="Latency/Ping", value=f"{ping}ms", inline=False
        )
        info_embed.add_field(
            name="Server Count", value=guild_count, inline=False
        )
        info_embed.add_field(
            name="Total Member Count",
            value=str(total_member_count),
            inline=False,
        )

        await ctx.send(embed=info_embed)

    @commands.command(name="invite", help="Invite Sparta to your server")
    async def invite(self, ctx: commands.Context):
        invite_url = "https://discord.com/oauth2/authorize?client_id=731763013417435247&scope=bot&permissions=403176703"
        beta_invite_url = "https://discord.com/api/oauth2/authorize?client_id=775798822844629013&permissions=8&scope=bot"

        invite_embed = discord.Embed(
            title="Sparta Invite", color=self.theme_color, url=invite_url
        )
        beta_invite_embed = discord.Embed(
            title="Sparta Beta Invite",
            color=self.theme_color,
            url=beta_invite_url,
        )

        await ctx.send(embed=invite_embed)
        await ctx.send(embed=beta_invite_embed)

    @commands.command(name="github", help="Link to the GitHub Repository")
    async def github(self, ctx: commands.Context):
        github_link = "https://github.com/SpartaDevTeam/SpartaBot"
        github_embed = discord.Embed(
            title="GitHub Repository", color=self.theme_color, url=github_link
        )
        await ctx.send(embed=github_embed)

    @commands.command(
        name="support", help="Invite link for Sparta Support Server"
    )
    async def support(self, ctx: commands.Context):
        support_link = "https://discord.gg/RrVY4bP"
        await ctx.send(support_link)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
