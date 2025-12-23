import os
import sys

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from api.services.cache_service import F1AnalysisCacheService
from api.models.function_specs import normalize_function_id


@pytest.mark.parametrize(
    "year, race, session",
    [
        (2025, "China", "R"),
        (2025, "Italy", "R"),
    ],
)
def test_team_pitstop_cache_returns_matching_function(year, race, session):
    """Ensure cached lookup for function 4 never returns driver data."""
    service = F1AnalysisCacheService()

    result = service.search_cached_analysis(4, year=year, race=race, session=session)
    assert result is not None, "Expected cached team pitstop data to be available"

    function_id = result.get("function_id")
    assert function_id is not None, "Cached result should declare function_id"
    assert normalize_function_id(function_id) == "4"

    data = result.get("data")
    assert isinstance(data, list) and data, "Team pitstop data should be a non-empty list"
    assert all("team" in item for item in data), "Each entry should describe a team"
