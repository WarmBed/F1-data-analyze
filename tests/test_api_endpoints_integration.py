from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from refactored_api import app

client = TestClient(app)

COMMON_PARAMS = {
    "year": 2025,
    "race": "Japan",
    "session": "R",
}

TEST_CASES = [
    {
        "function_id": 1,
        "extra_params": {},
        "description": "Rain analysis baseline",
    },
    {
        "function_id": 2,
        "extra_params": {},
        "description": "Track analysis baseline",
    },
    {
        "function_id": 3,
        "extra_params": {},
        "description": "Driver fastest pitstop ranking",
    },
    {
        "function_id": 4,
        "extra_params": {},
        "description": "Team pitstop ranking",
    },
    {
        "function_id": 5,
        "extra_params": {},
        "description": "Driver pitstop detail records",
    },
    {
        "function_id": 8,
        "extra_params": {},
        "description": "All incidents summary",
    },
    {
        "function_id": 12,
        "extra_params": {},
        "description": "All drivers telemetry overview",
    },
    {
        "function_id": 13,
        "extra_params": {"driver1": "VER", "driver2": "LEC"},
        "description": "Telemetry comparison (VER vs LEC)",
    },
    {
        "function_id": 26,
        "extra_params": {"driver1": "VER"},
        "description": "Tyre strategy (VER focus)",
    },
    {
        "function_id": 28,
        "extra_params": {"driver1": "VER"},
        "description": "Detailed lap analysis (VER)",
    },
]


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: f"function_{c['function_id']}")
def test_analysis_execute_endpoints(case: Dict[str, Any]) -> None:
    params = {"function_id": case["function_id"], **COMMON_PARAMS, **case["extra_params"]}

    response = client.post("/api/v2/analysis/execute", params=params)

    assert response.status_code == 200, response.text

    body = response.json()

    assert body.get("success") is True, body
    assert body.get("message")
    spec_id = body.get("function_spec", {}).get("function_id")
    assert str(spec_id) == str(case["function_id"])
    assert body.get("data"), "Expected data payload to be present"
    assert body.get("source") in {"cache", "cli", "cli_failed", "service_error"}

    if body.get("source") == "cli_failed":
        pytest.fail(f"CLI execution failed for function {case['function_id']}: {body}")
    if body.get("source") == "service_error":
        pytest.fail(f"Service error for function {case['function_id']}: {body}")
