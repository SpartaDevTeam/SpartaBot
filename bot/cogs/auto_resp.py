import asyncio
import discord
from uuid import uuid4
from discord.ext import commands
from sqlalchemy.future import select

from bot import MyBot, db
from bot.db import models
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

        activation = options_split[0].strip()
        response = options_split[1].strip()

        async with db.async_session() as session:
            q = (
                select(models.AutoResponse)
                .where(models.AutoResponse.guild_id == ctx.guild.id)
                .where(models.AutoResponse.activation == activation)
            )
            result = await session.execute(q)
            duplicate_auto_resp: models.AutoResponse | None = result.scalar()

            if duplicate_auto_resp:

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

                duplicate_auto_resp.response = response

            else:
                new_auto_resp = models.AutoResponse(
                    id=uuid4().hex,
                    guild_id=ctx.guild.id,
                    activation=activation,
                    response=response,
                )
                session.add(new_auto_resp)

            await session.commit()

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
        self, ctx: commands.Context, id: str = None
    ):
        if id:
            async with db.async_session() as session:
                auto_resp: models.AutoResponse | None = await session.get(
                    models.AutoResponse, id
                )

                if not auto_resp:
                    await ctx.send(
                        "An auto response with this ID does not exist"
                    )
                    return

                await session.delete(auto_resp)
                await session.commit()

                await ctx.send(
                    f"Auto response with\nactivation: `{auto_resp.activation}`\nresponse: `{auto_resp.response}`\nhas been removed"
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
                    async with db.async_session() as session:
                        q = select(models.AutoResponse).where(
                            models.AutoResponse.guild_id == ctx.guild.id
                        )
                        results = await session.execute(q)
                        tasks = [session.delete(r) for r in results.scalars()]
                        await asyncio.gather(*tasks)
                        await session.commit()

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
        async with db.async_session() as session:
            q = select(models.AutoResponse).where(
                models.AutoResponse.guild_id == ctx.guild.id
            )
            result = await session.execute(q)
            auto_resps: list[models.AutoResponse] = result.scalars().all()

        if len(auto_resps) > 0:
            auto_resps_embed = discord.Embed(
                title=f"Auto Responses in {ctx.guild}", color=self.theme_color
            )

            for ar in auto_resps:
                field_value = (
                    f"Activation: `{ar.activation}`\nResponse: `{ar.response}`"
                )
                auto_resps_embed.add_field(
                    name=ar.id, value=field_value, inline=False
                )

            await ctx.send(embed=auto_resps_embed)

        else:
            await ctx.send("This server does not have any auto responses")


def setup(bot):
    bot.add_cog(AutoResponse(bot))
