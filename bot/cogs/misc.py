import asyncio
import discord
import humanize
from discord.ext import commands
from datetime import datetime

from bot.data import Data
from bot.utils import str_time_to_datetime


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Some commands to do general tasks"
        self.theme_color = discord.Color.purple()

    async def reminder(
        self,
        user: discord.User,
        seconds: float,
        reminder_msg: str,
        reminder_start_time: datetime,
    ):
        await asyncio.sleep(seconds)
        rem_start_time_str = humanize.naturaltime(reminder_start_time)
        await user.send(
            f"You asked me to remind you {rem_start_time_str} about:\n*{reminder_msg}*"
        )

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

        info_embed.add_field(name="Latency/Ping", value=f"{ping}ms", inline=False)
        info_embed.add_field(name="Server Count", value=guild_count, inline=False)
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

    @commands.command(name="support", help="Invite link for Sparta Support Server")
    async def support(self, ctx: commands.Context):
        support_link = "https://discord.gg/RrVY4bP"
        await ctx.send(support_link)

    @commands.command(name="vote", help="Get bot list links to vote for Sparta")
    async def vote(self, ctx: commands.Context):
        top_gg_link = "https://top.gg/bot/731763013417435247"

        vote_embed = discord.Embed(title="Vote for Sparta Bot", color=self.theme_color)

        vote_embed.add_field(
            name="Vote every 12 hours", value=f"[Top.gg]({top_gg_link})"
        )

        await ctx.send(embed=vote_embed)

    @commands.command(
        name="remind",
        aliases=["rem"],
        brief="Set a reminder",
        help="Set a reminder. Example: 1d 2h 12m 5s, make lunch (Note: all time options are not required)",
    )
    async def remind(self, ctx: commands.Context, *, options: str):
        args = options.split(",")
        remind_time_string = args[0]
        reminder_msg = args[1].strip()

        now = datetime.now()
        remind_time = str_time_to_datetime(remind_time_string)

        time_to_end = humanize.naturaldelta(remind_time)

        await ctx.send(
            f"I will remind you in {time_to_end} about:\n*{reminder_msg}*"
        )

        # TODO: Store reminders in DB until completed
        await asyncio.create_task(
            self.reminder(ctx.author, remind_time.total_seconds(), reminder_msg, now)
        )

    @commands.command(name="afk", help="Lets others know that you are AFK when someone mentions you")
    async def afk(self, ctx: commands.Context, *, reason: str):
        already_afk = Data.afk_entry_exists(ctx.author)

        if already_afk:
            Data.c.execute("UPDATE afks SET afk_reason = :new_reason WHERE user_id = :user_id", {"new_reason": reason, "user_id": ctx.author.id})
        else:
            Data.create_new_afk_data(ctx.author, reason)

        Data.conn.commit()
        await ctx.send(f"You have been AFK'd for the following reason:\n*{reason}*")


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
