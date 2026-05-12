from __future__ import annotations

import pytest

from shrutilens.packs import load_pack_dir


@pytest.fixture
def packs():
    return load_pack_dir()
