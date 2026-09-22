import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class K6Runner:
    def __init__(self, executable: str = "k6") -> None:
        self.executable = executable

    def run(self, script_path: Path, result_path: Path) -> dict[str, Any]:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            completed = subprocess.run(
                [self.executable, "run", "--out", f"json={result_path}", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("k6 is not installed or not on PATH") from exc
        if completed.returncode != 0:
            raise RuntimeError(f"k6 failed: {completed.stderr.strip() or completed.stdout.strip()}")
        return parse_k6_json(result_path)


def parse_k6_json(path: Path) -> dict[str, Any]:
    durations: list[float] = []
    failed = 0
    timestamps: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        point = json.loads(line)
        if point.get("type") != "Point":
            continue
        metric = point.get("metric")
        data = point.get("data", {})
        if data.get("time"):
            timestamps.append(_timestamp_ms(data["time"]))
        if metric == "http_req_duration":
            durations.append(float(data["value"]))
        elif metric == "http_req_failed" and float(data["value"]) == 1:
            failed += 1
    if not durations or len(timestamps) < 2:
        raise ValueError("k6 result is empty or missing timing data")
    elapsed_seconds = (max(timestamps) - min(timestamps)) / 1000
    return {"durations_ms": durations, "failed_requests": failed, "elapsed_seconds": elapsed_seconds}


def _timestamp_ms(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000