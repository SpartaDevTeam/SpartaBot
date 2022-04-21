import asyncio
import uuid
import discord
from datetime import datetime
from discord.ext import commands
from sqlalchemy.future import select

from bot import TESTING_GUILDS, THEME, db
from bot.db import models
from bot.utils import str_time_to_timedelta
from bot.views import SuggestView


class SlashMiscellaneous(commands.Cog):
    """
    Commands to do general tasks
    """

    launched_at = int(datetime.now().timestamp())
    reminders_loaded = False

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def reminder(
        self,
        reminder_id: str,
        user_id: discord.User,
        seconds: float,
        reminder_msg: str,
        reminder_start_time: datetime,
    ):
        await asyncio.sleep(seconds)
        rem_start_time_str = f"<t:{int(reminder_start_time.timestamp())}:R>"

        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(
                f"You asked me to remind you {rem_start_time_str} about:"
                f"\n*{reminder_msg}*",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            pass

        async with db.async_session() as session:
            rem_data = await session.get(models.Reminder, reminder_id)
            await session.delete(rem_data)
            await session.commit()

    def load_reminder(self, reminder_data: models.Reminder):
        now = datetime.now()
        time_diff = (reminder_data.due - now).total_seconds()

        asyncio.create_task(
            self.reminder(
                reminder_data.id,
                reminder_data.user_id,
                time_diff,
                reminder_data.message,
                reminder_data.start,
            )
        )

    async def load_pending_reminders(self):
        print("Loading pending reminders...")

        async with db.async_session() as session:
            q = select(models.Reminder)
            result = await session.execute(q)

            for reminder in result.scalars():
                self.load_reminder(reminder)

        self.reminders_loaded = True  # TODO: Make this globally accessible
        print("Loaded reminders!")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_pending_reminders()

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def info(self, ctx: discord.ApplicationContext):
        """
        Display bot information
        """

        ping = int(self.bot.latency * 1000)
        guild_count = str(len(self.bot.guilds))
        total_member_count = 0

        for guild in self.bot.guilds:
            total_member_count += guild.member_count

        info_embed = discord.Embed(title="Sparta Bot Information", color=THEME)
        info_embed.set_author(
            name=str(ctx.author), icon_url=ctx.author.avatar.url
        )
        info_embed.set_thumbnail(url=self.bot.user.avatar.url)

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

        await ctx.respond(embed=info_embed)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def invite(self, ctx: discord.ApplicationContext):
        """
        Get Sparta's invite URL
        """

        invite_url = "https://discord.com/api/oauth2/authorize?client_id=731763013417435247&permissions=8&scope=bot%20applications.commands"
        beta_invite_url = "https://discord.com/api/oauth2/authorize?client_id=775798822844629013&permissions=8&scope=applications.commands%20bot"

        invite_embed = discord.Embed(title="Invite Links", color=THEME)
        invite_embed.add_field(
            name="Sparta", value=f"[Click here]({invite_url})", inline=False
        )
        invite_embed.add_field(
            name="Sparta Beta",
            value=f"[Click here]({beta_invite_url})",
            inline=False,
        )

        await ctx.respond(embed=invite_embed)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def github(self, ctx: discord.ApplicationContext):
        """
        Link to the GitHub Repository
        """

        github_link = "https://github.com/SpartaDevTeam/SpartaBot"
        await ctx.respond(github_link)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def support(self, ctx: discord.ApplicationContext):
        """
        Invite link for Sparta Support Server
        """

        support_link = "https://discord.gg/RrVY4bP"
        await ctx.respond(support_link)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def vote(self, ctx: discord.ApplicationContext):
        """
        Get bot list links to vote for Sparta
        """

        top_gg_link = "https://top.gg/bot/731763013417435247"

        vote_embed = discord.Embed(title="Vote for Sparta Bot", color=THEME)
        vote_embed.add_field(
            name="Vote every 12 hours", value=f"[Top.gg]({top_gg_link})"
        )

        await ctx.respond(embed=vote_embed)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def remind(
        self,
        ctx: discord.ApplicationContext,
        remind_time: str,
        message: str,
    ):
        """
        Set a reminder. Example: /remind 1d 2h 12m 5s make lunch (All time options are not required)
        """

        # Wait till bot finishes loading all reminders
        # Prevents duplicate reminders
        if not self.reminders_loaded:
            await ctx.respond(
                "The bot is starting up. Please try again in a few minutes."
            )
            return

        now = datetime.now()
        remind_timedelta = str_time_to_timedelta(remind_time)
        time_to_end = f"<t:{int((now + remind_timedelta).timestamp())}>"

        reminder_id = uuid.uuid4()
        new_reminder = models.Reminder(
            id=reminder_id.hex,
            user_id=ctx.author.id,
            message=message,
            start=now,
            due=now + remind_timedelta,
        )
        self.load_reminder(new_reminder)

        async with db.async_session() as session:
            session.add(new_reminder)
            await session.commit()

        await ctx.respond(
            f"Reminder set for {time_to_end} about:\n{message}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def afk(self, ctx: discord.ApplicationContext, reason: str):
        """
        Sets your AFK status
        """

        async with db.async_session() as session:
            afk_data: models.AFK | None = await session.get(
                models.AFK, ctx.author.id
            )

            if afk_data:
                afk_data.message = reason
            else:
                new_afk_data = models.AFK(
                    user_id=ctx.author.id, message=reason
                )
                session.add(new_afk_data)

            await session.commit()

        await ctx.respond(
            f"You have been AFK'd for the following reason:\n{reason}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def unafk(self, ctx: discord.ApplicationContext):
        """
        Unset your AFK status
        """

        async with db.async_session() as session:
            afk_data: models.AFK | None = await session.get(
                models.AFK, ctx.author.id
            )

            if afk_data:
                await session.delete(afk_data)
                await session.commit()
                await ctx.respond("You are no longer AFK'd")
            else:
                await ctx.respond("You are not currently AFK'd")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def uptime(self, ctx: discord.ApplicationContext):
        """
        Check how long the bot has been up for
        """

        humanized_time = f"<t:{self.launched_at}:R>"
        await ctx.respond(f"I was last restarted {humanized_time}")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def suggest(self, ctx: discord.ApplicationContext, suggestion: str):
        """
        Suggest a new feature or change to the Devs
        """

        suggest_view = SuggestView(ctx.author.id)
        await ctx.respond(
            "Do you want to include your username with the suggestion, so we can contact you if needed?",
            view=suggest_view,
        )
        timed_out = await suggest_view.wait()

        if timed_out or suggest_view.anonymous:
            suggestion_msg = (
                f"Anonymous user has given a suggestion:\n{suggestion}"
            )
            await ctx.respond(
                f"Thank you {ctx.author.mention}, your anonymous suggestion has been recorded."
            )

        else:
            suggestion_msg = (
                f"**{ctx.author}** has given a suggestion:\n{suggestion}"
            )
            await ctx.respond(
                f"Thank you {ctx.author.mention}, your non-anonymous suggestion has been recorded."
            )

        suggestion_channel = 848474796856836117
        suggest_channel = await self.bot.fetch_channel(suggestion_channel)
        await suggest_channel.send(
            suggestion_msg, allowed_mentions=discord.AllowedMentions.none()
        )


def setup(bot):
    bot.add_cog(SlashMiscellaneous(bot))
