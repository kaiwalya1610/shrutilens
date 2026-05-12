from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

from shrutilens.models import AssessmentMode, AssessmentPack, ResponseType


PACK_DIR = Path(__file__).resolve().parent / "packs"
COMPLETE = "__complete__"


class PackError(Exception):
    pass


class PackNotFoundError(PackError):
    pass


def load_pack(path: str | Path) -> AssessmentPack:
    pack_path = Path(path)
    if not pack_path.exists():
        raise PackNotFoundError(f"pack file not found: {pack_path}")

    raw = pack_path.read_text()
    suffix = pack_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
    elif suffix == ".json":
        data = json.loads(raw)
    else:
        raise PackError(f"unsupported pack format: {pack_path.suffix}")

    return validate_pack(AssessmentPack.model_validate(data))


def load_pack_dir(root: str | Path = PACK_DIR) -> dict[str, AssessmentPack]:
    root_path = Path(root)
    paths = sorted(p for p in root_path.rglob("*") if p.suffix.lower() in {".yaml", ".yml", ".json"})
    return {pack.id: pack for pack in (load_pack(p) for p in paths)}


def validate_pack(pack: AssessmentPack) -> AssessmentPack:
    if not pack.items:
        raise PackError("pack must define at least one item")

    item_ids = [item.id for item in pack.items]
    duplicates = [i for i, c in Counter(item_ids).items() if c > 1]
    if duplicates:
        raise PackError(f"duplicate item ids: {', '.join(duplicates)}")

    item_id_set = set(item_ids)
    for item in pack.items:
        if item.response_type in {ResponseType.choice, ResponseType.multi_select, ResponseType.rating} and not item.anchors:
            raise PackError(f"{item.id} requires response anchors")
        if pack.mode == AssessmentMode.clinical_locked:
            if item.required and item.allow_skip:
                raise PackError(f"{item.id} cannot be both required and skippable in clinical_locked mode")
            if not item.locked_wording:
                raise PackError(f"{item.id} must use locked wording in clinical_locked mode")

    for branch in pack.branches:
        if branch.item_id not in item_id_set:
            raise PackError(f"branch {branch.id} references missing item {branch.item_id}")
        if branch.goto != COMPLETE and branch.goto not in item_id_set:
            raise PackError(f"branch {branch.id} points to missing item {branch.goto}")

    for hook in pack.safety_hooks:
        if hook.item_id is not None and hook.item_id not in item_id_set:
            raise PackError(f"safety hook {hook.id} references missing item {hook.item_id}")
        if hook.kind == "anchor_match" and not hook.anchor_ids:
            raise PackError(f"safety hook {hook.id} needs anchor_ids")
        if hook.kind == "score_threshold" and hook.threshold is None:
            raise PackError(f"safety hook {hook.id} needs threshold")
        if hook.kind == "keyword" and not hook.keywords:
            raise PackError(f"safety hook {hook.id} needs keywords")

    return pack
