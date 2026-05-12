from __future__ import annotations

from pathlib import Path

import pytest

from shrutilens import runner as _runner
from shrutilens.packs import load_pack


PACK_ROOT = Path(__file__).resolve().parents[2] / "shrutilens" / "packs"


@pytest.fixture
def runner():
    return _runner


@pytest.fixture
def loader():
    from types import SimpleNamespace
    return SimpleNamespace(load=load_pack)


@pytest.fixture
def phq9_pack():
    return load_pack(PACK_ROOT / "phq9.yaml")


@pytest.fixture
def market_pack():
    return load_pack(PACK_ROOT / "market_discovery.yaml")
