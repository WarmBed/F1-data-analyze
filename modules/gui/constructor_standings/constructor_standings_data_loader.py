#!/usr/bin/env python3
"""
車隊積分榜資料載入器
Constructor Standings Data Loader

負責載入和轉換 CLI Function 97 輸出的車隊積分資料
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-10-12
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

from core.logger import get_logger
logger = get_logger(__name__)


class ConstructorStandingsDataLoader(UniversalDataLoader):
    """
    車隊積分榜資料載入器
    
    繼承自 UniversalDataLoader，實作車隊積分資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=97)
    - 本地 JSON: json/championship_standings_{year}_R{round}.json
    
    資料結構：
    {
        "success": true,
        "data": {
            "constructor_standings": [
                {
                    "position": int,
                    "position_text": str,
                    "points": float,
                    "wins": int,
                    "points_delta": float,
                    "constructor": {
                        "id": str,
                        "name": str,
                        "nationality": str
                    }
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
    ANALYSIS_TYPE = "constructor_standings"
    
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
    
    def _validate_data_format(self, raw_data: Dict[str, Any]) -> bool:
        """
        驗證資料格式是否符合預期
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            bool: 驗證是否通過
        """
        if not isinstance(raw_data, dict):
            logger.error("[VALIDATION] ❌ 數據必須是 dict")
            return False
        
        if not raw_data.get("success"):
            logger.error(f"[VALIDATION] ❌ success=False: {raw_data.get('message')}")
            return False
        
        data = raw_data.get("data")
        if not isinstance(data, dict):
            logger.error("[VALIDATION] ❌ 缺少 data 欄位")
            return False
        
        constructors = data.get("constructors")
        if not isinstance(constructors, list):
            logger.error("[VALIDATION] ❌ constructors 必須是列表")
            return False
        
        if len(constructors) == 0:
            logger.warning("[VALIDATION] ⚠️  constructors 為空")
            return False
        
        # 檢查第一筆資料結構
        first_entry = constructors[0]
        required_fields = ["position", "points", "constructor"]
        for field in required_fields:
            if field not in first_entry:
                logger.error(f"[VALIDATION] ❌ 缺少欄位: {field}")
                return False
        
        constructor_info = first_entry.get("constructor")
        if not isinstance(constructor_info, dict):
            logger.error("[VALIDATION] ❌ constructor 必須是 dict")
            return False
        
        logger.info(f"[VALIDATION] ✅ 數據驗證通過 ({len(constructors)} 支車隊)")
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
        
        logger.debug(f"[PATTERN] 搜尋模式: {patterns}")
        return patterns
    
    def _load_team_slug_mapping(self) -> Dict[str, str]:
        """
        通過 API (Function 98) 獲取 team_name → team_slug 映射表
        
        遵循 API-ONLY 模式政策，通過 REST API 獲取數據
        
        Returns:
            Dict[str, str]: {team_name: team_slug} 映射表
        """
        import requests
        from core.api_base_url import resolve_api_base_url
        
        team_slug_map = {}
        
        try:
            api_base = resolve_api_base_url()
            endpoint = f"{api_base}/api/v2/analysis/execute"
            
            logger.debug(f"[TEAM_SLUG_MAP] 調用 API Function 98 獲取車隊顏色數據")
            
            response = requests.post(
                endpoint,
                params={
                    "function_id": 98,
                    "year": int(self.year)
                },
                timeout=15,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 從 API 響應中提取 teams 數據
                    teams_data = data.get("data", {}).get("teams", {})
                    for team_slug, info in teams_data.items():
                        team_name = info.get("team_name")
                        if team_name:
                            team_slug_map[team_name] = team_slug
                    
                    logger.info(f"[TEAM_SLUG_MAP] ✅ API 載入 {len(team_slug_map)} 個映射")
                    return team_slug_map
                else:
                    logger.warning(f"[TEAM_SLUG_MAP] ⚠️ API 返回失敗: {data.get('message')}")
            else:
                logger.warning(f"[TEAM_SLUG_MAP] ⚠️ API 請求失敗: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning("[TEAM_SLUG_MAP] ⚠️ API 請求超時")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[TEAM_SLUG_MAP] ⚠️ API 請求異常: {e}")
        except Exception as e:
            logger.error(f"[TEAM_SLUG_MAP] ❌ 載入失敗: {e}")
        
        # 如果 API 失敗，使用預設映射表作為後備
        # 這是為了確保 EXE 環境中即使 API 不可用也能基本運作
        logger.warning("[TEAM_SLUG_MAP] ⚠️ 使用預設映射表作為後備")
        return {
            "Red Bull Racing": "red-bull-racing",
            "Red Bull": "red-bull-racing",
            "Ferrari": "ferrari",
            "McLaren": "mclaren",
            "Mercedes": "mercedes",
            "Aston Martin": "aston-martin",
            "Alpine": "alpine",
            "Williams": "williams",
            "RB": "rb",
            "Visa Cash App RB": "rb",
            "Kick Sauber": "kick-sauber",
            "Sauber": "kick-sauber",
            "Haas": "haas",
            "Haas F1 Team": "haas",
        }
    
    def _transform_data_for_display(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將原始數據轉換為 GUI 顯示格式
        
        Args:
            raw_data: 原始 JSON 數據
            
        Returns:
            轉換後的數據（適用於 Widget 顯示）
        """
        data = raw_data.get("data", {})
        constructors = data.get("constructors", [])
        metadata = data.get("metadata", {})
        
        # 載入 team_name → team_slug 映射表（用於顏色查詢）
        team_slug_map = self._load_team_slug_mapping()
        
        # 轉換為表格友好格式
        transformed_rows = []
        for entry in constructors:
            constructor_info = entry.get("constructor", {})
            team_name = constructor_info.get("name", "Unknown")
            
            # 移除 " F1 Team" 後綴
            team_name = team_name.replace(" F1 Team", "").strip()
            
            # 查詢對應的 team_slug（用於 color_palette_provider 查詢）
            team_slug = team_slug_map.get(team_name, team_name.lower())
            
            transformed_rows.append({
                "position": entry.get("position"),
                "position_text": entry.get("position_text"),
                "constructor_name": team_name,
                "team_slug": team_slug,  # ✅ 新增：用於顏色查詢
                "points": entry.get("points"),
                "wins": entry.get("wins", 0),
                "points_delta": entry.get("points_delta"),
                "nationality": constructor_info.get("nationality", "Unknown")
            })
        
        logger.info(f"[TRANSFORM] ✅ 轉換 {len(transformed_rows)} 支車隊資料")
        
        return {
            "standings": transformed_rows,
            "metadata": metadata,
            "season_year": metadata.get("season_year", int(self.year)),
            "round": metadata.get("resolved_round", metadata.get("round", 0))  # ✅ 優先使用 resolved_round
        }
    
    def load_data(self, force_refresh: bool = False):
        """
        載入車隊積分資料
        
        Args:
            force_refresh: 是否強制刷新（忽略緩存）
        """
        params = {
            "year": self.year,
            "function_id": self.CLI_FUNCTION,
            "force_refresh": force_refresh
        }
        
        logger.debug(f"[LOAD] 開始載入車隊積分資料: {params}")
        
        # 調用基類的 load_data() 方法
        super().load_data(**params)
