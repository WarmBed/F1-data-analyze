import pandas as pd

from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import (
    AllDriversStraightLineSpeedAnalysis,
)


class StubCarData(pd.DataFrame):
    def __init__(self, data):
        super().__init__(data)

    @property
    def _constructor(self):  # pragma: no cover - pandas requirement for subclassing
        return StubCarData

    def add_distance(self):
        return self


class StubLap:
    def __init__(self, lap_number, speeds):
        self.LapNumber = lap_number
        self._car_data = StubCarData(
            {
                "Speed": speeds,
                "Distance": [idx * 10.0 for idx, _ in enumerate(speeds, start=1)],
                "Time": pd.to_timedelta(range(len(speeds)), unit="s"),
                "Throttle": [95.0] * len(speeds),
                "DRS": [1] * len(speeds),
            }
        )

    def get_car_data(self):
        return self._car_data.copy()


class StubDriverLaps:
    def __init__(self, laps):
        self._laps = laps

    @property
    def empty(self):
        return len(self._laps) == 0

    def iterlaps(self):
        for idx, lap in enumerate(self._laps):
            yield idx, lap


class StubLaps:
    def __init__(self, mapping):
        self._mapping = mapping

    def pick_driver(self, driver):
        laps = [StubLap(lap_no, speeds) for lap_no, speeds in self._mapping.get(driver, [])]
        return StubDriverLaps(laps)


class StubDataLoader:
    def __init__(self):
        self.session_loaded = True
        self.year = 2025
        self.race_name = "TestGP"
        self.session_type = "R"
        self.results = pd.DataFrame(
            {
                "Abbreviation": ["VER", "LEC"],
                "DriverNumber": [1, 16],
                "FullName": ["Max Verstappen", "Charles Leclerc"],
                "TeamName": ["Red Bull Racing", "Ferrari"],
            }
        )
        self.laps = StubLaps(
            {
                "VER": [(1, [300, 310, 320]), (2, [330, 325])],
                "LEC": [(1, [295, 302, 299]), (2, [310, 315, 318])],
            }
        )
        self.loaded_data = {}


def test_all_drivers_straight_line_speed_analysis_basic():
    loader = StubDataLoader()
    analysis = AllDriversStraightLineSpeedAnalysis(loader)

    result = analysis.run()

    assert result["success"] is True
    assert result["function_id"] == "48"

    data = result["data"]
    assert data["metadata"]["drivers_total"] == 2
    speeds = data["driver_speeds"]
    # Expect descending order by max speed
    assert speeds[0]["driver"] == "VER"
    assert speeds[0]["max_speed_kmh"] == 330.0
    assert speeds[0]["lap_number"] == 2

    chart = data["chart_data"]
    assert chart["type"] == "bar"
    assert chart["x"][0] == "VER"
    assert chart["values"][0] == 330.0

    summary = data["summary"]
    assert summary["fastest_driver"] == "VER"
    assert summary["drivers_analysed"] == 2
