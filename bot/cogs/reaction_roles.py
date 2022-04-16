import asyncio
import emoji
import discord
from uuid import uuid4
from discord.ext import commands
from sqlalchemy.future import select

from bot import MyBot, db
from bot.db import models
from bot.utils import dbl_vote_required


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.theme_color = discord.Color.purple()
        self.description = "Commands to setup reaction roles for members of your server to give themselves roles"

    async def react_prompt(
        self, ctx: commands.Context, prompt_msg: str
    ) -> discord.Reaction:
        message = await ctx.send(prompt_msg)

        def check_reaction(reaction: discord.Reaction, member: discord.Member):
            return member == ctx.author and reaction.message == message

        response = await self.bot.wait_for(
            "reaction_add", check=check_reaction, timeout=120
        )
        return response[0]

    async def msg_prompt(
        self, ctx: commands.Context, prompt_msg: str
    ) -> discord.Message:
        def check_msg(message: discord.Message):
            return (
                message.author == ctx.author and message.channel == ctx.channel
            )

        await ctx.send(prompt_msg)
        response: discord.Message = await self.bot.wait_for(
            "message", check=check_msg, timeout=120
        )
        return response

    # @commands.Cog.listener()
    # async def on_raw_reaction_add(
    #     self, payload: discord.RawReactionActionEvent
    # ):
    #     guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
    #     member: discord.Member = await guild.fetch_member(payload.user_id)

    #     if member == self.bot.user:
    #         return

    #     Data.c.execute(
    #         "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
    #         {"guild_id": guild.id},
    #     )
    #     react_roles = Data.c.fetchall()

    #     for rr in react_roles:
    #         rr_channel_id = rr[0]
    #         rr_message_id = rr[1]

    #         try:
    #             rr_emoji: discord.Emoji = await guild.fetch_emoji(int(rr[2]))
    #         except ValueError:
    #             rr_emoji: discord.PartialEmoji = discord.PartialEmoji(
    #                 name=emoji.emojize(rr[2])
    #             )

    #         rr_role: discord.Role = guild.get_role(int(rr[3]))

    #         if (
    #             payload.channel_id == rr_channel_id
    #             and payload.message_id == rr_message_id
    #             and payload.emoji.name == rr_emoji.name
    #         ):
    #             await member.add_roles(rr_role, reason="Sparta Reaction Role")
    #             await member.send(
    #                 f"You have been given the **{rr_role}** role in **{guild}**"
    #             )

    # @commands.Cog.listener()
    # async def on_raw_reaction_remove(
    #     self, payload: discord.RawReactionActionEvent
    # ):
    #     guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
    #     member: discord.Member = await guild.fetch_member(payload.user_id)

    #     if member == self.bot.user:
    #         return

    #     Data.c.execute(
    #         "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
    #         {"guild_id": guild.id},
    #     )
    #     react_roles = Data.c.fetchall()

    #     for rr in react_roles:
    #         rr_channel_id = rr[0]
    #         rr_message_id = rr[1]

    #         try:
    #             rr_emoji: discord.Emoji = await guild.fetch_emoji(int(rr[2]))
    #         except ValueError:
    #             rr_emoji: discord.PartialEmoji = discord.PartialEmoji(
    #                 name=emoji.emojize(rr[2])
    #             )

    #         rr_role: discord.Role = guild.get_role(int(rr[3]))

    #         if (
    #             payload.channel_id == rr_channel_id
    #             and payload.message_id == rr_message_id
    #             and payload.emoji.name == rr_emoji.name
    #         ):
    #             await member.remove_roles(
    #                 rr_role, reason="Sparta Reaction Role"
    #             )
    #             await member.send(
    #                 f"Your **{rr_role}** role in **{guild}** has been removed"
    #             )

    @commands.command(
        name="addreactionrole",
        aliases=["addrr", "reactionrole"],
        help="Add a reaction role",
    )
    @commands.bot_has_guild_permissions(manage_roles=True, add_reactions=True)
    @commands.has_guild_permissions(manage_roles=True)
    @dbl_vote_required()
    async def add_reaction_role(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild

        try:
            rr_channel = None
            while not rr_channel:
                channel_msg = await self.msg_prompt(
                    ctx,
                    "Please mention the channel where you want to setup a reaction role",
                )
                channel_mentions = channel_msg.channel_mentions

                if channel_mentions:
                    rr_channel = channel_mentions[0]

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        try:
            rr_message = None
            while not rr_message:
                message_msg = await self.msg_prompt(
                    ctx,
                    "Please send the ID of the message where you want to setup a reaction role",
                )
                try:
                    message = await rr_channel.fetch_message(
                        int(message_msg.content)
                    )

                    if message:
                        rr_message = message
                except ValueError:
                    continue

                except discord.NotFound:
                    await ctx.send("Could not fetch message with that ID")

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        try:
            rr_emoji = None
            while not rr_emoji:
                emoji_react = await self.react_prompt(
                    ctx,
                    "Please react to this message with the emoji you want to use for the reaction role",
                )
                rr_emoji = emoji_react.emoji

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        try:
            rr_role = None
            while not rr_role:
                role_msg = await self.msg_prompt(
                    ctx,
                    "Please mention or send the ID of the role you want to give to members",
                )

                try:
                    role_id = int(role_msg.content)
                    role = guild.get_role(role_id)
                    if role:
                        rr_role = role

                except ValueError:
                    role_mentions = role_msg.role_mentions
                    if role_mentions:
                        rr_role = role_mentions[0]

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        await rr_message.add_reaction(rr_emoji)

        if isinstance(rr_emoji, str):
            em = rr_emoji
        else:
            em = str(rr_emoji.id)

        async with db.async_session() as session:
            q = (
                select(models.ReactionRole)
                .where(models.ReactionRole.guild_id == ctx.guild.id)
                .where(models.ReactionRole.channel_id == rr_channel.id)
                .where(models.ReactionRole.message_id == rr_message.id)
                .where(models.ReactionRole.emoji == em)
                .where(models.ReactionRole.role_id == rr_role.id)
            )
            result = await session.execute(q)
            existing_rr: models.ReactionRole = result.scalar()

        if existing_rr:
            await ctx.send(
                f"A reaction role with this configuration already exists with ID `{existing_rr.id}`"
            )
        else:
            new_rr_id = uuid4()

            async with db.async_session() as session:
                new_rr = models.ReactionRole(
                    id=new_rr_id.hex,
                    guild_id=ctx.guild.id,
                    channel_id=rr_channel.id,
                    message_id=rr_message.id,
                    emoji=em,
                    role_id=rr_role.id,
                )
                session.add(new_rr)
                await session.commit()

            await ctx.send(
                f"Reaction Role for {rr_role.mention} has been created with {rr_emoji} at {rr_channel.mention}",
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @commands.command(
        name="removereactionrole",
        aliases=["rrr", "removerr"],
        help="Remove a reaction role",
    )
    @commands.bot_has_guild_permissions(manage_roles=True, add_reactions=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_reaction_role(self, ctx: commands.Context, id: str):
        async with db.async_session() as session:
            rr = await session.get(models.ReactionRole, id)

            if rr:
                await session.delete(rr)
                await session.commit()
                await ctx.send(
                    f"Reaction Role with ID `{id}` has been removed"
                )
            else:
                await ctx.send(
                    "Could not find a reaction role with the given ID"
                )

    @commands.command(
        name="viewreactionroles",
        aliases=["vrr", "viewrr"],
        help="See the reaction roles setup in your server. If you've deleted any channel, emoji, or role that was used in an RR, this command will cleanup their entries from your server.",
    )
    async def view_reaction_roles(self, ctx: commands.Context):
        async with db.async_session() as session:
            q = select(models.ReactionRole).where(
                models.ReactionRole.guild_id == ctx.guild.id
            )
            result = await session.execute(q)
            reaction_roles: list[models.ReactionRole] = result.scalars().all()

        if not reaction_roles:
            await ctx.send(
                "There aren't any reaction roles setup in this server"
            )
            return

        guild_roles = await ctx.guild.fetch_roles()
        rr_embed = discord.Embed(
            title=f"{ctx.guild.name} Reaction Roles", color=self.theme_color
        )

        async with ctx.typing():
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
                    rr_message: discord.Message = (
                        await rr_channel.fetch_message(rr.message_id)
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
                    rr_emoji = emoji.emojize(rr.emoji)

                if not (
                    rr_role := discord.utils.get(guild_roles, id=rr.role_id)
                ):
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

        await ctx.send(embed=rr_embed)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
