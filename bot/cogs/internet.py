import os
import urllib.request
import re
import urbanpython
import discord
from discord.ext import commands


class InternetStuff(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.theme_color = discord.Color.purple()
        self.description = (
            "Commands to surf the interwebs without leaving Discord"
        )
        self.urban = urbanpython.Urban(os.environ["SPARTA_URBAN_API_KEY"])
        self.yt_search_url = "https://www.youtube.com/results?search_query="
        self.yt_video_url = "https://www.youtube.com/watch?v="

    @commands.command(
        name="urban", help="Find word definitions on Urban Dictionary"
    )
    async def urban_dictionary(self, ctx: commands.Context, *, query: str):
        with ctx.typing():
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

    @commands.command(
        name="youtube", aliases=["yt"], help="Search YouTube for videos"
    )
    async def youtube(self, ctx: commands.Context, *, query: str):
        formatted_query = "+".join(query.split())
        html = urllib.request.urlopen(self.yt_search_url + formatted_query)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        first_result = self.yt_video_url + video_ids[0]
        await ctx.send(first_result)


def setup(bot):
    bot.add_cog(InternetStuff(bot))
