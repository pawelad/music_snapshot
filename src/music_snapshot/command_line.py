"""music_snapshot command line interface."""

import dataclasses
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import click
import pylast
import questionary
import rich_click
import spotipy
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import track

from music_snapshot.config import MusicSnapshotConfig
from music_snapshot.utils import DefaultRichGroup, validate_date, validate_time

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
    rich_console.print("Authorize Spotify")
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

    # Select first song
    lastfm_user = obj.lastfm_api.get_user(obj.config.lastfm_username)

    # Without the `time_to` parameter set, the API seemed to default to now...
    # (which of course isn't mentioned anywhere in the API docs)
    end_datetime = start_datetime + timedelta(days=5)
    song_candidates = lastfm_user.get_recent_tracks(
        limit=500,
        time_from=int(start_datetime.timestamp()),
        time_to=int(end_datetime.timestamp()),
    )
    # Even though we use the `from` filtering, the song list is still 'newest first'
    song_candidates.reverse()

    if len(song_candidates) == 0:
        raise click.ClickException("No song candidates found.")

    page = 0
    page_size = 10
    first_song = None
    first_song_n = None
    while True:
        song_choices = []
        for n, played_track in enumerate(
            song_candidates[page * page_size : (page + 1) * page_size],
            start=page * page_size,
        ):
            played_at = datetime.fromtimestamp(int(played_track.timestamp), UTC)
            played_at = played_at.astimezone()  # Local timezone
            track_name = played_track.track.get_name()
            artist = played_track.track.get_artist().get_name()
            album = played_track.album

            title = [
                ("class:date", played_at.strftime("%Y-%m-%d")),
                ("", " "),
                ("class:time", played_at.strftime("%H:%M")),
                ("", " | "),
                ("class:track", track_name),
                ("", " by "),
                ("class:artist", artist),
                ("", " from "),
                ("class:album", album),
            ]
            song_choice = questionary.Choice(title, (n, played_track))
            song_choices.append(song_choice)

        if page > 0:
            song_choices = ["Previous"] + song_choices

        if (page + 1) * page_size < len(song_candidates):
            song_choices = song_choices + ["Next"]

        message = "Select first song:"
        selected_song = questionary.select(
            message,
            song_choices,
            style=QUESTIONARY_STYLE,
        ).ask()

        if selected_song == "Previous":
            page -= 1
            continue
        elif selected_song == "Next":
            page += 1
            continue
        elif selected_song is None:
            break
        else:
            first_song_n, first_song = selected_song
            break

    if first_song is None or first_song_n is None:
        raise click.ClickException("You need to select the first song.")

    # Try to guess the end song
    guess_last_song = None
    guess_last_song_n = page
    for n, played_track in enumerate(
        song_candidates[first_song_n:],
        start=first_song_n,
    ):
        track_played_at = datetime.fromtimestamp(int(played_track.timestamp), UTC)

        try:
            next_track = song_candidates[n + 1]
        except KeyError:
            break

        next_track_played_at = datetime.fromtimestamp(int(next_track.timestamp), UTC)

        # If the difference between two songs is more then 60 minutes, the earlier
        # one could be the end song. We could also involve track duration into the
        # math, but this is easier for now.
        if (next_track_played_at - track_played_at) > timedelta(minutes=60):
            guess_last_song = (n, played_track)
            guess_last_song_n = n
            break

    # Select last song (while trying to default to the guessed value)
    page = int(guess_last_song_n / page_size)
    last_song = None
    last_song_n = None
    while True:
        song_choices = []
        for n, played_track in enumerate(
            song_candidates[page * page_size : (page + 1) * page_size],
            start=page * page_size,
        ):
            played_at = datetime.fromtimestamp(int(played_track.timestamp), UTC)
            played_at = played_at.astimezone()  # Local timezone
            track_name = played_track.track.get_name()
            artist = played_track.track.get_artist().get_name()
            album = played_track.album

            title = [
                ("class:date", played_at.strftime("%Y-%m-%d")),
                ("", " "),
                ("class:time", played_at.strftime("%H:%M")),
                ("", " | "),
                ("class:track", track_name),
                ("", " by "),
                ("class:artist", artist),
                ("", " from "),
                ("class:album", album),
            ]
            song_choice = questionary.Choice(title, (n, played_track))
            song_choices.append(song_choice)

        if page > 0:
            song_choices = ["Previous"] + song_choices

        if (page + 1) * page_size < len(song_candidates):
            song_choices = song_choices + ["Next"]

        message = "Select last song:"
        selected_song = questionary.select(
            message,
            song_choices,
            default=guess_last_song,
            style=QUESTIONARY_STYLE,
        ).ask()

        if selected_song == "Previous":
            page -= 1
            guess_last_song = None
            continue
        elif selected_song == "Next":
            page += 1
            guess_last_song = None
            continue
        elif selected_song is None:
            break
        else:
            last_song_n, last_song = selected_song
            break

    if last_song is None or last_song_n is None:
        raise click.ClickException("You need to select a last song.")

    # Playlist name
    first_song_played_at = datetime.fromtimestamp(int(first_song.timestamp), UTC)
    first_song_played_at = first_song_played_at.astimezone()  # Local timezone

    message = "Playlist name:"
    default_name = first_song_played_at.date().isoformat()
    snapshot_name = questionary.text(message, default=default_name).ask()

    if snapshot_name is None:
        raise click.ClickException("You need to input playlist name.")

    # Create playlist
    spotify_user = obj.spotify_api.me()
    spotify_user_id = spotify_user["id"]

    # Unfortunately, Spotify API doesn't allow creating truly private playlists
    # through the API. See:
    # - https://github.com/spotipy-dev/spotipy/issues/879
    # - https://community.spotify.com/t5/Spotify-for-Developers/Api-to-create-a-private-playlist-doesn-t-work/m-p/5407807#M5076
    playlist = obj.spotify_api.user_playlist_create(
        user=spotify_user_id,
        name=snapshot_name,
        description="🎵 📸",
        public=False,
    )
    playlist_id = playlist["id"]

    # Add songs to playlist
    songs_to_add = []
    for played_track in track(
        song_candidates[first_song_n : last_song_n + 1],
        console=rich_console,
    ):
        artist = played_track.track.get_artist().get_name()

        track_name = played_track.track.get_name()
        # Last.fm and Spotify naming conventions sometimes differ, so it's safer
        # to remove some of the extra suffixes
        for suffix in ["(ft", "(feat", "ft", "feat"]:
            track_name = track_name.split(suffix)[0]

        # Using `album:` for some reason doesn't work with singles
        q = f"artist:{artist} track:{track_name}"
        spotify_search_results = obj.spotify_api.search(q=q, limit=1, type="track")
        results = spotify_search_results["tracks"]["items"]

        # TODO: Error handling?
        if len(results) == 0:
            rich_console.print(f"Couldn't find a match for track: {track_name}")
            rich_console.print(spotify_search_results)
        else:
            spotify_song = results[0]
            spotify_song_id = spotify_song["id"]

            songs_to_add.append(spotify_song_id)

    obj.spotify_api.playlist_add_items(
        playlist_id=playlist_id,
        items=songs_to_add,
    )

    rich_console.print(
        Markdown(
            f"Successfully added {len(songs_to_add)} songs to `{snapshot_name}`.",
            style="green",
        )
    )
