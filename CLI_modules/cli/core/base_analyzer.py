"""
BaseAnalyzer - 所有 CLI 分析功能的抽象基類
============================================
提供統一的：
- 標準結果格式 _standard_result()
- 統一 try/except 保護 execute()
- data_loader / year / race / session / driver 屬性
- 日誌輸出 _log() / _debug()

使用方式：
    class RainAnalyzer(BaseAnalyzer):
        function_id = 1
        name = "Rain Intensity Analysis"
        category = "weather"

        def _run(self) -> dict:
            # 實際分析邏輯（不需要 try/except）
            data = self.data_loader.get_weather_data(...)
            return self._standard_result(True, data=data)
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """所有分析功能的抽象基類。

    子類必須實作 `_run()` 方法，並宣告類別屬性：
      - function_id: int
      - name: str
      - category: str  (e.g. "weather", "telemetry", "race")
    """

    function_id: int = 0
    name: str = "未命名分析"
    category: str = "general"

    def __init__(
        self,
        data_loader=None,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        driver: Optional[str] = None,
        driver2: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.driver = driver or "VER"
        self.driver2 = driver2 or "LEC"
        self._extra_kwargs = kwargs

    # ── 公開介面 ──────────────────────────────────────────────────────

    def execute(self) -> dict:
        """執行分析，統一 try/except 與計時。子類只需實作 _run()。"""
        start = time.perf_counter()
        try:
            result = self._run()
            elapsed = f"{time.perf_counter() - start:.2f}s"
            result.setdefault("execution_time", elapsed)
            result.setdefault("function_id", str(self.function_id))
            logger.info(
                "[%s] F%s 執行完成 (%s)",
                self.__class__.__name__,
                self.function_id,
                elapsed,
            )
            return result
        except Exception as exc:
            elapsed = f"{time.perf_counter() - start:.2f}s"
            logger.error(
                "[%s] F%s 執行失敗: %s",
                self.__class__.__name__,
                self.function_id,
                exc,
                exc_info=True,
            )
            return self._error_result(str(exc), elapsed)

    # ── 子類必須實作 ──────────────────────────────────────────────────

    @abstractmethod
    def _run(self) -> dict:
        """實際分析邏輯。回傳標準結果字典。"""

    # ── 輔助方法 ──────────────────────────────────────────────────────

    def _standard_result(
        self,
        success: bool,
        *,
        data: Any = None,
        message: str = "",
        cache_used: bool = False,
        **extra: Any,
    ) -> dict:
        """產生標準格式結果字典。"""
        return {
            "success": success,
            "function_id": str(self.function_id),
            "message": message or (f"{self.name} 分析完成" if success else f"{self.name} 失敗"),
            "data": data,
            "cache_used": cache_used,
            **extra,
        }

    def _error_result(self, error_message: str, elapsed: str = "N/A") -> dict:
        """產生失敗結果字典。"""
        return {
            "success": False,
            "function_id": str(self.function_id),
            "message": f"{self.name} 執行失敗: {error_message}",
            "data": None,
            "cache_used": False,
            "error": error_message,
            "execution_time": elapsed,
        }

    def _log(self, message: str) -> None:
        """INFO 等級日誌（取代 print）。"""
        logger.info("[F%s] %s", self.function_id, message)

    def _debug(self, message: str) -> None:
        """DEBUG 等級日誌。"""
        logger.debug("[F%s] %s", self.function_id, message)


__all__ = ["BaseAnalyzer"]
