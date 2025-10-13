#!/usr/bin/env python3
"""
車手積分榜資料載入器
Driver Standings Data Loader

負責載入和轉換 CLI Function 97 輸出的車手積分資料
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-10-12
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List


class DriverStandingsDataLoader(UniversalDataLoader):
    """
    車手積分榜資料載入器
    
    繼承自 UniversalDataLoader，實作車手積分資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=97)
    - 本地 JSON: json/championship_standings_{year}_R{round}.json
    
    資料結構：
    {
        "success": true,
        "data": {
            "driver_standings": [
                {
                    "position": int,
                    "position_text": str,
                    "points": float,
                    "wins": int,
                    "points_delta": float,
                    "driver": {
                        "code": str,
                        "full_name": str,
                        "number": int,
                        "nationality": str
                    },
                    "constructors": [
                        {"name": str, "nationality": str}
                    ]
                }
            ],
            "metadata": {
                "season_year": int,
                "round": int
            }
        }
    }
    """
    
    # CLI 功能編號
    CLI_FUNCTION = 97
    
    # JSON 檔案命名模式
    JSON_PATTERN = "championship_standings_{year}_R*.json"
    
    # 分析類型標識
    ANALYSIS_TYPE = "driver_standings"
    
    def __init__(self, year: str, parent=None):
        """
        初始化資料載入器
        
        Args:
            year: 賽季年份 (例如: "2025")
            parent: 父元件 (用於信號連接)
        """
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)

        # API-ONLY 模式：允許本地 JSON 後備（已存在的檔案）
        self._allow_local_fallback = True
        self._debug(f"[DRIVER_STANDINGS_LOADER] 初始化完成: year={year}")
    
    def _validate_data_format(self, raw_data: Dict[str, Any]) -> bool:
        """
        驗證資料格式是否符合預期
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            bool: 驗證是否通過
        """
        if not isinstance(raw_data, dict):
            self._debug("[VALIDATION] ❌ 數據必須是 dict")
            return False
        
        if not raw_data.get("success"):
            self._debug(f"[VALIDATION] ❌ success=False: {raw_data.get('message')}")
            return False
        
        data = raw_data.get("data")
        if not isinstance(data, dict):
            self._debug("[VALIDATION] ❌ 缺少 data 欄位")
            return False
        
        drivers = data.get("drivers")
        if not isinstance(drivers, list):
            self._debug("[VALIDATION] ❌ drivers 必須是列表")
            return False
        
        if len(drivers) == 0:
            self._debug("[VALIDATION] ⚠️  drivers 為空")
            return False
        
        # 檢查第一筆資料結構
        first_entry = drivers[0]
        required_fields = ["position", "points", "driver"]
        for field in required_fields:
            if field not in first_entry:
                self._debug(f"[VALIDATION] ❌ 缺少欄位: {field}")
                return False
        
        driver_info = first_entry.get("driver")
        if not isinstance(driver_info, dict):
            self._debug("[VALIDATION] ❌ driver 必須是 dict")
            return False
        
        self._debug(f"[VALIDATION] ✅ 數據驗證通過 ({len(drivers)} 位車手)")
        return True
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """
        構建檔案名稱搜尋模式
        
        Args:
            **kwargs: 搜尋參數（包含 year）
            
        Returns:
            List[str]: 檔案名稱模式列表
        """
        year = kwargs.get("year", self.year)
        
        # 積分榜檔案命名模式：championship_standings_{year}_R{round}.json
        patterns = [
            f"championship_standings_{year}_R*.json",  # 任意回合
            f"championship_standings_{year}*.json",    # 任意格式
        ]
        
        self._debug(f"[PATTERN] 搜尋模式: {patterns}")
        return patterns
    
    def _transform_data_for_display(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將原始數據轉換為 GUI 顯示格式
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            轉換後的數據（適用於 Widget 顯示）
        """
        data = raw_data.get("data", {})
        drivers = data.get("drivers", [])
        metadata = data.get("metadata", {})
        
        # 轉換為表格友好格式
        transformed_rows = []
        for entry in drivers:
            driver_info = entry.get("driver", {})
            constructors = entry.get("constructors", [])
            team_name = constructors[0].get("name", "Unknown") if constructors else "Unknown"
            
            # 移除 " F1 Team" 後綴
            team_name = team_name.replace(" F1 Team", "").strip()
            
            transformed_rows.append({
                "position": entry.get("position"),
                "position_text": entry.get("position_text"),
                "driver_code": driver_info.get("code", "N/A"),
                "driver_name": driver_info.get("full_name", "Unknown"),
                "team": team_name,
                "points": entry.get("points"),
                "wins": entry.get("wins", 0),
                "points_delta": entry.get("points_delta"),
                "nationality": driver_info.get("nationality", "Unknown")
            })
        
        self._debug(f"[TRANSFORM] ✅ 轉換 {len(transformed_rows)} 位車手資料")
        
        return {
            "standings": transformed_rows,
            "metadata": metadata,
            "season_year": metadata.get("season_year", int(self.year)),
            "round": metadata.get("round", 0)
        }
    
    def load_data(self, force_refresh: bool = False):
        """
        載入車手積分資料
        
        Args:
            force_refresh: 是否強制刷新（忽略緩存）
        """
        params = {
            "year": self.year,
            "function_id": self.CLI_FUNCTION,
            "force_refresh": force_refresh
        }
        
        self._debug(f"[LOAD] 開始載入車手積分資料: {params}")
        
        # 調用基類的 load_data() 方法
        super().load_data(**params)
