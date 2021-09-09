import os
import asyncio

from dotenv import load_dotenv

import discord
import topgg
import humanize
from discord.ext import commands, ipc
from discord.ext.prettyhelp import PrettyHelp

from bot.data import Data
from bot.errors import DBLVoteRequired

load_dotenv()

TOKEN = os.environ["SPARTA_TOKEN"]
THEME = discord.Color.purple()

intents = discord.Intents.default()
intents.members = True
intents.reactions = True


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ipc = ipc.Server(
            self,
            host="0.0.0.0",
            port=6000,
            secret_key=os.environ["SPARTA_SECRET_KEY"],
        )
        self.topgg_client = topgg.DBLClient(
            bot=self, token=os.environ["SPARTA_DBL_TOKEN"], autopost=True
        )

    async def on_ready(self):
        guild_count = len(self.guilds)
        print(f"Bot logged into {guild_count} guilds...")

    async def on_ipc_ready(self):
        print("IPC Server is ready!")

    async def on_ipc_error(self, endpoint, error):
        print("Endpoint", endpoint, "threw error:", error)


def get_prefix(client: commands.Bot, message: discord.Message):
    if not message.guild:
        return commands.when_mentioned_or("s!")(client, message)

    Data.check_guild_entry(message.guild)

    Data.c.execute(
        "SELECT prefix FROM guilds WHERE id = :guild_id",
        {"guild_id": message.guild.id},
    )
    prefix = Data.c.fetchone()[0]

    return commands.when_mentioned_or(prefix)(client, message)


help_cmd = PrettyHelp(
    color=THEME, verify_checks=False, command_attrs={"hidden": True}
)
bot = MyBot(
    command_prefix=get_prefix,
    description=(
        "I'm a cool moderation and automation bot to help "
        "you manage your server better..."
    ),
    intents=intents,
    case_insensitive=True,
    help_command=help_cmd,
)


@bot.event
async def on_command_error(ctx: commands.Context, exception):
    prefix = get_prefix(bot, ctx.message)

    if isinstance(exception, commands.MissingRequiredArgument):
        await ctx.send(
            f"`{exception.param.name}` is a required input, try using "
            f"`{prefix[2]}help {ctx.invoked_with}` for more information"
        )

    elif isinstance(exception, commands.MissingPermissions):
        msg = "You don't have permission to run this command. You need the following permissions:"

        for missing_perm in exception.missing_perms:
            msg += f"\n{missing_perm.title()}"

        await ctx.send(msg)

    elif isinstance(exception, commands.BotMissingPermissions):
        msg = "I don't have permission to run this command. I will need the following permissions:"

        for missing_perm in exception.missing_perms:
            msg += f"\n{missing_perm.title()}"

        await ctx.send(msg)

    elif isinstance(exception, commands.CommandOnCooldown):
        try_after = humanize.precisedelta(exception.retry_after)
        await ctx.send(
            f"This commands is on cooldown, try again after {try_after}..."
        )

    elif isinstance(exception, commands.NotOwner):
        await ctx.send("You must be the bot owner to use this command")

    elif isinstance(exception, commands.CommandNotFound):
        pass

    elif isinstance(exception, commands.CommandInvokeError):
        await ctx.send(
            f"An error occured while running that command:\n```{exception}```"
        )
        raise exception

    elif isinstance(exception, commands.NSFWChannelRequired):
        await ctx.send(
            "Please enable NSFW on this channel to use this command"
        )

    elif isinstance(exception, DBLVoteRequired):
        await ctx.send(
            f"Please vote for me on Top.gg to use this command. Try using `{prefix[2]}vote` for voting links."
        )

    elif isinstance(exception, commands.CheckFailure):
        pass

    else:
        raise exception


@bot.event
async def on_message(message: discord.Message):
    if (
        message.content == f"<@!{bot.user.id}>"
        and message.author != bot.user
        and not message.reference
        and not message.author.bot
    ):
        prefixes = get_prefix(bot, message)
        prefixes.remove(f"{bot.user.mention} ")
        prefixes.remove(f"<@!{bot.user.id}> ")

        prefix_count = len(prefixes)
        prefixes_string = ", ".join(prefixes)

        if prefix_count == 1:
            await message.channel.send(
                f"{message.author.mention}, my prefix in this server "
                f"is `{prefixes_string}`"
            )
        else:
            await message.channel.send(
                f"{message.author.mention}, my prefixes in this server "
                f"are `{prefixes_string}`"
            )

    await bot.process_commands(message)


def add_cogs():
    cogs_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "cogs"
    )
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"bot.cogs.{filename[:-3]}")
            print(f"Loaded {filename[:-3]} cog!")

    # Extensions
    bot.load_extension("jishaku")


def main():
    try:
        Data.create_tables()
        add_cogs()

        from bot import ipc_routes

        bot.ipc.start()
        bot.run(TOKEN)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
    finally:
        Data.conn.close()
        print("Exiting...")
