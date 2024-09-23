"""Click based command line interface."""

import dataclasses
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import click
import pylast
import questionary
import rich_click
import spotipy
from click import ClickException
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import track as rich_progress_bar
from spotipy import SpotifyException

from music_snapshot.config import MusicSnapshotConfig
from music_snapshot.tracks import guess_end_track, lastfm_track_to_spotify, select_track
from music_snapshot.utils import (
    DATETIME_FORMAT,
    TIME_FORMAT,
    DefaultRichGroup,
    chunks,
    validate_date,
    validate_time,
)

UTC = timezone.utc  # Python 3.11

MUSIC_SNAPSHOT_CONFIG_PATH = Path.home() / ".music_snapshot"
SPOTIPY_CACHE_PATH = Path.home() / ".spotipy"
SPOTIPY_SCOPES = [
    "playlist-modify-public",
    "playlist-modify-private",
]
QUESTIONARY_STYLE = questionary.Style(
    [
        ("date", "fg:LightSkyBlue"),
        ("time", "fg:LightGreen"),
        ("track", "bold"),
        ("artist", "fg:cyan italic"),
        ("album", "fg:grey"),
    ]
)

help_config = rich_click.RichHelpConfiguration(
    max_width=88,
    use_markdown=True,
)

rich_console = Console()


@dataclasses.dataclass
class MusicSnapshotContext:
    """TODO: Docstrings."""

    config: MusicSnapshotConfig
    spotify_api: spotipy.Spotify
    lastfm_api: pylast.LastFMNetwork


@click.group(cls=DefaultRichGroup, default="create", default_if_no_args=True)
@rich_click.rich_config(help_config=help_config)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """TODO: Docstrings."""
    if ctx.invoked_subcommand != "authorize":
        try:
            config = MusicSnapshotConfig.load_from_disk(MUSIC_SNAPSHOT_CONFIG_PATH)
        except FileNotFoundError:
            raise click.UsageError(
                "Config file not found. You need to run `authorize` subcommand first."
            ) from None

        try:
            spotify_api = spotipy.Spotify(
                auth_manager=spotipy.SpotifyOAuth(
                    client_id=config.spotify_client_id,
                    client_secret=config.spotify_client_secret,
                    redirect_uri=config.spotify_redirect_uri,
                    scope=SPOTIPY_SCOPES,
                    cache_handler=spotipy.CacheFileHandler(
                        cache_path=SPOTIPY_CACHE_PATH,
                    ),
                )
            )
        except spotipy.SpotifyException as e:
            raise click.UsageError(str(e)) from e

        try:
            lastfm_api = pylast.LastFMNetwork(
                api_key=config.lastfm_api_key,
                api_secret=config.lastfm_api_secret,
            )
        except pylast.PyLastError as e:
            raise click.UsageError(str(e)) from e

        ctx.obj = MusicSnapshotContext(
            config=config,
            spotify_api=spotify_api,
            lastfm_api=lastfm_api,
        )


