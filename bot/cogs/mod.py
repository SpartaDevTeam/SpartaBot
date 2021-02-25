import json
import discord
from discord.ext import commands
from bot.data.data import Data


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.theme_color = discord.Color.blurple()

    @commands.command(name="warn", help="Warn a member for doing something they weren't supposed to")
    @commands.has_guild_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute("SELECT infractions FROM guilds WHERE id = :guild_id", {"guild_id": ctx.guild.id})
        guild_infractions: list = json.loads(Data.c.fetchone()[0])

        new_infraction = {
            "member": member.id,
            "reason": reason
        }
        guild_infractions.append(new_infraction)

        Data.c.execute(
            "UPDATE guilds SET infractions = :new_infractions WHERE id = :guild_id",
            {
                "new_infractions": json.dumps(guild_infractions),
                "guild_id": ctx.guild.id
            }
        )
        Data.conn.commit()
        await ctx.send(f"**{member}** has been warned because: *{reason}*")

    @commands.command(name="infractions", aliases=["inf"], help="See all the times a person has been warned")
    @commands.has_guild_permissions(administrator=True)
    async def infractions(self, ctx, member: discord.Member = None):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute("SELECT infractions FROM guilds WHERE id = :guild_id", {"guild_id": ctx.guild.id})

        if member is None:
            infracs = json.loads(Data.c.fetchone()[0])
            embed_title = f"All Infractions in {ctx.guild.name}"
        else:
            infracs = [infrac for infrac in json.loads(Data.c.fetchone()[0]) if infrac["member"] == member.id]
            embed_title = f"Infractions by {member} in {ctx.guild.name}"

        infractions_embed = discord.Embed(title=embed_title)

        for infrac in infracs:
            if member is not None:
                guild_member = member
            else:
                guild_member = ctx.guild.get_member(infrac["member"])

            reason = infrac["reason"]
            infractions_embed.add_field(name=str(guild_member), value=f"Reason: *{reason}*", inline=False)

        await ctx.send(embed=infractions_embed)

    @commands.command(name="clearinfractions", aliases=["clearinf"])
    @commands.has_guild_permissions(administrator=True)
    async def clear_infractions(self, ctx, member: discord.Member = None):
        Data.check_guild_entry(ctx.guild)

        if member is None:
            Data.c.execute("UPDATE guilds SET infractions = '[]' WHERE id = :guild_id", {"guild_id": ctx.guild.id})
            Data.conn.commit()

            await ctx.send("Cleared all infractions in this server...")

        else:
            Data.c.execute("SELECT infractions FROM guilds WHERE id = :guild_id", {"guild_id": ctx.guild.id})
            user_infractions = json.loads(Data.c.fetchone()[0])
            new_infractions = [inf for inf in user_infractions if inf["member"] != member.id]
            Data.c.execute(
                "UPDATE guilds SET infractions = :new_infractions WHERE id = :guild_id",
                {
                    "new_infractions": json.dumps(new_infractions),
                    "guild_id": ctx.guild.id
                }
            )
            Data.conn.commit()

            await ctx.send(f"Cleared all infractions by **{member}** in this server...")

def setup(bot):
    bot.add_cog(Moderation(bot))
