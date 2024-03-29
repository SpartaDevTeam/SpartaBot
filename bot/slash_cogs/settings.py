import aiohttp
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME, db
from bot.db import models


class SlashSettings(commands.Cog):
    """
    Commands to change Sparta settings for the current server
    """

    @commands.slash_command(name="muterole", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(manage_roles=True)
    async def mute_role(
        self, ctx: discord.ApplicationContext, role: discord.Role
    ):
        """
        Set a role to give to people when you mute them
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            if guild:
                guild.mute_role = role.id
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, mute_role=role.id
                )
                session.add(new_guild_data)

            await session.commit()

        await ctx.respond(
            f"The mute role has been set to {role.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.slash_command(name="welcomemessage", guilds_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def welcome_message(
        self, ctx: discord.ApplicationContext, message: str = None
    ):
        """
        Change the welcome message of your server. Variables you can use: [mention], [member], [server]
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            if guild:
                guild.welcome_message = message
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, welcome_message=message
                )
                session.add(new_guild_data)

            await session.commit()

        if message:
            await ctx.respond(
                f"This server's welcome message has been set to:\n{message}"
            )
        else:
            await ctx.respond(
                "This server's welcome message has been reset to default"
            )

    @commands.slash_command(name="leavemessage", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def leave_message(
        self, ctx: discord.ApplicationContext, message: str = None
    ):
        """
        Change the leave message of your server. Variables you can use: [member], [server]
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            if guild:
                guild.leave_message = message
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, leave_message=message
                )
                session.add(new_guild_data)

            await session.commit()

        if message:
            await ctx.respond(
                f"This server's leave message has been set to:\n{message}"
            )
        else:
            await ctx.respond(
                "This server's leave message has been reset to default"
            )

    @commands.slash_command(name="welcomechannel", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def welcome_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = None,
    ):
        """
        Change the channel where welcome messages are sent (don't pass a channel to disable welcome message)
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            ch = str(channel.id) if channel else "disabled"

            if guild:
                guild.welcome_channel = ch
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, welcome_channel=ch
                )
                session.add(new_guild_data)

            await session.commit()

        if channel:
            await ctx.respond(
                f"The server's welcome channel has been set to {channel.mention}"
            )
        else:
            await ctx.respond("The server's welcome message has been disabled")

    @commands.slash_command(name="leavechannel", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def leave_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel = None,
    ):
        """
        Change the channel where leave messages are sent (don't pass a channel to disable leave message)
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            ch = str(channel.id) if channel else "disabled"

            if guild:
                guild.leave_channel = ch
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, leave_channel=ch
                )
                session.add(new_guild_data)

            await session.commit()

        if channel:
            await ctx.respond(
                f"The server's leave channel has been set to {channel.mention}"
            )
        else:
            await ctx.respond("The server's leave message has been disabled")

    @commands.slash_command(name="autorole", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def auto_role(
        self, ctx: discord.ApplicationContext, role: discord.Role = None
    ):
        """
        Set a role to give to new members who join your server
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            role_id = role.id if role else None

            if guild:
                guild.auto_role = role_id
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild_id, auto_role=role_id
                )
                session.add(new_guild_data)

            await session.commit()

        if role:
            await ctx.respond(
                f"Auto role has been set to {role.mention}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await ctx.respond("Auto role has been removed")

    @commands.slash_command(name="serverinfo", guild_ids=TESTING_GUILDS)
    async def server_info(self, ctx: discord.ApplicationContext):
        """
        Get general information about the server
        """

        human_count = len(
            [member for member in ctx.guild.members if not member.bot]
        )
        bot_count = ctx.guild.member_count - human_count

        si_embed = discord.Embed(
            title=f"{ctx.guild.name} Information", color=THEME
        )
        if icon := ctx.guild.icon:
            si_embed.set_thumbnail(url=icon.url)

        si_embed.add_field(
            name="Human Members", value=str(human_count), inline=False
        )
        si_embed.add_field(
            name="Bot Members", value=str(bot_count), inline=False
        )
        si_embed.add_field(
            name="Total Members",
            value=str(ctx.guild.member_count),
            inline=False,
        )
        si_embed.add_field(
            name="Role Count", value=str(len(ctx.guild.roles)), inline=False
        )
        si_embed.add_field(
            name="Server Owner", value=str(ctx.guild.owner), inline=False
        )
        si_embed.add_field(name="Server ID", value=ctx.guild.id, inline=False)
        si_embed.add_field(
            name="Server Age",
            value=f"Created on <t:{int(ctx.guild.created_at.timestamp())}>",
            inline=False,
        )

        await ctx.respond(embed=si_embed)

    @commands.slash_command(name="memberinfo", guild_ids=TESTING_GUILDS)
    async def member_info(
        self, ctx: discord.ApplicationContext, member: discord.Member = None
    ):
        """
        Get general information about a member
        """

        if not member:
            member = ctx.author

        mi_embed = discord.Embed(title=f"{member} Information", color=THEME)
        if avatar := member.avatar:
            mi_embed.set_thumbnail(url=avatar.url)

        mi_embed.add_field(name="Member ID", value=member.id, inline=False)
        mi_embed.add_field(
            name="Joined Discord",
            value=f"<t:{int(member.created_at.timestamp())}>",
            inline=False,
        )
        mi_embed.add_field(
            name="Joined Server",
            value=f"<t:{int(member.joined_at.timestamp())}>",
            inline=False,
        )
        mi_embed.add_field(
            name="Highest Role", value=member.top_role.mention, inline=False
        )
        mi_embed.add_field(
            name="Bot?", value="Yes" if member.bot else "No", inline=False
        )

        await ctx.respond(embed=mi_embed)

    @commands.slash_command(name="steal", guild_ids=TESTING_GUILDS)
    @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    async def steal_emoji(
        self,
        ctx: discord.ApplicationContext,
        emoji: str,
        new_name: str = None,
    ):
        """
        Steal another server's emoji
        """

        emoji = emoji.strip()

        if not emoji.startswith("<") and emoji.endswith(">"):
            await ctx.respond("Please provide a valid custom emoji")
            return

        emoji_split = emoji.strip("<>").split(":")
        emoji_id = emoji_split[-1]

        if not emoji_id.isnumeric():
            await ctx.respond("Unable to read the given custom emoji")
            return

        if emoji_split[0] == "a":
            url = (
                "https://cdn.discordapp.com/emojis/"
                + str(emoji_split[2])
                + ".gif?v=1"
            )
        else:
            url = (
                "https://cdn.discordapp.com/emojis/"
                + str(emoji_split[2])
                + ".png?v=1"
            )

        await ctx.defer()
        async with aiohttp.request("GET", url) as resp:
            image_data = await resp.read()

        if not new_name:
            new_name = emoji_split[1]

        try:
            await ctx.guild.create_custom_emoji(
                name=new_name,
                image=image_data,
                reason=f"Added by {ctx.author} using /steal command",
            )
            await ctx.respond(f"{emoji} has been added as `:{new_name}:`")

        except discord.HTTPException as e:
            await ctx.respond(
                f"An error occured while added the emoji: `{e.text}`"
            )

    @commands.slash_command(name="clearcap", guild_ids=TESTING_GUILDS)
    @commands.has_guild_permissions(administrator=True)
    async def clear_cap(
        self, ctx: discord.ApplicationContext, limit: int = None
    ):
        """
        Set the maximum number of messages that can be cleared using /clear
        """

        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild_id
            )

            if guild:
                guild.clear_cap = limit
            else:
                new_guild_data = models.Guild(id=ctx.guild_id, clear_cap=limit)
                session.add(new_guild_data)

            await session.commit()

        if limit:
            await ctx.respond(
                f"Clear command limit has been set to **{limit} messages** at a time."
            )
        else:
            await ctx.respond("Clear command limit has been removed.")


def setup(bot):
    bot.add_cog(SlashSettings())
