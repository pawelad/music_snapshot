"""Tracks (songs) related utils.

I prefer 'song' terminology, but decided to follow `pylast` naming conventions in
Last.fm context, and 'song' in Spotify context.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import pylast
import questionary
import spotipy

from music_snapshot.utils import DATE_FORMAT, TIME_FORMAT

UTC = timezone.utc  # Python 3.11

MUSIC_SNAPSHOT_QUESTIONARY_STYLE = questionary.Style(
    [
        ("date", "fg:LightSkyBlue"),
        ("time", "fg:LightGreen"),
        ("track", "bold"),
        ("artist", "fg:cyan italic"),
        ("album", "fg:grey"),
    ]
)


class EnumeratedTrack(TypedDict):
    """Simple dict schema for an enumerated track.

    Attributes:
        n: Position of the track within the track list.
        played_track: Played track details.
    """

    n: int
    played_track: pylast.PlayedTrack


def get_played_track_title(played_track: pylast.PlayedTrack) -> list[tuple[str, str]]:
    """Create a (`questionary` compatible) nicely formatted title for a 'played track'.

    Attributes:
        played_track: Played track to generate a title for.
    """
    played_at = datetime.fromtimestamp(int(played_track.timestamp), UTC)
    played_at = played_at.astimezone()  # Local timezone
    track_name = played_track.track.get_name()
    artist = played_track.track.get_artist().get_name()
    album = played_track.album

    title = [
        ("class:date", played_at.strftime(DATE_FORMAT)),
        ("", " "),
        ("class:time", played_at.strftime(TIME_FORMAT)),
        ("", " | "),
        ("class:track", track_name),
        ("", " by "),
        ("class:artist", artist),
        ("", " from "),
        ("class:album", album),
    ]

    return title


def select_track(
    tracks: list[pylast.PlayedTrack],
    *,
    default_choice: dict[str, Any] | None = None,
    page: int = 0,
    page_size: int = 10,
    style: questionary.Style = MUSIC_SNAPSHOT_QUESTIONARY_STYLE,
    select_message: str = "Select track:",
    previous_choice: questionary.Choice | None = None,
    next_choice: questionary.Choice | None = None,
) -> EnumeratedTrack | None:
    """TODO: Docstrings."""
    if not previous_choice:
        previous_choice = questionary.Choice("Previous")

    if not next_choice:
        next_choice = questionary.Choice("Next")

    while True:
        track_choices = []
        for n, played_track in enumerate(
            tracks[page * page_size : (page + 1) * page_size],
            start=page * page_size,
        ):
            track_title = get_played_track_title(played_track)
            track_choice = questionary.Choice(
                title=track_title,
                value=EnumeratedTrack(n=n, played_track=played_track),
            )
            track_choices.append(track_choice)

        # Show 'Previous' choice on all pages, except the first one
        if page > 0:
            track_choices = [previous_choice] + track_choices

        # Show 'Next' choice only if there's a next page
        if (page + 1) * page_size < len(tracks):
            track_choices = track_choices + [next_choice]

        selected_track = questionary.select(
            select_message,
            track_choices,
            default=default_choice,
            style=style,
        ).ask()

        if selected_track == previous_choice.value:
            page -= 1
            default_choice = None
            continue
        elif selected_track == next_choice.value:
            page += 1
            default_choice = None
            continue
        else:
            break

    return selected_track


def guess_end_track(
    tracks: list[pylast.PlayedTrack],
    first_track_n: int,
    *,
    threshold: int = 60,
) -> EnumeratedTrack | None:
    """TODO: Docstrings."""
    guessed_track = None
    for n, played_track in enumerate(tracks[first_track_n:], start=first_track_n):
        track_played_at = datetime.fromtimestamp(int(played_track.timestamp), UTC)

        # In case we traverse the whole list and don't find an end track, default
        # to the last track
        try:
            next_track = tracks[n + 1]
        except IndexError:
            guessed_track = EnumeratedTrack(n=n, played_track=played_track)
            break

        next_track_played_at = datetime.fromtimestamp(int(next_track.timestamp), UTC)

        # If the difference between two tracks is more then the threshold, the earlier
        # one could be the end track. We could also involve track duration into the
        # math, but this is easier for now.
        if (next_track_played_at - track_played_at) > timedelta(minutes=threshold):
            guessed_track = EnumeratedTrack(n=n, played_track=played_track)
            break

    return guessed_track


def lastfm_track_to_spotify(
    spotify_api: spotipy.Spotify,
    track: pylast.Track,
) -> dict:
    """TODO: Docstrings."""
    artist_name: str = track.get_artist().get_name()

    track_name: str = track.get_name()
    # Last.fm and Spotify naming conventions sometimes differ, so it's safer
    # to remove some of the extra words and 'suffixes'
    for word in ["the", "The"]:
        artist_name = artist_name.replace(word, "")

    for suffix in ["ft", "Ft", "(ft", "(Ft", "feat", "Feat", "(feat", "(Feat"]:
        track_name = track_name.removesuffix(suffix)

    artist_name = artist_name.strip()
    track_name = track_name.strip()

    # Using `album:` for some reason doesn't work with some singles
    q = f"artist:{artist_name} track:{track_name}"
    spotify_search_results = spotify_api.search(q=q, limit=1, type="track")
    results = spotify_search_results["tracks"]["items"]

    if len(results) == 0:
        raise ValueError(f"Couldn't find '{track_name} by {artist_name}' in Spotify.")

    return results[0]
