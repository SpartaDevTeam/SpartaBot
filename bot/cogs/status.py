import discord
from discord.ext import commands, tasks

from bot import MyBot


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
        self.theme_color = discord.Color.purple()
        self.status_msgs = [
            (discord.ActivityType.watching, "[guild_count] servers"),
            (discord.ActivityType.playing, "Hypixel"),
            (discord.ActivityType.listening, "Shawty's Like a Melody"),
            (discord.ActivityType.streaming, "Minecraft Bedwars"),
            (discord.ActivityType.playing, "Amogus"),
            (discord.ActivityType.watching, "out for s!help"),
        ]
        self.status_index = 0

    @commands.Cog.listener()
    async def on_ready(self):
        self.status_task.start()

    def cog_unload(self):
        self.status_task.cancel()

    @tasks.loop(seconds=120)
    async def status_task(self):
        activity = self.status_msgs[self.status_index]
        activ_type = activity[0]
        activ_msg = activity[1]

        if "[guild_count]" in activ_msg:
            guild_count = len(self.bot.guilds)
            activ_msg = activ_msg.replace("[guild_count]", str(guild_count))

        activ = discord.Activity(type=activ_type, name=activ_msg)
        await self.bot.change_presence(activity=activ)

        self.status_index += 1
        if self.status_index >= len(self.status_msgs):
            self.status_index = 0


def setup(bot):
    # bot.add_cog(Status(bot))
    pass
