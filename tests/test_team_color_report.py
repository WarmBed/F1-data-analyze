import importlib
from pathlib import Path


def test_generate_team_color_report_basic(monkeypatch, tmp_path):
    monkeypatch.setenv("F1_ANALYSIS_JSON_DIR", str(tmp_path))

    module = importlib.import_module("CLI_modules.cli.analyzer.team_color_analysis")
    module = importlib.reload(module)

    result = module.generate_team_color_report(
        year=2024,
        include_drivers=False,
        save_json=True,
    )

    assert result["success"] is True
    teams = result["data"]["teams"]
    assert "red bull" in teams

    output_path = Path(result["metadata"]["output_file"])
    assert output_path.exists()
    assert output_path.parent == tmp_path

    official = module.generate_team_color_report(
        year=2024,
        colormap="official",
        include_drivers=False,
        save_json=False,
    )
    assert (
        official["data"]["teams"]["red bull"]["selected_hex"]
        == official["data"]["teams"]["red bull"]["official_hex"]
    )

