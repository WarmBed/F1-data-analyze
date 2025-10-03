from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from modules.gui.shared import season_calendar_provider as scp
from modules.gui.shared.season_calendar_provider import (
    SeasonCalendarError,
    SeasonCalendarProvider,
)


class DummyResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):  # pragma: no cover - trivial
        return self._payload


@pytest.fixture
def frozen_datetime(monkeypatch):
    fixed_now = datetime(2025, 3, 30, 12, 0, tzinfo=timezone.utc)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(scp, "datetime", _FrozenDateTime)
    return fixed_now


def _make_provider(monkeypatch, tmp_path) -> SeasonCalendarProvider:
    monkeypatch.setattr(scp, "JSON_DIR", tmp_path)
    return SeasonCalendarProvider(base_url="http://example.test")


def test_provider_transforms_completed_events(monkeypatch, tmp_path, frozen_datetime):
    payload = {
        "success": True,
        "data": [
            {
                "round": 1,
                "event_name": "Australian Grand Prix",
                "location": "Melbourne",
                "country": "Australia",
                "race_date_local": "2025-03-16T15:00:00+11:00",
                "is_completed": True,
                "session_dates": {
                    "session1_name": "Practice 1",
                    "session1_local": "2025-03-14T11:30:00+11:00",
                    "session1_utc": "2025-03-14T00:30:00Z",
                    "session2_name": "Qualifying",
                    "session2_local": "2025-03-16T16:00:00+11:00",
                    "session2_utc": "2025-04-01T04:00:00Z",  # future -> filtered out
                    "session3_name": "Race",
                    "session3_local": "2025-03-16T15:00:00+11:00",
                    "session3_utc": "2025-03-16T04:00:00Z",
                },
            },
            {
                "round": 2,
                "event_name": "Beta Grand Prix",
                "location": "Beta Town",
                "country": "Example Republic",
                "race_date_local": "2025-04-20T14:00:00+02:00",
                "is_completed": False,
                "session_dates": {},
            },
        ],
    }

    def fake_post(_url, *_args, **_kwargs):
        return DummyResponse(payload)

    monkeypatch.setattr(scp.requests, "post", fake_post)

    provider = _make_provider(monkeypatch, tmp_path)
    events = provider.get_completed_events(2025)

    assert len(events) == 2

    completed, upcoming = events

    assert completed.race_key == "Australia"
    assert completed.round == 1
    assert completed.race_date == "2025-03-16"
    assert completed.is_completed is True

    session_codes = [session.code for session in completed.sessions]
    assert session_codes == ["FP1", "R"]  # future qualifying filtered out

    assert upcoming.race_key == "Example Republic"
    assert upcoming.is_completed is False
    assert upcoming.sessions == []

    # cached result should be reused
    cached = provider.get_completed_events(2025)
    assert cached is events


def test_provider_handles_api_wrapped_payload(monkeypatch, tmp_path, frozen_datetime):
    inner_payload = {
        "success": True,
        "data": [
            {
                "round": 7,
                "event_name": "Gamma Grand Prix",
                "location": "Gamma City",
                "country": "Gamma Republic",
                "race_date_local": "2025-05-18T15:00:00+02:00",
                "is_completed": True,
                "session_dates": {},
            },
            {
                "round": 8,
                "event_name": "Delta Grand Prix",
                "location": "Delta Circuit",
                "country": "Delta",
                "race_date_local": "2025-06-01T14:00:00+02:00",
                "is_completed": False,
                "session_dates": {},
            },
        ],
        "metadata": {"year": 2025},
    }

    api_payload = {
        "success": True,
        "data": inner_payload,
        "source": "cache",
    }

    def fake_post(_url, *_args, **_kwargs):
        return DummyResponse(api_payload)

    monkeypatch.setattr(scp.requests, "post", fake_post)

    provider = _make_provider(monkeypatch, tmp_path)
    events = provider.get_completed_events(2025)

    assert [event.race_key for event in events] == ["Gamma Republic", "Delta"]
    assert events[0].is_completed is True
    assert events[1].is_completed is False


def test_provider_falls_back_to_json(monkeypatch, tmp_path):
    def failing_post(*_args, **_kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(scp.requests, "post", failing_post)
    monkeypatch.setattr(scp, "JSON_DIR", tmp_path)

    data = {
        "success": True,
        "data": [
            {
                "round": 4,
                "event_name": "Great Britain Grand Prix",
                "location": "Silverstone",
                "country": "United Kingdom",
                "race_date_local": "2024-07-14T15:00:00+01:00",
                "is_completed": True,
                "session_dates": {
                    "session1_name": "Practice 1",
                    "session1_local": "2024-07-12T11:30:00+01:00",
                    "session1_utc": "2024-07-12T10:30:00Z",
                    "session2_name": "Race",
                    "session2_local": "2024-07-14T15:00:00+01:00",
                    "session2_utc": "2024-07-14T14:00:00Z",
                },
            }
        ],
    }

    json_path = tmp_path / "season_calendar_2024_test.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    provider = SeasonCalendarProvider(base_url="http://example.test")
    events = provider.get_completed_events(2024)

    assert len(events) == 1
    event = events[0]
    assert event.race_key == "Great Britain"
    assert event.is_completed is True
    assert [session.code for session in event.sessions] == ["FP1", "R"]


def test_provider_raises_when_no_sources(monkeypatch, tmp_path):
    def failing_post(*_args, **_kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(scp.requests, "post", failing_post)
    monkeypatch.setattr(scp, "JSON_DIR", tmp_path)

    provider = SeasonCalendarProvider(base_url="http://example.test")

    with pytest.raises(SeasonCalendarError):
        provider.get_completed_events(2030)
