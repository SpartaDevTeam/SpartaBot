import asyncio
import os
import sys
import time

import discord
import topgg
from discord.ext import commands
from discord.ext.prettyhelp import PrettyHelp

from bot import db
from bot.db import models
from bot.views import PaginatedEmbedView
from bot.errors import DBLVoteRequired

THEME = discord.Color.purple()

TESTING_GUILDS = (
    list(map(int, os.getenv("TESTING_GUILDS").split(",")))
    if "--debug" in sys.argv and "TESTING_GUILDS" in os.environ
    else None
)
HELP_EMBEDS: list[discord.Embed] = []

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topgg_client = topgg.DBLClient(
            bot=self, token=os.environ["DBL_TOKEN"], autopost=True
        )

    async def on_ready(self):
        guild_count = len(self.guilds)
        print(f"Bot logged into {guild_count} guilds...")


async def get_prefix(
    client: commands.Bot, message: discord.Message
) -> list[str]:
    if not message.guild:
        return commands.when_mentioned_or("s!")(client, message)

    async with db.async_session() as session:
        guild_data: models.Guild | None = await session.get(
            models.Guild, message.guild.id
        )

        if guild_data:
            prefix = guild_data.prefix
        else:
            new_guild_data = models.Guild(id=message.guild.id)
            session.add(new_guild_data)
            await session.commit()

            prefix = models.Guild.prefix.default

    return commands.when_mentioned_or(prefix)(client, message)


help_cmd = PrettyHelp(
    color=THEME,
    verify_checks=False,
    command_attrs={"hidden": True},
    ending_note=(
        "Please use the new slash commands (/help), use of prefix commands "
        "(s!help) is discouraged. Type {ctx.clean_prefix}{help.invoked_with} "
        "command for more info on a command."
    ),
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

        for missing_perm in exception.missing_permissions:
            perm_str = missing_perm.title().replace("_", " ")
            msg += f"\n{perm_str}"

        await ctx.send(msg)

    elif isinstance(exception, commands.BotMissingPermissions):
        msg = "I don't have permission to run this command. I will need the following permissions:"

        for missing_perm in exception.missing_permissions:
            perm_str = missing_perm.title().replace("_", " ")
            msg += f"\n{perm_str}"

        await ctx.send(msg)

    elif isinstance(exception, commands.CommandOnCooldown):
        now_epoch = time.time()
        try_after = f"<t:{int(now_epoch + exception.retry_after)}:R>"
        await ctx.send(
            f"This commands is on cooldown, try again {try_after}..."
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
async def on_application_command_error(
    ctx: discord.ApplicationContext, exception
):
    if isinstance(exception, commands.MissingPermissions):
        msg = "You don't have permission to run this command. You need the following permissions:"

        for missing_perm in exception.missing_permissions:
            perm_str = missing_perm.title().replace("_", " ")
            msg += f"\n{perm_str}"

        await ctx.respond(msg, ephemeral=True)

    elif isinstance(exception, commands.BotMissingPermissions):
        msg = "I don't have permission to run this command. I need the following permissions:"

        for missing_perm in exception.missing_permissions:
            perm_str = missing_perm.title().replace("_", " ")
            msg += f"\n{perm_str}"

        await ctx.respond(msg, ephemeral=True)

    elif isinstance(exception, commands.CommandOnCooldown):
        now_epoch = time.time()
        try_after = f"<t:{int(now_epoch + exception.retry_after)}:R>"
        await ctx.respond(
            f"This commands is on cooldown, try again {try_after}...",
            ephemeral=True,
        )

    elif isinstance(exception, commands.NotOwner):
        await ctx.respond("You must be the bot owner to use this command")

    elif isinstance(exception, commands.CommandInvokeError):
        await ctx.respond(
            f"An error occured while running that command:\n```{exception}```",
            ephemeral=True,
        )
        raise exception

    elif isinstance(exception, commands.NSFWChannelRequired):
        await ctx.respond(
            "Please enable NSFW on this channel to use this command",
            ephemeral=True,
        )

    elif isinstance(exception, DBLVoteRequired):
        await ctx.respond(
            "Please vote for me on Top.gg to use this command. Try using `/vote` for voting links.",
            ephemeral=True,
        )

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


@bot.slash_command(guild_ids=TESTING_GUILDS)
async def help(ctx: discord.ApplicationContext, command: str = None):
    """
    Get a list of commands or more information about a specific command
    """

    if command:
        cmd_info: discord.SlashCommand = bot.get_application_command(command)

        if not cmd_info:
            await ctx.respond(f"Command not found: `{command}`")
            return

        cmd_name = cmd_info.qualified_name
        formatted_options = []

        for option in cmd_info.options:
            if option.required:
                formatted_options.append(f"<{option.name}>")
            elif option.default is None:
                formatted_options.append(f"[{option.name}]")
            else:
                formatted_options.append(f"[{option.name}={option.default}]")

        options_str = " ".join(formatted_options)

        help_embed = discord.Embed(
            title=f"/{cmd_name}", color=THEME, description=cmd_info.description
        )
        help_embed.set_footer(
            text=(
                "Options wrapped in <> are required\n"
                "Options wrapped in [] are optional"
            )
        )

        help_embed.add_field(
            name="Usage",
            value=f"```/{cmd_name} {options_str}```",
            inline=False,
        )

        await ctx.respond(embed=help_embed)

    else:
        embed_view = PaginatedEmbedView(ctx.author.id, HELP_EMBEDS)
        msg = await ctx.respond(embed=HELP_EMBEDS[0], view=embed_view)
        timed_out = await embed_view.wait()

        if timed_out:
            if isinstance(msg, discord.Interaction):
                await msg.delete_original_message()
            else:
                await msg.delete()


def add_cogs():
    # Prefix Command Cogs
    cogs_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "cogs"
    )
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"bot.cogs.{filename[:-3]}")
            print(f"Loaded {filename[:-3]} prefix cog!")

    # Slash Command Cogs
    # TODO: Remove "Slash" from cog names
    slash_cogs_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "slash_cogs"
    )
    for filename in os.listdir(slash_cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"bot.slash_cogs.{filename[:-3]}")
            print(f"Loaded {filename[:-3]} slash cog!")

    # Extensions
    bot.load_extension("jishaku")


def generate_help_embeds():
    index_embed = discord.Embed(
        title="Index", color=THEME, description=bot.description
    )
    index_embed.set_footer(
        text="You can use /help command to get more information about a command"
    )

    cog_embeds = []

    for cog_name, cog in list(bot.cogs.items()):
        # TODO: Remove conditional and replace call when renaming slash command cogs

        if not cog_name.startswith("Slash"):
            continue

        cog_name = cog_name.replace("Slash", "")
        index_embed.add_field(name=cog_name, value=cog.description)

        embed = discord.Embed(
            title=cog_name, color=THEME, description=cog.description
        )

        for cmd_info in cog.walk_commands():
            embed.add_field(
                name=f"/{cmd_info.qualified_name}",
                value=cmd_info.description,
            )

        cog_embeds.append(embed)

    HELP_EMBEDS.append(index_embed)
    HELP_EMBEDS.extend(cog_embeds)
    print("Generated Help Embeds!")


def main():
    loop = asyncio.get_event_loop()
    token = os.environ["TOKEN"]

    try:
        db.init_engine()
        add_cogs()
        generate_help_embeds()
        loop.run_until_complete(bot.start(token))
    except KeyboardInterrupt or SystemExit:
        pass
    finally:
        print("Exiting...")
        loop.run_until_complete(bot.close())
        loop.run_until_complete(db.close())
