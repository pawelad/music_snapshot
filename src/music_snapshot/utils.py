"""music_snapshot utils."""

from collections.abc import Generator, Sequence
from datetime import date, time

from click_default_group import DefaultGroup
from rich_click import RichGroup

DATE_FORMAT = "%Y-%m-%d"
"""Default `music_snapshot` date format."""

TIME_FORMAT = "%H:%M"
"""Default `music_snapshot` time format."""

DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
"""Default `music_snapshot` datetime format."""


class DefaultRichGroup(DefaultGroup, RichGroup):
    """Make `click-default-group` work with `rick-click`."""


def chunks(seq: Sequence, n: int) -> Generator[Sequence]:
    """Yield successive `n` sized chunks from `seq`.

    Arguments:
        seq: Sequence to chunk.
        n: Chunk size.

    Returns:
        Generator that yields `n` sized chunks from passed `seq`.
    """
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def validate_date(value: str) -> bool:
    """Check if passed value is in ISO date format.

    Arguments:
        value: Value to check

    Returns:
        Whether passed value is in ISO date format.
    """
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    else:
        return True


def validate_time(value: str) -> bool:
    """Check if passed value is in ISO time format.

    Arguments:
        value: Value to check

    Returns:
        Whether passed value is in ISO time format.
    """
    try:
        time.fromisoformat(value)
    except ValueError:
        return False
    else:
        return True
