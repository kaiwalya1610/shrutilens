from __future__ import annotations

import json
from pathlib import Path

from shrutilens.core.contracts import AssessmentPack


PACK_DIR = Path(__file__).resolve().parent


class PackNotFoundError(KeyError):
    pass


class PackRepository:
    def __init__(self, pack_dir: Path = PACK_DIR) -> None:
        self.pack_dir = pack_dir
        self._cache: dict[str, AssessmentPack] = {}

    def list_packs(self) -> list[AssessmentPack]:
        return [self._load_file(path) for path in sorted(self.pack_dir.glob("*.json"))]

    def get(self, pack_id: str) -> AssessmentPack:
        if pack_id in self._cache:
            return self._cache[pack_id]
        path = self.pack_dir / f"{pack_id}.json"
        try:
            pack = self._load_file(path)
        except FileNotFoundError:
            raise PackNotFoundError(pack_id)
        self._cache[pack_id] = pack
        return pack

    def _load_file(self, path: Path) -> AssessmentPack:
        return AssessmentPack.model_validate(json.loads(path.read_text()))
