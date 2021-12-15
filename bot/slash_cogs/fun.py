import discord
from discord.ext import commands

from bot import THEME, TESTING_GUILDS
from bot.views import PollView


class SlashFun(commands.Cog):
    """
    Commands to have some fun and relieve stress (or induce it)
    """

    eight_ball_responses = [
        [
            "No.",
            "Nope.",
            "Highly Doubtful.",
            "Not a chance.",
            "Not possible.",
            "Don't count on it.",
        ],
        [
            "Yes.",
            "Yup",
            "Extremely Likely",
            "It is possible",
            "Very possibly.",
        ],
        ["I'm not sure", "Maybe get a second opinion", "Maybe"],
    ]

    emojify_symbols = {
        "0": ":zero:",
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
        "9": ":nine:",
        "!": ":exclamation:",
        "#": ":hash:",
        "?": ":question:",
        "*": ":asterisk:",
    }

    emoji_numbers = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
    }

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def poll(
        self,
        ctx: discord.ApplicationContext,
        length: float,
        question: str,
        options: str,
    ):
        """
        Ask a question. The time must be in minutes. Separate each option with a comma (,).
        """

        length_lower_limit = 1  # 1 minute
        length_upper_limit = 7200  # 5 days
        option_limit = 10

        # Convert options in string format to list
        options = list(map(lambda x: x.strip(), options.split(",")))

        if length < length_lower_limit:
            await ctx.respond(
                f"The poll must last at least {length_lower_limit} minute."
            )
            return

        if length > length_upper_limit:
            await ctx.respond(
                f"The poll must last less than {length_upper_limit} minutes."
            )
            return

        if len(options) > option_limit:
            await ctx.respond(
                f"You can only have up to {option_limit} options."
            )
            return

        poll_embed = discord.Embed(
            title=question, color=THEME, description="**Options:**\n"
        )
        poll_embed.set_author(
            name=str(ctx.author), icon_url=ctx.author.avatar.url
        )
        # TODO: add an "Ends in..." message in the embed

        for i, option in enumerate(options):
            poll_embed.description += f"{i+1}) {option}\n"

        poll_view = PollView(options, length)
        interaction = await ctx.respond(embed=poll_embed, view=poll_view)
        await poll_view.wait()

        sorted_votes = sorted(
            list(poll_view.votes.items()), key=lambda x: x[1], reverse=True
        )

        poll_over_embed = discord.Embed(
            title="Poll Over", color=THEME, description="**Results:**\n"
        )
        poll_over_embed.set_author(
            name=str(ctx.author), icon_url=ctx.author.avatar.url
        )
        poll_over_embed.add_field(
            name="Total Votes", value=len(poll_view.voters)
        )
        poll_over_embed.add_field(name="Top Voted", value=sorted_votes[0][0])

        for i, (option, vote_count) in enumerate(sorted_votes):
            poll_over_embed.description += (
                f"{i+1}) {option} - {vote_count} votes\n"
            )

        await interaction.edit_original_message(
            embed=poll_over_embed, view=None
        )


def setup(bot):
    bot.add_cog(SlashFun())
