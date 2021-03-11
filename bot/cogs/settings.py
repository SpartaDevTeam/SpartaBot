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

        await ctx.send(f"The mute role has been set to {role.mention}")


def setup(bot):
    bot.add_cog(Settings(bot))
