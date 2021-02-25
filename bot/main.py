import os
import discord
from discord.ext import commands

TOKEN = os.environ["SPARTA_TOKEN"]
PREFIX = "sb!"  # TODO: Change to s! after rewrite complete
THEME = discord.Color.blurple()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    description="I'm a cool moderation and automation bot to help you manage your server better...",
    intents=intents,
    case_insensitive=True
)


@bot.event
async def on_ready():
    guild_count = len(bot.guilds)
    print(f"Bot logged into {guild_count} guilds...")


def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
