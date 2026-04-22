import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.models.function_specs import FUNCTION_SPECS
from api.services.simple_analysis_service import SimpleF1AnalysisService
from core.local_requests import _extract_params


def test_function_specs_basic_properties():
    expected_ids = {"1", "2", "13", "26", "28", "98", "99"}
    actual_ids = set(FUNCTION_SPECS.keys())
    assert expected_ids.issubset(actual_ids)

    for spec in FUNCTION_SPECS.values():
        assert spec.name
        assert spec.cache_patterns
        for param in spec.required_params:
            assert param in spec.cli_flag_map

    calendar_spec = FUNCTION_SPECS["99"]
    assert calendar_spec.required_params == []
    assert calendar_spec.optional_params == ["year"]
    assert calendar_spec.cli_flag_map.get("year") == "-y"

    color_spec = FUNCTION_SPECS["98"]
    assert color_spec.optional_params == ["year", "colormap"]
    assert color_spec.cli_flag_map.get("colormap") == "--colormap"


def test_build_cli_command_mapping():
    service = SimpleF1AnalysisService()
    spec = FUNCTION_SPECS["13"]
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


def test_function_spec_straight_line_speed_registered():
    spec = FUNCTION_SPECS["48"]
    assert spec.required_params == ["year", "race", "session"]
    assert "all_drivers_straight_line_speed" in spec.cache_patterns
    assert spec.cli_flag_map["year"] == "-y"


def test_local_request_params_flattens_gui_payload():
    params = _extract_params(
        None,
        {
            "function_id": "96",
            "parameters": {"year": 2025, "race": "Australia"},
        },
    )

    assert params == {"year": 2025, "race": "Australia"}
