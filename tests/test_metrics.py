import pytest

from app.metrics import calculate_metrics, evaluate_thresholds
from app.models import Thresholds


def test_metrics_are_calculated_deterministically():
    metrics = calculate_metrics([100, 200, 300, 400, 500], 1, 2)
    assert metrics.p50_ms == 300
    assert metrics.p95_ms == 480
    assert metrics.p99_ms == 496
    assert metrics.throughput_rps == 2.5
    assert metrics.error_rate == 0.2


def test_thresholds_use_program_calculated_values():
    metrics = calculate_metrics([100, 200, 300], 0, 1)
    result = evaluate_thresholds(metrics, Thresholds(p95_ms=200, error_rate=0))
    assert result.p95 == "FAIL"
    assert result.error_rate == "PASS"


def test_empty_metrics_are_rejected():
    with pytest.raises(ValueError):
        calculate_metrics([], 0, 1)