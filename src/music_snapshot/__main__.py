"""Command line entrypoint for `music_snapshot`."""
import multiprocessing
import sys

from music_snapshot.cli import cli

# A SemLock created in a fork context is being shared with a process in a
# spawn context. This is not supported.
#
# A SemLock created in a fork context is being shared with a process in a
# spawn context. This is not supported.
#
# See: https://github.com/zauberzeug/nicegui/issues/2195
if multiprocessing.get_start_method(allow_none=True) is None:
    multiprocessing.set_start_method("spawn")


def main(args: list[str] | None = None) -> None:
    """Click CLI entrypoint for `music_snapshot`.

    Arguments:
        args: CLI arguments.
    """
    cli.main(args, "music_snapshot")


if __name__ == "__main__":
    main(sys.argv[1:])
