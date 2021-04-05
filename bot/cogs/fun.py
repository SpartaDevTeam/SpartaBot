import string
import random
import pyfiglet
import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands to have some fun and relieve stress (or induce it)"
        self.theme_color = discord.Color.purple()
        self.eight_ball_responses = [
            [
                'No.',
                'Nope.',
                'Highly Doubtful.',
                'Not a chance.',
                'Not possible.',
                'Don\'t count on it.'
            ],
            [
                'Yes.',
                'Yup',
                'Extremely Likely',
                'It is possible',
                'Very possibly.'
            ],
            [
                "I'm not sure",
                "Maybe get a second opinion",
                "Maybe"
            ]
        ]

        self.emojify_symbols = {
            '0': ':zero:',
            '1': ':one:',
            '2': ':two:',
            '3': ':three:',
            '4': ':four:',
            '5': ':five:',
            '6': ':six:',
            '7': ':seven:',
            '8': ':eight:',
            '9': ':nine:',
            '!': ':exclamation:',
            '#': ':hash:',
            '?': ':question:',
            '*': ':asterisk:'
        }

    @commands.command(name="coinflip", aliases=["coin", "flip"], help="Flip a coin!")
    async def coin_flip(self, ctx):
        result = random.choice(["heads", "tails"])
        await ctx.send(f"The coin has been flipped and resulted in **{result}**")

    @commands.command(name="roll", aliases=["dice"], help="Roll a dice!")
    async def dice_roll(self, ctx, dice_count: int = 1):
        number = random.randint(1, dice_count * 6)

        if dice_count > 1:
            await ctx.send(f"You rolled **{dice_count} dice** and got a **{number}**")
        else:
            await ctx.send(f"You rolled a **{number}**")

    @commands.command(name="avatar", aliases=["av", "pfp"], help="Get somebody's Discord avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        if member:
            m = member
        else:
            m = ctx.author

        av_embed = discord.Embed(title=f"{m}'s Avatar", color=self.theme_color)
        av_embed.set_image(url=m.avatar_url)
        await ctx.send(embed=av_embed)

    @commands.command(name="choose", aliases=["choice"], help="Let Sparta choose the best option for you. Separate the choices with a comma (,)")
    async def choose(self, ctx, *, options: str):
        items = [option.strip().replace("*", "") for option in options.split(",")]
        choice = random.choice(items)
        await ctx.send(f"I choose **{choice}**")

    @commands.command(name="8ball", aliases=["8"], help="Call upon the powers of the all knowing magic 8Ball")
    async def eight_ball(self, ctx, question: str):
        group = random.choice(self.eight_ball_responses)
        response = random.choice(group)

        await ctx.send(response)

    @commands.command(name="emojify", aliases=["emoji"], help="Turn a sentence into emojis")
    async def emojify(self, ctx, *, sentence: str):
        emojified_sentence = ""

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
    async def ascii(self, ctx, *, sentence: str):
        ascii_text = pyfiglet.figlet_format(sentence)
        await ctx.send(f"```{ascii_text}```")


def setup(bot):
    bot.add_cog(Fun(bot))
