import json
import os

from api.services.cache_service import F1AnalysisCacheService


def test_cache_lookup_supports_space_in_race_name(tmp_path):
    json_dir = tmp_path / "json"
    cache_dir = tmp_path / "cache"
    json_dir.mkdir()
    cache_dir.mkdir()

    payload = {
        "success": True,
        "metadata": {
            "function_id": 53,
            "year": 2025,
            "race": "Great Britain",
            "session": "R",
        },
        "analysis_result": {},
    }

    file_path = json_dir / "ideal_lap_ranking_2025_Great Britain_R.json"
    with open(file_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False)

    service = F1AnalysisCacheService(json_dir=f"{json_dir}{os.sep}", cache_dir=f"{cache_dir}{os.sep}")

    result = service.search_cached_analysis(53, year=2025, race="Great Britain", session="R")

    assert result is not None, "Cache result should be found for existing JSON"
    cache_info = result.get("cache_info", {})
    assert cache_info.get("cache_hit") is True
    assert result.get("file_info", {}).get("file_name") == os.path.basename(file_path)
