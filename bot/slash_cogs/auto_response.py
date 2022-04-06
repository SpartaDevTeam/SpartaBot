import asyncio
import discord
from uuid import uuid4
from discord.ext import commands
from sqlalchemy.future import select

from bot import TESTING_GUILDS, THEME, db
from bot.db import models
from bot.utils import dbl_vote_required
from bot.views import ConfirmView


class SlashAutoResponse(commands.Cog):
    """
    Commands to make Sparta automatically reply to certain phrases
    """

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content: str = message.content
        channel: discord.TextChannel = message.channel

        async with db.async_session() as session:
            q = (
                select(models.AutoResponse)
                .where(models.AutoResponse.guild_id == message.guild.id)
                .where(models.AutoResponse.activation == content)
            )
            results = await session.execute(q)
            auto_resp: models.AutoResponse | None = results.scalar()

        if not auto_resp:
            return

        response = auto_resp.response

        # Auto Response Variables
        response = response.replace("[member]", str(message.author))
        response = response.replace("[nick]", message.author.display_name)
        response = response.replace("[name]", message.author.name)

        await channel.send(
            response, allowed_mentions=discord.AllowedMentions.none()
        )

    @dbl_vote_required()
    @commands.slash_command(name="addautoresponse", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def add_auto_response(
        self, ctx: discord.ApplicationContext, activation: str, response: str
    ):
        """
        Add an auto response phrase. Variables you can use: [member], [nick], [name]
        """

        async with db.async_session() as session:
            q = (
                select(models.AutoResponse)
                .where(models.AutoResponse.guild_id == ctx.guild.id)
                .where(models.AutoResponse.activation == activation)
            )
            result = await session.execute(q)
            duplicate_auto_resp: models.AutoResponse | None = result.scalar()

            if duplicate_auto_resp:
                confirm_view = ConfirmView(ctx.author.id)
                await ctx.respond(
                    "An auto response with this activation already exists and will be overwritten by the new one. Do you want to continue?",
                    view=confirm_view,
                )
                await confirm_view.wait()

                if confirm_view.do_action:
                    duplicate_auto_resp.response = response
                    ar_id = duplicate_auto_resp.id
                else:
                    return

            else:
                new_auto_resp = models.AutoResponse(
                    id=uuid4().hex,
                    guild_id=ctx.guild.id,
                    activation=activation,
                    response=response,
                )
                session.add(new_auto_resp)
                ar_id = new_auto_resp.id

            await session.commit()

        ar_embed = discord.Embed(title="New Auto Response", color=THEME)
        ar_embed.add_field(name="ID", value=ar_id, inline=False)
        ar_embed.add_field(name="Activation", value=activation, inline=False)
        ar_embed.add_field(name="Response", value=response, inline=False)
        await ctx.respond(embed=ar_embed)

    @commands.slash_command(
        name="removeautoresponse", guild_ids=TESTING_GUILDS
    )
    @commands.has_guild_permissions(administrator=True)
    async def remove_auto_response(
        self, ctx: discord.ApplicationContext, id: str = None
    ):
        """
        Remove an auto response phrase
        """

        if id:
            async with db.async_session() as session:
                auto_resp: models.AutoResponse | None = await session.get(
                    models.AutoResponse, id
                )

                if not auto_resp:
                    await ctx.respond(
                        "An auto response with this ID does not exist"
                    )
                    return

                await session.delete(auto_resp)
                await session.commit()

            ar_embed = discord.Embed(
                title="Deleted Auto Response", color=THEME
            )
            ar_embed.add_field(name="ID", value=id, inline=False)
            ar_embed.add_field(
                name="Activation",
                value=auto_resp.activation,
                inline=False,
            )
            ar_embed.add_field(
                name="Response", value=auto_resp.response, inline=False
            )
            await ctx.respond(embed=ar_embed)

        else:
            confirm_view = ConfirmView(ctx.author.id)
            await ctx.respond(
                "You are about to delete all auto responses in this server. Do you want to continue?",
                view=confirm_view,
            )
            await confirm_view.wait()

            if confirm_view.do_action:
                async with db.async_session() as session:
                    q = select(models.AutoResponse).where(
                        models.AutoResponse.guild_id == ctx.guild.id
                    )
                    results = await session.execute(q)
                    tasks = [session.delete(r) for r in results.scalars()]
                    await asyncio.gather(*tasks)
                    await session.commit()

                await ctx.respond(
                    "All auto responses in this server have been deleted"
                )

    @commands.slash_command(name="viewautoresponses", guild_ids=TESTING_GUILDS)
    async def view_auto_responses(self, ctx: discord.ApplicationContext):
        """
        See all the auto responses in the server
        """

        async with db.async_session() as session:
            q = select(models.AutoResponse).where(
                models.AutoResponse.guild_id == ctx.guild.id
            )
            result = await session.execute(q)
            auto_resps: list[models.AutoResponse] = result.scalars().all()

        if auto_resps:
            auto_resps_embed = discord.Embed(
                title=f"Auto Responses in {ctx.guild}", color=THEME
            )

            for ar in auto_resps:
                field_value = (
                    f"Activation: `{ar.activation}`\nResponse: `{ar.response}`"
                )
                auto_resps_embed.add_field(
                    name=ar.id, value=field_value, inline=False
                )

            await ctx.respond(embed=auto_resps_embed)

        else:
            await ctx.respond("This server does not have any auto responses")


def setup(bot):
    bot.add_cog(SlashAutoResponse())
