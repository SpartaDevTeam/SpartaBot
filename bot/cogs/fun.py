import asyncio
import random
import string

import discord
import pyfiglet
from discord.ext import commands

from bot.data import Data


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = (
            "Commands to have some fun and relieve stress (or induce it)"
        )
        self.theme_color = discord.Color.purple()
        self.eight_ball_responses = [
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

        self.emojify_symbols = {
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

        self.emoji_numbers = {
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

    @commands.command(name="poll", brief="Makes a poll!")
    async def make_poll(self, ctx, length: int, *, poll: str):
        """Usage: poll time description | option 1 | option 2
        Example: poll 30 Cats or Dogs? | Dogs | Cats
        """
        split = poll.split("|")
        description = split.pop(0)

        if length < 5:
            await ctx.send("The poll must last at least 5 seconds.")
            return
        if length > 120:
            await ctx.send("The poll must last less than 120 seconds.")
            return
        if len(split) > 9:
            await ctx.send("You can only have up to 9 options.")
            return

        options = [
            f"{self.emoji_numbers[i+1]} {t}\n" for i, t in enumerate(split)
        ]

        embed = discord.Embed(
            title=description,
            description=("".join(options)),
            color=self.theme_color,
        ).set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        m: discord.Message = await ctx.send(embed=embed)

        for i in range(len(options)):
            await m.add_reaction(self.emoji_numbers[i + 1])

        await asyncio.sleep(length)

        m = await ctx.channel.fetch_message(m.id)

        results = []

        for r in m.reactions:
            results.append((r.emoji, r.count))

        results.sort(key=lambda t: t[1], reverse=True)

        embed = embed.add_field(name="Result", value=results[0][0])
        await m.edit(embed=embed)

    @commands.command(
        name="coinflip", aliases=["coin", "flip"], help="Flip a coin!"
    )
    async def coin_flip(self, ctx):
        result = random.choice(["heads", "tails"])
        await ctx.send(
            f"The coin has been flipped and resulted in **{result}**"
        )

    @commands.command(name="roll", aliases=["dice"], help="Roll a dice!")
    async def dice_roll(self, ctx: commands.Context, dice_count: int = 1):
        number = random.randint(dice_count, dice_count * 6)

        if dice_count > 1:
            await ctx.send(
                f"You rolled **{dice_count} dice** and got a **{number}**"
            )
        else:
            await ctx.send(f"You rolled a **{number}**")

    @commands.command(
        name="avatar",
        aliases=["av", "pfp"],
        help="Get somebody's Discord avatar",
    )
    async def avatar(
        self, ctx: commands.Context, member: discord.Member = None
    ):
        if member:
            m = member
        else:
            m = ctx.author

        av_embed = discord.Embed(title=f"{m}'s Avatar", color=self.theme_color)
        av_embed.set_image(url=m.avatar_url)
        await ctx.send(embed=av_embed)

    @commands.command(
        name="choose",
        aliases=["choice"],
        help="Let Sparta choose the best option for you. Separate the choices with a comma (,)",
    )
    async def choose(self, ctx: commands.Context, *, options: str):
        items = [
            option.strip().replace("*", "") for option in options.split(",")
        ]
        choice = random.choice(items)
        await ctx.send(
            f"I choose **{choice}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(
        name="8ball",
        aliases=["8"],
        help="Call upon the powers of the all knowing magic 8Ball",
    )
    async def eight_ball(self, ctx: commands.Context, question: str):
        group = random.choice(self.eight_ball_responses)
        response = random.choice(group)

        await ctx.send(response)

    @commands.command(
        name="emojify", aliases=["emoji"], help="Turn a sentence into emojis"
    )
    async def emojify(self, ctx: commands.Context, *, sentence: str):
        emojified_sentence = ""
        sentence = sentence.lower()

        for char in sentence:
            char_lower = char.lower()

            if char_lower in string.ascii_lowercase:
                emojified_sentence += f":regional_indicator_{char}:"
            elif char_lower in self.emojify_symbols:
                emojified_sentence += self.emojify_symbols[char_lower]
            else:
                emojified_sentence += char

        await ctx.send(emojified_sentence)

    @commands.command(name="ascii", help="Turn a sentence into cool ASCII art")
    async def ascii(self, ctx: commands.Context, *, sentence: str):
        ascii_text = pyfiglet.figlet_format(sentence)
        await ctx.send(f"```{ascii_text}```")

    @commands.command(
        name="impersonate",
        aliases=["imp"],
        help="Pretend to be another member of your server",
    )
    async def impersonate(
        self, ctx: commands.Context, member: discord.Member, *, message: str
    ):
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
                Data.create_new_webhook_data(ctx.channel, webhook.url)

        else:
            webhook: discord.Webhook = await ctx.channel.create_webhook(
                name="Sparta Impersonate Command",
                reason="Impersonation Command",
            )
            Data.create_new_webhook_data(ctx.channel, webhook.url)

        await ctx.message.delete()
        await webhook.send(
            message,
            username=member.display_name,
            avatar_url=member.avatar_url,
            allowed_mentions=discord.AllowedMentions.none(),
        )


def setup(bot):
    bot.add_cog(Fun(bot))
