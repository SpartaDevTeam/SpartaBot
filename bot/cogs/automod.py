from re import search
import datetime
from discord.ext import commands
import discord


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.theme_color = discord.Colour.red()

    @commands.command(name="automod", help="Allows you to enable/disable automod features")
    @commands.has_guild_permissions(administrator=True)
    async def automod(self, ctx, is_disable: str=None):
        if is_disable.lower() == "false" or is_disable.lower() == "disable" or is_disable.lower() == "off":
            pass
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
        if False:
            if search(url_regex, message.content):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, You cannot send links in this channel!",
                                           delete_after=3)
                
        # if channel id's data contains "images"
        if False:
            if any([hasattr(a, "width") for a in message.attachments]):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, You cannot send images in this channel!",
                                           delete_after=3)

        # if channel id's data contains "spam":
        if False:
            if len(list(filter(lambda m: spam_check(m), client.cached_messages))) >= 5:
                await message.channel.send(f"{message.author.mention}, Do not spam mentions in this channel!",
                                           delete_after=3)
    
def setup(bot):
    client.add_cog(AutoMod(bot))
