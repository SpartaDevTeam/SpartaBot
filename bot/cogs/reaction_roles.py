import asyncio
import discord
from discord.ext import commands

from bot.data import Data


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
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
        channel: discord.TextChannel = await self.bot.fetch_channel(
            payload.channel_id
        )
        message: discord.Message = await channel.fetch_message(
            payload.message_id
        )
        member: discord.Member = await guild.fetch_member(payload.user_id)

        Data.c.execute(
            "SELECT channel_id, message_id, emoji_id, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": guild.id},
        )
        react_roles = Data.c.fetchall()

        for rr in react_roles:
            rr_channel: discord.TextChannel = await self.bot.fetch_channel(
                rr[0]
            )
            rr_message: discord.Message = await rr_channel.fetch_message(rr[1])
            rr_emoji: discord.Emoji = await guild.fetch_emoji(rr[2])
            rr_role: discord.Role = guild.get_role(rr[3])

            if (
                channel == rr_channel
                and message == rr_message
                and payload.emoji == rr_emoji
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
        channel: discord.TextChannel = await self.bot.fetch_channel(
            payload.channel_id
        )
        message: discord.Message = await channel.fetch_message(
            payload.message_id
        )
        member: discord.Member = await guild.fetch_member(payload.user_id)

        Data.c.execute(
            "SELECT channel_id, message_id, emoji_id, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": guild.id},
        )
        react_roles = Data.c.fetchall()

        for rr in react_roles:
            rr_channel: discord.TextChannel = await self.bot.fetch_channel(
                rr[0]
            )
            rr_message: discord.Message = await rr_channel.fetch_message(rr[1])
            rr_emoji: discord.Emoji = await guild.fetch_emoji(rr[2])
            rr_role: discord.Role = guild.get_role(rr[3])

            if (
                channel == rr_channel
                and message == rr_message
                and payload.emoji == rr_emoji
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
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def add_reaction_role(self, ctx: commands.Context):
        # TODO: add extra type checks
        guild: discord.Guild = ctx.guild

        rr_channel = None
        while not rr_channel:
            channel_msg = await self.msg_prompt(
                ctx,
                "Please mention the channel where you want to setup a reaction role",
            )
            channel_mentions = channel_msg.channel_mentions

            if channel_mentions:
                rr_channel = channel_mentions[0]

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

        rr_emoji = None
        while not rr_emoji:
            emoji_react = await self.react_prompt(
                ctx,
                "Please react to this message with the emoji you want to use for the reaction role",
            )
            rr_emoji = emoji_react.emoji

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

        await rr_message.add_reaction(rr_emoji)
        Data.create_new_reaction_role_entry(
            guild, rr_channel, rr_message, rr_emoji, rr_role
        )
        await ctx.send(
            f"Reaction Role for {rr_role.mention} has been created with {rr_emoji} at {rr_channel.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
