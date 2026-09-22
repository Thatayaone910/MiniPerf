import pytest

from app.performance.k6_runner import K6Runner


def test_missing_k6_is_reported_clearly(tmp_path):
    with pytest.raises(RuntimeError, match="not installed"):
        K6Runner("definitely-not-k6").run(tmp_path / "test.js", tmp_path / "result.jsonl")