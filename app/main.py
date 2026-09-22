import json
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException

from .ai.service import AIService, GeminiProvider
from .metrics import calculate_metrics, evaluate_thresholds
from .models import TestRequest, TestResult
from .performance.k6_runner import K6Runner
from .script_generator import generate_k6_script
from .storage import ResultStore

app = FastAPI(title="MiniPerf")


def get_ai_service() -> AIService:
    try:
        return AIService(GeminiProvider())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def get_runner() -> K6Runner:
    return K6Runner()


def get_store() -> ResultStore:
    return ResultStore()


@app.post("/tests", response_model=TestResult, status_code=201)
def create_test(
    request: TestRequest,
    ai: AIService = Depends(get_ai_service),
    runner: K6Runner = Depends(get_runner),
    store: ResultStore = Depends(get_store),
) -> TestResult:
    try:
        plan = ai.create_plan(request)
        test_id = str(uuid.uuid4())
        script_path = Path("generated") / f"{test_id}.js"
        result_path = Path("results") / f"{test_id}.jsonl"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(generate_k6_script(plan), encoding="utf-8")
        raw = runner.run(script_path, result_path)
        metrics = calculate_metrics(**raw)
        threshold_results = evaluate_thresholds(metrics, plan.thresholds)
        evidence = {
            "metrics": metrics.model_dump(),
            "thresholds": plan.thresholds.model_dump(),
            "threshold_results": threshold_results.model_dump(),
        }
        analysis = ai.analyze(evidence)
        result = TestResult(
            test_id=test_id,
            target_url=plan.api_url,
            method=plan.method,
            test_plan=plan,
            metrics=metrics,
            thresholds=plan.thresholds,
            threshold_results=threshold_results,
            ai_analysis=analysis,
        )
        store.save(result)
        return result
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/tests", response_model=list[TestResult])
def list_tests(store: ResultStore = Depends(get_store)) -> list[TestResult]:
    return [TestResult.model_validate(item) for item in store.list()]


@app.get("/tests/{test_id}", response_model=TestResult)
def get_test(test_id: str, store: ResultStore = Depends(get_store)) -> TestResult:
    item = store.get(test_id)
    if item is None:
        raise HTTPException(status_code=404, detail="test not found")
    return TestResult.model_validate(item)