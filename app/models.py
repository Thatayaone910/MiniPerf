from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class TestRequest(BaseModel):
    api_url: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    virtual_users: int = Field(gt=0, le=1000)
    duration_seconds: int = Field(gt=0, le=3600)
    max_p95_ms: float = Field(gt=0)
    max_error_rate: float = Field(ge=0, le=1)

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("api_url must be a complete HTTP or HTTPS URL")
        return value


class Thresholds(BaseModel):
    p95_ms: float = Field(gt=0)
    error_rate: float = Field(ge=0, le=1)


class TestPlan(BaseModel):
    test_type: Literal["load"] = "load"
    api_url: str
    method: str
    virtual_users: int = Field(gt=0)
    duration_seconds: int = Field(gt=0)
    thresholds: Thresholds
    rationale: str


class Metrics(BaseModel):
    p50_ms: float
    p95_ms: float
    p99_ms: float
    throughput_rps: float
    error_rate: float


class ThresholdResults(BaseModel):
    p95: Literal["PASS", "FAIL"]
    error_rate: Literal["PASS", "FAIL"]


class Analysis(BaseModel):
    summary: str
    observations: list[str]
    investigation_areas: list[str]


class TestResult(BaseModel):
    test_id: str
    target_url: str
    method: str
    test_plan: TestPlan
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Metrics
    thresholds: Thresholds
    threshold_results: ThresholdResults
    ai_analysis: Analysis