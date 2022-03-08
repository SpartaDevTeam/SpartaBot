import asyncio
import json
import discord
from discord.ext import commands

from bot import MyBot
from bot.data import Data
from bot.utils import dbl_vote_required


class AutoResponse(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = "Commands to setup Sparta Bot to automatically reply to certain phrases"
        self.theme_color = discord.Color.purple()

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.bot:
    #         return

    #     Data.c.execute(
    #         "SELECT auto_responses FROM guilds WHERE id = :guild_id",
    #         {"guild_id": message.guild.id},
    #     )
    #     auto_resps = json.loads(Data.c.fetchone()[0])
    #     content: str = message.content
    #     channel: discord.TextChannel = message.channel

    #     for activation in auto_resps:
    #         response = auto_resps[activation]

    #         # Auto Response Variables
    #         response = response.replace("[member]", str(message.author))
    #         response = response.replace("[nick]", message.author.display_name)
    #         response = response.replace("[name]", message.author.name)

    #         if content == activation:
    #             await channel.send(
    #                 response, allowed_mentions=discord.AllowedMentions.none()
    #             )

    @commands.command(
        name="addautoresponse",
        aliases=["addauto", "aar"],
        help="Add an auto response phrase.\n\nExample: addautoresponse activation, response\n\nVariables you can use: [member], [nick], [name]",
    )
    @dbl_vote_required()
    @commands.has_guild_permissions(administrator=True)
    async def add_auto_response(self, ctx: commands.Context, *, options: str):
        options_split = options.split(",", maxsplit=1)

        if len(options_split) < 2:
            await ctx.send("Please provide all the fields.")
            return

        Data.check_guild_entry(ctx.guild)
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

    @commands.command(
        name="removeautoresponse",
        aliases=["removeauto", "rar"],
        help="Remove an auto response phrase",
    )
    @commands.has_guild_permissions(administrator=True)
    async def remove_auto_response(
        self, ctx: commands.Context, *, activation: str = None
    ):
        Data.check_guild_entry(ctx.guild)

        if activation:
            Data.c.execute(
                "SELECT auto_responses FROM guilds WHERE id = :guild_id",
                {"guild_id": ctx.guild.id},
            )
            current_auto_resps = json.loads(Data.c.fetchone()[0])

            if activation not in current_auto_resps:
                await ctx.send(
                    "An auto response with this activation phrase does not exist"
                )
                return

            del current_auto_resps[activation]

            Data.c.execute(
                "UPDATE guilds SET auto_responses = :new_responses WHERE id = :guild_id",
                {
                    "new_responses": json.dumps(current_auto_resps),
                    "guild_id": ctx.guild.id,
                },
            )
            Data.conn.commit()
            await ctx.send(
                f"Auto response with activation:```{activation}```has been removed"
            )

        else:

            def check_msg(message: discord.Message):
                return (
                    message.author == ctx.author
                    and message.channel == ctx.channel
                )

            await ctx.send(
                "You are about to delete all auto responses in this server. Do you want to continue? (Yes to continue, anything else to abort)"
            )

            try:
                confirmation: discord.Message = await self.bot.wait_for(
                    "message", check=check_msg, timeout=30
                )

                if confirmation.content.lower() == "yes":
                    Data.c.execute(
                        "UPDATE guilds SET auto_responses = '{}' WHERE id = :guild_id",
                        {"guild_id": ctx.guild.id},
                    )
                    Data.conn.commit()
                    await ctx.send(
                        "All auto responses in this server have been deleted"
                    )
                else:
                    await ctx.send("Aborting!")

            except asyncio.TimeoutError:
                await ctx.send("No response received, aborting!")

    @commands.command(
        name="viewautoresponses",
        aliases=["viewauto", "var"],
        help="See all the auto responses in your server",
    )
    async def view_auto_responses(self, ctx: commands.Context):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT auto_responses FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        auto_resps = json.loads(Data.c.fetchone()[0])

        if len(auto_resps) > 0:
            auto_resps_embed = discord.Embed(
                title=f"Auto Responses in {ctx.guild}", color=self.theme_color
            )

            for activation in auto_resps:
                response = auto_resps[activation]
                auto_resps_embed.add_field(
                    name=activation, value=response, inline=False
                )

            await ctx.send(embed=auto_resps_embed)

        else:
            await ctx.send("This server does not have any auto responses")


def setup(bot):
    bot.add_cog(AutoResponse(bot))