@cli.command()
@click.option(
    "--spotify_client_id",
    type=str,
    required=True,
    prompt="Spotify OAuth client ID",
    help="Spotify OAuth client ID.",
)
@click.option(
    "--spotify_client_secret",
    type=str,
    required=True,
    prompt="Spotify OAuth client secret",
    hide_input=True,
    help="Spotify OAuth client secret.",
)
@click.option(
    "--spotify_redirect_uri",
    type=str,
    default="http://localhost:6600/music_snapshot",
    help="Spotify redirect URI specified in OAuth client.",
)
@click.option(
    "--lastfm_api_key",
    type=str,
    required=True,
    prompt="Last.fm API key",
    help="Last.fm API key.",
)
@click.option(
    "--lastfm_api_secret",
    type=str,
    required=True,
    prompt="Last.fm API secret",
    hide_input=True,
    help="Last.fm API secret.",
)
@click.option(
    "--lastfm_username",
    type=str,
    required=True,
    prompt="Last.fm username",
    help="Last.fm username.",
)
def authorize(
    spotify_client_id: str,
    spotify_client_secret: str,
    spotify_redirect_uri: str,
    lastfm_api_key: str,
    lastfm_api_secret: str,
    lastfm_username: str,
) -> None:
    """TODO: Docstrings."""
    # Spotify
    spotify_client = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            scope=SPOTIPY_SCOPES,
            cache_handler=spotipy.CacheFileHandler(
                cache_path=SPOTIPY_CACHE_PATH,
            ),
        ),
    )

    # Test request
    spotify_client.me()

    # Last.fm
    lastfm_api = pylast.LastFMNetwork(
        api_key=lastfm_api_key,
        api_secret=lastfm_api_secret,
    )

    # Test request
    lastfm_user = lastfm_api.get_user(lastfm_username)
    lastfm_user.get_name(True)

    # Save config to disk
    config = MusicSnapshotConfig(
        # Spotipy has its own caching logic, but doesn't actually save the `client_id`,
        # `client_secret` and `redirect_uri` values there, even though it *does*
        # require them to initialize the API client (so you need to explicitly provide
        # it each time). I feel like that would provide bad user experience, so I
        # 'cache' them separately.
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret,
        spotify_redirect_uri=spotify_redirect_uri,
        lastfm_api_key=lastfm_api_key,
        lastfm_api_secret=lastfm_api_secret,
        lastfm_username=lastfm_username,
    )
    config.save_to_disk(MUSIC_SNAPSHOT_CONFIG_PATH)

    rich_console.print(
        Markdown(
            f"Successfully saved config in in `{MUSIC_SNAPSHOT_CONFIG_PATH}`.",
            style="green",
        )
    )


