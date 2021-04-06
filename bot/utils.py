from datetime import datetime
import re


def get_time(key: str, string: str) -> int:  # CircuitSacul == pog (he made this)
    string = f"{string} "
    results = re.findall(f" [0-9]+{key}", string)
    if len(list(results)) < 1:
        return 0
    r = results[0]
    r = r[1 : 0 - len(key)]
    return int(r)


def str_time_to_datetime(
    time_string: str,
) -> datetime:  # CircuitSacul == pog (he made this)
    time_string = time_string.lower()

    days = get_time("d", time_string) + 1
    hours = get_time("h", time_string)
    minutes = get_time("m", time_string)
    seconds = get_time("s", time_string)

    now = datetime.now()
    datetime_obj = datetime(
        year=now.year,
        month=now.month,
        day=days,
        hour=hours,
        minute=minutes,
        second=seconds,
    )
    return datetime_obj


def str_time_to_seconds(time_string: str) -> int:
    split_terms = time_string.split()
    total_seconds = 0

    for term in split_terms:
        if "d" in term:
            term = term.replace("d", "")
            total_seconds += int(term) * 86400
        elif "h" in term:
            term = term.replace("h", "")
            total_seconds += int(term) * 3600
        elif "m" in term:
            term = term.replace("m", "")
            total_seconds += int(term) * 60
        elif "s" in term:
            term = term.replace("s", "")
            total_seconds += int(term)

    return total_seconds
