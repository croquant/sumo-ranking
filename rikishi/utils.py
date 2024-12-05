from django.utils.text import slugify

from rikishi.constants import DIRECTION_NAMES_SHORT, RANK_NAMES_SHORT


def convert_long_to_short_rank(rank_name: str):
    if rank_name == "":
        return None
    rank_parts = rank_name.split(" ")

    title = rank_parts[0]
    order = rank_parts[1] if len(rank_parts) > 1 else None
    direction = rank_parts[2] if len(rank_parts) > 2 else None

    shorthand = RANK_NAMES_SHORT[title]
    if order and direction:
        dir_shorthand = DIRECTION_NAMES_SHORT[direction]
        return slugify(f"{shorthand}{order}{dir_shorthand}")
    else:
        return slugify(shorthand)
