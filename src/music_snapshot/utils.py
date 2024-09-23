"""music_snapshot utils."""

from collections.abc import Generator, Sequence
from datetime import date, time

from click_default_group import DefaultGroup
from rich_click import RichGroup

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"


class DefaultRichGroup(DefaultGroup, RichGroup):
    """Make `click-default-group` work with `rick-click`."""


def chunks(lst: Sequence, n: int) -> Generator[Sequence]:
    """Yield successive n-sized chunks from l.

    :param lst: iterable to chunk
    :param n: size of chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def validate_date(value: str) -> bool:
    """TODO: Docstrings."""
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    else:
        return True


def validate_time(value: str) -> bool:
    """TODO: Docstrings."""
    try:
        time.fromisoformat(value)
    except ValueError:
        return False
    else:
        return True
