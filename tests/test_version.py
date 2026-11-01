import re
from pathlib import Path

from version import __version__


def test_version_matches_pyproject():
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    assert re.search(r'^version = "(.+)"', pyproject, re.M).group(1) == __version__
