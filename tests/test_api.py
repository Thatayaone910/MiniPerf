from pathlib import Path

from fastapi.testclient import TestClient

from app.ai.service import AIService
from app.main import app, get_ai_service, get_runner, get_store
from app.storage import ResultStore


class FakeProvider:
    def generate_plan(self, request):
        return {
            "test_type": "load", "api_url": request["api_url"], "method": request["method"],
            "virtual_users": request["virtual_users"], "duration_seconds": request["duration_seconds"],
            "thresholds": {"p95_ms": request["max_p95_ms"], "error_rate": request["max_error_rate"]},
            "rationale": "Local test.",
        }

    def analyze_results(self, evidence):
        assert "metrics" in evidence
        return {"summary": "The test passed.", "observations": ["Latency met the limit."], "investigation_areas": []}


class FakeRunner:
    def run(self, script_path, result_path):
        assert Path(script_path).exists()
        return {"durations_ms": [100, 200, 300], "failed_requests": 0, "elapsed_seconds": 1}


def test_create_and_read_test(tmp_path):
    app.dependency_overrides[get_ai_service] = lambda: AIService(FakeProvider())
    app.dependency_overrides[get_runner] = FakeRunner
    app.dependency_overrides[get_store] = lambda: ResultStore(tmp_path / "tests.json")
    client = TestClient(app)
    payload = {"api_url": "http://localhost:8000/users", "method": "GET", "virtual_users": 2,
               "duration_seconds": 1, "max_p95_ms": 500, "max_error_rate": 0.01}
    response = client.post("/tests", json=payload)
    assert response.status_code == 201
    test_id = response.json()["test_id"]
    assert response.json()["threshold_results"] == {"p95": "PASS", "error_rate": "PASS"}
    assert client.get("/tests").status_code == 200
    assert client.get(f"/tests/{test_id}").status_code == 200
    assert client.get("/tests/missing").status_code == 404
    app.dependency_overrides.clear()