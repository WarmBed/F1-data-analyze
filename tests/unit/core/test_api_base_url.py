"""
測試 1: core/api_base_url.py - API URL 解析邏輯
================================================
系統改為本地模式 (localhost:8000)。
驗證 resolve_api_base_url() 正確解析本地與外部位址，
預設回退至 http://localhost:8000。
"""
import pytest
from pathlib import Path

from core.api_base_url import (
    PUBLIC_API_BASE_URL,
    resolve_api_base_url,
    _is_internal_host,
    _normalize_candidate,
)


# ── 常數拼寫保護 ────────────────────────────────────────────────────────────

class TestPublicApiConstant:
    """PUBLIC_API_BASE_URL 常數必須指向本地 API 伺服器。"""

    def test_public_api_base_url_is_localhost(self):
        assert PUBLIC_API_BASE_URL == "http://localhost:8000"

    def test_public_api_base_url_starts_with_http(self):
        assert PUBLIC_API_BASE_URL.startswith("http://")

    def test_public_api_base_url_no_trailing_slash(self):
        assert not PUBLIC_API_BASE_URL.endswith("/")


# ── 內部主機偵測 (輔助函數，供參考用) ─────────────────────────────────────

class TestIsInternalHost:
    """_is_internal_host() 正確識別本地/內部位址（函數仍存在，但 resolve 不再拒絕本地位址）。"""

    @pytest.mark.parametrize("host", [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "mydevbox.local",
        "192.168.1.100",
        "10.0.0.1",
        "",
    ])
    def test_internal_hosts_are_flagged(self, host: str):
        assert _is_internal_host(host) is True, f"預期 {host!r} 為內部位址"

    @pytest.mark.parametrize("host", [
        "f1.example.com",
        "8.8.8.8",
        "1.1.1.1",
    ])
    def test_external_hosts_are_not_flagged(self, host: str):
        assert _is_internal_host(host) is False, f"預期 {host!r} 為外部位址"


# ── URL 正規化 ───────────────────────────────────────────────────────────────

class TestNormalizeCandidate:
    """_normalize_candidate() 正確解析 URL 並移除尾部斜線，保留 http/https scheme。"""

    def test_localhost_http_url_preserved(self):
        result = _normalize_candidate("http://localhost:8000")
        assert result == "http://localhost:8000"

    def test_https_url_preserved(self):
        result = _normalize_candidate("https://example.com")
        assert result is not None
        assert result.startswith("https://")

    def test_empty_string_returns_none(self):
        assert _normalize_candidate("") is None

    def test_trailing_slash_stripped(self):
        result = _normalize_candidate("http://localhost:8000/")
        assert result is not None
        assert not result.endswith("/")

    def test_invalid_scheme_returns_none(self):
        assert _normalize_candidate("ftp://localhost") is None


# ── resolve_api_base_url 主流程 ──────────────────────────────────────────────

class TestResolveApiBaseUrl:
    """resolve_api_base_url() 的完整行為驗證（本地模式）。"""

    def test_returns_localhost_fallback_when_no_env_no_config(
        self, api_base_url_env, tmp_path
    ):
        """無環境變數、無設定檔時必須回傳 localhost 預設值。"""
        api_base_url_env(None)
        result = resolve_api_base_url(config_path=tmp_path / "nonexistent.json")
        assert result == PUBLIC_API_BASE_URL  # http://localhost:8000

    def test_accepts_localhost_from_env(self, api_base_url_env, tmp_path):
        """環境變數設為 localhost 時應被接受。"""
        api_base_url_env("http://localhost:8000")
        result = resolve_api_base_url(config_path=tmp_path / "nonexistent.json")
        assert result == "http://localhost:8000"

    def test_accepts_127_0_0_1_from_env(self, api_base_url_env, tmp_path):
        """環境變數設為 127.0.0.1 時應被接受。"""
        api_base_url_env("http://127.0.0.1:8000")
        result = resolve_api_base_url(config_path=tmp_path / "nonexistent.json")
        assert result == "http://127.0.0.1:8000"

    def test_accepts_custom_port_from_env(self, api_base_url_env, tmp_path):
        """環境變數設為自訂 port 時應被接受。"""
        api_base_url_env("http://localhost:9000")
        result = resolve_api_base_url(config_path=tmp_path / "nonexistent.json")
        assert result == "http://localhost:9000"

    def test_accepts_valid_url_from_preferred_urls(self, api_base_url_env, tmp_path):
        """preferred_urls 有效時應優先使用。"""
        api_base_url_env(None)
        preferred = [("test", "http://localhost:8000")]
        result = resolve_api_base_url(
            config_path=tmp_path / "nonexistent.json",
            preferred_urls=preferred,
        )
        assert result == "http://localhost:8000"

    def test_reads_valid_url_from_config_json(self, api_base_url_env, tmp_path):
        """設定檔中含有效 URL 時應從設定檔讀取。"""
        import json

        api_base_url_env(None)
        config_file = tmp_path / "api_config.json"
        config_file.write_text(
            json.dumps({"api_base_url": "http://localhost:8000"}),
            encoding="utf-8",
        )
        result = resolve_api_base_url(config_path=config_file)
        assert result == "http://localhost:8000"

    def test_invalid_url_in_config_falls_back_to_default(self, api_base_url_env, tmp_path):
        """設定檔中為無效 URL（如 ftp://）時應回退至預設值。"""
        import json

        api_base_url_env(None)
        config_file = tmp_path / "api_config.json"
        config_file.write_text(
            json.dumps({"api_base_url": "ftp://localhost:8000"}),
            encoding="utf-8",
        )
        result = resolve_api_base_url(config_path=config_file)
        assert result == PUBLIC_API_BASE_URL
