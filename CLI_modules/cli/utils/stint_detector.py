#!/usr/bin/env python3
"""
Stint Detector - 共用 Stint 偵測模組

從 F120 (fp2_corner_all_laps_analysis.py) 抽取的共用 stint 偵測邏輯
可被 F120, F121, F122 等模組複用

參考實現：Long Run Calculator 的邏輯

作者: F1T Team
日期: 2026-01-19
版本: 1.0.0
"""

from typing import Any, Dict, List, Optional
import pandas as pd


class StintDetector:
    """
    Stint 偵測器
    
    使用 FastF1 的 Stint 欄位進行分組偵測
    """
    
    # 常數配置
    MIN_CONSECUTIVE_LAPS = 1  # 允許所有 stint（GUI 會顯示全部供用戶選擇）
    OUTLAP_TIME_THRESHOLD = 5.0  # 秒 - 比平均慢超過此值視為 outlap
    MAX_LAP_TIME_STDDEV = 1.5  # 秒 - 低於此標準差視為穩定的 long run
    LONG_RUN_MIN_LAPS = 4  # Long Run 最少需要的圈數
    
    def __init__(self, debug: bool = False):
        """
        初始化 Stint 偵測器
        
        Args:
            debug: 是否輸出調試信息
        """
        self.debug = debug
    
    def detect_stints(self, driver_laps: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        偵測車手的所有 stint
        
        完全參考 Long Run Calculator 的邏輯：
        1. 使用 FastF1 的 Stint 欄位進行分組
        2. 排除 PitIn/PitOut 圈和無效圈
        3. 排除 outlap（比平均慢超過閾值的圈）
        4. 計算穩定性分數判斷是否為 long run
        
        Args:
            driver_laps: 車手的圈數 DataFrame（需包含 Stint, LapNumber, LapTime 等欄位）
        
        Returns:
            List of stint dictionaries:
            [
                {
                    "stint_id": int,
                    "compound": str,
                    "lap_range": [start_lap, end_lap],
                    "lap_count": int,
                    "type": "long_run" | "quali_sim" | "unknown",
                    "is_long_run": bool,
                    "confidence": float,
                    "stddev": float,
                    "laps_detail": [
                        {
                            "lap_number": int,
                            "lap_time_seconds": float,
                            "tyre_life": int | None
                        },
                        ...
                    ]
                },
                ...
            ]
        """
        try:
            # 檢查是否有 Stint 欄位
            if 'Stint' not in driver_laps.columns:
                if self.debug:
                    print("  [STINT_DETECTOR] 沒有 Stint 欄位，無法偵測 stint")
                return []
            
            stints = []
            
            # 按 FastF1 的 Stint 欄位分組
            stint_groups = driver_laps.groupby('Stint', sort=True)
            
            for stint_num, stint_laps_df in stint_groups:
                if pd.isna(stint_num):
                    continue
                
                stint_id = int(stint_num)
                
                # Step 1: 過濾 - 排除 pit 圈和無效圈
                valid_laps = self._filter_valid_laps(stint_laps_df)
                
                # 如果沒有有效圈，跳過此 stint
                if not valid_laps:
                    continue
                
                # Step 2: 排除 outlap
                clean_laps = self._remove_outlaps(valid_laps)
                
                # 如果過濾後沒有圈數，使用原始有效圈
                if not clean_laps:
                    clean_laps = valid_laps
                
                # Step 3: 計算穩定性分數
                stddev, is_long_run, confidence = self._calculate_stability(clean_laps)
                
                # Step 4: 獲取 compound
                compound = clean_laps[0]['compound'] if clean_laps else 'UNKNOWN'
                
                # Step 5: 建構 stint 資料
                stint_data = self._build_stint_data(
                    stint_id=stint_id,
                    clean_laps=clean_laps,
                    compound=compound,
                    stddev=stddev,
                    is_long_run=is_long_run,
                    confidence=confidence
                )
                stints.append(stint_data)
            
            if self.debug:
                print(f"  [STINT_DETECTOR] 偵測到 {len(stints)} 個 stint")
            
            return stints
            
        except Exception as e:
            if self.debug:
                print(f"  [STINT_DETECTOR] Stint 偵測失敗: {e}")
                import traceback
                traceback.print_exc()
            return []
    
    def _filter_valid_laps(self, stint_laps_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        過濾有效圈 - 排除 pit 圈和無效圈
        
        Args:
            stint_laps_df: 單一 stint 的圈數 DataFrame
        
        Returns:
            有效圈列表
        """
        valid_laps = []
        
        for idx, lap in stint_laps_df.iterrows():
            is_pit_in = pd.notna(lap.get('PitInTime'))
            is_pit_out = pd.notna(lap.get('PitOutTime'))
            is_valid = lap.get('IsAccurate', True)
            if pd.isna(is_valid):
                is_valid = True
            
            # 排除 pit 圈和無效圈
            if is_pit_in or is_pit_out or not is_valid:
                continue
            
            # 獲取圈時
            lap_time = lap.get('LapTime')
            if pd.notna(lap_time):
                if hasattr(lap_time, 'total_seconds'):
                    lap_time_sec = float(lap_time.total_seconds())
                else:
                    lap_time_sec = float(lap_time)
            else:
                lap_time_sec = None
            
            # 只有有效圈時才加入
            if lap_time_sec and lap_time_sec > 0:
                valid_laps.append({
                    'lap_number': int(lap['LapNumber']),
                    'lap_time_seconds': lap_time_sec,
                    'tyre_life': int(lap['TyreLife']) if pd.notna(lap.get('TyreLife')) else None,
                    'compound': lap.get('Compound', 'UNKNOWN') if pd.notna(lap.get('Compound')) else 'UNKNOWN'
                })
        
        return valid_laps
    
    def _remove_outlaps(self, valid_laps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        排除 outlap（比平均慢超過閾值的圈）
        
        Args:
            valid_laps: 有效圈列表
        
        Returns:
            清理後的圈列表
        """
        if not valid_laps:
            return []
        
        lap_times = [lap['lap_time_seconds'] for lap in valid_laps]
        avg_time = sum(lap_times) / len(lap_times)
        
        clean_laps = [
            lap for lap in valid_laps
            if lap['lap_time_seconds'] < avg_time + self.OUTLAP_TIME_THRESHOLD
        ]
        
        return clean_laps
    
    def _calculate_stability(self, clean_laps: List[Dict[str, Any]]) -> tuple:
        """
        計算穩定性分數
        
        Args:
            clean_laps: 清理後的圈列表
        
        Returns:
            tuple: (stddev, is_long_run, confidence)
        """
        clean_times = [lap['lap_time_seconds'] for lap in clean_laps]
        
        if len(clean_times) > 1:
            import statistics
            stddev = statistics.stdev(clean_times)
        else:
            stddev = 0
        
        is_long_run = (
            stddev < self.MAX_LAP_TIME_STDDEV and 
            len(clean_laps) >= self.LONG_RUN_MIN_LAPS
        )
        
        confidence = max(0, 1 - (stddev / self.MAX_LAP_TIME_STDDEV)) if self.MAX_LAP_TIME_STDDEV > 0 else 0
        
        return stddev, is_long_run, confidence
    
    def _build_stint_data(self, stint_id: int, clean_laps: List[Dict[str, Any]],
                          compound: str, stddev: float, is_long_run: bool,
                          confidence: float) -> Dict[str, Any]:
        """
        建構 stint 資料結構
        
        Args:
            stint_id: Stint ID
            clean_laps: 清理後的圈列表
            compound: 輪胎類型
            stddev: 標準差
            is_long_run: 是否為 long run
            confidence: 信心分數
        
        Returns:
            stint 字典
        """
        lap_numbers = [lap['lap_number'] for lap in clean_laps]
        lap_count = len(clean_laps)
        
        # 判斷 stint 類型
        if lap_count >= 5:
            stint_type = "long_run"
        elif lap_count <= 2:
            stint_type = "quali_sim"
        else:
            stint_type = "unknown"
        
        return {
            "stint_id": stint_id,
            "compound": compound,
            "lap_range": [min(lap_numbers), max(lap_numbers)] if lap_numbers else [0, 0],
            "lap_count": lap_count,
            "type": stint_type,
            "is_long_run": is_long_run,
            "confidence": round(confidence, 3),
            "stddev": round(stddev, 3),
            "laps_detail": [
                {
                    "lap_number": lap['lap_number'],
                    "lap_time_seconds": lap['lap_time_seconds'],
                    "tyre_life": lap['tyre_life']
                }
                for lap in clean_laps
            ]
        }


# 便利函數
def detect_stints(driver_laps: pd.DataFrame, debug: bool = False) -> List[Dict[str, Any]]:
    """
    便利函數：偵測車手的所有 stint
    
    Args:
        driver_laps: 車手的圈數 DataFrame
        debug: 是否輸出調試信息
    
    Returns:
        stint 列表
    """
    detector = StintDetector(debug=debug)
    return detector.detect_stints(driver_laps)
