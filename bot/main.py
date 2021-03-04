import os
import discord
from discord.ext import commands
from bot.data.data import Data

TOKEN = os.environ["SPARTA_TOKEN"]
PREFIX = "sb!"  # TODO: Change to s! after rewrite complete

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


def add_cogs():
    cogs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded {filename[:-3]} cog!")


def main():
    Data.create_tables()
    add_cogs()

    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
    finally:
        print("Exiting...")
        Data.conn.close()


if __name__ == "__main__":
    main()
