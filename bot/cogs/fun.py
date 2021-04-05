import random
import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands to have some fun and relieve stress (or induce it)"
        self.theme_color = discord.Color.purple()

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
        responses = [
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

        group = random.choice(responses)
        response = random.choice(group)

        await ctx.send(response)


def setup(bot):
    bot.add_cog(Fun(bot))
