import os

import discord
from discord.ext import commands
from pretty_help import Navigation, PrettyHelp

from bot.data import Data

TOKEN = os.environ["SPARTA_TOKEN"]
THEME = discord.Color.purple()

intents = discord.Intents.default()
intents.members = True


def get_prefix(client, message):
    Data.check_guild_entry(message.guild)

    Data.c.execute(
        "SELECT prefix FROM guilds WHERE id = :guild_id",
        {"guild_id": message.guild.id},
    )
    prefix = Data.c.fetchone()[0]

    return prefix


bot = commands.Bot(
    command_prefix=get_prefix,
    description="I'm a cool moderation and automation bot to help you manage your server better...",
    intents=intents,
    case_insensitive=True,
    help_command=PrettyHelp(navigation=Navigation(), color=THEME),
)


@bot.event
async def on_ready():
    guild_count = len(bot.guilds)
    print(f"Bot logged into {guild_count} guilds...")


@bot.event
async def on_command_error(ctx: commands.Context, exception):
    if isinstance(exception, commands.errors.MissingRequiredArgument):
        prefix = get_prefix(bot, ctx.message)
        await ctx.send(
            f"`{exception.param.name}` is a required input. Try using `{prefix}help {ctx.invoked_with}` for more information."
        )

    elif isinstance(exception, commands.MissingPermissions):
        await ctx.send(
            "You don't have permission to run this command. You need the following permissions:"
        )

        for missing_perm in exception.missing_perms:
            await ctx.send(missing_perm.title())

    else:
        raise exception


@bot.event
async def on_message(message: discord.Message):
    if bot.user in message.mentions:
        guild_prefix = get_prefix(bot, message)
        await message.channel.send(
            f"{message.author.mention}, my prefix in this server is `{guild_prefix}`"
        )

    await bot.process_commands(message)


def add_cogs():
    cogs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"bot.cogs.{filename[:-3]}")
            print(f"Loaded {filename[:-3]} cog!")

    # Extensions
    bot.load_extension("jishaku")


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
