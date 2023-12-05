from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def data_dir():
    yield Path(__file__).parent / "data"
