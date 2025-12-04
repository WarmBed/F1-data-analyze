#!/usr/bin/env python3
"""
正賽預測資料載入器
Race Prediction Data Loader

負責載入和轉換 CLI Function 80 輸出的正賽預測資料
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-11-27
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from core.gui_i18n import tr
from typing import Dict, Any, Optional, List


class RacePredictionDataLoader(UniversalDataLoader):
    """
    正賽預測資料載入器
    
    繼承自 UniversalDataLoader，實作正賽預測資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=80)
    - 本地 JSON: json/prediction/dynamic_team_rating_*.json
    
    資料結構：
    {
        "success": true,
        "data": {
            "current_ratings": {
                "rankings": [{"team": str, "rating": float}, ...]
            },
            "driver_team_mapping": {"VER": "Red Bull Racing", ...},
            "timestamp": str
        }
    }
    """
    
    # CLI 功能編號
    CLI_FUNCTION = 80  # Function 80 - 動態車隊評級分析
    
    # JSON 檔案命名模式
    JSON_PATTERN = "dynamic_team_rating_{year}_{race}.json"
    
    # 分析類型標識
    ANALYSIS_TYPE = "race_prediction"
    
    def __init__(self, year: str = None, race: str = None, parent=None):
        """
        初始化資料載入器
        
        Args:
            year: 賽季年份 (例如: "2025")
            race: 賽事名稱 (例如: "Japan", "Austria")
            parent: 父元件 (用於信號連接)
        """
        # 調用基類 __init__
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year) if year else "2025"
        self.race = race or "Japan"

        # API-ONLY 模式：停用本地 JSON 後備
        self._allow_local_fallback = False
        self._debug("[RACE_PRED_LOADER] API-ONLY mode enabled")
        
        self._debug(f"[RACE_PRED_LOADER] Initialized: {self.year} {self.race}")
    
    def _validate_data_format(self, data: Any) -> bool:
        """
        驗證資料格式是否符合預期
        
        檢查項目：
        1. 資料必須是字典
        2. 必須包含 "metadata" + "predictions"（新格式）
        3. 或包含 "data" 內的 "current_ratings"（舊格式）
        
        Args:
            data: 待驗證的資料
            
        Returns:
            bool: 資料格式是否正確
        """
        try:
            # 檢查基本類型
            if not isinstance(data, dict):
                self._debug("[VALIDATE] Data is not a dictionary")
                return False
            
            # 檢查新格式（Q->R 預測 JSON）
            if "metadata" in data and "predictions" in data:
                predictions = data.get("predictions", [])
                if predictions:
                    self._debug(f"[VALIDATE] New format detected: {len(predictions)} predictions")
                    return True
            
            # 檢查 API 回應格式
            if "success" in data:
                if not data.get("success"):
                    self._debug("[VALIDATE] API returned success=false")
                    return False
                
                # 檢查 data 下是否有 predictions（新格式）
                inner_data = data.get("data", {})
                if "predictions" in inner_data or "predictions" in data:
                    self._debug("[VALIDATE] API response with predictions")
                    return True
                
                # 檢查舊格式（車隊評級）
                if isinstance(inner_data, dict):
                    current_ratings = inner_data.get("current_ratings", {})
                    rankings = current_ratings.get("rankings", [])
                    if rankings:
                        self._debug(f"[VALIDATE] Old format: {len(rankings)} team ratings")
                        return True
            
            # 檢查直接的資料格式（本地 JSON）
            if "predictions" in data or "current_ratings" in data:
                self._debug("[VALIDATE] Local JSON format detected")
                return True
            
            self._debug("[VALIDATE] Unknown data format")
            return False
            
        except Exception as e:
            self._debug(f"[VALIDATE] Validation error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        處理數據為標準格式
        
        重寫基類方法，確保調用 _transform_data_for_display() 進行數據轉換
        
        Args:
            raw_data: 原始數據
            
        Returns:
            Dict[str, Any]: 處理並轉換後的數據
        """
        self._debug("[PROCESS_DATA] Processing data...")
        
        # 基本類型檢查
        if isinstance(raw_data, dict):
            # 如果已經是顯示格式，直接返回
            if "metadata" in raw_data and "predictions" in raw_data:
                self._debug("[PROCESS_DATA] Data already in display format")
                return raw_data
            
            # 調用轉換方法
            transformed_data = self._transform_data_for_display(raw_data)
            self._debug("[PROCESS_DATA] Data transformation complete")
            return transformed_data
        
        if raw_data is None:
            self._debug("[PROCESS_DATA] Raw data is None")
            return {}
        
        self._debug("[PROCESS_DATA] Unexpected data type, wrapping")
        return {"raw_data": raw_data}
    
    def _transform_data_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換資料為顯示格式
        
        支援兩種資料格式：
        1. 新格式（Q->R 預測）：包含 metadata 和 predictions
        2. 舊格式（車隊評級）：包含 current_ratings 和 driver_team_mapping
        
        Args:
            data: 原始資料
            
        Returns:
            Dict: 轉換後的資料（統一格式）
        """
        try:
            self._debug("[TRANSFORM] Starting data transformation...")
            
            # 處理 API 回應包裝
            if "success" in data and "data" not in data:
                # 新 API 格式：直接在根級別有 predictions
                if "predictions" in data:
                    pass  # 繼續處理
                else:
                    self._debug("[TRANSFORM] API success but no data found")
                    return self._empty_result()
            
            # 檢查是否是新格式（直接包含 predictions）
            if "predictions" in data and "metadata" in data:
                self._debug("[TRANSFORM] New format (Q->R prediction) detected")
                return self._transform_new_format(data)
            
            # 檢查是否在 data 包裝內
            if "data" in data:
                inner_data = data.get("data", {})
                if "predictions" in inner_data:
                    self._debug("[TRANSFORM] New format in data wrapper")
                    return self._transform_new_format(inner_data)
            
            # 處理舊格式（車隊評級）
            self._debug("[TRANSFORM] Old format (team rating) detected")
            return self._transform_old_format(data)
            
        except Exception as e:
            self._debug(f"[TRANSFORM] Transformation error: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _transform_new_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換新格式（Q->R 預測）資料
        
        新格式已包含完整的 predictions，只需統一欄位名稱
        """
        try:
            metadata = data.get("metadata", {})
            predictions = data.get("predictions", [])
            team_ratings = data.get("team_ratings", {})
            
            self._debug(f"[TRANSFORM_NEW] {len(predictions)} predictions found")
            
            # 統一欄位名稱（rank_change -> position_change）
            for pred in predictions:
                if "rank_change" in pred and "position_change" not in pred:
                    pred["position_change"] = pred.get("rank_change")
            
            # 展平 team_ratings 結構（從嵌套格式轉為扁平格式）
            # JSON 格式: {"McLaren": {"current": 6.30, "base": 6.00}, ...}
            # Widget 期望: {"McLaren": 6.30, ...}
            flat_team_ratings = {}
            for team_name, rating_data in team_ratings.items():
                if isinstance(rating_data, dict):
                    flat_team_ratings[team_name] = rating_data.get("current", 5.0)
                else:
                    flat_team_ratings[team_name] = rating_data
            
            self._debug(f"[TRANSFORM_NEW] Flattened {len(flat_team_ratings)} team ratings")
            
            # 確保 metadata 包含必要欄位
            metadata.setdefault("track", self.race)
            metadata.setdefault("year", int(self.year) if self.year else 2025)
            metadata.setdefault("total_drivers", len(predictions))
            
            # 計算準確度統計
            if metadata.get("has_actual_results"):
                accuracy = metadata.get("accuracy", {})
                metadata["top1_correct"] = accuracy.get("top1_correct", False)
                metadata["top3_correct"] = accuracy.get("top3_correct", 0)
            
            # 添加可靠性評估
            if flat_team_ratings:
                avg_rating = sum(flat_team_ratings.values()) / len(flat_team_ratings)
            else:
                avg_rating = 5.0
            
            metadata["avg_team_rating"] = avg_rating
            metadata["reliability_text"], metadata["reliability_color"] = self._get_reliability(avg_rating)
            
            return {
                "metadata": metadata,
                "predictions": predictions,
                "team_ratings": flat_team_ratings,  # 使用展平後的評級
                "rating_changes": data.get("rating_changes", [])
            }
            
        except Exception as e:
            self._debug(f"[TRANSFORM_NEW] Error: {e}")
            return self._empty_result()
    
    def _transform_old_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換舊格式（車隊評級）資料
        
        舊格式需要從車隊評級構建 predictions
        """
        try:
            # 提取 API 數據
            if "success" in data:
                api_data = data.get("data", {})
            else:
                api_data = data
            
            # 獲取車隊評級
            current_ratings = api_data.get("current_ratings", {})
            rankings = current_ratings.get("rankings", [])
            
            # 建立車隊評級字典
            team_ratings = {}
            for item in rankings:
                team_name = item.get("team", "Unknown")
                rating = item.get("rating", 5.0)
                team_ratings[team_name] = rating
            
            self._debug(f"[TRANSFORM_OLD] Found {len(team_ratings)} teams")
            
            # 從 driver_team_mapping 獲取車手資訊
            driver_teams = api_data.get("driver_team_mapping", {})
            
            if not driver_teams:
                driver_teams = self._get_default_driver_mapping()
                self._debug("[TRANSFORM_OLD] Using default driver mapping")
            
            # 構建預測列表（基於車隊評級排序）
            predictions = []
            
            sorted_drivers = sorted(
                driver_teams.items(),
                key=lambda x: team_ratings.get(x[1], 5.0),
                reverse=True
            )
            
            for rank, (driver, team) in enumerate(sorted_drivers, 1):
                team_rating = team_ratings.get(team, 5.0)
                
                predictions.append({
                    "rank": rank,
                    "driver": driver,
                    "team": team,
                    "team_rating": team_rating,
                    "q_position": rank,
                    "predicted_position": rank,
                    "actual_position": None,
                    "position_change": None
                })
            
            self._debug(f"[TRANSFORM_OLD] Created {len(predictions)} predictions")
            
            # 構建 metadata
            avg_rating = sum(team_ratings.values()) / len(team_ratings) if team_ratings else 5.0
            reliability_text, reliability_color = self._get_reliability(avg_rating)
            
            metadata = {
                "track": self.race,
                "year": int(self.year) if self.year else 2025,
                "session": "R",
                "prediction_time": api_data.get("timestamp", ""),
                "model_version": "dynamic_team_rating_v1.0",
                "total_drivers": len(predictions),
                "avg_team_rating": avg_rating,
                "has_actual_results": False,
                "reliability_text": reliability_text,
                "reliability_color": reliability_color
            }
            
            return {
                "metadata": metadata,
                "predictions": predictions,
                "team_ratings": team_ratings,
                "rating_formula": api_data.get("formula", {}),
                "rating_changes": api_data.get("rating_changes", [])
            }
            
        except Exception as e:
            self._debug(f"[TRANSFORM_OLD] Error: {e}")
            return self._empty_result()
    
    def _get_reliability(self, avg_rating: float) -> tuple:
        """計算可靠性評估"""
        if avg_rating >= 6.0:
            return (tr("rating_high", "High Confidence"), "green")
        elif avg_rating >= 4.5:
            return (tr("rating_medium", "Medium Confidence"), "orange")
        else:
            return (tr("rating_low", "Low Confidence"), "red")
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空結果結構"""
        return {
            "metadata": {"track": self.race, "year": int(self.year) if self.year else 2025},
            "predictions": [],
            "team_ratings": {}
        }
    
    def _get_default_driver_mapping(self) -> Dict[str, str]:
        """
        獲取預設車手-車隊映射（2025 賽季）
        
        Returns:
            Dict[str, str]: 車手代碼 -> 車隊名稱
        """
        return {
            "VER": "Red Bull Racing",
            "LAW": "Red Bull Racing",
            "NOR": "McLaren",
            "PIA": "McLaren",
            "LEC": "Ferrari",
            "HAM": "Ferrari",
            "RUS": "Mercedes",
            "ANT": "Mercedes",
            "ALO": "Aston Martin",
            "STR": "Aston Martin",
            "GAS": "Alpine",
            "DOO": "Alpine",
            "ALB": "Williams",
            "SAI": "Williams",
            "TSU": "Racing Bulls",
            "HAD": "Racing Bulls",
            "HUL": "Kick Sauber",
            "BOR": "Kick Sauber",
            "OCO": "Haas F1 Team",
            "BEA": "Haas F1 Team"
        }
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        API-ONLY 模式: 禁止 CLI 調用
        
        根據 API-ONLY 政策，GUI 模組不允許直接調用 CLI 進程
        
        Returns:
            bool: 固定返回 False
        """
        self._debug("[API-ONLY] CLI calls are disabled")
        self._debug("Tip: Use API to get prediction data")
        self._debug("CLI example: python f1_analysis_modular_main.py -f 80")
        return False
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        Args:
            params: 參數字典
            
        Returns:
            bool: 參數是否有效
        """
        # 正賽預測只需要 year 和 race
        required = ["year", "race"]
        for key in required:
            if key not in params:
                self._debug(f"Missing required parameter: {key}")
                return False
        return True
    
    def _build_filename_patterns(self, **params) -> List[str]:
        """
        建立檔案搜尋模式
        
        Args:
            **params: 載入參數 (year, race)
            
        Returns:
            List[str]: 檔案搜尋模式列表
        """
        year = params.get("year", self.year)
        race = params.get("race", self.race)
        
        # 正賽預測的檔案命名模式
        patterns = [
            f"dynamic_team_rating_{year}_{race}.json",
            f"dynamic_team_rating_*.json",
            f"race_prediction_{year}_{race}.json",
            f"*race*prediction*{year}*{race}*.json"
        ]
        
        return patterns


