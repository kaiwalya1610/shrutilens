from __future__ import annotations

from pathlib import Path

import pytest

from shrutilens.core.runner import build_default_runner
from shrutilens.packs.loader import PackRepository


@pytest.fixture
def pack_repository() -> PackRepository:
    return PackRepository()


@pytest.fixture
def runner(tmp_path: Path):
    return build_default_runner(tmp_path / "data", tmp_path / "exports")
