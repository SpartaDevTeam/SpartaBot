import discord
from discord.ext import commands
from bot.data.data import Data


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands to change Sparta settings for the current server"
        self.theme_color = discord.Color.purple()

    @commands.command(name="setmuterole", aliases=["setmute", "smr"], help="Set a role to give to people when you mute them")
    @commands.has_guild_permissions(manage_roles=True)
    async def set_mute_role(self, ctx, role: discord.Role):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET mute_role = :mute_role_id WHERE id = :guild_id",
            {
                "mute_role_id": role.id,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        await ctx.send(f"The mute role has been set to **{role}**")

    @commands.command(name="setwelcomemessage", aliases=["wmsg"], help="Change the welcome message of the current server")
    @commands.has_guild_permissions(administrator=True)
    async def set_welcome_message(self, ctx, *, message: str = None):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET welcome_message = :new_message WHERE id = :guild_id",
            {
                "new_message": message,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        if message:
            await ctx.send(f"This server's welcome message has been set to:\n{message}")
        else:
            await ctx.send("This server's welcome message has been reset to default")

    @commands.command(name="setleavemessage", aliases=["lmsg"], help="Change the leave message of the current server")
    @commands.has_guild_permissions(administrator=True)
    async def set_leave_message(self, ctx, *, message: str = None):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET leave_message = :new_message WHERE id = :guild_id",
            {
                "new_message": message,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        if message:
            await ctx.send(f"This server's leave message has been set to:\n{message}")
        else:
            await ctx.send("This server's leave message has been reset to default")

    @commands.command(name="setwelcomechannel", aliases=["wchannel"], help="Change the channel where welcome messages are sent")
    @commands.has_guild_permissions(administrator=True)
    async def set_welcome_channel(self, ctx, *, channel: discord.TextChannel):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET welcome_channel = :channel_id WHERE id = :guild_id",
            {
                "channel_id": channel.id,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        await ctx.send(f"The server's welcome channel has been set to {channel.mention}")

    @commands.command(name="setleavechannel", aliases=["lchannel"], help="Change the channel where leave messages are sent")
    @commands.has_guild_permissions(administrator=True)
    async def set_leave_channel(self, ctx, *, channel: discord.TextChannel):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET leave_channel = :channel_id WHERE id = :guild_id",
            {
                "channel_id": channel.id,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        await ctx.send(f"The server's leave channel has been set to {channel.mention}")

    @commands.command(name="setautorole", aliases=["setauto", "autorole", "arole"], help="Set a role to give to new members of the server")
    @commands.has_guild_permissions(administrator=True)
    async def set_auto_role(self, ctx, role: discord.Role):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute(
            "UPDATE guilds SET auto_role = :auto_role_id WHERE id = :guild_id",
            {
                "auto_role_id": role.id,
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()

        await ctx.send(f"The auto role has been set to **{role}**")


def setup(bot):
    bot.add_cog(Settings(bot))
