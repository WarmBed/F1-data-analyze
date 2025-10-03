#!/usr/bin/env python3
"""
TrackDataLoader - F1T 賽道分析專用數據載入器
==============================================

基於通用數據載入器架構實現的賽道分析數據載入器，負責：
- 賽道位置數據的載入和處理
- CLI -f2 (賽道分析) 的自動調用
- JSON 數據格式的解析和正規化
- 賽道地圖數據的快取管理

數據來源：CLI -f2 生成的賽道位置 JSON 檔案
輸出格式：標準化的賽道分析數據結構

Author: F1T Team
Date: 2025-09-11
Version: 1.0.0
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 導入通用基礎類別
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    # 備用路徑（相對導入）
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig


class TrackUniversalDataLoader(UniversalDataLoader):
    """
    賽道分析通用數據載入器
    
    基於 UniversalDataLoader 實現的賽道專門載入器，
    支援 CLI -f2 自動調用和賽道數據處理。
    """
    
    def __init__(self, parent=None):
        # 配置賽道分析參數
        config = AnalysisConfig(
            display_name="賽道分析",
            debug_prefix="TRACK_ANALYSIS",
            data_source="json",
            cli_function="2",  # CLI -f2 賽道分析
            file_patterns=["track_positions_*_{year}_{race}_{session}.json"],
            cache_pattern="track_analysis_{year}_{race}_{session}.pkl",
            description="賽道位置和地圖數據分析",
            search_directories=["json", "json_exports", "cache"]
        )
        
        # 註冊賽道分析類型
        analysis_type = "track_analysis"
        if analysis_type not in self.ANALYSIS_TYPES:
            self.register_analysis_type(analysis_type, config)
        
        super().__init__(analysis_type, parent)
        print(f"[TRACK_ANALYSIS] 初始化完成，使用專門的 TrackDataLoader")
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        required_params = ["year", "race", "session"]
        for param in required_params:
            if param not in params:
                print(f"[TRACK_ANALYSIS] 缺少必要參數: {param}")
                return False
        
        # 驗證參數類型和範圍
        year = params.get("year")
        if not isinstance(year, int) or year < 2020 or year > 2030:
            print(f"[TRACK_ANALYSIS] 年份參數無效: {year}")
            return False
        
        return True
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """構建檔案名稱搜尋模式"""
        year = kwargs.get("year", "????")
        race = kwargs.get("race", "*")
        session = kwargs.get("session", "*")
        
        patterns = [
            f"track_positions_{year}_{race}_{session}.json",
            f"track_data_{year}_{race}_{session}.json",
            f"*track*_{year}_{race}_{session}.json",
            f"{race}_{year}_track_*.json"
        ]
        
        return patterns
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 透過 CLI 工具生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        """
        print(f"[TRACK_ANALYSIS] ⚠️  [API-ONLY] CLI 調用已禁用")
        print(f"[TRACK_ANALYSIS] 💡 提示: 請使用 API 獲取賽道分析數據")
        return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(raw_data, dict):
            print(f"[TRACK_ANALYSIS] 數據不是字典格式")
            return False
        
        # 檢查必要的鍵 - 適應新的JSON格式
        required_keys = ["position_analysis", "session_info"]
        missing_keys = [key for key in required_keys if key not in raw_data]
        
        if missing_keys:
            print(f"[TRACK_ANALYSIS] 缺少必要鍵: {missing_keys}")
            return False
        
        # 檢查賽道數據結構
        position_analysis = raw_data.get("position_analysis", {})
        if not isinstance(position_analysis, dict):
            print(f"[TRACK_ANALYSIS] position_analysis 格式錯誤")
            return False
        
        return True
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理數據為標準格式"""
        try:
            print(f"[TRACK_ANALYSIS] 開始處理賽道分析數據...")
            
            # 提取基本信息
            race_info = raw_data.get("race_info", {})
            track_data = raw_data.get("track_data", {})
            
            # 處理賽道位置數據
            positions = self._process_track_positions(track_data)
            
            # 處理賽道統計數據
            statistics = self._process_track_statistics(track_data)
            
            # 構建標準化輸出
            processed_data = {
                "metadata": {
                    "analysis_type": "track_analysis",
                    "year": race_info.get("year"),
                    "race": race_info.get("race"),
                    "session": race_info.get("session"),
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "CLI_f2"
                },
                "track_positions": positions,
                "track_statistics": statistics,
                "race_info": race_info,
                "raw_data": raw_data
            }
            
            print(f"[TRACK_ANALYSIS] 數據處理完成")
            return processed_data
            
        except Exception as e:
            print(f"[TRACK_ANALYSIS] 數據處理失敗: {e}")
            return {}
    
    def generate_cli_command(self, year: int, race: str, session: str) -> List[str]:
        """生成 CLI -f2 賽道分析命令"""
        return [
            "python", "f1_analysis_modular_main.py",
            "-f", "2",  # 賽道分析功能
            "-y", str(year),
            "-r", race,
            "-s", session
        ]
    
    def validate_json_data(self, data: Dict[str, Any]) -> bool:
        """驗證賽道分析 JSON 數據格式（向後兼容）"""
        return self._validate_data_format(data)
    
    def process_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理和正規化賽道分析數據（向後兼容）"""
        return self._process_data(data)
    
    def _process_track_positions(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理賽道位置數據"""
        positions = track_data.get("positions", track_data.get("coordinates", {}))
        
        if not positions:
            return {}
        
        processed_positions = {
            "total_points": len(positions) if isinstance(positions, list) else 0,
            "coordinates": positions,
            "bounds": self._calculate_track_bounds(positions)
        }
        
        return processed_positions
    
    def _process_track_statistics(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理賽道統計數據"""
        statistics = {
            "lap_count": track_data.get("lap_count", 0),
            "track_length": track_data.get("track_length", 0),
            "sector_count": track_data.get("sector_count", 3),
            "corner_count": track_data.get("corner_count", 0)
        }
        
        return statistics
    
    def _calculate_track_bounds(self, positions) -> Dict[str, float]:
        """計算賽道邊界"""
        if not positions or not isinstance(positions, list):
            return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
        
        try:
            x_coords = [pos.get("x", 0) for pos in positions if isinstance(pos, dict)]
            y_coords = [pos.get("y", 0) for pos in positions if isinstance(pos, dict)]
            
            if not x_coords or not y_coords:
                return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
            
            return {
                "min_x": min(x_coords),
                "max_x": max(x_coords),
                "min_y": min(y_coords),
                "max_y": max(y_coords)
            }
        except Exception:
            return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}


