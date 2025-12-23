from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import fastf1
import pandas as pd
import pytest

from CLI_modules.cli.analyzer import season_calendar_analysis as sca


@pytest.fixture(autouse=True)
def _reset_fastf1_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(fastf1.Cache, "enable_cache", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(fastf1.Cache, "disabled", False, raising=False)
    monkeypatch.setattr(sca, "FASTF1_CACHE_DIR", tmp_path.as_posix(), raising=False)
    monkeypatch.setattr(sca, "JSON_OUTPUT_DIR", tmp_path.as_posix(), raising=False)


def test_generate_season_calendar_transforms_schedule(monkeypatch):
    fixed_now = datetime(2025, 3, 20, 12, 0, tzinfo=timezone.utc)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(sca, "datetime", _FixedDateTime, raising=False)

    schedule_rows = [
        {
            "RoundNumber": 1,
            "EventName": "Alpha Grand Prix",
            "OfficialEventName": "FORMULA 1 ALPHA GRAND PRIX 2025",
            "Country": "Testland",
            "Location": "Alpha City",
            "Session1": "Practice 1",
            "Session1Date": pd.Timestamp("2025-03-08 10:00:00+01:00"),
            "Session1DateUtc": pd.Timestamp("2025-03-08 09:00:00+00:00"),
            "Session5": "Race",
            "Session5Date": pd.Timestamp("2025-03-10 15:00:00+01:00"),
            "Session5DateUtc": pd.Timestamp("2025-03-10 14:00:00+00:00"),
        },
        {
            "RoundNumber": 2,
            "EventName": "Beta Grand Prix",
            "OfficialEventName": "FORMULA 1 BETA GRAND PRIX 2025",
            "Country": "Example Republic",
            "Location": "Beta Town",
            "Session1": "Practice 1",
            "Session1Date": pd.Timestamp("2025-03-29 11:00:00+02:00"),
            "Session1DateUtc": pd.Timestamp("2025-03-29 09:00:00+00:00"),
            "Session5": "Race",
            "Session5Date": pd.Timestamp("2025-04-01 16:00:00+02:00"),
            "Session5DateUtc": pd.Timestamp("2025-04-01 14:00:00+00:00"),
        },
        {
            "RoundNumber": 0,
            "EventName": "Pre-Season Testing",
            "OfficialEventName": "FORMULA 1 PRE-SEASON TESTING",
            "Country": "Testland",
            "Location": "Circuit",
            "Session5": "Testing",
            "Session5Date": pd.NaT,
            "Session5DateUtc": pd.NaT,
        },
    ]

    schedule_df = pd.DataFrame(schedule_rows)
    monkeypatch.setattr(fastf1, "get_event_schedule", lambda _year: schedule_df)

    result = sca.generate_season_calendar(2025, save_json=True)

    assert result["success"] is True
    metadata = result["metadata"]
    assert metadata["total_rounds"] == 2
    assert metadata["completed_rounds"] == 1
    assert metadata["upcoming_rounds"] == 1

    output_path = Path(metadata["output_file"])
    assert output_path.exists()

    first_event, second_event = result["data"]
    assert first_event["is_completed"] is True
    assert second_event["is_completed"] is False
    assert second_event["days_until_race"] == 12

    summary = result["summary"]
    assert summary["last_completed_event"]["round"] == 1
    assert summary["next_event"]["round"] == 2