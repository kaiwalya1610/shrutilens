from __future__ import annotations

import pytest

from shrutilens.packs import PackError


def test_loads_yaml_and_validates_clinical_pack(loader, phq9_pack):
    assert phq9_pack.id == "phq9"
    assert phq9_pack.mode == "clinical_locked"
    assert len(phq9_pack.items) == 9
    assert all(item.locked_wording for item in phq9_pack.items)


def test_loads_research_pack_with_branch(loader, market_pack):
    assert market_pack.id == "market_discovery"
    assert market_pack.branches[0].goto == "current_solution"
    assert market_pack.policy.adaptive_followup_allowed is True


def test_missing_pack_raises_loader_error(loader, tmp_path):
    with pytest.raises(PackError):
        loader.load(tmp_path / "missing.yaml")


def test_invalid_clinical_unlocked_wording_raises(loader, tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
id: bad
version: 0.1.0
title: Bad
mode: clinical_locked
items:
  - id: item_1
    text: Hi
    response_type: open_text
    locked_wording: false
"""
    )
    with pytest.raises(PackError):
        loader.load(path)
