"""Config related code."""

import dataclasses
import json
import os
import sys
from functools import partial
from pathlib import Path

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


@dataclasses.dataclass
class MusicSnapshotConfig:
    """Config schema for `music_snapshot`.

    Attributes:
        spotify_client_id: Spotify OAuth client ID.
        spotify_client_secret: Spotify OAuth client secret.
        spotify_redirect_uri: Spotify OAuth redirect URI.
        lastfm_api_key: Last.fm API key.
        lastfm_api_secret: Last.fm API secret.
        lastfm_username: Last.fm username.
    """

    # Spotify
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None
    spotify_redirect_uri: str | None = None

    # Last.fm
    lastfm_api_key: str | None = None
    lastfm_api_secret: str | None = None
    lastfm_username: str | None = None

    @classmethod
    def load_from_disk(cls, config_path: Path | str) -> Self:
        """Load `music_snapshot` config from disk.

        Arguments:
            config_path: Config file path.

        Returns:
            Loaded music_snapshot config.
        """
        with open(config_path) as f:
            config = json.load(f)

        return cls(**config)

    def save_to_disk(self, config_path: Path | str) -> None:
        """Save `music_snapshot` config to disk.

        Arguments:
            config_path: Config file path.
        """
        # Make sure the file is not publicly accessible
        # Source: https://github.com/python/cpython/issues/73400
        os.umask(0o077)
        with open(config_path, "w", opener=partial(os.open, mode=0o600)) as f:
            f.write(json.dumps(dataclasses.asdict(self), indent=2))
