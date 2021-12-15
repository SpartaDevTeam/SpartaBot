import random
import string
import pyfiglet
import discord
from discord.ext import commands

from bot import THEME, TESTING_GUILDS
from bot.data import Data
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

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def coinflip(self, ctx: discord.ApplicationContext):
        """
        Flip a coin
        """

        result = random.choice(["heads", "tails"])
        await ctx.respond(
            f"The coin has been flipped and resulted in **{result}**"
        )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def roll(self, ctx: discord.ApplicationContext, dice_count: int = 1):
        """
        Roll a dice
        """

        number = random.randint(dice_count, dice_count * 6)

        if dice_count > 1:
            await ctx.respond(
                f"You rolled **{dice_count} dice** and got a **{number}**"
            )
        else:
            await ctx.respond(f"You rolled a **{number}**")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def avatar(
        self, ctx: discord.ApplicationContext, member: discord.Member = None
    ):
        """
        Get somebody's Discord avatar
        """

        if not member:
            member = ctx.author

        av_embed = discord.Embed(title=f"{member}'s Avatar", color=THEME)
        av_embed.set_image(url=member.avatar.url)
        await ctx.respond(embed=av_embed)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def choose(self, ctx: commands.Context, options: str):
        """
        Let Sparta choose the best option for you. Separate the choices with a comma (,).
        """

        items = list(map(lambda x: x.strip(), options.split(",")))
        choice = random.choice(items)
        await ctx.respond(
            f"I choose {choice}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.slash_command(name="8ball", guild_ids=TESTING_GUILDS)
    async def eight_ball(self, ctx: discord.ApplicationContext, question: str):
        """
        Call upon the powers of the all knowing magic 8Ball
        """

        group = random.choice(self.eight_ball_responses)
        response = random.choice(group)
        await ctx.respond(response)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def emojify(self, ctx: discord.ApplicationContext, sentence: str):
        """
        Turn a sentence into emojis
        """

        emojified_sentence = ""
        sentence = sentence.lower()

        for char in sentence:
            char_lower = char.lower()

            if char_lower in string.ascii_lowercase:
                emojified_sentence += f":regional_indicator_{char}:"
            elif char_lower in self.emojify_symbols:
                emojified_sentence += self.emojify_symbols[char_lower]
            elif char_lower == " ":
                emojified_sentence += "  "
            else:
                emojified_sentence += char

        await ctx.respond(emojified_sentence)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def ascii(self, ctx: discord.ApplicationContext, sentence: str):
        """
        Turn a sentence into cool ASCII art
        """

        ascii_text = pyfiglet.figlet_format(sentence)
        await ctx.respond(f"```{ascii_text}```")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def impersonate(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        message: str,
    ):
        """
        Pretend to be another member of your server
        """

        webhook_url = Data.webhook_entry_exists(ctx.channel)

        if webhook_url:
            webhook = discord.utils.get(
                await ctx.channel.webhooks(), url=webhook_url
            )

            if not webhook:
                webhook: discord.Webhook = await ctx.channel.create_webhook(
                    name="Sparta Impersonate Command",
                    reason="Impersonation Command",
                )
                Data.c.execute(
                    "UPDATE webhooks SET webhook_url = :new_url WHERE channel_id = :ch_id",
                    {"new_url": webhook.url, "ch_id": ctx.channel.id},
                )
                Data.conn.commit()

        else:
            webhook: discord.Webhook = await ctx.channel.create_webhook(
                name="Sparta Impersonate Command",
                reason="Impersonation Command",
            )
            Data.create_new_webhook_data(ctx.channel, webhook.url)

        await webhook.send(
            message,
            username=member.display_name,
            avatar_url=member.avatar.url,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await ctx.respond("Amogus", ephemeral=True)


def setup(bot):
    bot.add_cog(SlashFun())
