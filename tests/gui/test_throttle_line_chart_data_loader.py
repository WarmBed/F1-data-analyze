import pytest

from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader import (
    ThrottleLineChartDataLoader,
)


@pytest.fixture()
def loader():
    instance = ThrottleLineChartDataLoader()
    instance._target_driver = "VER"  # 設定目標車手以便呼叫私有流程
    return instance


def _sample_payload():
    return {
        "metadata": {
            "year": 2025,
            "race": "Japan",
            "session": "R",
            "thresholds": {"full_throttle": 0.9, "coast": 0.2},
        },
        "analysis": {
            "summary": {"total_laps": 3},
            "drivers": [
                {
                    "driver_code": "VER",
                    "team": "Red Bull Racing",
                    "summary": {
                        "avg_full_throttle_duration_s": 31.5,
                        "valid_laps": 3,
                    },
                    "laps": [
                        {
                            "lap_number": 10,
                            "lap_time_seconds": 92.432,
                            "lap_time_formatted": "01:32.432",
                            "full_throttle_duration_s": 34.2,
                            "full_throttle_ratio": 0.37,
                            "average_throttle": 0.62,
                            "coasting_duration_s": 5.2,
                            "drs_usage_ratio": 0.45,
                            "ers_deploy_ratio": 0.63,
                            "speed_avg_kmh": 201.5,
                            "top_speed_kmh": 312.0,
                            "compound": "SOFT",
                            "tyre_life": 4,
                            "stint": 1,
                            "pit_status": "",
                            "track_status": "1",
                            "data_status": "ok",
                        },
                        {
                            "lap_number": 11,
                            "lap_time_seconds": 91.987,
                            "full_throttle_duration_s": 35.0,
                            "full_throttle_ratio": 0.39,
                            "average_throttle": 0.64,
                            "drs_usage_ratio": 0.5,
                            "ers_deploy_ratio": 0.6,
                            "compound": "SOFT",
                            "tyre_life": 5,
                            "stint": 1,
                            "pit_status": "",
                            "track_status": "1",
                            "data_status": "ok",
                        },
                        {
                            "lap_number": 12,
                            "lap_time_seconds": 97.250,
                            "full_throttle_duration_s": 26.8,
                            "full_throttle_ratio": 0.30,
                            "average_throttle": 0.48,
                            "drs_usage_ratio": 0.1,
                            "ers_deploy_ratio": 0.2,
                            "compound": "MEDIUM",
                            "tyre_life": 1,
                            "stint": 2,
                            "pit_status": "PIT",
                            "track_status": "2",
                            "data_status": "ok",
                        },
                    ],
                },
                {
                    "driver_code": "LEC",
                    "team": "Ferrari",
                    "laps": [],
                },
            ],
        },
    }


def test_process_data_extracts_chart_series(loader):
    payload = loader._process_data(_sample_payload())

    assert payload["driver"]["code"] == "VER"
    assert payload["driver"]["team"] == "Red Bull Racing"
    assert payload["metadata"]["driver_code"] == "VER"

    chart = payload["chart_series"]
    assert chart["lap_numbers"] == [10, 11, 12]
    assert chart["full_throttle_duration_s"] == [34.2, 35.0, 26.8]
    assert chart["full_throttle_ratio_percent"] == [37.0, 39.0, 30.0]
    assert chart["tooltip"][11]["compound"] == "SOFT"
    assert chart["tooltip"][12]["drs_percent"] == 10.0

    annotations = payload["annotations"]
    assert annotations["pit_laps"] == [12]
    assert annotations["caution_laps"] == [12]
    assert annotations["invalid_laps"] == []
    assert annotations["stint_ranges"] == [
        {"stint": 1, "compound": "SOFT", "start_lap": 10, "end_lap": 11},
        {"stint": 2, "compound": "MEDIUM", "start_lap": 12, "end_lap": 12},
    ]


def test_lap_time_delta_is_relative_to_best(loader):
    payload = loader._process_data(_sample_payload())
    laps = payload["lap_records"]
    base = min(lap["lap_time_seconds"] for lap in laps)
    deltas = [lap["lap_time_delta"] for lap in laps]
    assert deltas[1] == pytest.approx(0.0, abs=1e-6)
    assert deltas[0] == pytest.approx(laps[0]["lap_time_seconds"] - base, abs=1e-6)


def test_missing_driver_raises_error(loader):
    loader._target_driver = "HAM"
    payload = _sample_payload()
    with pytest.raises(ValueError):
        loader._process_data(payload)


def test_filename_pattern_generation(loader):
    patterns = loader._build_filename_patterns(year=2025, race="São Paulo", session="Q")
    assert "throttle_ratio_2025_são_paulo_Q.json" in patterns
    assert "throttle_ratio_2025_são_paulo_q.json" in patterns
    assert patterns[-1] == "throttle_ratio_2025_são_paulo_*.json"


def test_lap_numbers_reassigned_when_missing(loader):
    payload = _sample_payload()
    for lap in payload["analysis"]["drivers"][0]["laps"]:
        lap["lap_number"] = 0

    result = loader._process_data(payload)
    lap_numbers = [record["lap_number"] for record in result["lap_records"]]

    assert lap_numbers == list(range(1, len(lap_numbers) + 1))
    assert all(record.get("raw_lap_number") == 0 for record in result["lap_records"])
