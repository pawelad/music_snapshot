"""music_snapshot pytest configuration and utils."""

import pytest
from click.testing import CliRunner


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Return a `CliRunner` instance."""
    return CliRunner()
