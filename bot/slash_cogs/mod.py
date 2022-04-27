import asyncio
import random
import time
import discord
from typing import Sequence
from uuid import uuid4
from discord.errors import HTTPException
from discord.ext import commands
from sqlalchemy.future import select

from bot import TESTING_GUILDS, THEME, db
from bot import views
from bot.db import models
from bot.utils import str_time_to_timedelta
from bot.views import ConfirmView


class SlashModeration(commands.Cog):
    """
    Commands to uphold the peace and integrity of the server
    """

    async def create_mute_role(self, guild: discord.Guild) -> discord.Role:
        print(f"Creating new mute role for server {guild.name}")

        role_perms = discord.Permissions(send_messages=False)
        role_color = discord.Color.dark_gray()
        mute_role = await guild.create_role(
            name="Muted",
            permissions=role_perms,
            color=role_color,
            reason="No existing mute role provided",
        )

        guild_channels: Sequence[
            discord.abc.GuildChannel
        ] = await guild.fetch_channels()

        # Set permissions for channels
        for channel in guild_channels:
            await channel.set_permissions(mute_role, send_messages=False)

        # Set permissions for categories
        for category in guild.categories:
            await category.set_permissions(mute_role, send_messages=False)

        # Add new mute_role to database
        async with db.async_session() as session:
            guild_data: models.Guild | None = await session.get(
                models.Guild, guild.id
            )

            if guild_data:
                guild_data.mute_role = mute_role.id  # type: ignore
            else:
                new_guild_data = models.Guild(
                    id=guild.id, mute_role=mute_role.id
                )
                session.add(new_guild_data)

            await session.commit()

        return mute_role

    async def get_guild_mute_role(self, guild: discord.Guild) -> discord.Role:
        async with db.async_session() as session:
            guild_data: models.Guild | None = await session.get(
                models.Guild, guild.id
            )

            if guild_data:
                mute_role_id = guild_data.mute_role
            else:
                new_guild_data = models.Guild(id=guild.id)
                session.add(new_guild_data)
                await session.commit()

                mute_role_id = None

        if mute_role_id is None:
            # Create mute role if none is provided
            mute_role = await self.create_mute_role(guild)

        else:
            # Get mute role if one was provided
            mute_role = guild.get_role(mute_role_id)  # type: ignore

            # Check if the provided role still exists
            if mute_role is None:
                mute_role = await self.create_mute_role(guild)

        return mute_role

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def warn(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        *,
        reason: str,
    ):
        """
        Warn a member for doing something they weren't supposed to
        """

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.respond(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        new_infraction = models.Infraction(
            id=uuid4().hex,
            guild_id=ctx.guild_id,
            user_id=member.id,
            moderator_id=ctx.author.id,
            reason=reason,
        )

        async with db.async_session() as session:
            session.add(new_infraction)
            await session.commit()

        await ctx.respond(f"**{member}** has been warned because: *{reason}*")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def infractions(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member = None,
    ):
        """
        See all the infractions in this server
        """

        async with db.async_session() as session:
            q = select(models.Infraction).where(
                models.Infraction.guild_id == ctx.guild_id
            )

            if member:
                q = q.where(models.Infraction.user_id == member.id)

            result = await session.execute(q)
            infracs: list[models.Infraction] = result.scalars().all()

        if member:
            embed_title = f"Infractions by {member} in {ctx.guild.name}"
        else:
            embed_title = f"All Infractions in {ctx.guild.name}"

        infractions_embed = discord.Embed(title=embed_title, color=THEME)

        if infracs:

            async def embed_task(infraction: models.Infraction):
                if member:
                    guild_member = member
                else:
                    guild_member = await ctx.guild.fetch_member(
                        infraction.user_id
                    )

                moderator = await ctx.guild.fetch_member(
                    infraction.moderator_id
                )

                infractions_embed.add_field(
                    name=f"ID: {infraction.id}",
                    value=(
                        f"**Member:** {guild_member.mention}\n"
                        f"**Reason:** {infraction.reason}\n"
                        f"**Warned by:** {moderator.mention}"
                    ),
                    inline=False,
                )

            tasks = [embed_task(inf) for inf in infracs]
            await asyncio.gather(*tasks)

        elif member:
            infractions_embed.description = (
                f"There are no infractions for {member}"
            )
        else:
            infractions_embed.description = (
                "There are no infractions in this server"
            )

        await ctx.respond(embed=infractions_embed)

    @commands.slash_command(name="clearinfractions", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def clear_infractions(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member = None,
    ):
        """
        Clear somebody's infractions in the current server
        """

        if member is None:
            confirm_view = ConfirmView(ctx.author.id)
            await ctx.respond(
                "You are about to clear everyone's infractions in this server. Do you want to continue?",
                view=confirm_view,
            )
            await confirm_view.wait()

            if confirm_view.do_action:
                async with db.async_session() as session:
                    q = select(models.Infraction).where(
                        models.Infraction.guild_id == ctx.guild_id
                    )
                    result = await session.execute(q)
                    tasks = [
                        session.delete(inf) for inf in result.scalars().all()
                    ]
                    await asyncio.gather(*tasks)
                    await session.commit()

                await ctx.respond("Cleared all infractions in this server")

        else:
            if (
                ctx.guild.owner_id != ctx.author.id
                and ctx.author.top_role <= member.top_role
            ):
                await ctx.respond(
                    "You cannot use the command on this person because their top role is higher than or equal to yours."
                )
                return

            async with db.async_session() as session:
                q = (
                    select(models.Infraction)
                    .where(models.Infraction.guild_id == ctx.guild_id)
                    .where(models.Infraction.user_id == member.id)
                )
                result = await session.execute(q)
                tasks = [session.delete(inf) for inf in result.scalars().all()]
                await asyncio.gather(*tasks)
                await session.commit()

            await ctx.respond(
                f"Cleared all infractions by **{member}** in this server"
            )

    @commands.slash_command(name="removeinfraction", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def remove_infraction(
        self, ctx: discord.ApplicationContext, id: str
    ):
        """
        Delete a particular infraction
        """

        async with db.async_session() as session:
            inf = await session.get(models.Infraction, id)

            if inf:
                await session.delete(inf)
                await session.commit()
                await ctx.respond(f"Deleted infraction with ID `{id}`")
            else:
                await ctx.respond("Unable to find an infraction with that ID")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        mute_time: str = None,
    ):
        """
        Prevent someone from sending messages. For temp mute, specify a time. Example: /mute @member 5h
        """

        if member.id == ctx.bot.user.id:
            await ctx.respond(f"**{member}** can no longer- Wait a minute...")
            return

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.respond(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        await ctx.defer()
        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.add_roles(mute_role)

        if mute_time:
            now_epoch = time.time()
            mute_timedelta = str_time_to_timedelta(mute_time)
            humanized_time_str = (
                f"<t:{int(now_epoch + mute_timedelta.total_seconds())}:R>"
            )

            await ctx.respond(
                f"**{member}** will be unmuted {humanized_time_str}"
            )
            await asyncio.sleep(mute_timedelta.total_seconds())
            unmute_str = f"**{member}** was unmuted {humanized_time_str}"

            if mute_role in member.roles:
                await member.remove_roles(mute_role)
                await ctx.send(unmute_str)

        else:
            await ctx.respond(f"**{member}** can no longer speak")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(
        self, ctx: discord.ApplicationContext, member: discord.Member
    ):
        """
        Return the ability to talk to someone
        """

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.respond(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.remove_roles(mute_role)
        await ctx.respond(f"**{member}** can speak now")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        *,
        reason: str = None,
    ):
        """
        Permanently remove a person from the server
        """

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.respond(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        await ctx.guild.ban(
            member,
            reason=f"Banned by {ctx.author}, Reason: {reason}",
            delete_message_days=0,
        )
        await ctx.respond(f"**{member}** has been banned from this server")

        if not member.bot:
            await member.send(
                f"You have been banned from **{ctx.guild.name}**"
            )

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: discord.ApplicationContext, *, username: str):
        """
        Unban a person from the server
        """

        if username[-5] != "#":
            await ctx.send(
                "Please give a username in this format: *username#0000*"
            )
            return

        name = username[:-5]  # first character to 6th last character
        discriminator = username[-4:]  # last 4 characters
        user_to_unban = None

        async for ban_entry in ctx.guild.bans():
            banned_user: discord.User = ban_entry.user

            if (
                banned_user.name == name
                and banned_user.discriminator == discriminator
            ):
                user_to_unban = banned_user
                break

        if user_to_unban:
            await ctx.guild.unban(
                user_to_unban, reason=f"Unbanned by {ctx.author}"
            )
            await ctx.respond(
                f"**{user_to_unban}** has been unbanned from this server"
            )
            await user_to_unban.send(
                f"You have been unbanned from **{ctx.guild.name}**"
            )
        else:
            await ctx.respond("This person does not appear to be banned")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        *,
        reason: str = None,
    ):
        """
        Remove a person from the server
        """

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.respond(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        await ctx.guild.kick(
            member, reason=f"Kicked by {ctx.author}, Reason: {reason}"
        )
        await ctx.respond(f"**{member}** has been kicked from this server")

        if not member.bot:
            await member.send(
                f"You have been kicked from **{ctx.guild.name}**"
            )

    @commands.slash_command(name="lock", guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def lock_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = None,
    ):
        """
        Prevent non-admins from sending messages in this channel
        """

        if not channel:
            channel = ctx.channel

        await channel.set_permissions(
            ctx.guild.default_role, send_messages=False
        )
        await ctx.respond(f":lock: {channel.mention} has been locked")

    @commands.slash_command(name="unlock", guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def unlock_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = None,
    ):
        """
        Reverse the effects of /lock
        """

        if not channel:
            channel = ctx.channel

        await channel.edit(sync_permissions=True)
        await ctx.respond(f":unlock: {channel.mention} has been unlocked")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: discord.ApplicationContext, delay: int):
        """
        Add slowmode delay in the current channel
        """

        await ctx.channel.edit(slowmode_delay=delay)

        if delay > 0:
            await ctx.respond(f"Added a slowmode delay of **{delay} seconds**")
        else:
            await ctx.respond("Slowmode has been disabled")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx: discord.ApplicationContext, amount: int):
        """
        Clear messages in a channel
        """

        await ctx.defer(ephemeral=True)

        async with db.async_session() as session:
            guild_data: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            if guild_data:
                limit = guild_data.clear_cap
            else:
                new_guild_data = models.Guild(id=ctx.guild_id)
                session.add(new_guild_data)
                await session.commit()

                limit = new_guild_data.clear_cap

        if limit and amount > limit:
            exceeds_by = amount - limit
            await ctx.respond(
                f"Clear amount exceeds this server's limit by {exceeds_by}. The limit is {limit}.",
                ephemeral=True,
            )
            return

        await ctx.channel.purge(limit=amount)
        await ctx.respond(f"Cleared {amount} message(s)", ephemeral=True)

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(administrator=True)
    async def nuke(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = None,
    ):
        """
        Clear all messages at once in a channel
        """

        if not channel:
            channel = ctx.channel

        nuke_gifs = [
            "https://media1.tenor.com/images/3ddd966749079d6802bcea8dbcceb365/tenor.gif",
            "https://media1.tenor.com/images/403968cd056f0d0bfb5cce75e131b4d4/tenor.gif",
            "https://media1.tenor.com/images/1daf50232c9eda10459560e8c1e532ea/tenor.gif",
        ]
        confirm_view = ConfirmView(ctx.author.id)
        await ctx.respond(
            f"Are you sure you want to nuke {channel.mention}? This action cannot be undone.",
            view=confirm_view,
        )
        await confirm_view.wait()

        if confirm_view.do_action:
            reason = f"Channel Nuke by {ctx.author}"
            ch_pos = channel.position
            new_ch = await channel.clone(reason=reason)

            try:
                await channel.delete(reason=reason)
                await new_ch.edit(reason=reason, position=ch_pos)

                nuke_embed = discord.Embed(title=reason, color=THEME)
                nuke_embed.set_image(url=random.choice(nuke_gifs))

                await new_ch.send(embed=nuke_embed)

            except HTTPException as e:
                await new_ch.delete()
                await ctx.send(f"Unable to nuke {channel.mention}: {e.text}")

    @commands.slash_command(name="impersonatelogs", guild_id=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def impersonate_logs(self, ctx: discord.ApplicationContext):
        """
        See the impersonation logs for this server
        """

        await ctx.defer()

        async with db.async_session() as session:
            q = select(models.ImpersonationLog).where(
                models.ImpersonationLog.guild_id == ctx.guild_id
            )
            results = await session.execute(q)
            logs: list[models.ImpersonationLog] = results.scalars().all()
            logs.sort(key=lambda x: x.timestamp, reverse=True)

        if not logs:
            await ctx.respond(
                "Nobody has used impersonate in this server yet",
                ephemeral=True,
            )
            return

        base_embed = discord.Embed(
            title=f"Impersonation Logs for {ctx.guild}", color=THEME
        )
        base_embed.set_author(
            name=str(ctx.author), icon_url=ctx.author.display_avatar.url
        )

        max_per_page = 5
        page_count = len(logs) // max_per_page + 1
        log_embeds: list[discord.Embed] = [
            base_embed.copy().set_footer(text=f"Page {i+1} of {page_count}")
            for i in range(page_count)
        ]

        for i, imp in enumerate(logs):
            current_embed = log_embeds[i // max_per_page]

            jump_url = f"https://discord.com/channels/{imp.guild_id}/{imp.channel_id}/{imp.message_id}"
            embed_str = (
                f"Impersonated User: <@{imp.user_id}>\n"
                f"Impersonator: <@{imp.impersonator_id}>\n"
                f"Sent on: <t:{int(imp.timestamp.timestamp())}>\n"
                f"[Jump to Message]({jump_url})"
            )

            current_embed.add_field(
                name=imp.message, value=embed_str, inline=False
            )

        if len(logs) > max_per_page:
            page_view = views.PaginatedEmbedView(ctx.author.id, log_embeds)
            msg = await ctx.respond(embed=log_embeds[0], view=page_view)

            if await page_view.wait():  # if the view timed out
                if isinstance(msg, discord.Interaction):
                    msg.delete_original_message()
                else:
                    msg.delete()
        else:
            await ctx.respond(embed=log_embeds[0])


def setup(bot):
    bot.add_cog(SlashModeration())
