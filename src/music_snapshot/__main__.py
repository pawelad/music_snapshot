"""Command line entrypoint for `music_snapshot`."""

import sys

from music_snapshot.cli import cli


def main(args: list[str] | None = None) -> None:
    """Click CLI entrypoint for `music_snapshot`.

    Arguments:
        args: CLI arguments.
    """
    cli.main(args, "music_snapshot")


if __name__ == "__main__":
    main(sys.argv[1:])
