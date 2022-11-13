import discord
from discord.ext import commands, tasks


class SlashStatus(commands.Cog):
    """
    Automatically changing status
    """

    status_msgs = [
        (discord.ActivityType.listening, "my new music commands"),
        (discord.ActivityType.watching, "[guild_count] servers"),
        (discord.ActivityType.playing, "Hypixel"),
        (discord.ActivityType.competing, "Steel Ball Run"),
        (discord.ActivityType.watching, "JoJo"),
        (discord.ActivityType.playing, "Amogus"),
        (discord.ActivityType.watching, "out for /help and s!help"),
    ]
    status_index = 0

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
    bot.add_cog(SlashStatus(bot))
