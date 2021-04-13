import re
from discord.ext import commands
from datetime import timedelta


def get_time(
    key: str, string: str
) -> int:  # CircuitSacul == pog (he made this)
    string = f" {string} "
    results = re.findall(f" [0-9]+{key}", string)
    if len(list(results)) < 1:
        return 0
    r = results[0]
    r = r[1 : 0 - len(key)]
    return int(r)


def str_time_to_datetime(
    time_string: str,
) -> timedelta:  # CircuitSacul == pog (he made this)
    time_string = time_string.lower()

    days = get_time("d", time_string)
    hours = get_time("h", time_string)
    minutes = get_time("m", time_string)
    seconds = get_time("s", time_string)

    actual_seconds = 0
    if hours:
        actual_seconds += hours * 3600
    if minutes:
        actual_seconds += minutes * 60
    if seconds:
        actual_seconds += seconds

    datetime_obj = timedelta(
        days=days,
        seconds=actual_seconds,
    )
    return datetime_obj


def ping_prot(ctx: commands.Context):
    mentions = ctx.message.mentions
    role_mentions = ctx.message.role_mentions
    return mentions != [] and role_mentions != []


def mass_ping_prot(ctx: commands.Context):
    mentions = ctx.message.role_mentions
    def_role = ctx.guild.default_role
    return mentions != [] and def_role not in mentions

