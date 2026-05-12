from __future__ import annotations

from shrutilens.models import AssessmentPack, BranchRule, NormalizedResponse
from shrutilens.packs import COMPLETE


def next_item_id(
    pack: AssessmentPack, current_item_id: str, responses: dict[str, NormalizedResponse]
) -> str | None:
    for branch in pack.branches:
        if branch.item_id != current_item_id:
            continue
        response = responses.get(branch.item_id)
        if response is not None and _matches(branch, response):
            return None if branch.goto == COMPLETE else branch.goto

    ids = [item.id for item in pack.items]
    index = ids.index(current_item_id)
    return ids[index + 1] if index + 1 < len(ids) else None


def _matches(branch: BranchRule, response: NormalizedResponse) -> bool:
    actual = response.anchor_id if response.anchor_id is not None else response.value
    expected = branch.value
    op = branch.operator

    if op == "equals":
        return actual == expected
    if op == "not_equals":
        return actual != expected
    if op == "in":
        return actual in expected if isinstance(expected, list) else False

    if not isinstance(actual, int | float) or not isinstance(expected, int | float):
        return False
    if op == "gte":
        return actual >= expected
    if op == "lte":
        return actual <= expected
    if op == "gt":
        return actual > expected
    if op == "lt":
        return actual < expected
    return False
