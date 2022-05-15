import discord
from discord.ext import commands
from discord.ext.commands.core import command
from bot import TESTING_GUILDS, db
from afks import afks

class AFK(commands.Cog):
    """
   A Global AFK command 
    """
    def remove(afk):
        if "(AFK)" in afk.split():
            return " ".join(afk.split()[1:])
        else:
             return AFK

    @commands.slash_command( guild_ids=TESTING_GUILDS)
    async def afk( 
        self, 
        ctx:discord.ApplicationContext, 
        reason = "No Reason Given!"
        ):

        """
        Set's your AFK status
        """
        member = ctx.author

        if member.id in afks.keys():
           afks.pop(member.id)
        else:
            try:
                await member.edit(nick = f"(AFK) {member.display_name}")
            except:
                pass

        afks[member.id] = reason 
        embed = discord.Embed(
            title = "Member AFK",
            description = f"{member.mention} has gone AFK ",
            colour = member.color
        )
        embed.set_thumbnail(url = ctx.bot.avatar.url)
        embed.set_author(
            name = ctx.author,
            icon_url = ctx.user.avatar.url
        )
        embed.add_field(
            name = 'AFK note :',
            value = reason
             )
        await ctx.respond(embed = embed)

    @commands.Cog.listener()
    async def on_message(self,message):

        if message.author.id in afks.keys():
            afks.pop(message.author.id)
            try:
                authorname = message.author.display_name.replace("(AFK)", "")
                await message.author.edit(nick = authorname)
            except:
                pass
            await message.channel.send(f'Welcome back {message.author.name}, I removed you AFK')

        for id, reason in afks.items():
            member = discord.utils.get(message.guild.members, id = id)
            if (message.reference and member == (await message.channel.fetch_message(message.reference.message_id)).author) or member.id in message.raw_mentions:
                await message.reply(f"{member.name} is AFK Because ***{reason}***")
def setup(bot):
    bot.add_cog(AFK()) 

