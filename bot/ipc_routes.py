from bot import bot


@bot.ipc.route("get_guild_ids")
async def get_guild_ids(data):
    return [guild.id for guild in bot.guilds]
