def seconds_to_eta(seconds: int) -> str:
    if seconds < 120:
        return f"{seconds} seconds"
    elif seconds < 7200:
        return f"{round(seconds / 60)} minutes"
    else:
        return f"{round(seconds / 3600)} hours"


def plural(noun: str, amount: int) -> str:
    if amount > 1 or amount == 0:
        return f"{amount} {noun}s"
    return f"{amount} {noun}"


def seconds_to_time(seconds: int) -> str:
    second_remainder = seconds % 60
    minute_remainder = (seconds // 60) % 60
    hours = seconds // 3600
    str_time = ""
    if hours > 0:
        str_time += f"{plural('hour', hours)} "
    if minute_remainder > 0:
        str_time += f"{plural('minute', minute_remainder)} "
    if second_remainder > 0:
        str_time += plural("second", second_remainder)
    return str_time
