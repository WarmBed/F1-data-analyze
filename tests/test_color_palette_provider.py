import sys
from pathlib import Path

import requests
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib

color_module = importlib.import_module("modules.gui.themes.color_palette_provider")
from modules.gui.themes.color_palette_provider import ColorPaletteProvider, ColorPaletteError


def test_color_palette_provider_uses_defaults_when_api_fails(monkeypatch):
    def fail_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(color_module.requests, "post", fail_post)

    provider = ColorPaletteProvider(timeout=0.05)
    provider.ensure_loaded(year=2025)

    # Should have fallen back to the refreshed built-in palette (2025 grid).
    assert provider.get_driver_color("VER", format="hex") == "#0600EF"
    assert provider.get_driver_color("LEC", format="rgb") == (232, 0, 32)
    assert provider.get_driver_color("HAM", format="hex") == "#E80020"
    assert provider.get_driver_color("ANT", format="hex") == "#27F4D2"
    assert provider.get_team_color("williams", format="hex") == "#00A0DD"
    # Default colour still available for unknown driver.
    assert provider.get_driver_color("UNK", format="hex") == "#808080"


def test_color_palette_provider_respects_api_only_policy(monkeypatch):
    def fail_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setenv("F1T_COLOR_PALETTE_ALLOW_FALLBACK", "0")
    monkeypatch.setattr(color_module.requests, "post", fail_post)

    provider = ColorPaletteProvider(timeout=0.05)
    with pytest.raises(ColorPaletteError):
        provider.ensure_loaded(year=2025)
