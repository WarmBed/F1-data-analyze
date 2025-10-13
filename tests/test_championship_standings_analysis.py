from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd


def _build_driver_df():
    return pd.DataFrame(
        [
            {
                "position": 1,
                "positionText": "1",
                "points": 150.0,
                "wins": 3,
                "driverId": "max_verstappen",
                "driverNumber": 1,
                "driverCode": "VER",
                "driverUrl": "http://example.com/ver",
                "givenName": "Max",
                "familyName": "Verstappen",
                "dateOfBirth": pd.Timestamp("1997-09-30", tz="UTC"),
                "driverNationality": "Dutch",
                "constructorIds": ["red_bull"],
                "constructorUrls": ["http://example.com/redbull"],
                "constructorNames": ["Red Bull"],
                "constructorNationalities": ["Austrian"],
            },
            {
                "position": 2,
                "positionText": "2",
                "points": 140.0,
                "wins": 1,
                "driverId": "lando_norris",
                "driverNumber": 4,
                "driverCode": "NOR",
                "driverUrl": "http://example.com/nor",
                "givenName": "Lando",
                "familyName": "Norris",
                "dateOfBirth": pd.Timestamp("1999-11-13", tz="UTC"),
                "driverNationality": "British",
                "constructorIds": ["mclaren"],
                "constructorUrls": ["http://example.com/mclaren"],
                "constructorNames": ["McLaren"],
                "constructorNationalities": ["British"],
            },
        ]
    )


def _build_constructor_df():
    return pd.DataFrame(
        [
            {
                "position": 1,
                "positionText": "1",
                "points": 280.0,
                "wins": 4,
                "constructorId": "red_bull",
                "constructorUrl": "http://example.com/redbull",
                "constructorName": "Red Bull",
                "constructorNationality": "Austrian",
            },
            {
                "position": 2,
                "positionText": "2",
                "points": 260.0,
                "wins": 2,
                "constructorId": "mclaren",
                "constructorUrl": "http://example.com/mclaren",
                "constructorName": "McLaren",
                "constructorNationality": "British",
            },
        ]
    )


class _FakeErgastResponse:
    def __init__(self, dataframe: pd.DataFrame, round_number: int):
        self.content = [dataframe]
        self.description = pd.DataFrame([{"season": 2025, "round": round_number}])


class _FakeErgast:
    def __init__(self):
        self._driver_df = _build_driver_df()
        self._constructor_df = _build_constructor_df()

    def get_driver_standings(self, *, season: int, round: str | None = None):
        return _FakeErgastResponse(self._driver_df.copy(), round_number=7)

    def get_constructor_standings(self, *, season: int, round: str | None = None):
        return _FakeErgastResponse(self._constructor_df.copy(), round_number=7)


def test_generate_championship_standings(monkeypatch, tmp_path):
    monkeypatch.setenv("F1_ANALYSIS_JSON_DIR", str(tmp_path))

    module = importlib.import_module("CLI_modules.cli.analyzer.championship_standings_analysis")
    module = importlib.reload(module)

    monkeypatch.setattr(module, "Ergast", lambda: _FakeErgast())

    result = module.generate_championship_standings(year=2025, save_json=True)

    assert result["success"] is True
    assert result["metadata"]["season_year"] == 2025
    assert result["metadata"]["resolved_round"] == 7

    drivers = result["data"]["drivers"]
    assert len(drivers) == 2
    assert drivers[0]["driver"]["code"] == "VER"
    assert drivers[1]["points_delta"] == 10.0

    constructors = result["data"]["constructors"]
    assert constructors[0]["constructor"]["name"] == "Red Bull"

    output_path = Path(result["metadata"]["output_file"])
    assert output_path.exists()
    assert output_path.parent == tmp_path

    reused = module.generate_championship_standings(year=2025)
    assert reused["metadata"]["is_fresh"] is True
    assert reused["data"]["drivers"][0]["driver"]["code"] == "VER"

