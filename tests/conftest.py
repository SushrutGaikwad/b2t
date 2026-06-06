import shutil
from pathlib import Path

import pytest

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"

# Build files shipped with the sample deck; the workflow accepts decks with
# build artifacts, and clean_build must delete exactly these.
FIXTURE_BUILD_FILES = {
    "main.aux",
    "main.fdb_latexmk",
    "main.fls",
    "main.log",
    "main.nav",
    "main.out",
    "main.snm",
    "main.synctex.gz",
    "main.toc",
}


@pytest.fixture
def deck_copy(tmp_path):
    """A writable copy of the sample deck, so tests never mutate the fixture."""
    dest = tmp_path / "sample_deck"
    shutil.copytree(SAMPLE_DECK, dest)
    return dest
