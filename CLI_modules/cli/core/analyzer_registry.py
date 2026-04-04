"""
AnalyzerRegistry - 分析功能註冊系統
=====================================
替代 function_mapper.py God Class 中的分派邏輯。

使用裝飾器註冊分析功能：

    from CLI_modules.cli.core.analyzer_registry import AnalyzerRegistry
    from CLI_modules.cli.core.base_analyzer import BaseAnalyzer

    @AnalyzerRegistry.register(function_id=1, name="Rain Intensity", category="weather")
    class RainIntensityAnalyzer(BaseAnalyzer):
        def _run(self) -> dict:
            ...

執行功能：

    result = AnalyzerRegistry.execute(1, data_loader=loader, year=2025, race="Japan", session="R")

向後相容：
    現有的 function_mapper.py 不受影響，Registry 僅提供新架構的入口點。
    當 Registry 找不到功能時，會回傳 success=False 而不是拋出例外。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type

from CLI_modules.cli.core.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerEntry:
    """已註冊分析功能的元資料。"""
    function_id: int
    name: str
    category: str
    analyzer_class: Type[BaseAnalyzer]
    tags: list[str] = field(default_factory=list)


class AnalyzerRegistry:
    """全域分析功能註冊系統（類別方法介面）。"""

    _analyzers: Dict[int, AnalyzerEntry] = {}

    # ── 裝飾器：註冊分析器 ─────────────────────────────────────────

    @classmethod
    def register(
        cls,
        function_id: int,
        name: str = "",
        category: str = "general",
        tags: list[str] | None = None,
    ):
        """裝飾器：將分析類別註冊到 Registry。

        範例：
            @AnalyzerRegistry.register(function_id=1, name="Rain Analysis", category="weather")
            class RainAnalyzer(BaseAnalyzer):
                ...
        """
        def decorator(analyzer_cls: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
            if not issubclass(analyzer_cls, BaseAnalyzer):
                raise TypeError(
                    f"{analyzer_cls.__name__} 必須繼承 BaseAnalyzer"
                )
            entry = AnalyzerEntry(
                function_id=function_id,
                name=name or analyzer_cls.__name__,
                category=category,
                analyzer_class=analyzer_cls,
                tags=tags or [],
            )
            # 設定類別屬性
            analyzer_cls.function_id = function_id
            analyzer_cls.name = entry.name
            analyzer_cls.category = category

            if function_id in cls._analyzers:
                logger.warning(
                    "AnalyzerRegistry: 功能 %d (%s) 已存在，將被 %s 覆蓋",
                    function_id,
                    cls._analyzers[function_id].name,
                    entry.name,
                )
            cls._analyzers[function_id] = entry
            logger.debug("AnalyzerRegistry: 已註冊 F%d - %s [%s]", function_id, entry.name, category)
            return analyzer_cls

        return decorator

    # ── 執行功能 ───────────────────────────────────────────────────

    @classmethod
    def execute(cls, function_id: int, **kwargs: Any) -> dict:
        """執行指定 function_id 的分析器。

        找不到功能時回傳 success=False，不拋出例外。
        所有參數透過 kwargs 傳遞至分析器 __init__。
        """
        entry = cls._analyzers.get(function_id)
        if entry is None:
            return {
                "success": False,
                "function_id": str(function_id),
                "message": f"Registry 中找不到功能 {function_id}",
                "data": None,
            }
        try:
            analyzer = entry.analyzer_class(**kwargs)
            return analyzer.execute()
        except Exception as exc:
            logger.error("AnalyzerRegistry.execute(%d) 失敗: %s", function_id, exc, exc_info=True)
            return {
                "success": False,
                "function_id": str(function_id),
                "message": f"執行 {entry.name} 時發生例外: {exc}",
                "data": None,
                "error": str(exc),
            }

    # ── 查詢介面 ───────────────────────────────────────────────────

    @classmethod
    def get_entry(cls, function_id: int) -> Optional[AnalyzerEntry]:
        """回傳指定 function_id 的 AnalyzerEntry，不存在則回傳 None。"""
        return cls._analyzers.get(function_id)

    @classmethod
    def list_functions(cls) -> list[dict]:
        """回傳所有已註冊功能的摘要列表。"""
        return [
            {
                "function_id": entry.function_id,
                "name": entry.name,
                "category": entry.category,
                "tags": entry.tags,
                "class": entry.analyzer_class.__name__,
            }
            for entry in sorted(cls._analyzers.values(), key=lambda e: e.function_id)
        ]

    @classmethod
    def list_categories(cls) -> list[str]:
        """回傳所有已使用的功能分類。"""
        return sorted({entry.category for entry in cls._analyzers.values()})

    @classmethod
    def registered_ids(cls) -> list[int]:
        """回傳所有已註冊的 function_id 排序列表。"""
        return sorted(cls._analyzers.keys())

    @classmethod
    def is_registered(cls, function_id: int) -> bool:
        """檢查指定 function_id 是否已在 Registry 中。"""
        return function_id in cls._analyzers

    @classmethod
    def clear(cls) -> None:
        """清空 Registry（主要用於測試）。"""
        cls._analyzers.clear()


__all__ = ["AnalyzerRegistry", "AnalyzerEntry"]