# ========== 測試代碼 ==========
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    print("=" * 60)
    print("Race Prediction Data Loader - Standalone Test")
    print("=" * 60)
    
    # 創建 Qt 應用程式
    app = QApplication(sys.argv)
    
    # 創建測試實例
    loader = RacePredictionDataLoader(
        year="2025",
        race="Japan"
    )
    
    print(f"\nLoader Configuration:")
    print(f"  CLI Function: {loader.CLI_FUNCTION}")
    print(f"  JSON Pattern: {loader.JSON_PATTERN}")
    print(f"  Parameters: {loader.year} {loader.race}")
    
    # 測試檔案搜尋模式
    print(f"\nFile Search Patterns:")
    patterns = loader._build_filename_patterns(
        year=loader.year,
        race=loader.race
    )
    for i, pattern in enumerate(patterns, 1):
        print(f"  {i}. {pattern}")
    
    # 設置信號處理
    def on_data_loaded(data):
        print(f"\nData loaded successfully!")
        
        if "metadata" in data and "predictions" in data:
            metadata = data["metadata"]
            predictions = data["predictions"]
            team_ratings = data.get("team_ratings", {})
            
            print(f"\nData Summary:")
            print(f"  Track: {metadata.get('track', 'N/A')}")
            print(f"  Year: {metadata.get('year', 'N/A')}")
            print(f"  Prediction Count: {len(predictions)}")
            print(f"  Team Ratings: {len(team_ratings)}")
            
            # 顯示前 3 名預測
            print(f"\nTop 3 Predictions:")
            for i, pred in enumerate(predictions[:3]):
                print(
                    f"  {i+1}. {pred['driver']} ({pred['team']}) - "
                    f"Rating: {pred['team_rating']:.2f}"
                )
        
        app.quit()
    
    def on_load_error(error_msg):
        print(f"\nLoad error: {error_msg}")
        app.quit()
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_load_error)
    
    # 啟動載入
    print(f"\nStarting data load...")
    success = loader.load_data(
        year=loader.year,
        race=loader.race
    )
    
    if not success:
        print("Load startup failed")
        sys.exit(1)
    
    # 進入事件循環
    sys.exit(app.exec_())
