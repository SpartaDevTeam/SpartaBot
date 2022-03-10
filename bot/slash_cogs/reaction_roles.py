import asyncio
from emoji import emojize
import discord
from discord.ext import commands

from bot import TESTING_GUILDS, THEME
from bot.data import Data
from bot.utils import dbl_vote_required, async_mirror
from bot.views import PaginatedSelectView


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
                    name=emojize(rr[2])
                )

            rr_role: discord.Role = guild.get_role(int(rr[3]))

            if (
                payload.channel_id == rr_channel_id
                and payload.message_id == rr_message_id
                and payload.emoji.name == rr_emoji.name
            ):
                await member.add_roles(rr_role, reason="Reaction Role")
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

            if rr[2].isnumeric():
                rr_emoji: discord.Emoji = await guild.fetch_emoji(int(rr[2]))
            else:
                rr_emoji: discord.PartialEmoji = discord.PartialEmoji(
                    name=emojize(rr[2])
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

        if message_id.isnumeric():
            message_id = int(message_id)
        else:
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
                f"A reaction role with this configuration already exists with ID `{rr_entry[0]}`."
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
    async def remove_reaction_role(self, ctx: discord.ApplicationContext):
        """
        Remove a reaction role
        """

        await ctx.defer()

        Data.c.execute(
            "SELECT id, channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": ctx.guild_id},
        )
        reaction_roles = Data.c.fetchall()

        channel_tasks = [
            ctx.guild.fetch_channel(rr[1]) for rr in reaction_roles
        ]
        emoji_tasks = [
            ctx.guild.fetch_emoji(rr[3])
            if rr[3].isnumeric()
            else async_mirror(rr[3])
            for rr in reaction_roles
        ]
        total_tasks = []
        total_tasks.extend(channel_tasks)
        total_tasks.extend(emoji_tasks)

        rr_channels: list[discord.TextChannel] = []
        rr_emojis: list[discord.PartialEmoji] = []
        guild_roles: list[discord.Role] = await ctx.guild.fetch_roles()

        task_results = await asyncio.gather(*total_tasks)
        for result in task_results:
            if isinstance(result, discord.TextChannel):
                rr_channels.append(result)
            elif isinstance(result, discord.Emoji | str):
                rr_emojis.append(result)

        options = []
        values = []
        descriptions = []
        emojis = []

        for rr, channel, emoji in zip(reaction_roles, rr_channels, rr_emojis):
            role = discord.utils.get(guild_roles, id=rr[4])

            options.append(
                f"#{channel.name}, Role: {role.name}, Msg ID: {rr[2]}"
            )
            values.append(rr[0])
            descriptions.append(f"ID: {rr[0]}")
            emojis.append(emoji)

        select_view = PaginatedSelectView(
            ctx.author.id,
            options,
            values,
            descriptions,
            emojis,
            max_values=len(options),
        )
        msg = await ctx.respond(
            "Select the reaction roles to be removed", view=select_view
        )
        timed_out = await select_view.wait()

        if timed_out:
            await ctx.delete()
            return

        for rr_id in select_view.selected_values:
            Data.delete_reaction_role_entry(rr_id)

        await msg.edit(
            content=f"Deleted {len(select_view.selected_values)} reaction role(s)!",
            view=None,
        )

    @commands.slash_command(name="viewreactionroles", guild_ids=TESTING_GUILDS)
    async def view_reaction_roles(self, ctx: discord.ApplicationContext):
        """
        See the reaction roles setup in your server.
        """

        await ctx.defer()
        Data.c.execute(
            "SELECT id, channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = :guild_id",
            {"guild_id": ctx.guild_id},
        )
        if not (reaction_roles := Data.c.fetchall()):
            await ctx.respond(
                "There aren't any reaction roles setup in this server"
            )
            return

        guild_roles = await ctx.guild.fetch_roles()
        rr_embed = discord.Embed(
            title=f"{ctx.guild.name} Reaction Roles", color=THEME
        )

        for rr in reaction_roles:
            rr_id = rr[0]

            def delete_rr():
                Data.delete_reaction_role_entry(rr_id)

            try:
                rr_channel: discord.TextChannel = (
                    await ctx.guild.fetch_channel(rr[1])
                )
            except discord.NotFound:
                delete_rr()
                continue

            try:
                rr_message: discord.Message = await rr_channel.fetch_message(
                    rr[2]
                )
            except discord.NotFound:
                delete_rr()
                continue

            if rr[3].isnumeric():
                try:
                    rr_emoji: discord.Emoji = await ctx.guild.fetch_emoji(
                        rr[3]
                    )
                except discord.NotFound:
                    delete_rr()
                    continue
            else:
                rr_emoji = emojize(rr[3])

            if not (rr_role := discord.utils.get(guild_roles, id=rr[4])):
                delete_rr()
                continue

            str_list = [
                f"Emoji: {rr_emoji}",
                f"Role: {rr_role.mention}",
                f"Channel: {rr_channel.mention}",
                f"[Jump to Message]({rr_message.jump_url})",
            ]
            rr_embed.add_field(
                name=f"ID: {rr_id}", value="\n".join(str_list), inline=False
            )

        await ctx.respond(embed=rr_embed)


def setup(bot):
    bot.add_cog(SlashReactionRoles(bot))
