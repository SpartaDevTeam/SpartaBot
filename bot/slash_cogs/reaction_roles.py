from emoji import emojize
import discord
from discord.ext import commands

from bot import TESTING_GUILDS
from bot.data import Data
from bot.utils import dbl_vote_required


class SlashReactionRoles(commands.Cog):
    """
    Commands to setup reaction roles for members of your server to give
    themselves roles
    """

    # TODO: Enable when removing prefix commands
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
    #                 name=emojize(rr[2])
    #             )

    #         rr_role: discord.Role = guild.get_role(int(rr[3]))

    #         if (
    #             payload.channel_id == rr_channel_id
    #             and payload.message_id == rr_message_id
    #             and payload.emoji.name == rr_emoji.name
    #         ):
    #             await member.add_roles(rr_role, reason="Reaction Role")
    #             await member.send(
    #                 f"You have been given the **{rr_role}** role in **{guild}**"
    #             )

    # TODO: Enable when removing prefix commands
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
    #                 name=emojize(rr[2])
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
                emoji = int(emoji.strip("<>").split(":")[-1])
            except ValueError:
                await ctx.respond("Unable to read the given custom emoji")
                return

        try:
            message_id = int(message_id)
        except ValueError:
            await ctx.respond("Invalid message ID was provided")
            return

        await ctx.defer()
        Data.c.execute(
            "SELECT id FROM reaction_roles WHERE guild_id = :guild_id AND channel_id = :channel_id AND message_id = :message_id AND role_id = :role_id AND emoji = :emoji",
            {
                "guild_id": ctx.guild.id,
                "channel_id": channel.id,
                "message_id": message_id,
                "role_id": role.id,
                "emoji": emoji,
            },
        )
        rr_entry = Data.c.fetchone()

        if rr_entry:
            await ctx.respond(
                f"A reaction role with this configuration already exists with ID {rr_entry[0]}."
            )

        else:
            try:
                message = await channel.fetch_message(message_id)
                Data.create_new_reaction_role_entry(
                    ctx.guild, channel, message, emoji, role
                )

                await message.add_reaction(original_emoji)
                await ctx.respond(
                    f"Reaction Role for {role.mention} has been created with {original_emoji} at {channel.mention}",
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
    @dbl_vote_required()
    async def remove_reaction_role(self, ctx: discord.ApplicationContext):
        """
        Remove a reaction role
        """


def setup(bot):
    bot.add_cog(SlashReactionRoles())