@cli.command()
@click.pass_obj
def create(obj: MusicSnapshotContext) -> None:
    """TODO: Docstrings."""
    now = datetime.now(UTC)
    today = now.date()
    page_size = 10

    # Start date
    message = "Select snapshot start date:"
    date_choices = [(today - timedelta(days=n)).isoformat() for n in range(9)]
    start_date_str = questionary.select(message, date_choices + ["Other"]).ask()

    if start_date_str == "Other":
        message = "Input date in ISO format:"
        start_date_str = questionary.text(message, validate=validate_date).ask()

    if start_date_str is None:
        raise click.ClickException("You need to provide a start date.")

    start_date = date.fromisoformat(start_date_str)

    # Start time
    message = "Select snapshot (estimated) start time:"
    time_choices = [
        (datetime.combine(today, time(7)) + timedelta(hours=2 * n)).time().isoformat()
        for n in range(9)
    ]
    start_time_str = questionary.select(message, time_choices + ["Other"]).ask()

    if start_time_str == "Other":
        message = "Input time in ISO format:"
        start_time_str = questionary.text(message, validate=validate_time).ask()

    if start_time_str is None:
        raise click.ClickException("You need to provide a start time.")

    start_time = time.fromisoformat(start_time_str)

    # Combine start date and start time
    start_datetime = datetime.combine(start_date, start_time)
    start_datetime = start_datetime.astimezone()  # Local timezone
    start_datetime -= timedelta(minutes=60)  # Small buffer

    if start_datetime >= now:
        raise click.ClickException("Start date can't be in the future.")

    # Get song candidates from Last.fm history
    time_from = int(start_datetime.timestamp())
    # For some reason, nothing is returned without the `time_to` parameter set
    time_to = int((start_datetime + timedelta(days=2)).timestamp())

    lastfm_user = obj.lastfm_api.get_user(obj.config.lastfm_username)
    song_candidates = lastfm_user.get_recent_tracks(
        limit=500,
        time_from=time_from,
        time_to=time_to,
    )
    # Even though we use the `from` filtering, the song list is still 'newest first'
    song_candidates.reverse()

    if len(song_candidates) == 0:
        raise click.ClickException("No song candidates found.")

    # Select first track
    selected_first_track = select_track(
        tracks=song_candidates,
        page_size=page_size,
        select_message="Select first song:",
    )
    if not selected_first_track:
        raise click.ClickException("You need to select the first track.")

    first_song_n, first_song = (
        selected_first_track["n"],
        selected_first_track["played_track"],
    )

    # Try to guess the end track
    guessed_track = guess_end_track(
        tracks=song_candidates,
        first_track_n=first_song_n,
    )

    # Select last song (while trying to default to the guessed value)
    page = int(guessed_track["n"] / page_size) if guessed_track else 0
    default_choice = guessed_track if guessed_track else None
    selected_last_track = select_track(
        tracks=song_candidates,
        default_choice=dict(default_choice) if default_choice else None,  # For mypy
        page=page,
        page_size=page_size,
        select_message="Select last song:",
    )
    if not selected_last_track:
        raise click.ClickException("You need to select the last track.")

    last_song_n, last_song = (
        selected_last_track["n"],
        selected_last_track["played_track"],
    )

    # Some validation
    first_song_played_at = datetime.fromtimestamp(int(first_song.timestamp), UTC)
    first_song_played_at = first_song_played_at.astimezone()  # Local timezone
    last_song_played_at = datetime.fromtimestamp(int(last_song.timestamp), UTC)
    last_song_played_at = last_song_played_at.astimezone()  # Local timezone

    if first_song_played_at >= last_song_played_at:
        raise click.ClickException("First track needs to be before the last track.")

    # Playlist name
    default_name = first_song_played_at.date().isoformat()

    message = "Playlist name:"
    snapshot_name = questionary.text(message, default=default_name).ask()

    if snapshot_name is None:
        raise click.ClickException("You need to input playlist name.")

    # Confirm action
    song_count = last_song_n - first_song_n + 1
    message = (
        f"Do you want to create playlist '{snapshot_name}' and add {song_count} "
        f"songs to it?"
    )
    create_playlist = questionary.confirm(message).ask()

    if not create_playlist:
        raise click.ClickException("The playlist was not created.")

    # Create playlist
    spotify_user = obj.spotify_api.me()
    spotify_user_id = spotify_user["id"]

    songs_to_add = song_candidates[first_song_n : last_song_n + 1]

    # For some reason, line breaks aren't supported in the playlist description
    description = f"🎵 📸 | {first_song_played_at.strftime(DATETIME_FORMAT)} - "
    if first_song_played_at.date() == last_song_played_at.date():
        description += f"{last_song_played_at.strftime(TIME_FORMAT)}"
    else:
        description += f"{last_song_played_at.strftime(DATETIME_FORMAT)}"

    # Unfortunately, Spotify API doesn't allow creating truly private playlists
    # through the API. See:
    # - https://github.com/spotipy-dev/spotipy/issues/879
    # - https://community.spotify.com/t5/Spotify-for-Developers/Api-to-create-a-private-playlist-doesn-t-work/m-p/5407807#M5076
    public = False

    try:
        playlist = obj.spotify_api.user_playlist_create(
            user=spotify_user_id,
            name=snapshot_name,
            description=description,
            public=public,
        )
    except SpotifyException as e:
        raise ClickException(f"Error when creating the playlist:\n{e}") from e

    rich_console.print(
        f"> Successfully created '{snapshot_name}'.",
        style="green",
    )

    # Add songs to playlist
    spotify_songs_to_add = []
    for played_track in rich_progress_bar(
        songs_to_add,
        description="> Working...",
        console=rich_console,
    ):
        try:
            spotify_song = lastfm_track_to_spotify(
                spotify_api=obj.spotify_api,
                track=played_track.track,
            )
        except ValueError as e:
            rich_console.print(f"> {e}", style="red")
        else:
            spotify_songs_to_add.append(spotify_song["id"])

    songs_chunks = chunks(spotify_songs_to_add, n=75)
    for song_chunk in songs_chunks:
        obj.spotify_api.playlist_add_items(
            playlist_id=playlist["id"],
            items=song_chunk,
        )

    rich_console.print(
        f"> Successfully added {len(spotify_songs_to_add)} songs to '{snapshot_name}'.",
        style="bold green",
    )

    playlist_url = playlist.get("external_urls", {}).get("spotify")
    if playlist_url:
        rich_console.print(
            f"> You can find it at: {playlist_url}",
            style="bold cyan",
        )
