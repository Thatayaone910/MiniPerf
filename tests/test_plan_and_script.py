import pytest

from app.ai.service import AIService
from app.models import TestRequest as RequestModel
from app.script_generator import generate_k6_script


class FakeProvider:
    def generate_plan(self, request):
        return {
            "test_type": "load", "api_url": request["api_url"], "method": request["method"],
            "virtual_users": request["virtual_users"], "duration_seconds": request["duration_seconds"],
            "thresholds": {"p95_ms": request["max_p95_ms"], "error_rate": request["max_error_rate"]},
            "rationale": "A simple load test.",
        }

    def analyze_results(self, evidence):
        return {"summary": "Passed.", "observations": ["Evidence is within limits."], "investigation_areas": []}


def request():
    return RequestModel(
        api_url="http://localhost:8000/users", method="GET", virtual_users=5,
        duration_seconds=2, max_p95_ms=1000, max_error_rate=0.01,
    )


def test_plan_is_validated_and_preserves_user_values():
    plan = AIService(FakeProvider()).create_plan(request())
    assert plan.virtual_users == 5
    assert plan.thresholds.error_rate == 0.01


def test_ai_cannot_change_user_values():
    class ChangingProvider(FakeProvider):
        def generate_plan(self, data):
            result = super().generate_plan(data)
            result["virtual_users"] = 99
            return result

    with pytest.raises(ValueError, match="changed"):
        AIService(ChangingProvider()).create_plan(request())


def test_ai_analysis_is_validated_from_evidence():
    analysis = AIService(FakeProvider()).analyze({"metrics": {"p95_ms": 200}})
    assert analysis.summary == "Passed."
    assert analysis.investigation_areas == []


def test_k6_script_contains_request_and_thresholds():
    script = generate_k6_script(AIService(FakeProvider()).create_plan(request()))
    assert 'http.request("GET", "http://localhost:8000/users")' in script
    assert 'p(95)<1000.0' in script
    assert 'rate<0.01' in script