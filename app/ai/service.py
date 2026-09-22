import json
import os
from typing import Any, Protocol

from ..models import Analysis, TestPlan, TestRequest


class AIProvider(Protocol):
    def generate_plan(self, request: dict[str, Any]) -> dict[str, Any]: ...

    def analyze_results(self, evidence: dict[str, Any]) -> dict[str, Any]: ...


class GeminiProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        from google import genai

        self.client = genai.Client(api_key=self.api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _ask_json(self, prompt: str) -> dict[str, Any]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)

    def generate_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._ask_json(
            "Create a minimal load test plan. Return JSON only. Preserve every supplied "
            f"value exactly and do not invent settings: {json.dumps(request)}"
        )

    def analyze_results(self, evidence: dict[str, Any]) -> dict[str, Any]:
        return self._ask_json(
            "Analyze only this validated evidence. Return JSON with summary (string), "
            "observations (array of strings), and investigation_areas (array of strings). "
            "Never invent metrics, change values, or claim unsupported root causes: "
            f"{json.dumps(evidence)}"
        )


class AIService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def create_plan(self, request: TestRequest) -> TestPlan:
        data = self.provider.generate_plan(request.model_dump())
        plan = TestPlan.model_validate(data)
        if (
            plan.api_url != request.api_url
            or plan.method != request.method
            or plan.virtual_users != request.virtual_users
            or plan.duration_seconds != request.duration_seconds
            or plan.thresholds.p95_ms != request.max_p95_ms
            or plan.thresholds.error_rate != request.max_error_rate
        ):
            raise ValueError("AI test plan changed user-supplied values")
        return plan

    def analyze(self, evidence: dict[str, Any]) -> Analysis:
        return Analysis.model_validate(self.provider.analyze_results(evidence))