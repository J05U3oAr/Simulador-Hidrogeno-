from pathlib import Path

import pytest

from simulador.config import load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    return load_config(ROOT / "data/example.json")[0]
