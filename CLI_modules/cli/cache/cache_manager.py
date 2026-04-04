"""
CacheManager - 統一快取管理器
===============================
整合 CLI 的 pickle 快取與 API 的快取服務，
提供一致的 get / set / invalidate / generate_key 介面。

設計原則：
- CLI 端使用本機 pickle 檔案快取（向後相容現有行為）
- Key 格式：{function_id}_{year}_{race}_{session}_{driver}
- TTL 預設 1 小時；season 等靜態資料可設更長 TTL
- 提供 @cached 裝飾器供 BaseAnalyzer 子類使用

用法：
    from CLI_modules.cli.cache.cache_manager import CacheManager, cached

    manager = CacheManager()

    # 直接存取
    key = manager.generate_key(1, year=2025, race="Japan", session="R")
    data = manager.get(key)
    if data is None:
        data = run_analysis(...)
        manager.set(key, data, ttl=3600)

    # 裝飾器
    @cached(ttl=3600)
    def my_analysis(self, **kwargs):
        ...
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 預設快取目錄
DEFAULT_CACHE_DIR = Path("cache")


class CacheManager:
    """本機 pickle 快取管理器。"""

    def __init__(self, cache_dir: Path | str | None = None, default_ttl: int = 3600) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── 核心 CRUD ──────────────────────────────────────────────────

    def get(self, cache_key: str) -> Optional[dict]:
        """讀取快取。若不存在或已過期則回傳 None。"""
        cache_file = self._key_to_path(cache_key)
        if not cache_file.exists():
            logger.debug("[CacheManager] MISS: %s", cache_key)
            return None
        try:
            with cache_file.open("rb") as f:
                entry: dict = pickle.load(f)
            if entry.get("expires_at", 0) < time.time():
                logger.debug("[CacheManager] EXPIRED: %s", cache_key)
                cache_file.unlink(missing_ok=True)
                return None
            logger.debug("[CacheManager] HIT: %s", cache_key)
            return entry["data"]
        except Exception as exc:
            logger.warning("[CacheManager] 讀取失敗 %s: %s", cache_key, exc)
            return None

    def set(self, cache_key: str, data: dict, ttl: Optional[int] = None) -> bool:
        """寫入快取，回傳是否成功。"""
        ttl = ttl if ttl is not None else self.default_ttl
        cache_file = self._key_to_path(cache_key)
        entry = {
            "data": data,
            "expires_at": time.time() + ttl,
            "cache_key": cache_key,
        }
        try:
            with cache_file.open("wb") as f:
                pickle.dump(entry, f)
            logger.debug("[CacheManager] SET: %s (TTL=%ds)", cache_key, ttl)
            return True
        except Exception as exc:
            logger.warning("[CacheManager] 寫入失敗 %s: %s", cache_key, exc)
            return False

    def invalidate(self, pattern: str) -> int:
        """刪除符合 glob pattern 的快取檔案，回傳已刪除數量。"""
        deleted = 0
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
                deleted += 1
            except Exception:
                pass
        logger.info("[CacheManager] 清除 %d 個快取檔案（pattern: %s）", deleted, pattern)
        return deleted

    def purge_expired(self) -> int:
        """清除所有已過期的快取，回傳清除數量。"""
        now = time.time()
        deleted = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with cache_file.open("rb") as f:
                    entry = pickle.load(f)
                if entry.get("expires_at", 0) < now:
                    cache_file.unlink()
                    deleted += 1
            except Exception:
                # 損毀的快取檔案也清除
                try:
                    cache_file.unlink()
                    deleted += 1
                except Exception:
                    pass
        logger.info("[CacheManager] 已清除 %d 個過期快取", deleted)
        return deleted

    # ── Key 生成 ───────────────────────────────────────────────────

    @staticmethod
    def generate_key(
        function_id: int | str,
        year: int | str | None = None,
        race: str | None = None,
        session: str | None = None,
        driver: str | None = None,
        driver2: str | None = None,
        **extra: Any,
    ) -> str:
        """產生標準化的快取 key。

        格式：f{function_id}_{year}_{race}_{session}[_{driver}[_{driver2}]][_{hash(extra)}]
        所有部分都是小寫並去除空白。
        """
        parts = [f"f{function_id}"]
        if year:
            parts.append(str(year))
        if race:
            parts.append(str(race).lower().replace(" ", "_"))
        if session:
            parts.append(str(session).upper())
        if driver:
            parts.append(str(driver).upper())
        if driver2:
            parts.append(str(driver2).upper())
        if extra:
            # 對額外參數做短 hash，避免 key 過長
            extra_hash = hashlib.md5(
                json.dumps(extra, sort_keys=True, default=str).encode()
            ).hexdigest()[:8]
            parts.append(extra_hash)
        return "_".join(parts)

    # ── 私有方法 ───────────────────────────────────────────────────

    def _key_to_path(self, cache_key: str) -> Path:
        """將快取 key 轉換為檔案路徑。"""
        safe_key = cache_key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.pkl"

    # ── 統計資訊 ───────────────────────────────────────────────────

    def stats(self) -> dict:
        """回傳快取目錄的統計資訊。"""
        now = time.time()
        total = 0
        valid = 0
        expired = 0
        total_size = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            total += 1
            total_size += cache_file.stat().st_size
            try:
                with cache_file.open("rb") as f:
                    entry = pickle.load(f)
                if entry.get("expires_at", 0) >= now:
                    valid += 1
                else:
                    expired += 1
            except Exception:
                expired += 1
        return {
            "total_files": total,
            "valid": valid,
            "expired": expired,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }


# ── 單例（供全域使用）─────────────────────────────────────────────

_default_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """取得全域預設的 CacheManager 實例。"""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager()
    return _default_cache_manager


# ── @cached 裝飾器 ────────────────────────────────────────────────

def cached(ttl: int = 3600, cache_dir: Path | str | None = None):
    """方法裝飾器：自動快取 BaseAnalyzer._run() 的結果。

    用法：
        class MyAnalyzer(BaseAnalyzer):
            @cached(ttl=1800)
            def _run(self) -> dict:
                ...
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            manager = CacheManager(cache_dir) if cache_dir else get_cache_manager()
            key = manager.generate_key(
                self.function_id,
                year=getattr(self, "year", None),
                race=getattr(self, "race", None),
                session=getattr(self, "session", None),
                driver=getattr(self, "driver", None),
                driver2=getattr(self, "driver2", None),
            )
            cached_data = manager.get(key)
            if cached_data is not None:
                result = cached_data.copy()
                result["cache_used"] = True
                return result
            result = func(self, *args, **kwargs)
            if isinstance(result, dict) and result.get("success"):
                manager.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


__all__ = ["CacheManager", "cached", "get_cache_manager"]
