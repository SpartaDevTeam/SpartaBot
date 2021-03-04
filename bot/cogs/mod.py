import json
import discord
from discord.ext import commands
from bot.data.data import Data
import datetime
from re import search

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.theme_color = discord.Color.purple()

    async def create_mute_role(self, guild: discord.Guild):
        print(f"Creating new mute role for server {guild.name}")
        role_perms = discord.Permissions(send_messages=False)
        role_color = discord.Color.dark_gray()
        mute_role = await guild.create_role(name="Muted", permissions=role_perms, color=role_color, reason="No existing mute role provided")

        guild_channels = await guild.fetch_channels()

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

    @commands.command(name="mute", help="Prevent someone from sending messages")
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member):
        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.add_roles(mute_role)
        await ctx.send(f"**{member}** can no longer speak")

    @commands.command(name="unmute", help="Return the ability to talk to someone")
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        mute_role = await self.get_guild_mute_role(ctx.guild)
        await member.remove_roles(mute_role)
        await ctx.send(f"**{member}** can speak now")

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

    @commands.command(name="ban", help="Permanently remove a person from the server")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.ban(member, reason=reason, delete_message_days=0)
        await ctx.send(f"**{member}** has been banned from this server")
        await member.send(f"You have been banned from **{ctx.guild.name}**")

    @commands.command(name="unban", help="Unban a person from the server")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, username: str):
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
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f"**{member}** has been kicked from this server")
        await member.send(f"You have been kicked from **{ctx.guild.name}**")
       
    '''
    @commands.command(name="automod", help="Allows you to enable/disable automod features")
    @commands.has_guild_permissions(administrator=True)
    @commands.command(description="Sets up auto-mod features")
    async def automod(self, ctx, is_disable: str=None):
        if is_disable.lower() == "false" or is_disable.lower() == "disable" or is_disable.lower() == "off":
            # Create a channel id entry inside automod with an empty list

        def check(message: discord.Message):
            return message.channel == ctx.channel and message.author == ctx.message.author

        mod_embed = discord.Embed(title='Auto-Mod',
                                  description='Allow Sparta to administrate on its own.\n'
                                              'Reply with a particular feature.',
                                  color=self.theme_color)
        mod_embed.add_field(name='`links`', value='Bans links from being sent to this channel.', inline=False)
        mod_embed.add_field(name='`images`', value='Bans attachments from being sent to this channel.', inline=False)
        mod_embed.add_field(name='`spam`', value='Temporarily mutes users who are spamming in this channel.',
                            inline=False)
        mod_embed.set_footer(text="Reply with `stop` if you want to stop adding auto-mod features")
        await ctx.send(embed=mod_embed)

        available_features = ['links', 'images', 'spam']

        activated_features = []

        while True:

            if len(activated_features) == len(available_features):
                await ctx.send("You have activated all the features. Changes have been saved!")
                break

            msg = await self.bot.wait_for('message', check=check)
            msg = str(msg.content)

            if msg.lower() in available_features:
                if msg.lower() in activated_features:
                    await ctx.send("Feature already activated!")
                else:
                    await ctx.send(f"Added `{msg}`!")
                    activated_features.append(msg)

            elif msg == 'stop':
                await ctx.send("The changes have been saved!")
                break

            else:
                await ctx.send("Not a valid response!")

        # Create a channel id entry inside automod with value as activated_features
    
    
    @commands.Cog.listener()
    async def on_message(self, message):
        url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<" \
                r">]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

        def spam_check(msg):
            return (msg.author == message.author) and (len(msg.mentions)) and \
                   ((datetime.datetime.utcnow()-msg.created_at).seconds < 30)
        
        # if channel id's data contains "links":
            if search(url_regex, message.content):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, You cannot send links in this channel!",
                                           delete_after=3)
        # if channel id's data contains "images"
            if any([hasattr(a, "width") for a in message.attachments]):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, You cannot send images in this channel!",
                                           delete_after=3)

        # if channel id's data contains "spam":
            if len(list(filter(lambda m: spam_check(m), client.cached_messages))) >= 5:
                await message.channel.send(f"{message.author.mention}, Do not spam mentions in this channel!",
                                           delete_after=3)
'''


def setup(bot):
    bot.add_cog(Moderation(bot))
