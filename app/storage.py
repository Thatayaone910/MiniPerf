from __future__ import annotations

import json
from pathlib import Path

from .models import TestResult


class ResultStore:
    def __init__(self, path: Path = Path("results/tests.json")) -> None:
        self.path = path

    def save(self, result: TestResult) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        results = self._read()
        results.append(result.model_dump(mode="json"))
        self.path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    def list(self) -> list[dict]:
        return self._read()

    def get(self, test_id: str) -> dict | None:
        return next((item for item in self._read() if item["test_id"] == test_id), None)

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))