import pandas as pd
import pytest

from CLI_modules.cli.analyzer.driver_throttle_ratio import (
    calculate_throttle_metrics_from_telemetry,
)


def test_calculate_metrics_from_basic_telemetry():
    telemetry = pd.DataFrame(
        {
            "Time": [0.0, 1.0, 2.0],
            "Throttle": [0.0, 1.0, 0.0],
        }
    )

    result = calculate_throttle_metrics_from_telemetry(
        telemetry,
        lap_time_seconds=2.0,
        threshold=0.9,
        coast_threshold=0.2,
    )

    assert result["full_throttle_duration_s"] == pytest.approx(1.0, abs=1e-9)
    assert result["coasting_duration_s"] == pytest.approx(1.0, abs=1e-9)
    assert result["full_throttle_ratio"] == pytest.approx(0.5, abs=1e-9)
    assert result["average_throttle"] == pytest.approx(0.5, abs=1e-9)
    assert result["telemetry_sample_count"] == 3


def test_calculate_metrics_requires_multiple_samples():
    telemetry = pd.DataFrame({"Time": [0.0], "Throttle": [1.0]})

    result = calculate_throttle_metrics_from_telemetry(
        telemetry,
        lap_time_seconds=1.0,
        threshold=0.9,
        coast_threshold=0.2,
    )

    assert result["lap_number"] == 0
    assert result["full_throttle_duration_s"] is None
    assert result["coasting_duration_s"] is None
    assert result["full_throttle_ratio"] is None
    assert result["data_status"] == "insufficient"