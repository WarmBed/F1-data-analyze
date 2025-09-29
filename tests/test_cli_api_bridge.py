import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.models.function_specs import FUNCTION_SPECS
from api.services.simple_analysis_service import SimpleF1AnalysisService


def test_function_specs_basic_properties():
    expected_ids = {1, 2, 13, 26, 28}
    assert set(FUNCTION_SPECS.keys()) == expected_ids

    for spec in FUNCTION_SPECS.values():
        assert spec.name
        assert spec.cache_patterns
        for param in spec.required_params:
            assert param in spec.cli_flag_map


def test_build_cli_command_mapping():
    service = SimpleF1AnalysisService()
    spec = FUNCTION_SPECS[13]
    params = {
        "year": 2025,
        "race": "Japan",
        "session": "R",
        "driver1": "VER",
        "driver2": "LEC",
    }
    prepared = service._prepare_params(spec, params)
    cmd = service._build_cli_command(spec, prepared)
    assert "-f" in cmd and str(spec.function_id) in cmd
    assert "-d" in cmd and "VER" in cmd
    assert "-d2" in cmd and "LEC" in cmd


def test_execute_analysis_missing_param_returns_error():
    service = SimpleF1AnalysisService()
    result = asyncio.run(service.execute_analysis(1, year=2025, race="Japan"))
    assert result["success"] is False
    assert result["source"] == "service_error"