class TrackDataLoader:
    """
    賽道分析數據載入器
    
    提供簡化的介面來載入賽道分析數據，
    內部使用 TrackUniversalDataLoader 實現。
    """
    
    def __init__(self, parent=None):
        self.universal_loader = TrackUniversalDataLoader(parent)
        print(f"[TELEMETRY DEBUG] 初始化 賽道分析 載入器")
    
    def load_data(self, year: int, race: str, session: str, **kwargs) -> Dict[str, Any]:
        """載入賽道分析數據"""
        print(f"[TRACK_LOADER DEBUG] 接收參數: year={year} (類型: {type(year)}), race={race}, session={session}")
        # 將位置參數轉換為關鍵字參數傳遞給 universal_loader
        result = self.universal_loader.load_data(
            year=year, 
            race=race, 
            session=session, 
            **kwargs
        )
        print(f"[TRACK_LOADER DEBUG] universal_loader.load_data 返回: {type(result)}")
        return result
    
    def get_cache_status(self, year: int, race: str, session: str) -> Dict[str, Any]:
        """獲取快取狀態"""
        # 簡單的快取狀態實現
        return {
            "has_cache": False,
            "cache_path": None,
            "last_modified": None
        }


def create_track_data_loader(parent=None) -> TrackDataLoader:
    """
    創建賽道數據載入器實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        TrackDataLoader: 賽道數據載入器實例
    """
    return TrackDataLoader(parent)


# 測試函數
def test_track_data_loader():
    """測試賽道數據載入器"""
    try:
        print("🧪 測試賽道數據載入器...")
        
        # 創建載入器
        loader = create_track_data_loader()
        print("✅ 載入器創建成功")
        
        # 測試快取狀態
        cache_status = loader.get_cache_status(2025, "Japan", "R")
        print(f"📊 快取狀態: {cache_status}")
        
        print("✅ 賽道數據載入器測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_track_data_loader()
