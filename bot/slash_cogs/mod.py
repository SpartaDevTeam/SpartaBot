import asyncio
import json
import random
import time
import discord
from discord.errors import HTTPException
from discord.ext import commands

from bot import TESTING_GUILDS
from bot.data import Data
from bot.utils import str_time_to_timedelta
from bot.views.confirm import ConfirmView


class SlashModeration(commands.Cog):
    """
    Commands to uphold the peace and integrity of the server
    """

    def __init__(self):
        self.theme_color = discord.Color.purple()

    async def create_mute_role(
        self, ctx: discord.ApplicationContext
    ) -> discord.Role:
        print(f"Creating new mute role for server {ctx.guild.name}")
        await ctx.respond(
            "Setting up a new Muted role. This can take a second."
        )

        role_perms = discord.Permissions(send_messages=False)
        role_color = discord.Color.dark_gray()
        mute_role = await ctx.guild.create_role(
            name="Muted",
            permissions=role_perms,
            color=role_color,
            reason="No existing mute role provided",
        )

        guild_channels: list[
            discord.abc.GuildChannel
        ] = await ctx.guild.fetch_channels()

        # Set permissions for channels
        for channel in guild_channels:
            await channel.set_permissions(mute_role, send_messages=False)

        # Set permissions for categories
        for category in ctx.guild.categories:
            await category.set_permissions(mute_role, send_messages=False)

        Data.c.execute(
            "UPDATE guilds SET mute_role = :mute_role_id WHERE id = :guild_id",
            {"mute_role_id": mute_role.id, "guild_id": ctx.guild.id},
        )
        Data.conn.commit()

        return mute_role

    async def get_guild_mute_role(
        self, ctx: discord.ApplicationContext
    ) -> discord.Role:
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT mute_role FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild_id},
        )
        mute_role_id = Data.c.fetchone()[0]

        if mute_role_id is None:
            # Create mute role if none is provided
            with ctx.typing() as _:
                mute_role = await self.create_mute_role(ctx)

        else:
            # Get mute role if one was provided
            mute_role = ctx.guild.get_role(mute_role_id)

            # Check if the provided role still exists
            if mute_role is None:
                with ctx.typing() as _:
                    mute_role = await self.create_mute_role(ctx)

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

        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT infractions FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        guild_infractions: list = json.loads(Data.c.fetchone()[0])

        new_infraction = {"member": member.id, "reason": reason}
        guild_infractions.append(new_infraction)

        Data.c.execute(
            "UPDATE guilds SET infractions = :new_infractions WHERE id = :guild_id",
            {
                "new_infractions": json.dumps(guild_infractions),
                "guild_id": ctx.guild.id,
            },
        )
        Data.conn.commit()
        await ctx.respond(f"**{member}** has been warned because: *{reason}*")

    @commands.slash_command(guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def infractions(
        self, ctx: discord.ApplicationContext, member: discord.Member = None
    ):
        """
        See all the times a person has been warned
        """

        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "SELECT infractions FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )

        if member is None:
            infracs = json.loads(Data.c.fetchone()[0])
            embed_title = f"All Infractions in {ctx.guild.name}"
        else:
            infracs = [
                infrac
                for infrac in json.loads(Data.c.fetchone()[0])
                if infrac["member"] == member.id
            ]
            embed_title = f"Infractions by {member} in {ctx.guild.name}"

        infractions_embed = discord.Embed(
            title=embed_title, color=self.theme_color
        )

        if infracs:
            for infrac in infracs:
                if member:
                    guild_member = member
                else:
                    guild_member = await ctx.bot.fetch_user(infrac["member"])
                    if not guild_member:
                        guild_member = f"User ID: {infrac['member']}"

                reason = infrac["reason"]
                infractions_embed.add_field(
                    name=str(guild_member),
                    value=f"Reason: *{reason}*",
                    inline=False,
                )
        elif member:
            infractions_embed.description = (
                f"There are no infractions for {member}"
            )
        else:
            infractions_embed.description = "There are no infractions"

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

        if isinstance(member, int):
            member = ctx.guild.get_member(member)

        Data.check_guild_entry(ctx.guild)

        if member is None:
            Data.c.execute(
                "UPDATE guilds SET infractions = '[]' WHERE id = :guild_id",
                {"guild_id": ctx.guild.id},
            )
            Data.conn.commit()

            # TODO: ask for confirmation

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

            Data.c.execute(
                "SELECT infractions FROM guilds WHERE id = :guild_id",
                {"guild_id": ctx.guild.id},
            )
            user_infractions = json.loads(Data.c.fetchone()[0])
            new_infractions = [
                inf for inf in user_infractions if inf["member"] != member.id
            ]
            Data.c.execute(
                "UPDATE guilds SET infractions = :new_infractions WHERE id = :guild_id",
                {
                    "new_infractions": json.dumps(new_infractions),
                    "guild_id": ctx.guild.id,
                },
            )
            Data.conn.commit()

            await ctx.respond(
                f"Cleared all infractions by **{member}** in this server..."
            )

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

        mute_role = await self.get_guild_mute_role(ctx)
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

        # Fetch clear cap
        Data.c.execute(
            "SELECT clear_cap FROM guilds WHERE id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        limit = Data.c.fetchone()[0]

        if limit and amount > limit:
            exceeds_by = amount - limit
            await ctx.respond(
                f"Clear amount exceeds this server's limit by {exceeds_by}",
                ephemeral=True,
            )
            return

        await ctx.channel.purge(limit=amount + 1)
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
        confirm_view = ConfirmView()
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

                nuke_embed = discord.Embed(
                    title=reason, color=self.theme_color
                )
                nuke_embed.set_image(url=random.choice(nuke_gifs))

                await new_ch.send(embed=nuke_embed)

            except HTTPException as e:
                await new_ch.delete()
                await ctx.send(f"Unable to nuke {channel.mention}: {e.text}")


def setup(bot):
    bot.add_cog(SlashModeration())
