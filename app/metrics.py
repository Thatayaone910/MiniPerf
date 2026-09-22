from collections.abc import Iterable

from .models import Metrics, ThresholdResults, Thresholds


def percentile(values: Iterable[float], percentage: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("at least one latency value is required")
    position = (len(ordered) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 2)


def calculate_metrics(
    durations_ms: Iterable[float], failed_requests: int, elapsed_seconds: float
) -> Metrics:
    durations = list(durations_ms)
    if not durations or elapsed_seconds <= 0:
        raise ValueError("k6 result must contain requests and a positive duration")
    if failed_requests < 0 or failed_requests > len(durations):
        raise ValueError("failed request count is invalid")
    return Metrics(
        p50_ms=percentile(durations, 50),
        p95_ms=percentile(durations, 95),
        p99_ms=percentile(durations, 99),
        throughput_rps=round(len(durations) / elapsed_seconds, 2),
        error_rate=round(failed_requests / len(durations), 4),
    )


def evaluate_thresholds(metrics: Metrics, thresholds: Thresholds) -> ThresholdResults:
    return ThresholdResults(
        p95="PASS" if metrics.p95_ms <= thresholds.p95_ms else "FAIL",
        error_rate="PASS" if metrics.error_rate <= thresholds.error_rate else "FAIL",
    )