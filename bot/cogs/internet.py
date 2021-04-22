import os
import urbanpython
import discord
from datetime import datetime
from discord.ext import commands


class InternetStuff(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.theme_color = discord.Color.purple()
        self.description = (
            "Commands to surf the interwebs without leaving Discord"
        )
        self.urban = urbanpython.Urban(os.environ["SPARTA_URBAN_API_KEY"])

    @commands.command(
        name="urban", help="Find word definitions on Urban Dictionary"
    )
    async def urban_dictionary(self, ctx: commands.Context, *, query: str):
        try:
            result = self.urban.search(query)
        except IndexError:
            await ctx.send(
                f"No definition found for term: {query}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        body = f"**Definition:**\n{result.definition}\n\n**Example:\n**{result.example}"
        written_on = result.written_on[:10]

        urban_embed = discord.Embed(
            title=f"{query} Urban Definition",
            color=self.theme_color,
            description=body,
            url=result.permalink,
        )
        urban_embed.set_footer(
            text=f"Written by {result.author} on {written_on}"
        )

        if len(urban_embed.description) > 2048:
            urban_embed.description = urban_embed.description[:2048]
            await ctx.send(
                "This definition is too big, so some of the contents were hidden",
                embed=urban_embed,
            )
        else:
            await ctx.send(embed=urban_embed)


def setup(bot):
    bot.add_cog(InternetStuff(bot))
