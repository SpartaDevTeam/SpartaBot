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


def setup(bot):
    bot.add_cog(Fun(bot))
