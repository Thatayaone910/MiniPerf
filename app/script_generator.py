from .models import TestPlan


def generate_k6_script(plan: TestPlan) -> str:
    method = plan.method.upper()
    return f'''import http from "k6/http";
import {{ check }} from "k6";

export const options = {{
  vus: {plan.virtual_users},
  duration: "{plan.duration_seconds}s",
  thresholds: {{
    http_req_duration: ["p(95)<{plan.thresholds.p95_ms}"],
    http_req_failed: ["rate<{plan.thresholds.error_rate}"],
  }},
}};

export default function () {{
  const response = http.request("{method}", "{plan.api_url}");
  check(response, {{ "status is successful": (res) => res.status >= 200 && res.status < 400 }});
}}
'''