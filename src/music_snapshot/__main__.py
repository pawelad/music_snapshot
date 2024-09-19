"""Command line entrypoint for music_snapshot."""

import sys
from typing import List, Optional

from music_snapshot.command_line import cli


def main(args: Optional[List[str]] = None) -> None:
    """Run `music_snapshot`.

    Arguments:
        args: CLI arguments.
    """
    cli.main(args, "music_snapshot")


if __name__ == "__main__":
    main(sys.argv[1:])
