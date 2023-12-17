from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def data_dir():
    yield Path(__file__).parent / "data"


@pytest.fixture
def mock_config(monkeypatch):
    def wrapper(config):
        monkeypatch.setattr(
            "styled_prose.config.load_config",
            lambda _: config,
        )

    yield wrapper
