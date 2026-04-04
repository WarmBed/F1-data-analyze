"""
F1T 測試框架共用設定 (pytest conftest.py)
===========================================
所有測試共用的 fixtures、marks、路徑設定。
"""
import sys
import os
from pathlib import Path
import pytest

# ── 確保 workspace root 在 sys.path 最前面 ──────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── 共用 Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def project_root() -> Path:
    """回傳專案根目錄的 Path 物件。"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def json_dir(project_root: Path) -> Path:
    """回傳 JSON 輸出目錄。"""
    return project_root / "json"


@pytest.fixture(scope="session")
def config_dir(project_root: Path) -> Path:
    """回傳設定目錄。"""
    return project_root / "config"


@pytest.fixture
def api_base_url_env(monkeypatch):
    """
    用於測試 API URL 解析的 monkeypatch fixture。
    回傳一個可設定環境變數的 setter 函數。
    """
    def _set(url: str | None):
        if url is None:
            monkeypatch.delenv("F1_API_BASE_URL", raising=False)
        else:
            monkeypatch.setenv("F1_API_BASE_URL", url)
    return _set
