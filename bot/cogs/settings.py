from typing import Union
import aiohttp
import discord
from discord.ext import commands
from discord import utils

from bot import MyBot, db
from bot.db import models


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.description = (
            "Commands to change Sparta settings for the current server"
        )
        self.theme_color = discord.Color.purple()

    @commands.command(
        name="setmuterole",
        aliases=["setmute", "smr"],
        help="Set a role to give to people when you mute them",
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            if guild:
                guild.mute_role = role.id
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, mute_role=role.id
                )
                session.add(new_guild_data)

            await session.commit()

        await ctx.send(f"The mute role has been set to **{role}**")

    @commands.command(
        name="setwelcomemessage",
        aliases=["wmsg"],
        brief="Change the welcome message of the current server",
        help="Change the welcome message of the current server. Variables you can use: [mention], [member], [server]",
    )
    @commands.has_guild_permissions(administrator=True)
    async def set_welcome_message(
        self, ctx: commands.Context, *, message: str = None
    ):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            if guild:
                guild.welcome_message = message
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, welcome_message=message
                )
                session.add(new_guild_data)

            await session.commit()

        if message:
            await ctx.send(
                f"This server's welcome message has been set to:\n{message}"
            )
        else:
            await ctx.send(
                "This server's welcome message has been reset to default"
            )

    @commands.command(
        name="setleavemessage",
        aliases=["lmsg"],
        brief="Change the leave message of the current server",
        help="Change the leave message of the current server. Variables you can use: [member], [server]",
    )
    @commands.has_guild_permissions(administrator=True)
    async def set_leave_message(
        self, ctx: commands.Context, *, message: str = None
    ):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            if guild:
                guild.leave_message = message
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, leave_message=message
                )
                session.add(new_guild_data)

            await session.commit()

        if message:
            await ctx.send(
                f"This server's leave message has been set to:\n{message}"
            )
        else:
            await ctx.send(
                "This server's leave message has been reset to default"
            )

    @commands.command(
        name="setwelcomechannel",
        aliases=["wchannel"],
        help="Change the channel where welcome messages are sent. Leave the channel field empty to disable welcome messages.",
    )
    @commands.has_guild_permissions(administrator=True)
    async def set_welcome_channel(
        self, ctx: commands.Context, *, channel: discord.TextChannel = None
    ):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            ch = str(channel.id) if channel else "disabled"

            if guild:
                guild.welcome_channel = ch
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, welcome_channel=ch
                )
                session.add(new_guild_data)

            await session.commit()

        if channel:
            await ctx.send(
                f"The server's welcome channel has been set to {channel.mention}"
            )
        else:
            await ctx.send("The server's welcome message has been disabled")

    @commands.command(
        name="setleavechannel",
        aliases=["lchannel"],
        help="Change the channel where leave messages are sent. Leave the channel field empty to disable leave messages.",
    )
    @commands.has_guild_permissions(administrator=True)
    async def set_leave_channel(
        self, ctx: commands.Context, *, channel: discord.TextChannel = None
    ):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            ch = str(channel.id) if channel else "disabled"

            if guild:
                guild.leave_channel = ch
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, leave_channel=ch
                )
                session.add(new_guild_data)

            await session.commit()

        if channel:
            await ctx.send(
                f"The server's leave channel has been set to {channel.mention}"
            )
        else:
            await ctx.send("The server's leave message has been disabled")

    @commands.command(
        name="setautorole",
        aliases=["setauto", "autorole", "arole"],
        help="Set a role to give to new members of the server",
    )
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(administrator=True)
    async def set_auto_role(
        self, ctx: commands.Context, *, role: discord.Role
    ):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            role_id = role.id if role else None

            if guild:
                guild.auto_role = role_id
            else:
                new_guild_data = models.Guild(
                    id=ctx.guild.id, auto_role=role_id
                )
                session.add(new_guild_data)

            await session.commit()

        await ctx.send(
            f"The auto role has been set to **{role.mention}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(
        name="serverinfo",
        aliases=["si"],
        help="Get general information about the server",
    )
    async def server_info(self, ctx):
        guild: discord.Guild = ctx.guild
        human_count = len(
            [member for member in guild.members if not member.bot]
        )
        bot_count = guild.member_count - human_count

        si_embed = discord.Embed(
            title=f"{guild.name} Information", color=self.theme_color
        )
        si_embed.set_thumbnail(url=guild.icon.url)

        si_embed.add_field(
            name="Human Members", value=str(human_count), inline=False
        )
        si_embed.add_field(
            name="Bot Members", value=str(bot_count), inline=False
        )
        si_embed.add_field(
            name="Total Members", value=str(guild.member_count), inline=False
        )
        si_embed.add_field(
            name="Role Count", value=str(len(guild.roles)), inline=False
        )
        si_embed.add_field(
            name="Server Owner", value=str(guild.owner), inline=False
        )
        si_embed.add_field(name="Server ID", value=guild.id, inline=False)
        si_embed.add_field(
            name="Server Region", value=str(guild.region).title(), inline=False
        )

        await ctx.send(embed=si_embed)

    @commands.command(
        name="memberinfo",
        aliases=["mi", "ui"],
        help="Get general information about a member",
    )
    async def member_info(
        self, ctx: commands.Context, member: discord.Member = None
    ):
        if member:
            m = member
        else:
            m = ctx.author

        time_format = "%-d %b %Y %-I:%M %p"
        created_at = m.created_at.strftime(time_format)
        joined_at = m.joined_at.strftime(time_format)

        mi_embed = discord.Embed(
            title=f"{m} Information", color=self.theme_color
        )
        mi_embed.set_thumbnail(url=m.avatar.url)

        mi_embed.add_field(name="Member ID", value=m.id, inline=False)
        mi_embed.add_field(
            name="Joined Discord", value=created_at, inline=False
        )
        mi_embed.add_field(name="Joined Server", value=joined_at, inline=False)
        mi_embed.add_field(
            name="Highest Role", value=m.top_role.mention, inline=False
        )
        mi_embed.add_field(
            name="Bot?", value="Yes" if m.bot else "No", inline=False
        )

        await ctx.send(embed=mi_embed)

    @commands.command(
        name="prefix",
        help="Change the command prefix for Sparta in this server",
    )
    @commands.has_guild_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, pref: str = "s!"):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            if guild:
                guild.prefix = pref
            else:
                new_guild_data = models.Guild(id=ctx.guild.id, prefix=pref)
                session.add(new_guild_data)

            await session.commit()

        await ctx.send(f"The prefix has been changed to **{pref}**")

    @commands.command(
        name="steal",
        help="Add an emoji from another server to yours",
    )
    @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    async def steal(
        self,
        ctx: commands.Context,
        name: str,
        emoji: Union[discord.Emoji, str],
    ):
        emoji = str(emoji).replace("<", "")
        emoji = str(emoji).replace(">", "")
        emoji = emoji.split(":")

        if emoji[0] == "a":
            url = (
                "https://cdn.discordapp.com/emojis/"
                + str(emoji[2])
                + ".gif?v=1"
            )
        else:
            url = (
                "https://cdn.discordapp.com/emojis/"
                + str(emoji[2])
                + ".png?v=1"
            )

        try:
            async with aiohttp.request("GET", url) as resp:
                image_data = await resp.read()

            if name:
                await ctx.guild.create_custom_emoji(
                    name=name, image=image_data
                )
                emote = utils.get(ctx.guild.emojis, name=name)
                if emote.animated:
                    add = "a"
                else:
                    add = ""
                emote_display = f"<{add}:{emote.name}:{emote.id}>"
                await ctx.send(f'{emote_display} added with the name "{name}"')
            else:
                await ctx.guild.create_custom_emoji(
                    name=emoji[1], image=image_data
                )
                emote = utils.get(ctx.guild.emojis, name=emoji[1])
                if emote.animated:
                    add = "a"
                else:
                    add = ""
                emote_display = f"<{add}:{emote.name}:{emote.id}>"
                await ctx.send(f'{emote_display} has been added as "{name}"')

        except discord.HTTPException:
            await ctx.send("Failed to add emoji.")

    @commands.command(name="setclearcap", aliases=["clearcap", "cc"])
    @commands.has_guild_permissions(administrator=True)
    async def set_clear_cap(self, ctx: commands.Context, limit: int = None):
        async with db.async_session() as session:
            guild: models.Guild | None = await session.get(
                models.Guild, ctx.guild.id
            )

            if guild:
                guild.clear_cap = limit
            else:
                new_guild_data = models.Guild(id=ctx.guild.id, clear_cap=limit)
                session.add(new_guild_data)

            await session.commit()

        if limit:
            await ctx.send(
                f"Clear command limit has been set to **{limit} messages** at a time."
            )
        else:
            await ctx.send("Clear command limit has been removed.")


def setup(bot):
    bot.add_cog(Settings(bot))
