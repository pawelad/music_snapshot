"""Test `music_snapshot.cli` module."""

from click.testing import CliRunner

from music_snapshot import __version__
from music_snapshot.cli import cli


def test_cli_version(cli_runner: CliRunner) -> None:
    """Outputs app version."""
    result = cli_runner.invoke(cli, args=["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
