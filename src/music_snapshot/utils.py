"""music_snapshot utils."""

from datetime import date, time
from typing import Callable, Optional, Sequence, Union

import questionary
from click_default_group import DefaultGroup
from rich_click import RichGroup


class DefaultRichGroup(DefaultGroup, RichGroup):
    """Make `click-default-group` work with `rick-click`."""


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


def select_or_input(
    name: str,
    choices: Sequence[Union[str, questionary.Choice]],
    *,
    input_choice_value: str = "Other",
    input_message: str = "Input value:",
    input_validate: Optional[Callable[[str], bool]] = None,
) -> str:
    """TODO: Docstrings."""
    message = f"Select {name}:"
    value = questionary.select(message, choices).ask()

    if value == input_choice_value:
        value = questionary.text(input_message, validate=input_validate).ask()

    return value


def select_song(
    songs: list[dict],
) -> dict:
    """TODO: Docstrings."""
