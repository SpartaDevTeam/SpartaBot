import os
import aiohttp
import re
import urbanpython
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME


class SlashInternetStuff(commands.Cog):
    """
    Commands to surf the interwebs without leaving Discord
    """

    urban = urbanpython.Urban(os.environ["URBAN_API_KEY"])
    yt_search_url = "https://www.youtube.com/results?search_query="
    yt_video_url = "https://www.youtube.com/watch?v="

    @commands.slash_command(name="urban", guild_ids=TESTING_GUILDS)
    async def urban_dictionary(
        self, ctx: discord.ApplicationContext, query: str
    ):
        """
        Find word definitions on Urban Dictionary
        """

        await ctx.defer()
        try:
            result = self.urban.search(query)
        except IndexError:
            await ctx.respond(
                f"No definition found for term: {query}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        body = f"**Definition:**\n{result.definition}\n\n**Example:\n**{result.example}"
        written_on = result.written_on[:10]

        urban_embed = discord.Embed(
            title=f"Urban Dictionary: {query}",
            color=THEME,
            description=body,
            url=result.permalink,
        )
        urban_embed.set_author(
            name=str(ctx.author), icon_url=ctx.author.avatar.url
        )
        urban_embed.set_footer(
            text=f"By {result.author} on {written_on}\n👍 {result.thumbs_up} | 👎 {result.thumbs_down}"
        )

        if len(urban_embed) > 6000:
            urban_embed.description = urban_embed.description[:5900] + "..."
            await ctx.respond(
                "This definition is too big, so some of the contents were hidden",
                embed=urban_embed,
            )
        else:
            await ctx.respond(embed=urban_embed)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    async def youtube(self, ctx: discord.ApplicationContext, query: str):
        """
        Search YouTube for videos
        """

        formatted_query = "+".join(query.split())
        request_url = self.yt_search_url + formatted_query

        await ctx.defer()
        async with aiohttp.request("GET", request_url) as resp:
            html = (await resp.read()).decode()

        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        first_result = self.yt_video_url + video_ids[0]
        await ctx.respond(first_result)


def setup(bot):
    bot.add_cog(SlashInternetStuff())
