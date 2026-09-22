# MiniPerf: An AI-Assisted Performance Testing and Analysis Tool

MiniPerf is a small school project for testing one explicitly supplied HTTP endpoint. It combines a Gemini-generated test plan with deterministic Python calculations and a simple k6 run. The AI explains evidence; Python decides the metrics and pass/fail result.

## Why It Exists

Performance testing is easier to understand when the responsibilities are separate. MiniPerf demonstrates API design, input validation, external-process integration, automated testing, and the difference between AI reasoning and program logic without recreating a production platform.

## Architecture

```text
HTTP request
		|
		v
FastAPI -> AIService -> GeminiProvider -> validated TestPlan
		|                                      |
		|                                      v
		+------------------------------> k6 script -> k6 -> raw JSON
																							 |
																							 v
																	 Python metrics + thresholds
																							 |
																							 v
																	 AI result explanation
																							 |
																							 v
																			JSON result store
```

The application has one service and two external adapters: Gemini and k6. Tests replace both adapters with fakes, so normal tests do not call a network service or run a load test.

## AI Responsibilities

Gemini performs two limited tasks:

1. It turns the user's endpoint and requirements into a small JSON load-test plan. MiniPerf validates the response and rejects any plan that changes user-supplied values.
2. It receives only validated metrics and threshold results, then returns a summary, observations, and possible investigation areas.

Gemini does not calculate p50, p95, p99, throughput, error rate, or pass/fail status. It cannot claim a root cause from evidence that was not supplied.

## Deterministic Metrics

Python uses sorted request durations and linear interpolation for percentiles. For percentile `p`, the position is `(n - 1) * p / 100`; neighboring values are interpolated. Throughput is request count divided by elapsed seconds, and error rate is failed requests divided by total requests. Thresholds pass when the calculated value is less than or equal to the user's maximum.

## Installation

Python 3.12 and k6 are required for a real run. Install Python dependencies in a virtual environment where possible:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Install k6 using the instructions for your operating system: <https://grafana.com/docs/k6/latest/set-up/install-k6/>.

Set the Gemini key in the shell. The key is never stored in result files:

```bash
export GEMINI_API_KEY="your-key"
```

`GEMINI_MODEL` is optional and defaults to `gemini-2.5-flash`.

## Run the Application

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. FastAPI's interactive documentation is at `/docs`.

Run a sample test against a local endpoint:

```bash
curl -X POST http://127.0.0.1:8000/tests \
	-H 'content-type: application/json' \
	-d '{"api_url":"http://localhost:8000/health","method":"GET","virtual_users":5,"duration_seconds":10,"max_p95_ms":1000,"max_error_rate":0.01}'
```

The request uses a decimal error rate: `0.01` means 1%. Results are saved in `results/tests.json`, with generated scripts in `generated/` and raw k6 output in `results/`.

## API

- `POST /tests` creates and runs a test.
- `GET /tests` returns saved test results.
- `GET /tests/{test_id}` returns one saved result.

Invalid URLs, invalid requirements, missing k6, failed k6 runs, empty results, and missing Gemini configuration are reported instead of being hidden.

## Tests

```bash
pytest -q
```

The test suite covers plan validation, AI fakes, script generation, metric calculation, threshold evaluation, API endpoints, persistence, and missing-k6 handling. It does not require a Gemini key or an installed k6 executable.

## Limitations

MiniPerf tests one endpoint with one simple request and has no authentication, database server, job queue, dashboard, distributed load generation, request body editor, or production deployment configuration. A real run can generate load against any URL the user explicitly enters, so use localhost or a system where testing is authorized.

## Future Improvements

Reasonable next steps would be request headers and bodies, a background job for long tests, richer k6 result parsing, SQLite storage, and a small browser form. These are intentionally outside the current MVP.