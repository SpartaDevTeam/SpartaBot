import discord
from discord.ext import commands

from bot.data import Data


class WelcomeLeave(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.theme_color = discord.Color.purple()
        self.default_welcome_msg = (
            lambda guild: f"Hello [mention], welcome to {guild.name}!"
        )
        self.default_leave_msg = (
            lambda guild: f"Goodbye [member], thanks for staying at {guild.name}!"
        )

    async def find_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel or None:
        channels: list[discord.TextChannel] = await guild.fetch_channels()

        for channel in channels:
            if "welcome" in channel.name:
                return channel

        return None

    async def find_leave_channel(self, guild: discord.Guild) -> discord.TextChannel or None:
        channels: list[discord.TextChannel] = await guild.fetch_channels()

        for channel in channels:
            if "bye" in channel.name:
                return channel

        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild: discord.Guild = member.guild
        Data.check_guild_entry(guild)

        Data.c.execute(
            "SELECT welcome_message, welcome_channel, auto_role FROM guilds WHERE id = :guild_id",
            {"guild_id": guild.id},
        )
        data = Data.c.fetchone()
        welcome_message = data[0]

        welcome_channel_id = data[1]

        if welcome_channel_id == "disabled":
            return

        welcome_channel = guild.get_channel(int(welcome_channel_id))
        if data[2]:
            auto_role = guild.get_role(int(data[2]))
        else:
            auto_role = None

        if not welcome_message:
            welcome_message = self.default_welcome_msg(guild)

        if not welcome_channel:
            welcome_channel = await self.find_welcome_channel(guild)

            # Exit the function if no welcome channel is provided or automatically found
            if not welcome_channel:
                return

        # Replace placeholders with actual information
        welcome_message = welcome_message.replace("[mention]", member.mention)
        welcome_message = welcome_message.replace("[member]", str(member))

        await welcome_channel.send(welcome_message)

        # Give auto role to new member if they are not a bot
        if not member.bot and auto_role:
            await member.add_roles(auto_role)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild: discord.Guild = member.guild
        Data.check_guild_entry(guild)

        Data.c.execute(
            "SELECT leave_message, leave_channel FROM guilds WHERE id = :guild_id",
            {"guild_id": guild.id},
        )
        data = Data.c.fetchone()
        leave_message = data[0]
        leave_channel_id = data[1]

        if leave_channel_id == "disabled":
            return

        leave_channel = guild.get_channel(int(leave_channel_id))

        if not leave_message:
            leave_message = self.default_leave_msg(guild)

        if not leave_channel:
            leave_channel = await self.find_leave_channel(guild)

            # Exit the function if no leave channel is provided or automatically found
            if not leave_channel:
                return

        # Replace placeholders with actual information
        leave_message = leave_message.replace("[mention]", member.mention)
        leave_message = leave_message.replace("[member]", str(member))

        await leave_channel.send(leave_message)


def setup(bot):
    bot.add_cog(WelcomeLeave(bot))
