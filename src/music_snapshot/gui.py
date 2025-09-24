import dataclasses
from datetime import datetime, time, timedelta
import pylast
import spotipy
from nicegui import app, ui
from .config import MusicSnapshotConfig
from .cli import MUSIC_SNAPSHOT_CONFIG_PATH, SPOTIPY_SCOPES, SPOTIPY_CACHE_PATH
from .tracks import lastfm_track_to_spotify

@dataclasses.dataclass
class GuiTrack:
    """A track displayed in the GUI."""
    name: str
    artist: str
    album: str
    cover_url: str
    played_at: str
    played_track: pylast.PlayedTrack

@ui.page('/')
def main_page():
    """The main page of the Music Snapshot GUI."""
    # Font Awesome
    ui.add_head_html('<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.1/css/all.min.css" rel="stylesheet" />')

    # Header
    with ui.header(elevated=True).classes('flex justify-between text-h4'):
        ui.label('Music Snapshot').classes('bold')

        # Settings modal
        config = MusicSnapshotConfig()
        with ui.dialog() as dialog, ui.card():
            def load_config():
                try:
                    loaded_config = MusicSnapshotConfig.load_from_disk(MUSIC_SNAPSHOT_CONFIG_PATH)
                    config.spotify_client_id = loaded_config.spotify_client_id
                    config.spotify_client_secret = loaded_config.spotify_client_secret
                    config.lastfm_api_key = loaded_config.lastfm_api_key
                    config.lastfm_api_secret = loaded_config.lastfm_api_secret
                    config.lastfm_username = loaded_config.lastfm_username
                except FileNotFoundError:
                    pass  # Config file doesn't exist yet

            def save_config():
                config.save_to_disk(MUSIC_SNAPSHOT_CONFIG_PATH)
                ui.notify("Settings saved!", color="positive")
                dialog.close()

            dialog.on('before-show', load_config)

            # Spotify config
            with ui.card().classes('w-[500px]'):
                with ui.element('q-item').classes('text-h5'):
                    with ui.element('q-item-section').props('avatar'):
                        ui.avatar('fa fa-brands fa-spotify', color="green")

                    with ui.element('q-item-section'):
                        ui.label('Spotify')

                with ui.card_section().classes('w-full pt-0'):
                    spotify_client_id = ui.input(label='Spotify Client ID').bind_value(config, 'spotify_client_id')
                    spotify_client_secret = ui.input(label='Spotify Client Secret', password=True).bind_value(config, 'spotify_client_secret')

            # Last.fm config
            with ui.card().classes('w-[500px]'):
                with ui.element('q-item').classes('text-h5'):
                    with ui.element('q-item-section').props('avatar'):
                        ui.avatar('fa fa-brands fa-lastfm', color="pink")

                    with ui.element('q-item-section'):
                        ui.label('Last.fm')
                with ui.card_section().classes('w-full pt-0'):
                    lastfm_api_key = ui.input(label='Last.fm API Key').bind_value(config, 'lastfm_api_key')
                    lastfm_api_secret = ui.input(label='Last.fm API Secret', password=True).bind_value(config, 'lastfm_api_secret')
                    lastfm_username = ui.input(label='Last.fm username').bind_value(config, 'lastfm_username')

            with ui.row().classes('w-full justify-end'):
                ui.button('Close', on_click=dialog.close)
                ui.button('Save', on_click=save_config)

        ui.button(icon='settings', color='secondary', on_click=dialog.open).props('round')

    with ui.row().classes("w-[600px] self-center"):
        with ui.card().classes('w-full'):
            ui.label("Select start date and time").classes('text-h5')

            with ui.input('Start date').classes("w-full") as start_date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(start_date):
                        with ui.row().classes('justify-end'):
                            ui.button('Close', on_click=menu.close).props('flat')
                with start_date.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            with ui.input('Start time').classes("w-full") as start_time:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.time().bind_value(start_time):
                        with ui.row().classes('justify-end'):
                            ui.button('Close', on_click=menu.close).props('flat')
                with start_time.add_slot('append'):
                    ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')

            async def load_tracks():
                try:
                    config = MusicSnapshotConfig.load_from_disk(MUSIC_SNAPSHOT_CONFIG_PATH)
                except FileNotFoundError:
                    ui.notify("Settings not found. Please configure the application first.", color="negative")
                    return

                try:
                    lastfm_api = pylast.LastFMNetwork(
                        api_key=config.lastfm_api_key,
                        api_secret=config.lastfm_api_secret,
                    )
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
                except Exception as e:
                    ui.notify(f"Error initializing API clients: {e}", color="negative")
                    return

                if not start_date.value or not start_time.value:
                    ui.notify("Please select a start date and time.", color="negative")
                    return

                try:
                    start_datetime = datetime.combine(datetime.fromisoformat(start_date.value).date(), time.fromisoformat(start_time.value))
                    time_from = int(start_datetime.timestamp())
                    time_to = int((start_datetime + timedelta(days=2)).timestamp())

                    lastfm_user = lastfm_api.get_user(config.lastfm_username)
                    track_candidates = lastfm_user.get_recent_tracks(
                        limit=500,
                        time_from=time_from,
                        time_to=time_to,
                    )
                    track_candidates.reverse()

                    gui_tracks = []
                    for played_track in track_candidates:
                        track = played_track.track
                        cover_url = track.get_cover_image()
                        if not cover_url:
                            # Use a placeholder image if no cover art is available
                            cover_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

                        gui_tracks.append(GuiTrack(
                            name=track.get_name(),
                            artist=track.get_artist().get_name(),
                            album=played_track.album,
                            cover_url=cover_url,
                            played_at=datetime.fromtimestamp(int(played_track.timestamp)).strftime("%Y-%m-%d %H:%M:%S"),
                            played_track=played_track,
                        ))

                    app.storage.user['tracks'] = gui_tracks
                    ui.notify(f"Loaded {len(gui_tracks)} tracks.", color="positive")
                    app.storage.user['update_track_grid']()

                except Exception as e:
                    ui.notify(f"Error loading tracks: {e}", color="negative")

            with ui.row().classes('w-full justify-end'):
                ui.button('Load tracks', on_click=load_tracks)

        with ui.card().classes('w-full'):
            ui.label("Select first track").classes('text-h5')
            track_grid = ui.grid(columns=2).classes('w-full')

            def update_track_grid():
                track_grid.clear()
                with track_grid:
                    for track in app.storage.user.get('tracks', []):
                        with ui.card().on('click', lambda track=track: handle_track_click(track)):
                            ui.image(track.cover_url).classes('w-full')
                            with ui.card_section():
                                ui.label(track.name).classes('text-subtitle2')
                                ui.label(track.artist).classes('text-caption')
                                ui.label(track.album).classes('text-caption')
                                ui.label(track.played_at).classes('text-caption')

            app.storage.user['update_track_grid'] = update_track_grid

        app.storage.user['selecting_start_track'] = True
        app.storage.user['start_track'] = None
        app.storage.user['end_track'] = None

        with ui.card().classes('w-full'):
            ui.label("Selection").classes('text-h5')
            start_track_label = ui.label("Start track: ")
            end_track_label = ui.label("End track: ")

            def clear_selection():
                app.storage.user['start_track'] = None
                app.storage.user['end_track'] = None
                app.storage.user['selecting_start_track'] = True
                start_track_label.text = "Start track: "
                end_track_label.text = "End track: "
                ui.notify("Selection cleared.")

            ui.button("Clear Selection", on_click=clear_selection)

        def handle_track_click(track: GuiTrack):
            if app.storage.user['selecting_start_track']:
                app.storage.user['start_track'] = track
                start_track_label.text = f"Start track: {track.name}"
                ui.notify(f"Selected start track: {track.name}")
                app.storage.user['selecting_start_track'] = False
            else:
                app.storage.user['end_track'] = track
                end_track_label.text = f"End track: {track.name}"
                ui.notify(f"Selected end track: {track.name}")

        with ui.card().classes('w-full'):
            ui.label("Create Playlist").classes('text-h5')
            playlist_name = ui.input("Playlist name")

            async def create_playlist():
                start_track = app.storage.user.get('start_track')
                end_track = app.storage.user.get('end_track')
                tracks = app.storage.user.get('tracks', [])

                if not start_track or not end_track:
                    ui.notify("Please select a start and end track.", color="negative")
                    return

                if not playlist_name.value:
                    ui.notify("Please enter a playlist name.", color="negative")
                    return

                try:
                    config = MusicSnapshotConfig.load_from_disk(MUSIC_SNAPSHOT_CONFIG_PATH)
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

                    start_index = tracks.index(start_track)
                    end_index = tracks.index(end_track)

                    if start_index > end_index:
                        ui.notify("Start track must be before end track.", color="negative")
                        return

                    tracks_to_add = tracks[start_index : end_index + 1]

                    spotify_user = spotify_api.me()
                    spotify_user_id = spotify_user["id"]

                    playlist = spotify_api.user_playlist_create(
                        user=spotify_user_id,
                        name=playlist_name.value,
                        public=False,
                    )

                    spotify_songs_to_add = []
                    for track in tracks_to_add:
                        try:
                            spotify_song = lastfm_track_to_spotify(
                                spotify_api=spotify_api,
                                track=track.played_track.track,
                            )
                            spotify_songs_to_add.append(spotify_song["id"])
                        except ValueError as e:
                            ui.notify(str(e), color="negative")

                    spotify_api.playlist_add_items(
                        playlist_id=playlist["id"],
                        items=spotify_songs_to_add,
                    )

                    ui.notify(f"Playlist '{playlist_name.value}' created successfully!", color="positive")

                except Exception as e:
                    ui.notify(f"Error creating playlist: {e}", color="negative")

            create_playlist_button = ui.button("Create Playlist", on_click=create_playlist)
            create_playlist_button.bind_enabled_from(app.storage.user, 'start_track', lambda val: val is not None and app.storage.user.get('end_track') is not None)
            create_playlist_button.bind_enabled_from(app.storage.user, 'end_track', lambda val: val is not None and app.storage.user.get('start_track') is not None)
