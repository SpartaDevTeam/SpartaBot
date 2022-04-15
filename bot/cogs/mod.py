import asyncio
import json
import time
import random
from uuid import uuid4

import discord
from discord.ext import commands
from sqlalchemy.future import select

from bot import MyBot, db
from bot.db import models
from bot.utils import str_time_to_timedelta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = (
            "Commands to uphold the peace and integrity of the server"
        )
        self.theme_color = discord.Color.purple()
        self.nuke_gifs = [
            "https://media1.tenor.com/images/3ddd966749079d6802bcea8dbcceb365/tenor.gif",
            "https://media1.tenor.com/images/403968cd056f0d0bfb5cce75e131b4d4/tenor.gif",
            "https://media1.tenor.com/images/1daf50232c9eda10459560e8c1e532ea/tenor.gif",
        ]

    async def create_mute_role(self, guild: discord.Guild):
        print(f"Creating new mute role for server {guild.name}")
        role_perms = discord.Permissions(send_messages=False)
        role_color = discord.Color.dark_gray()
        mute_role = await guild.create_role(
            name="Muted",
            permissions=role_perms,
            color=role_color,
            reason="No existing mute role provided",
        )

        guild_channels: list[
            discord.abc.GuildChannel
        ] = await guild.fetch_channels()

        # Set permissions for channels
        for channel in guild_channels:
            await channel.set_permissions(mute_role, send_messages=False)

        # Set permissions for categories
        for category in guild.categories:
            await category.set_permissions(mute_role, send_messages=False)

        Data.c.execute(
            "UPDATE guilds SET mute_role = :mute_role_id WHERE id = :guild_id",
            {"mute_role_id": mute_role.id, "guild_id": guild.id},
        )
        Data.conn.commit()

        return mute_role

    async def get_guild_mute_role(self, guild: discord.Guild):
        Data.check_guild_entry(guild)

        Data.c.execute(
            "SELECT mute_role FROM guilds WHERE id = :guild_id",
            {"guild_id": guild.id},
        )
        mute_role_id = Data.c.fetchone()[0]

        if mute_role_id is None:  # Create mute role if none is provided
            mute_role = await self.create_mute_role(guild)

        else:  # Get mute role if one was provided
            mute_role = guild.get_role(mute_role_id)

            # Check if the role provided still exists
            if mute_role is None:
                mute_role = await self.create_mute_role(guild)

        return mute_role

    @commands.command(
        name="warn",
        help="Warn a member for doing something they weren't supposed to",
    )
    @commands.has_guild_permissions(administrator=True)
    async def warn(
        self, ctx: commands.Context, member: discord.Member, *, reason: str
    ):
        if ctx.author.top_role <= member.top_role:
            await ctx.send(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        new_infraction = models.Infraction(
            id=uuid4().hex,
            guild_id=ctx.guild.id,
            user_id=member.id,
            moderator_id=ctx.author.id,
            reason=reason,
        )

        async with db.async_session() as session:
            session.add(new_infraction)
            await session.commit()

        await ctx.send(f"**{member}** has been warned because: *{reason}*")

    @commands.command(
        name="infractions",
        aliases=["inf"],
        help="See all the times a person has been warned",
    )
    @commands.has_guild_permissions(administrator=True)
    async def infractions(
        self, ctx: commands.Context, member: discord.Member = None
    ):
        async with db.async_session() as session:
            q = select(models.Infraction).where(
                models.Infraction.guild_id == ctx.guild.id
            )

            if member:
                q = q.where(models.Infraction.user_id == member.id)

            result = await session.execute(q)
            infracs: list[models.Infraction] = result.scalars().all()

        if member:
            embed_title = f"Infractions by {member} in {ctx.guild.name}"
        else:
            embed_title = f"All Infractions in {ctx.guild.name}"

        infractions_embed = discord.Embed(title=embed_title, color=self.theme_color)

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

        await ctx.send(embed=infractions_embed)

    @commands.command(
        name="clearinfractions",
        aliases=["clearinf"],
        help="Clear somebody's infractions in the current server",
    )
    @commands.has_guild_permissions(administrator=True)
    async def clear_infractions(
        self, ctx: commands.Context, member: discord.Member | int | None = None
    ):
        if isinstance(member, int):
            member: discord.Member = ctx.guild.get_member(member)

        if member is None:
            async with db.async_session() as session:
                q = select(models.Infraction).where(
                    models.Infraction.guild_id == ctx.guild.id
                )
                result = await session.execute(q)
                tasks = [session.delete(inf) for inf in result.scalars().all()]
                await asyncio.gather(*tasks)
                await session.commit()

            await ctx.send("Cleared all infractions in this server...")

        else:
            if ctx.guild.owner_id != ctx.author.id and ctx.author.top_role <= member.top_role:
                await ctx.send(
                    "You cannot use the command on this person because their top role is higher than or equal to yours."
                )
                return

            async with db.async_session() as session:
                q = (
                    select(models.Infraction)
                    .where(models.Infraction.guild_id == ctx.guild.id)
                    .where(models.Infraction.user_id == member.id)
                )
                result = await session.execute(q)
                tasks = [session.delete(inf) for inf in result.scalars().all()]
                await asyncio.gather(*tasks)
                await session.commit()

            await ctx.send(
                f"Cleared all infractions by **{member}** in this server..."
            )

    @commands.command(
        name="mute",
        help="Prevent someone from sending messages.\nFor temp mute, specify a time in days, hours, minutes, or seconds. Example: mute @member 5h",
    )
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        unmute_time: str = None,
    ):
        if member.id == ctx.bot.user.id:
            await ctx.send(f"**{member}** can no longer- Wait a minute...")
            return

        if (
            ctx.guild.owner_id != ctx.author.id
            and ctx.author.top_role <= member.top_role
        ):
            await ctx.send(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.add_roles(mute_role)

        if unmute_time:
            now_epoch = time.time()
            unmute_timedelta = str_time_to_timedelta(unmute_time)
            humanized_time_str = (
                f"<t:{int(now_epoch + unmute_timedelta.total_seconds())}:R>"
            )

            mute_msg: discord.Message = await ctx.send(
                f"**{member}** will be unmuted {humanized_time_str}"
            )
            await asyncio.sleep(unmute_timedelta.total_seconds())

            unmute_str = f"**{member}** was unmuted {humanized_time_str}"
            await mute_msg.edit(content=unmute_str)

            if mute_role in member.roles:
                await member.remove_roles(mute_role)
                await ctx.send(unmute_str)

        else:
            await ctx.send(f"**{member}** can no longer speak")

    @commands.command(
        name="unmute", help="Return the ability to talk to someone"
    )
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        if ctx.author.top_role <= member.top_role:
            await ctx.send(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.remove_roles(mute_role)
        await ctx.send(f"**{member}** can speak now")

    @commands.command(
        name="ban", help="Permanently remove a person from the server"
    )
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self, ctx: commands.Context, member: discord.Member, *, reason=None
    ):
        if ctx.author.top_role <= member.top_role:
            await ctx.send(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        if not member.bot:
            await member.send(
                f"You have been banned from **{ctx.guild.name}**"
            )
        await ctx.guild.ban(member, reason=reason, delete_message_days=0)
        await ctx.send(f"**{member}** has been banned from this server")

    @commands.command(name="unban", help="Unban a person from the server")
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, username: str):
        if username[-5] != "#":
            await ctx.send(
                "Please give a username in this format: *username#0000*"
            )
            return

        name = username[:-5]  # first character to 6th last character
        discriminator = username[-4:]  # last 4 characters
        guild_bans = await ctx.guild.bans()
        user_to_unban = None

        for ban_entry in guild_bans:
            banned_user: discord.User = ban_entry.user

            if (
                banned_user.name == name
                and banned_user.discriminator == discriminator
            ):
                user_to_unban = banned_user
                break

        if user_to_unban:
            await ctx.guild.unban(user_to_unban)
            await ctx.send(
                f"**{user_to_unban}** has been unbanned from this server"
            )
            await user_to_unban.send(
                f"You have been unbanned from **{ctx.guild.name}**"
            )
        else:
            await ctx.send("This person was not found to be banned")

    @commands.command(name="kick", help="Remove a person from the server")
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self, ctx: commands.Context, member: discord.Member, *, reason=None
    ):
        if ctx.author.top_role <= member.top_role:
            await ctx.send(
                "You cannot use the command on this person because their top role is higher than or equal to yours."
            )
            return

        if not member.bot:
            await member.send(
                f"You have been kicked from **{ctx.guild.name}**"
            )
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f"**{member}** has been kicked from this server")

    @commands.command(
        name="lockchannel",
        aliases=["lock"],
        help="Prevent non-admins from sending messages in this channel",
    )
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def lock_channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f":lock: {ch.mention} has been locked")

    @commands.command(
        name="unlockchannel",
        aliases=["unlock"],
        help="Reverse the effects of lockchannel command",
    )
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def unlock_channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        await ch.edit(sync_permissions=True)
        await ctx.send(f":unlock: {ch.mention} has been unlocked")

    @commands.command(
        name="slowmode", help="Add slowmode delay on the current channel"
    )
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, time: int):
        await ctx.channel.edit(slowmode_delay=time)

        if time > 0:
            await ctx.send(f"Added a slowmode delay of **{time} seconds**")
        else:
            await ctx.send("Slowmode has been disabled")

    @commands.command(
        name="clear", aliases=["purge"], help="Clear messages in a channel"
    )
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(
        self,
        ctx: commands.Context,
        message_count: int,
        channel: discord.TextChannel = None,
    ):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        async with db.async_session() as session:
            guild_data: models.Guild | None = await session.get(models.Guild, ctx.guild.id)

            if guild_data:
                limit = guild_data.clear_cap
            else:
                new_guild_data = models.Guild(id=ctx.guild.id)
                session.add(new_guild_data)
                await session.commit()

                limit = new_guild_data.clear_cap

        if limit and message_count > limit:
            exceeds_by = message_count - limit
            await ctx.send(
                f"Message clear count exceeds this server's limit by {exceeds_by}. The limit is {limit}."
            )
            return

        await ch.purge(limit=message_count + 1)
        await ctx.send(f"Cleared {message_count} message(s)", delete_after=3)

    @commands.command(
        name="nuke", help="Clear all messages at once in a channel"
    )
    @commands.bot_has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(administrator=True)
    async def nuke(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        def confirmation_check(message: discord.Message):
            return (
                message.author == ctx.author
                and message.channel.id == ctx.channel.id
            )

        # Confirmation
        await ctx.send(
            f"Are you sure you want to nuke `{ch}`? This action cannot be undone."
        )

        # Receive confirmation response
        try:
            confirmation_msg: discord.Message = await self.bot.wait_for(
                "message", check=confirmation_check, timeout=30
            )

            if confirmation_msg.content.lower() != "yes":
                await ctx.send("Aborting channel nuke!")
                return

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        reason = f"Channel Nuke by {ctx.author}"
        ch_pos = ch.position
        new_ch = await ch.clone(reason=reason)
        await ch.delete(reason=reason)
        await new_ch.edit(reason=reason, position=ch_pos)

        nuke_embed = discord.Embed(title=reason, color=self.theme_color)
        nuke_embed.set_image(url=random.choice(self.nuke_gifs))

        await new_ch.send(embed=nuke_embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
