import shutil
from pathlib import Path

import pytest

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"


@pytest.fixture
def deck_copy(tmp_path):
    """A writable copy of the sample deck, so tests never mutate the fixture."""
    dest = tmp_path / "sample_deck"
    shutil.copytree(SAMPLE_DECK, dest)
    return dest
