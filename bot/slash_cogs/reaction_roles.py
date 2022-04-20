import discord
from uuid import uuid4
from discord.ext import commands
from emoji import emojize
from sqlalchemy.future import select

from bot import TESTING_GUILDS, THEME, db
from bot.db import models
from bot.utils import dbl_vote_required


class SlashReactionRoles(commands.Cog):
    """
    Commands to setup reaction roles for members of your server to give
    themselves roles
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ):
        if not payload.guild_id:
            return

        guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
        member: discord.Member = await guild.fetch_member(payload.user_id)
        emoji: str | None = str(payload.emoji.id or payload.emoji.name)

        if member == self.bot.user or not emoji:
            return

        async with db.async_session() as session:
            q = (
                select(models.ReactionRole)
                .where(models.ReactionRole.guild_id == guild.id)
                .where(models.ReactionRole.channel_id == payload.channel_id)
                .where(models.ReactionRole.message_id == payload.message_id)
                .where(models.ReactionRole.emoji == emoji)
            )
            result = await session.execute(q)
            rr: models.ReactionRole = result.scalar()

            if rr:
                if role := guild.get_role(rr.role_id):  # type: ignore
                    await member.add_roles(role, reason="Reaction Role")
                    await member.send(
                        f"You have been given the **{role}** role in **{guild}**"
                    )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self, payload: discord.RawReactionActionEvent
    ):
        if not payload.guild_id:
            return

        guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
        member: discord.Member = await guild.fetch_member(payload.user_id)
        emoji: str | None = str(payload.emoji.id or payload.emoji.name)

        if member == self.bot.user or not emoji:
            return

        async with db.async_session() as session:
            q = (
                select(models.ReactionRole)
                .where(models.ReactionRole.guild_id == guild.id)
                .where(models.ReactionRole.channel_id == payload.channel_id)
                .where(models.ReactionRole.message_id == payload.message_id)
                .where(models.ReactionRole.emoji == emoji)
            )
            result = await session.execute(q)
            rr: models.ReactionRole = result.scalar()

            if rr:
                if role := guild.get_role(rr.role_id):  # type: ignore
                    await member.remove_roles(role, reason="Reaction Role")
                    await member.send(
                        f"Your **{role}** role in **{guild}** has been removed"
                    )

    @commands.slash_command(name="addreactionrole", guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_roles=True, add_reactions=True)
    @commands.has_guild_permissions(manage_roles=True)
    @dbl_vote_required()
    async def add_reaction_role(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel,
        role: discord.Role,
        emoji: str,
        message_id: str,
    ):
        """
        Add a reaction role
        """

        original_emoji = emoji = emoji.strip()

        if emoji.startswith("<") and emoji.endswith(">"):
            try:
                emoji = emoji.strip("<>").split(":")[-1]
            except ValueError:
                await ctx.respond("Unable to read the given custom emoji")
                return

        if message_id.isnumeric():
            message_id = int(message_id)
        else:
            await ctx.respond("Invalid message ID was provided")
            return

        await ctx.defer()

        async with db.async_session() as session:
            q = (
                select(models.ReactionRole)
                .where(models.ReactionRole.guild_id == ctx.guild_id)
                .where(models.ReactionRole.channel_id == channel.id)
                .where(models.ReactionRole.message_id == message_id)
                .where(models.ReactionRole.emoji == emoji)
                .where(models.ReactionRole.role_id == role.id)
            )
            result = await session.execute(q)
            existing_rr: models.ReactionRole = result.scalar()

        if existing_rr:
            await ctx.respond(
                f"A reaction role with this configuration already exists with ID `{existing_rr.id}`"
            )

        else:
            try:
                message = await channel.fetch_message(message_id)
                await message.add_reaction(original_emoji)
                new_rr_id = uuid4()

                async with db.async_session() as session:
                    new_rr = models.ReactionRole(
                        id=new_rr_id.hex,
                        guild_id=ctx.guild_id,
                        channel_id=channel.id,
                        message_id=message_id,
                        emoji=emoji,
                        role_id=role.id,
                    )
                    session.add(new_rr)
                    await session.commit()

                await ctx.respond(
                    f"Reaction Role with ID `{new_rr_id.hex}` for {role.mention} has been created with {original_emoji}.\n\nJump to message: {message.jump_url}",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

            except discord.NotFound:
                await ctx.respond("Could not find a message with the given ID")

            except discord.Forbidden:
                await ctx.respond(
                    "Cannot access the message with the given ID"
                )

    @commands.slash_command(
        name="removereactionrole", guild_ids=TESTING_GUILDS
    )
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_reaction_role(
        self, ctx: discord.ApplicationContext, id: str
    ):
        """
        Remove a reaction role
        """

        async with db.async_session() as session:
            rr = await session.get(models.ReactionRole, id)

            if rr:
                await session.delete(rr)
                await session.commit()
                await ctx.respond(
                    f"Reaction Role with ID `{id}` has been removed"
                )
            else:
                await ctx.respond(
                    "Could not find a reaction role with the given ID"
                )

    @commands.slash_command(name="viewreactionroles", guild_ids=TESTING_GUILDS)
    async def view_reaction_roles(self, ctx: discord.ApplicationContext):
        """
        See the reaction roles setup in your server.
        """

        await ctx.defer()

        async with db.async_session() as session:
            q = select(models.ReactionRole).where(
                models.ReactionRole.guild_id == ctx.guild_id
            )
            result = await session.execute(q)
            reaction_roles: list[models.ReactionRole] = result.scalars().all()

        if not reaction_roles:
            await ctx.respond(
                "There aren't any reaction roles setup in this server"
            )
            return

        guild_roles = await ctx.guild.fetch_roles()
        rr_embed = discord.Embed(
            title=f"{ctx.guild.name} Reaction Roles", color=THEME
        )

        for rr in reaction_roles:

            async def delete_rr():
                async with db.async_session() as session:
                    await session.delete(rr)
                    await session.commit()

            try:
                rr_channel: discord.TextChannel = (
                    await ctx.guild.fetch_channel(rr.channel_id)
                )
            except discord.NotFound:
                await delete_rr()
                continue

            try:
                rr_message: discord.Message = await rr_channel.fetch_message(
                    rr.message_id
                )
            except discord.NotFound:
                await delete_rr()
                continue

            if rr.emoji.isnumeric():
                try:
                    rr_emoji: discord.Emoji = await ctx.guild.fetch_emoji(
                        int(rr.emoji)
                    )
                except discord.NotFound:
                    await delete_rr()
                    continue
            else:
                rr_emoji = emojize(rr.emoji)

            if not (rr_role := discord.utils.get(guild_roles, id=rr.role_id)):
                await delete_rr()
                continue

            embed_str = (
                f"Emoji: {rr_emoji}\n"
                f"Role: {rr_role.mention}\n"
                f"Channel: {rr_channel.mention}\n"
                f"[Jump to Message]({rr_message.jump_url})"
            )
            rr_embed.add_field(
                name=f"ID: {rr.id}", value=embed_str, inline=False
            )

        await ctx.respond(embed=rr_embed)


def setup(bot):
    bot.add_cog(SlashReactionRoles(bot))
