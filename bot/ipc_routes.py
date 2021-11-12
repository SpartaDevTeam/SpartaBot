from bot import bot


@bot.ipc.route()
async def get_guild_ids(data):
    return [guild.id for guild in bot.guilds]


@bot.ipc.route()
async def get_guild_info(data):
    guild = await bot.fetch_guild(data.guild_id)

    guild_info = {"name": guild.name, "icon_url": str(guild.icon_url)}
    return guild_info
