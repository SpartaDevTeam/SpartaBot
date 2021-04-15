import asyncio
import json
import discord
from discord.ext import commands

from bot.data import Data


class AutoResponse(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Commands to setup Sparta Bot to automatically reply to certain phrases"
        self.theme_color = discord.Color.purple()

    @commands.command(
        name="addautoresponse",
        aliases=["addauto"],
        help="Add an auto response phrase. Example: addautoresponse this is the activation, this is the response",
    )
    @commands.has_guild_permissions(administrator=True)
    async def add_auto_response_phrase(
        self, ctx: commands.Context, *, options: str
    ):
        options_split = options.split(",", maxsplit=1)

        if len(options_split) < 2:
            await ctx.send("Please provide all the fields.")
            return

        activation = options_split[0].strip()
        response = options_split[1].strip()

        Data.c.execute(
            "SELECT auto_responses FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )

        current_auto_resps = json.loads(Data.c.fetchone()[0])

        if activation in current_auto_resps:

            def check_msg(message: discord.Message):
                return (
                    message.author == ctx.author
                    and message.channel == ctx.channel
                )

            await ctx.send(
                "An auto response with this activation already exists and will be overwritten by the new one. Do you want to continue? (Yes to continue, anything else to abort)"
            )
            try:
                confirmation: discord.Message = await self.bot.wait_for(
                    "message", check=check_msg, timeout=30
                )

                if confirmation.content.lower() == "yes":
                    await ctx.send("Overwriting existing auto response!")
                else:
                    await ctx.send("Aborting!")
                    return

            except asyncio.TimeoutError:
                await ctx.send("No response received, aborting!")
                return

        current_auto_resps[activation] = response

        Data.c.execute(
            "UPDATE guilds SET auto_responses = :new_responses WHERE id = :guild_id",
            {
                "new_responses": json.dumps(current_auto_resps),
                "guild_id": ctx.guild.id,
            },
        )
        Data.conn.commit()

        await ctx.send(
            f"New auto response added with\n\nActivation Phrase:```{activation}```\nResponse:```{response}```"
        )


def setup(bot):
    bot.add_cog(AutoResponse(bot))
