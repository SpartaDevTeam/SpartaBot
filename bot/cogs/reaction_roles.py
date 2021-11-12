import asyncio
import emoji
import discord
from discord.ext import commands

from bot import MyBot
from bot.data import Data
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ):
        guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
        member: discord.Member = await guild.fetch_member(payload.user_id)

        if member == self.bot.user:
            return

        Data.c.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": guild.id},
        )
        react_roles = Data.c.fetchall()

        for rr in react_roles:
            rr_channel_id = rr[0]
            rr_message_id = rr[1]

            try:
                rr_emoji: discord.Emoji = await guild.fetch_emoji(int(rr[2]))
            except ValueError:
                rr_emoji: discord.PartialEmoji = discord.PartialEmoji(
                    name=emoji.emojize(rr[2])
                )

            rr_role: discord.Role = guild.get_role(int(rr[3]))

            if (
                payload.channel_id == rr_channel_id
                and payload.message_id == rr_message_id
                and payload.emoji.name == rr_emoji.name
            ):
                await member.add_roles(rr_role, reason="Sparta Reaction Role")
                await member.send(
                    f"You have been given the **{rr_role}** role in **{guild}**"
                )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self, payload: discord.RawReactionActionEvent
    ):
        guild: discord.Guild = await self.bot.fetch_guild(payload.guild_id)
        member: discord.Member = await guild.fetch_member(payload.user_id)

        if member == self.bot.user:
            return

        Data.c.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": guild.id},
        )
        react_roles = Data.c.fetchall()

        for rr in react_roles:
            rr_channel_id = rr[0]
            rr_message_id = rr[1]

            try:
                rr_emoji: discord.Emoji = await guild.fetch_emoji(int(rr[2]))
            except ValueError:
                rr_emoji: discord.PartialEmoji = discord.PartialEmoji(
                    name=emoji.emojize(rr[2])
                )

            rr_role: discord.Role = guild.get_role(int(rr[3]))

            if (
                payload.channel_id == rr_channel_id
                and payload.message_id == rr_message_id
                and payload.emoji.name == rr_emoji.name
            ):
                await member.remove_roles(
                    rr_role, reason="Sparta Reaction Role"
                )
                await member.send(
                    f"Your **{rr_role}** role in **{guild}** has been removed"
                )

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
            em = emoji.demojize(rr_emoji)
        else:
            em = rr_emoji

        Data.c.execute(
            "SELECT emoji FROM reaction_roles WHERE guild_id = :guild_id AND channel_id = :channel_id AND message_id = :message_id AND role_id = :role_id",
            {
                "guild_id": guild.id,
                "channel_id": rr_channel.id,
                "message_id": rr_message.id,
                "role_id": rr_role.id,
            },
        )
        rr_entry = Data.c.fetchone()

        if rr_entry:
            try:
                em = await guild.fetch_emoji(int(rr_entry[0]))
            except ValueError:
                em = discord.PartialEmoji(name=emoji.emojize(rr_entry[0]))

            await ctx.send(
                f"A reaction role with this configuration already exists as {em}"
            )
        else:
            Data.create_new_reaction_role_entry(
                guild, rr_channel, rr_message, em, rr_role
            )
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
    async def remove_reaction_role(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild

        try:
            rr_channel = None
            while not rr_channel:
                channel_msg = await self.msg_prompt(
                    ctx,
                    "Please mention the channel where you want to remove a reaction role",
                )
                channel_mentions = channel_msg.channel_mentions

                if channel_mentions:
                    rr_channel = channel_mentions[0]

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        try:
            rr_message_id = None
            while not rr_message_id:
                message_msg = await self.msg_prompt(
                    ctx,
                    "Please send the ID of the message where you want to remove a reaction role",
                )
                try:
                    rr_message_id = int(message_msg.content)
                except ValueError:
                    continue

        except asyncio.TimeoutError:
            await ctx.send("No response received, aborting!")
            return

        try:
            rr_role = None
            while not rr_role:
                role_msg = await self.msg_prompt(
                    ctx,
                    "Please mention or send the ID of the role for the reaction role you want to remove",
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

        Data.c.execute(
            "SELECT emoji FROM reaction_roles WHERE guild_id = :guild_id AND channel_id = :channel_id AND message_id = :message_id AND role_id = :role_id",
            {
                "guild_id": guild.id,
                "channel_id": rr_channel.id,
                "message_id": rr_message_id,
                "role_id": rr_role.id,
            },
        )
        rr_entry = Data.c.fetchone()

        if rr_entry:
            Data.delete_reaction_role_entry(
                guild, rr_channel, rr_message_id, rr_role
            )

            try:
                rr_message = await rr_channel.fetch_message(rr_message_id)

                try:
                    em = await guild.fetch_emoji(int(rr_entry[0]))
                except ValueError:
                    em = discord.PartialEmoji(name=emoji.emojize(rr_entry[0]))

                await rr_message.clear_reaction(em)
            except discord.NotFound:
                pass

            await ctx.send("This reaction role has been removed")
        else:
            await ctx.send(
                "A reaction role with this configuration does not exist"
            )

    @commands.command(
        name="viewreactionroles",
        aliases=["vrr", "viewrr"],
        help="See the reaction roles setup in your server. If you've deleted any channel, emoji, or role that was used in an RR, this command will cleanup their entries from your server.",
    )
    async def view_reaction_roles(self, ctx: commands.Context):
        Data.c.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": ctx.guild.id},
        )
        reaction_roles = Data.c.fetchall()
        guild: discord.Guild = ctx.guild

        if reaction_roles:
            rr_embed = discord.Embed(
                title=f"{ctx.guild} Reaction Roles", color=self.theme_color
            )

            with ctx.typing():
                for rr in reaction_roles:
                    # Get channel
                    rr_channel: discord.TextChannel = guild.get_channel(rr[0])
                    if not rr_channel:
                        Data.delete_reaction_role_entry(
                            guild.id, rr[0], rr[1], rr[3]
                        )
                        continue

                    rr_msg_id = rr[1]

                    # Get emoji
                    try:
                        rr_emoji: discord.Emoji = await guild.fetch_emoji(
                            int(rr[2])
                        )
                    except ValueError:
                        rr_emoji: str = emoji.emojize(rr[2])

                    except discord.NotFound:
                        Data.delete_reaction_role_entry(
                            guild.id, rr[0], rr[1], rr[3]
                        )
                        continue

                    # Get role
                    rr_role: discord.Role = guild.get_role(rr[3])
                    if not rr_role:
                        Data.delete_reaction_role_entry(
                            guild.id, rr[0], rr[1], rr[3]
                        )
                        continue

                    rr_embed.add_field(
                        name=rr_emoji,
                        value=f"Channel: {rr_channel.mention}\nMessage ID: {rr_msg_id}\nRole: {rr_role.mention}",
                        inline=False,
                    )

            await ctx.send(embed=rr_embed)

        else:
            await ctx.send(
                "You don't have any reaction roles setup in this server"
            )


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
