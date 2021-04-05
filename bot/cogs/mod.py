import json
import discord
from discord.ext import commands
from bot.data import Data


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Commands to uphold the peace and integrity of the server"
        self.theme_color = discord.Color.purple()

    async def create_mute_role(self, guild: discord.Guild):
        print(f"Creating new mute role for server {guild.name}")
        role_perms = discord.Permissions(send_messages=False)
        role_color = discord.Color.dark_gray()
        mute_role = await guild.create_role(name="Muted", permissions=role_perms, color=role_color, reason="No existing mute role provided")

        guild_channels: list[discord.abc.GuildChannel] = await guild.fetch_channels()

        # Set permissions for channels
        for channel in guild_channels:
            await channel.set_permissions(mute_role, send_messages=False)

        # Set permissions for categories
        for category in guild.categories:
            await category.set_permissions(mute_role, send_messages=False)

        Data.c.execute(
            "UPDATE guilds SET mute_role = :mute_role_id WHERE id = :guild_id",
            {
                "mute_role_id": mute_role.id,
                "guild_id": guild.id
            }
        )
        Data.conn.commit()

        return mute_role

    async def get_guild_mute_role(self, guild: discord.Guild):
        Data.check_guild_entry(guild)

        Data.c.execute("SELECT mute_role FROM guilds WHERE id = :guild_id", {"guild_id": guild.id})
        mute_role_id = Data.c.fetchone()[0]

        if mute_role_id is None:  # Create mute role if none is provided
            mute_role = await self.create_mute_role(guild)

        else:  # Get mute role if one was provided
            mute_role = guild.get_role(mute_role_id)

            # Check if the role provided still exists
            if mute_role is None:
                mute_role = await self.create_mute_role(guild)

        return mute_role

    @commands.command(name="warn", help="Warn a member for doing something they weren't supposed to")
    @commands.has_guild_permissions(administrator=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
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
    async def infractions(self, ctx: commands.Context, member: discord.Member = None):
        Data.check_guild_entry(ctx.guild)

        Data.c.execute("SELECT infractions FROM guilds WHERE id = :guild_id", {"guild_id": ctx.guild.id})

        if member is None:
            infracs = json.loads(Data.c.fetchone()[0])
            embed_title = f"All Infractions in {ctx.guild.name}"
        else:
            infracs = [infrac for infrac in json.loads(Data.c.fetchone()[0]) if infrac["member"] == member.id]
            embed_title = f"Infractions by {member} in {ctx.guild.name}"

        infractions_embed = discord.Embed(title=embed_title, color=self.theme_color)

        for infrac in infracs:
            if member:
                guild_member = member
            else:
                guild_member = ctx.guild.get_member(infrac["member"])

            reason = infrac["reason"]
            infractions_embed.add_field(name=str(guild_member), value=f"Reason: *{reason}*", inline=False)

        await ctx.send(embed=infractions_embed)

    @commands.command(name="clearinfractions", aliases=["clearinf"], help="Clear somebody's infractions in the current server")
    @commands.has_guild_permissions(administrator=True)
    async def clear_infractions(self, ctx: commands.Context, member: discord.Member = None):
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

    @commands.command(name="mute", help="Prevent someone from sending messages")
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member):
        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.add_roles(mute_role)
        await ctx.send(f"**{member}** can no longer speak")

    @commands.command(name="unmute", help="Return the ability to talk to someone")
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.remove_roles(mute_role)
        await ctx.send(f"**{member}** can speak now")

    @commands.command(name="ban", help="Permanently remove a person from the server")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        await ctx.guild.ban(member, reason=reason, delete_message_days=0)
        await ctx.send(f"**{member}** has been banned from this server")
        await member.send(f"You have been banned from **{ctx.guild.name}**")

    @commands.command(name="unban", help="Unban a person from the server")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, username: str):
        if username[-5] != "#":
            await ctx.send("Please give a username in this format: *username#0000*")
            return

        name = username[:-5]  # first character to 6th last character
        discriminator = username[-4:]  # last 4 characters
        guild_bans = await ctx.guild.bans()
        user_to_unban = None

        for ban_entry in guild_bans:
            banned_user: discord.User = ban_entry.user

            if banned_user.name == name and banned_user.discriminator == discriminator:
                user_to_unban = banned_user
                break

        if user_to_unban:
            await ctx.guild.unban(user_to_unban)
            await ctx.send(f"**{user_to_unban}** has been unbanned from this server")
            await user_to_unban.send(f"You have been unbanned from **{ctx.guild.name}**")
        else:
            await ctx.send("This person was not found to be banned")

    @commands.command(name="kick", help="Remove a person from the server")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f"**{member}** has been kicked from this server")
        await member.send(f"You have been kicked from **{ctx.guild.name}**")

    @commands.command(name="lockchannel", aliases=["lock"], help="Prevent non-admins from sending messages in this channel")
    @commands.has_guild_permissions(manage_channels=True)
    async def lock_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f":lock: {ch.mention} has been locked")

    @commands.command(name="unlockchannel", aliases=["unlock"], help="Reverse the effects of lockchannel command")
    @commands.has_guild_permissions(manage_channels=True)
    async def unlock_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        if channel:
            ch = channel
        else:
            ch = ctx.channel

        await ch.edit(sync_permissions=True)
        await ctx.send(f":unlock: {ch.mention} has been unlocked")

    @commands.command(name="slowmode", help="Add slowmode delay on the current channel")
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, time: int):
        await ctx.channel.edit(slowmode_delay=time)

        if time > 0:
            await ctx.send(f"Added a slowmode delay of **{time} seconds**")
        else:
            await ctx.send("Slowmode has been disabled")


def setup(bot):
    bot.add_cog(Moderation(bot))
