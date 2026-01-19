"""
Function 120: FP2 彎道全圈數分析（雙模式：統一 + 分組）

功能：分析 FP2 所有車手在低/中/高速彎的全圈數表現
1. 模式 A：統一分析（所有有效圈）
2. 模式 B：分組分析（長距離 vs 排位模擬）
3. 嚴格異常值過濾（9 種規則 + 物理極限過濾）
4. 完整統計指標（中位數、平均數、標準差等 13 項指標）

作者：AI Assistant
日期：2025-12-13
版本：1.0
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict


class FP2CornerAllLapsAnalysis:
    """FP2 彎道全圈數分析類別"""
    
    def __init__(self, data_loader):
        """
        初始化
        
        Args:
            data_loader: F1 數據載入器（包含 session, laps 等）
        """
        self.data_loader = data_loader
        self.session = getattr(data_loader, 'session', None)
        self.laps = getattr(data_loader, 'laps', None)
        
        if not self.session:
            raise ValueError("數據載入器缺少 session 物件")
        if self.laps is None or self.laps.empty:
            raise ValueError("數據載入器缺少 laps 數據")
        
        # 檢查是否為 FP2
        session_type = getattr(data_loader, 'session_type', None)
        if session_type != 'FP2':
            print(f"[WARNING] 此功能專為 FP2 設計，當前 session: {session_type}")
    
    def analyze(self, show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行完整的 FP2 彎道全圈數分析
        
        Args:
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            分析結果字典（僅包含模式 A - 統一分析）
        """
        try:
            print("[F120 START] 開始 FP2 彎道全圈數分析（僅模式 A）...")
            
            # 步驟 1: 獲取並分類所有彎道（繼承 F47 邏輯）
            print("[STEP 1/4] 獲取賽道彎道資訊...")
            corners = self._get_circuit_corners()
            if corners is None or corners.empty:
                return {
                    "success": False,
                    "message": "無法獲取賽道彎道資訊",
                    "function_id": "120"
                }
            
            # 步驟 2: 分類彎道（低速/中速/高速）
            print("[STEP 2/4] 分析彎道速度特性...")
            classified_corners = self._classify_corners(corners)
            
            # 步驟 3: 選擇代表性彎道
            print("[STEP 3/4] 選擇代表性彎道...")
            selected_corners = self._select_representative_corners(classified_corners)
            
            if not selected_corners:
                return {
                    "success": False,
                    "message": "無法選擇代表性彎道",
                    "function_id": "120"
                }
            
            # 步驟 4: 模式 A - 統一分析（所有有效圈）
            print("[STEP 4/4] 執行模式 A：統一分析...")
            mode_a_result = self._analyze_unified_mode(selected_corners, show_detailed_output)
            
            # ⚠️ 模式 B 已停用（效能優化）
            # Mode B 的分組分析（Long Run vs Quali Sim）已停用以提升執行速度
            # GUI 只需要 Mode A 的統一分析數據
            
            # 步驟 5: 組裝結果
            print("[STEP 5/5] 組裝分析結果...")
            
            # 🆕 從 mode_a_result 提取每個車手的 stints，建立頂層 stints_available 字典
            stints_by_driver = {}
            if mode_a_result and mode_a_result.get('drivers'):
                for driver_data in mode_a_result['drivers']:
                    driver_code = driver_data.get('driver')
                    driver_stints = driver_data.get('stints', [])
                    if driver_code and driver_stints:
                        # 只保留 stint 基本資訊（不含 corners 詳細數據，避免重複）
                        stints_by_driver[driver_code] = [
                            {
                                "stint_id": s.get('stint_id'),
                                "compound": s.get('compound'),
                                "lap_range": s.get('lap_range'),
                                "lap_count": s.get('lap_count'),
                                "type": s.get('type'),
                                "is_long_run": s.get('is_long_run', False),
                                "confidence": s.get('confidence', 0),
                                "stddev": s.get('stddev', 0),
                                "laps_detail": s.get('laps_detail', [])
                            }
                            for s in driver_stints
                        ]
            
            print(f"[INFO] 提取 {len(stints_by_driver)} 位車手的 stint 資料")
            
            result = {
                "success": True,
                "function_id": "120",
                "year": getattr(self.data_loader, 'year', None),
                "race": getattr(self.data_loader, 'race_name', None),
                "session": getattr(self.data_loader, 'session_type', None),
                "analysis_type": "F120_corner_all_laps_analysis",
                "stints_available": stints_by_driver,  # 🆕 改為 dict: {driver: [stint1, stint2, ...]}
                "selected_corners": selected_corners,
                "mode_a_unified": mode_a_result,
                "mode_b_grouped": None  # 已停用
            }
            
            print("[F120 SUCCESS] FP2 彎道全圈數分析完成（僅模式 A）")
            return result
            
        except Exception as e:
            print(f"[F120 ERROR] 分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"分析失敗: {str(e)}",
                "function_id": "120"
            }
    
    # ==================== 彎道分類邏輯（繼承 F47） ====================
    
    def _get_circuit_corners(self) -> Optional[pd.DataFrame]:
        """獲取賽道彎道資訊（使用 FastF1 circuit_info）"""
        try:
            circuit_info = self.session.get_circuit_info()
            
            if circuit_info and hasattr(circuit_info, 'corners') and circuit_info.corners is not None:
                corners_df = circuit_info.corners
                print(f"[INFO] 找到 {len(corners_df)} 個彎道")
                return corners_df
            else:
                print("[WARNING] circuit_info.corners 不可用")
                return None
                
        except Exception as e:
            print(f"[ERROR] 獲取彎道資訊失敗: {e}")
            return None
    
    def _classify_corners(self, corners: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        分類彎道為低速/中速/高速（繼承 F47 標準）
        
        - 低速彎：< 100 km/h
        - 中速彎：100-200 km/h
        - 高速彎：> 200 km/h
        """
        try:
            classified = {
                "low_speed": [],
                "mid_speed": [],
                "high_speed": []
            }
            
            total_corners = len(corners)
            print(f"[INFO] 開始計算各彎道的平均速度... (共 {total_corners} 個彎道)")
            print("[PROGRESS] 進度: ", end="", flush=True)
            
            for idx, (_, corner) in enumerate(corners.iterrows(), 1):
                corner_number = corner['Number']
                apex_distance = corner['Distance']
                
                print(f"{idx}/{total_corners}", end=" ", flush=True)
                
                # 計算所有車手在此彎道的平均 apex 速度
                avg_speed = self._calculate_corner_average_speed(apex_distance)
                
                if avg_speed is None:
                    print(f"[SKIP T{int(corner_number)}]", end=" ", flush=True)
                    continue
                
                corner_data = {
                    "corner_number": int(corner_number),
                    "apex_distance": float(apex_distance),
                    "avg_apex_speed": float(avg_speed),
                    "angle": float(corner['Angle']),
                    "x": float(corner['X']),
                    "y": float(corner['Y'])
                }
                
                # 分類
                if avg_speed < 100:
                    classified["low_speed"].append(corner_data)
                    print(f"[LOW]", end=" ", flush=True)
                elif avg_speed < 200:
                    classified["mid_speed"].append(corner_data)
                    print(f"[MID]", end=" ", flush=True)
                else:
                    classified["high_speed"].append(corner_data)
                    print(f"[HIGH]", end=" ", flush=True)
            
            print()  # 換行
            print(f"[INFO] 彎道分類完成 - 低速:{len(classified['low_speed'])}, "
                  f"中速:{len(classified['mid_speed'])}, 高速:{len(classified['high_speed'])}")
            
            return classified
            
        except Exception as e:
            print(f"[ERROR] 彎道分類失敗: {e}")
            return {"low_speed": [], "mid_speed": [], "high_speed": []}
    
    def _calculate_corner_average_speed(self, apex_distance: float) -> Optional[float]:
        """
        計算所有車手在指定彎道 apex 的平均速度（優化版：使用前 5 位車手）
        
        修復說明（2025-12-13 v2）：
        - 使用 ±20m 固定範圍
        - 強制使用 Speed.min() 確保取得 apex 最低速度
        """
        try:
            speeds = []
            all_drivers = self.laps['Driver'].unique()[:5]
            
            for driver in all_drivers:
                try:
                    driver_laps = self.laps.pick_driver(driver)
                    fastest_lap = driver_laps.pick_fastest()
                    if fastest_lap is None:
                        continue
                    
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry is None or telemetry.empty:
                        continue
                    
                    # ✅ 修復：使用 ±20m 固定範圍
                    apex_tel = telemetry[
                        (telemetry['Distance'] >= apex_distance - 20) &
                        (telemetry['Distance'] <= apex_distance + 20)
                    ]
                    
                    if not apex_tel.empty:
                        # ✅ 修復：強制使用最小速度
                        apex_speed = apex_tel['Speed'].min()
                        speeds.append(apex_speed)
                        
                except Exception:
                    continue
            
            if not speeds:
                return None
            
            return float(np.mean(speeds))
            
        except Exception:
            return None
    
    def _select_representative_corners(self, classified_corners: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """選擇代表性彎道（每種類型選最慢的彎道）"""
        try:
            selected = {}
            
            for speed_type, corners in classified_corners.items():
                if not corners:
                    selected[speed_type] = None
                    print(f"[WARNING] {speed_type} 類型沒有彎道")
                    continue
                
                # 選擇平均速度最慢的彎道（更具挑戰性）
                slowest_corner = min(corners, key=lambda x: x['avg_apex_speed'])
                selected[speed_type] = slowest_corner
                print(f"[INFO] 選擇 {speed_type}: T{slowest_corner['corner_number']} "
                      f"(avg={slowest_corner['avg_apex_speed']:.1f} km/h)")
            
            return selected
            
        except Exception as e:
            print(f"[ERROR] 選擇代表性彎道失敗: {e}")
            return {}
    
    def _preload_all_telemetry(self) -> Dict[str, Dict]:
        """
        預先載入所有車手的所有圈遙測數據（效能優化）
        
        Returns:
            {
                'VER': {lap_index_1: telemetry_df, lap_index_2: telemetry_df, ...},
                'LEC': {lap_index_1: telemetry_df, ...},
                ...
            }
        """
        try:
            print("[PERF] 預載入所有車手遙測數據...")
            import time
            start_time = time.time()
            
            telemetry_cache = {}
            all_drivers = self.laps['Driver'].unique()
            total_laps_loaded = 0
            
            for driver in all_drivers:
                driver_laps = self.laps.pick_driver(driver)
                telemetry_cache[driver] = {}
                
                for idx, lap in driver_laps.iterrows():
                    try:
                        telemetry = lap.get_telemetry()
                        if telemetry is not None and not telemetry.empty:
                            telemetry_cache[driver][idx] = telemetry
                            total_laps_loaded += 1
                    except Exception:
                        continue
            
            elapsed = time.time() - start_time
            print(f"[PERF] 預載入完成：{len(telemetry_cache)} 位車手，{total_laps_loaded} 圈遙測，耗時 {elapsed:.1f}s")
            return telemetry_cache
            
        except Exception as e:
            print(f"[PERF WARNING] 預載入失敗，將使用即時載入: {e}")
            return {}
    
    # ==================== 模式 A：統一分析 ====================
    
    def _analyze_unified_mode(self, selected_corners: Dict[str, Any], 
                             show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        模式 A：統一分析
        分析所有有效圈的彎道表現（不區分長距離/排位模擬）
        """
        try:
            print("[MODE A] 開始統一分析...")
            
            # 🚀 效能優化：預先載入所有遙測數據
            telemetry_cache = self._preload_all_telemetry()
            
            drivers_data = []
            all_drivers = self.laps['Driver'].unique()
            
            for driver in all_drivers:
                try:
                    driver_laps = self.laps.pick_driver(driver)
                    if driver_laps.empty:
                        continue
                    
                    # 收集該車手在三個彎道的數據
                    corners_stats = {}
                    total_laps = len(driver_laps)
                    filtering_summary = defaultdict(int)
                    
                    for speed_type, corner_info in selected_corners.items():
                        if corner_info is None:
                            continue
                        
                        corner_key = f"{speed_type}_corner_{corner_info['corner_number']}"
                        apex_distance = corner_info['apex_distance']
                        
                        # 收集所有有效圈的三點速度
                        entry_speeds = []
                        apex_speeds = []
                        exit_speeds = []
                        lap_filter_reasons = []
                        
                        for idx, lap in driver_laps.iterrows():
                            # 嚴格過濾
                            is_valid, reason = self._is_valid_lap_strict(lap, driver_laps)
                            
                            if not is_valid:
                                filtering_summary[reason] += 1
                                lap_filter_reasons.append(reason)
                                continue
                            
                            # 獲取該圈的 Entry/Apex/Exit 速度
                            try:
                                # 從預載緩存中取得遙測（如果可用）
                                cached_telemetry = telemetry_cache.get(driver, {}).get(idx)
                                
                                three_points = self._get_corner_three_point_speeds(
                                    lap, apex_distance, 
                                    entry_offset=-50, exit_offset=50,
                                    preloaded_telemetry=cached_telemetry
                                )
                                
                                if three_points['entry_speed'] is not None:
                                    entry_speeds.append(three_points['entry_speed'])
                                if three_points['apex_speed'] is not None:
                                    apex_speeds.append(three_points['apex_speed'])
                                if three_points['exit_speed'] is not None:
                                    exit_speeds.append(three_points['exit_speed'])
                                
                                if all(v is None for v in three_points.values()):
                                    filtering_summary['no_speed_data'] += 1
                                    
                            except Exception:
                                filtering_summary['telemetry_error'] += 1
                                continue
                        
                        # 對三個位置分別進行中位數異常值過濾
                        filtered_entry, entry_outliers = self._filter_outliers_by_median(
                            entry_speeds, f"{driver} {corner_key} Entry", threshold=2.0
                        )
                        filtered_apex, apex_outliers = self._filter_outliers_by_median(
                            apex_speeds, f"{driver} {corner_key} Apex", threshold=2.0
                        )
                        filtered_exit, exit_outliers = self._filter_outliers_by_median(
                            exit_speeds, f"{driver} {corner_key} Exit", threshold=2.0
                        )
                        
                        # 計算統計指標（保留 apex 為主要指標，添加 entry/exit）
                        if len(filtered_apex) > 0:
                            stats = self._calculate_comprehensive_stats(
                                filtered_apex, total_laps, apex_outliers
                            )
                            # 添加 Entry/Exit 統計
                            if len(filtered_entry) > 0:
                                stats['entry_speed_median'] = float(np.median(filtered_entry))
                                stats['entry_speed_mean'] = float(np.mean(filtered_entry))
                                stats['entry_speeds_raw'] = [float(s) for s in filtered_entry]
                            if len(filtered_exit) > 0:
                                stats['exit_speed_median'] = float(np.median(filtered_exit))
                                stats['exit_speed_mean'] = float(np.mean(filtered_exit))
                                stats['exit_speeds_raw'] = [float(s) for s in filtered_exit]
                            
                            # 添加過濾旗標 (GUI 用於紫色標記)
                            stats['entry_filtered'] = entry_outliers > 0
                            stats['exit_filtered'] = exit_outliers > 0
                            stats['entry_outliers_count'] = entry_outliers
                            stats['exit_outliers_count'] = exit_outliers
                            
                            # GUI 相容欄位 (對應 F47 的命名)
                            stats['entry_50m_speed'] = stats.get('entry_speed_median', 0)
                            stats['exit_50m_speed'] = stats.get('exit_speed_median', 0)
                            stats['apex_speed'] = stats.get('median_speed', 0)
                            
                            corners_stats[corner_key] = stats
                        else:
                            print(f"  [WARNING] {driver} {corner_key}: 無有效數據")
                    
                    if corners_stats:
                        # 🆕 偵測 stints 並計算每個 stint 的統計
                        stints = self._detect_stints(driver_laps)
                        
                        # 為每個 stint 計算該 stint 範圍內的彎道統計
                        stints_with_corners = []
                        for stint in stints:
                            stint_lap_range = stint['lap_range']
                            stint_laps = driver_laps[
                                (driver_laps['LapNumber'] >= stint_lap_range[0]) &
                                (driver_laps['LapNumber'] <= stint_lap_range[1])
                            ]
                            
                            # 計算此 stint 的彎道統計
                            stint_corners = {}
                            for speed_type, corner_info in selected_corners.items():
                                if corner_info is None:
                                    continue
                                
                                corner_key = f"{speed_type}_corner_{corner_info['corner_number']}"
                                apex_distance = corner_info['apex_distance']
                                
                                stint_apex_speeds = []
                                stint_entry_speeds = []
                                stint_exit_speeds = []
                                
                                for idx, lap in stint_laps.iterrows():
                                    is_valid, _ = self._is_valid_lap_strict(lap, driver_laps)
                                    if not is_valid:
                                        continue
                                    
                                    try:
                                        cached_telemetry = telemetry_cache.get(driver, {}).get(idx)
                                        three_points = self._get_corner_three_point_speeds(
                                            lap, apex_distance,
                                            entry_offset=-50, exit_offset=50,
                                            preloaded_telemetry=cached_telemetry
                                        )
                                        
                                        if three_points['apex_speed'] is not None:
                                            stint_apex_speeds.append(three_points['apex_speed'])
                                        if three_points['entry_speed'] is not None:
                                            stint_entry_speeds.append(three_points['entry_speed'])
                                        if three_points['exit_speed'] is not None:
                                            stint_exit_speeds.append(three_points['exit_speed'])
                                    except Exception:
                                        continue
                                
                                # 計算此 stint 此彎道的統計
                                if stint_apex_speeds:
                                    stint_corners[corner_key] = {
                                        "median_speed": float(np.median(stint_apex_speeds)),
                                        "mean_speed": float(np.mean(stint_apex_speeds)),
                                        "valid_laps": len(stint_apex_speeds),
                                        "speeds_raw": [float(s) for s in stint_apex_speeds],
                                        "entry_speed_median": float(np.median(stint_entry_speeds)) if stint_entry_speeds else None,
                                        "exit_speed_median": float(np.median(stint_exit_speeds)) if stint_exit_speeds else None
                                    }
                            
                            # 組裝 stint 資料（包含彎道統計）
                            stint_with_corners = {
                                "stint_id": stint['stint_id'],
                                "compound": stint['compound'],
                                "lap_range": stint['lap_range'],
                                "lap_count": stint['lap_count'],
                                "type": stint['type'],
                                "is_long_run": stint.get('is_long_run', False),
                                "confidence": stint.get('confidence', 0),
                                "stddev": stint.get('stddev', 0),
                                "laps_detail": stint['laps_detail'],
                                "corners": stint_corners
                            }
                            stints_with_corners.append(stint_with_corners)
                        
                        drivers_data.append({
                            "driver": driver,
                            "total_laps": total_laps,
                            "stints": stints_with_corners,  # 🆕 新增 stints 陣列
                            "filtering_summary": dict(filtering_summary),
                            "corners": corners_stats  # 保留向後兼容
                        })
                        
                        if show_detailed_output:
                            valid_laps = sum(len(c.get('speeds_raw', [])) for c in corners_stats.values())
                            print(f"  [DATA] {driver}: {total_laps} 總圈數, "
                                  f"{len(stints_with_corners)} stints, "
                                  f"{valid_laps} 有效圈, {sum(filtering_summary.values())} 已過濾")
                
                except Exception as e:
                    print(f"  [ERROR] {driver} 分析失敗: {e}")
                    continue
            
            print(f"[MODE A] 統一分析完成 - 成功分析 {len(drivers_data)} 位車手")
            
            return {
                "mode": "unified",
                "description": "所有有效圈統一分析（不區分燃油狀態）",
                "total_drivers": len(drivers_data),
                "drivers": drivers_data
            }
            
        except Exception as e:
            print(f"[MODE A ERROR] 統一分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "mode": "unified",
                "description": "Analysis failed",
                "total_drivers": 0,
                "drivers": []
            }
    
    # ==================== 模式 B：分組分析 ====================
    
    def _analyze_grouped_mode(self, selected_corners: Dict[str, Any],
                             show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        模式 B：分組分析
        區分長距離模擬（Long Run）和排位模擬（Quali Sim）
        """
        try:
            print("[MODE B] 開始分組分析...")
            
            groups_result = {
                "long_run": {"description": "連續多圈模擬（高燃油）", "drivers": []},
                "quali_sim": {"description": "排位模擬（低燃油）", "drivers": []}
            }
            
            all_drivers = self.laps['Driver'].unique()
            
            for driver in all_drivers:
                try:
                    driver_laps = self.laps.pick_driver(driver)
                    if driver_laps.empty:
                        continue
                    
                    # 自動檢測 Long Run 和 Quali Sim 階段
                    phases = self._detect_fp2_phases(driver_laps)
                    
                    if show_detailed_output:
                        print(f"  [PHASE] {driver}: Long Run={len(phases['long_run'])} 圈, "
                              f"Quali Sim={len(phases['quali_sim'])} 圈")
                    
                    # 分析兩個階段
                    for phase_name, lap_numbers in [("long_run", phases['long_run']), 
                                                     ("quali_sim", phases['quali_sim'])]:
                        if not lap_numbers:
                            continue
                        
                        phase_laps = driver_laps[driver_laps['LapNumber'].isin(lap_numbers)]
                        
                        # 收集該階段的彎道數據
                        corners_stats = {}
                        filtering_summary = defaultdict(int)
                        
                        for speed_type, corner_info in selected_corners.items():
                            if corner_info is None:
                                continue
                            
                            corner_key = f"{speed_type}_corner_{corner_info['corner_number']}"
                            apex_distance = corner_info['apex_distance']
                            
                            entry_speeds = []
                            apex_speeds = []
                            exit_speeds = []
                            
                            for idx, lap in phase_laps.iterrows():
                                # 嚴格過濾
                                is_valid, reason = self._is_valid_lap_strict(lap, driver_laps)
                                
                                if not is_valid:
                                    filtering_summary[reason] += 1
                                    continue
                                
                                # 獲取 Entry/Apex/Exit 速度
                                try:
                                    three_points = self._get_corner_three_point_speeds(
                                        lap, apex_distance, entry_offset=-50, exit_offset=50
                                    )
                                    
                                    if three_points['entry_speed'] is not None:
                                        entry_speeds.append(three_points['entry_speed'])
                                    if three_points['apex_speed'] is not None:
                                        apex_speeds.append(three_points['apex_speed'])
                                    if three_points['exit_speed'] is not None:
                                        exit_speeds.append(three_points['exit_speed'])
                                        
                                except Exception:
                                    continue
                            
                            # 對三個位置分別進行中位數異常值過濾
                            filtered_entry, entry_outliers = self._filter_outliers_by_median(
                                entry_speeds, f"{driver} {corner_key} ({phase_name}) Entry", threshold=2.0
                            )
                            filtered_apex, apex_outliers = self._filter_outliers_by_median(
                                apex_speeds, f"{driver} {corner_key} ({phase_name}) Apex", threshold=2.0
                            )
                            filtered_exit, exit_outliers = self._filter_outliers_by_median(
                                exit_speeds, f"{driver} {corner_key} ({phase_name}) Exit", threshold=2.0
                            )
                            
                            # 計算統計指標（保留 apex 為主要指標，添加 entry/exit）
                            if len(filtered_apex) > 0:
                                stats = self._calculate_comprehensive_stats(
                                    filtered_apex, len(phase_laps), apex_outliers
                                )
                                # 添加 Entry/Exit 統計
                                if len(filtered_entry) > 0:
                                    stats['entry_speed_median'] = float(np.median(filtered_entry))
                                    stats['entry_speed_mean'] = float(np.mean(filtered_entry))
                                    stats['entry_speeds_raw'] = [float(s) for s in filtered_entry]
                                if len(filtered_exit) > 0:
                                    stats['exit_speed_median'] = float(np.median(filtered_exit))
                                    stats['exit_speed_mean'] = float(np.mean(filtered_exit))
                                    stats['exit_speeds_raw'] = [float(s) for s in filtered_exit]
                                
                                # 添加過濾旗標 (GUI 用於紫色標記)
                                stats['entry_filtered'] = entry_outliers > 0
                                stats['exit_filtered'] = exit_outliers > 0
                                stats['entry_outliers_count'] = entry_outliers
                                stats['exit_outliers_count'] = exit_outliers
                                
                                # GUI 相容欄位 (對應 F47 的命名)
                                stats['entry_50m_speed'] = stats.get('entry_speed_median', 0)
                                stats['exit_50m_speed'] = stats.get('exit_speed_median', 0)
                                stats['apex_speed'] = stats.get('median_speed', 0)
                                
                                corners_stats[corner_key] = stats
                        
                        if corners_stats:
                            groups_result[phase_name]["drivers"].append({
                                "driver": driver,
                                "lap_range": f"{min(lap_numbers)}-{max(lap_numbers)}",
                                "total_laps": len(phase_laps),
                                "filtering_summary": dict(filtering_summary),
                                "corners": corners_stats
                            })
                
                except Exception as e:
                    print(f"  [ERROR] {driver} 分組分析失敗: {e}")
                    continue
            
            # 計算各組車手數
            long_run_count = len(groups_result["long_run"]["drivers"])
            quali_sim_count = len(groups_result["quali_sim"]["drivers"])
            
            print(f"[MODE B] 分組分析完成 - Long Run: {long_run_count} 車手, Quali Sim: {quali_sim_count} 車手")
            
            return {
                "mode": "grouped",
                "description": "區分長距離模擬和排位模擬",
                "groups": groups_result
            }
            
        except Exception as e:
            print(f"[MODE B ERROR] 分組分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "mode": "grouped",
                "description": "Analysis failed",
                "groups": {}
            }
    
    # ==================== 異常值過濾邏輯 ====================
    
    def _is_valid_lap_strict(self, lap, all_driver_laps: pd.DataFrame) -> Tuple[bool, str]:
        """
        嚴格模式：判斷是否為有效分析圈
        
        Returns:
            (is_valid, filter_reason)
        """
        try:
            lap_number = lap['LapNumber']
            
            # 1. 基礎過濾（繼承 F47）
            if self._is_yellow_flag_lap(lap):
                return False, "yellow_flag"
            
            if self._is_red_flag_lap(lap):
                return False, "red_flag"
            
            if self._is_safety_car_lap(lap):
                return False, "safety_car"
            
            if self._is_pit_lap(lap):
                return False, "pit_lap"
            
            # 2. 新增過濾
            
            # IsAccurate 檢查
            if hasattr(lap, 'IsAccurate') and lap.get('IsAccurate') == False:
                return False, "inaccurate_lap"
            
            # In Lap 檢測（下一圈進站）
            next_lap = all_driver_laps[all_driver_laps['LapNumber'] == lap_number + 1]
            if not next_lap.empty:
                next_lap_row = next_lap.iloc[0]
                if pd.notna(next_lap_row.get('PitInTime')):
                    return False, "in_lap"
            
            # Out Lap 檢測（本圈出站）
            if pd.notna(lap.get('PitOutTime')):
                return False, "out_lap"
            
            # 首圈過濾
            if lap_number == 1:
                return False, "first_lap"
            
            # 最後一圈過濾
            max_lap = all_driver_laps['LapNumber'].max()
            if lap_number == max_lap:
                return False, "last_lap"
            
            return True, "valid"
            
        except Exception as e:
            print(f"  [WARNING] 過濾檢查失敗: {e}")
            return False, "filter_error"
    
    def _filter_by_physical_limits(self, speeds: List[float], 
                                    corner_type: str,
                                    corner_name: str) -> Tuple[List[float], int]:
        """
        基於物理特性的硬性速度範圍過濾（替代 IQR 統計方法）
        
        原理：
        1. 根據彎道類型定義合理速度範圍
        2. 移除物理上不可能的極端值（如低速彎出現 280 km/h）
        3. 保留所有合理範圍內的真實數據（包括失誤圈）
        
        Returns:
            (filtered_speeds, num_outliers)
        """
        try:
            if len(speeds) < 4:
                return speeds, 0
            
            # 定義各類彎道的物理極限（基於 F1 賽車特性）
            speed_limits = {
                "low_speed": (30, 130),    # 低速彎：髮夾彎、慢彎
                "mid_speed": (100, 240),   # 中速彎：一般彎道
                "high_speed": (180, 340)   # 高速彎：高速 Kink
            }
            
            min_limit, max_limit = speed_limits.get(corner_type, (30, 340))
            
            # 過濾：只移除物理上不可能的值
            filtered = [s for s in speeds if min_limit <= s <= max_limit]
            num_outliers = len(speeds) - len(filtered)
            
            if num_outliers > 0:
                outliers = [s for s in speeds if s < min_limit or s > max_limit]
                print(f"  [FILTER] {corner_name}: 移除 {num_outliers} 個物理極限違規 "
                      f"(範圍: {min_limit}-{max_limit} km/h, 異常值: {outliers})")
            
            return filtered, num_outliers
            
        except Exception as e:
            print(f"  [WARNING] 物理過濾失敗: {e}")
            return speeds, 0
    
    def _filter_outliers_by_median(self, speeds: List[float], 
                                    corner_name: str,
                                    threshold: float = 2.0) -> Tuple[List[float], int]:
        """
        基於中位數的異常值過濾
        
        原理：
        1. 計算速度列表的中位數
        2. 移除偏離中位數超過 threshold 倍的值
        3. 這能有效處理因數據缺失導致的極端異常值
        
        Args:
            speeds: 速度列表
            corner_name: 彎道名稱（用於日誌）
            threshold: 偏離閾值（默認 2.0，即偏離中位數 2 倍以上視為異常）
        
        Returns:
            (filtered_speeds, num_outliers)
        """
        try:
            if len(speeds) < 3:
                return speeds, 0
            
            median = np.median(speeds)
            
            if median <= 0:
                return speeds, 0
            
            # 過濾：移除偏離中位數超過 threshold 倍的值
            # 例如：median=69, threshold=2.0 → 只保留 34.5 - 138 km/h
            filtered = [s for s in speeds if abs(s - median) <= threshold * median]
            num_outliers = len(speeds) - len(filtered)
            
            if num_outliers > 0:
                outliers = [s for s in speeds if abs(s - median) > threshold * median]
                print(f"  [MEDIAN-FILTER] {corner_name}: 移除 {num_outliers} 個中位數異常值 "
                      f"(median={median:.1f}, threshold={threshold}x, outliers={[round(o, 1) for o in outliers]})")
            
            return filtered, num_outliers
            
        except Exception as e:
            print(f"  [WARNING] 中位數過濾失敗: {e}")
            return speeds, 0
    
    # ==================== 統計指標計算 ====================
    
    def _calculate_comprehensive_stats(self, speeds: List[float], 
                                       total_laps: int,
                                       filtered_count: int) -> Dict[str, Any]:
        """
        計算完整統計指標
        
        Returns:
            包含 13 種統計指標的字典
        """
        try:
            if not speeds:
                return {}
            
            speeds_array = np.array(speeds)
            
            # 基本統計
            median_speed = float(np.median(speeds_array))
            mean_speed = float(np.mean(speeds_array))
            std_dev = float(np.std(speeds_array)) if len(speeds) > 1 else 0.0
            
            # 四分位數
            q1 = float(np.percentile(speeds_array, 25))
            q3 = float(np.percentile(speeds_array, 75))
            iqr = float(q3 - q1)
            
            # 極值
            min_speed = float(np.min(speeds_array))
            max_speed = float(np.max(speeds_array))
            
            # Top/Bottom 3 圈平均
            sorted_speeds = sorted(speeds)
            top3_avg = float(np.mean(sorted_speeds[-3:])) if len(sorted_speeds) >= 3 else mean_speed
            bottom3_avg = float(np.mean(sorted_speeds[:3])) if len(sorted_speeds) >= 3 else mean_speed
            
            # 變異係數（相對穩定度）
            cv = (std_dev / mean_speed * 100) if mean_speed > 0 else 0.0
            
            stats = {
                "median_speed": round(median_speed, 2),
                "mean_speed": round(mean_speed, 2),
                "std_dev": round(std_dev, 2),
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "min_speed": round(min_speed, 2),
                "max_speed": round(max_speed, 2),
                "top3_avg": round(top3_avg, 2),
                "bottom3_avg": round(bottom3_avg, 2),
                "cv": round(cv, 2),
                "valid_laps": len(speeds),
                "filtered_laps": filtered_count,
                "speeds_raw": [round(s, 1) for s in speeds]  # 保留原始數據供後續視覺化
            }
            
            # 數據品質警告
            warnings = []
            if len(speeds) < 5:
                warnings.append(f"樣本量不足 ({len(speeds)} < 5)")
            if cv > 5.0:
                warnings.append(f"數據變異過大 (CV={cv:.2f}%)")
            
            if warnings:
                stats["warnings"] = warnings
            
            return stats
            
        except Exception as e:
            print(f"  [ERROR] 統計計算失敗: {e}")
            return {}
    
    # ==================== FP2 階段檢測 ====================
    
    def _detect_fp2_phases(self, driver_laps: pd.DataFrame) -> Dict[str, List[int]]:
        """
        自動識別 FP2 的長距離和排位模擬階段
        
        策略：
        1. 連續 5 圈以上 → Long Run
        2. 進站後 1-3 圈 → Quali Sim
        
        Returns:
            {"long_run": [1,2,3,...], "quali_sim": [15,16,...], "unknown": [...]}
        """
        try:
            phases = {"long_run": [], "quali_sim": [], "unknown": []}
            
            current_run = []
            
            for idx, lap in driver_laps.iterrows():
                lap_num = int(lap['LapNumber'])
                
                # 檢查是否為進出站圈
                is_pit_related = (
                    pd.notna(lap.get('PitInTime')) or 
                    pd.notna(lap.get('PitOutTime'))
                )
                
                if is_pit_related:
                    # 結束當前 run
                    if len(current_run) >= 5:
                        phases["long_run"].extend(current_run)
                    elif len(current_run) > 0:
                        phases["unknown"].extend(current_run)
                    current_run = []
                else:
                    current_run.append(lap_num)
            
            # 處理最後一個 run
            if len(current_run) >= 5:
                phases["long_run"].extend(current_run)
            elif len(current_run) > 0:
                # 短 run 視為 Quali Sim（通常在 FP2 後半段）
                phases["quali_sim"].extend(current_run)
            
            return phases
            
        except Exception as e:
            print(f"  [WARNING] FP2 階段檢測失敗: {e}")
            return {"long_run": [], "quali_sim": [], "unknown": []}
    
    def _detect_stints(self, driver_laps: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        偵測車手的所有 stint（用於 GUI stint selection）
        
        完全參考 Long Run Calculator 的邏輯：
        1. 使用 FastF1 的 Stint 欄位進行分組
        2. 排除 PitIn/PitOut 圈和無效圈
        3. 排除 outlap（比平均慢超過閾值的圈）
        4. 計算穩定性分數判斷是否為 long run
        
        Returns:
            List of stint dictionaries
        """
        # 參考 Long Run Calculator 的常數
        MIN_CONSECUTIVE_LAPS = 1  # F120 允許所有 stint（GUI 會顯示全部供用戶選擇）
        OUTLAP_TIME_THRESHOLD = 5.0  # 秒 - 比平均慢超過此值視為 outlap
        MAX_LAP_TIME_STDDEV = 1.5  # 秒 - 低於此標準差視為穩定的 long run
        
        try:
            # 檢查是否有 Stint 欄位
            if 'Stint' not in driver_laps.columns:
                print("  [WARNING] 沒有 Stint 欄位，無法偵測 stint")
                return []
            
            stints = []
            
            # 按 FastF1 的 Stint 欄位分組（與 Long Run Calculator 相同）
            stint_groups = driver_laps.groupby('Stint', sort=True)
            
            for stint_num, stint_laps_df in stint_groups:
                if pd.isna(stint_num):
                    continue
                
                stint_id = int(stint_num)
                
                # Step 1: 過濾 - 排除 pit 圈和無效圈（與 Long Run Calculator 相同）
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
                            'lap_time': lap_time_sec,
                            'tyre_life': int(lap['TyreLife']) if pd.notna(lap.get('TyreLife')) else None,
                            'compound': lap.get('Compound', 'UNKNOWN') if pd.notna(lap.get('Compound')) else 'UNKNOWN'
                        })
                
                # 如果沒有有效圈，跳過此 stint
                if not valid_laps:
                    continue
                
                # Step 2: 排除 outlap（與 Long Run Calculator 相同）
                lap_times = [lap['lap_time'] for lap in valid_laps]
                avg_time = sum(lap_times) / len(lap_times)
                
                clean_laps = [
                    lap for lap in valid_laps
                    if lap['lap_time'] < avg_time + OUTLAP_TIME_THRESHOLD
                ]
                
                # 如果過濾後沒有圈數，使用原始有效圈
                if not clean_laps:
                    clean_laps = valid_laps
                
                # Step 3: 計算穩定性分數（與 Long Run Calculator 相同）
                clean_times = [lap['lap_time'] for lap in clean_laps]
                if len(clean_times) > 1:
                    import statistics
                    stddev = statistics.stdev(clean_times)
                else:
                    stddev = 0
                
                is_long_run = stddev < MAX_LAP_TIME_STDDEV and len(clean_laps) >= 4
                confidence = max(0, 1 - (stddev / MAX_LAP_TIME_STDDEV)) if MAX_LAP_TIME_STDDEV > 0 else 0
                
                # Step 4: 獲取 compound（從第一圈，與 Long Run Calculator 相同）
                compound = clean_laps[0]['compound'] if clean_laps else 'UNKNOWN'
                
                # Step 5: 建構 stint 資料
                lap_numbers = [lap['lap_number'] for lap in clean_laps]
                
                # 判斷 stint 類型
                lap_count = len(clean_laps)
                if lap_count >= 5:
                    stint_type = "long_run"
                elif lap_count <= 2:
                    stint_type = "quali_sim"
                else:
                    stint_type = "unknown"
                
                stint_data = {
                    "stint_id": stint_id,
                    "compound": compound,
                    "lap_range": [min(lap_numbers), max(lap_numbers)],
                    "lap_count": lap_count,
                    "type": stint_type,
                    "is_long_run": is_long_run,
                    "confidence": round(confidence, 3),
                    "stddev": round(stddev, 3),
                    "laps_detail": [
                        {
                            "lap_number": lap['lap_number'],
                            "lap_time": lap['lap_time'],
                            "tyre_life": lap['tyre_life']
                        }
                        for lap in clean_laps
                    ]
                }
                stints.append(stint_data)
            
            return stints
            
        except Exception as e:
            print(f"  [WARNING] Stint 偵測失敗: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_stint_data(self, stint_id: int, laps_detail: List[Dict], 
                          compound: Optional[str]) -> Dict[str, Any]:
        """
        建構單一 stint 的資料結構
        """
        lap_numbers = [lap['lap_number'] for lap in laps_detail]
        lap_count = len(lap_numbers)
        
        # 判斷 stint 類型
        if lap_count >= 5:
            stint_type = "long_run"
        elif lap_count <= 3:
            stint_type = "quali_sim"
        else:
            stint_type = "unknown"
        
        return {
            "stint_id": stint_id,
            "compound": compound if compound else "UNKNOWN",
            "lap_range": [min(lap_numbers), max(lap_numbers)] if lap_numbers else [0, 0],
            "lap_count": lap_count,
            "type": stint_type,
            "laps_detail": laps_detail
        }
    
    # ==================== 輔助方法（繼承 F47） ====================
    
    def _get_speed_at_distance_v2(self, lap, target_distance: float,
                                   tolerance: float = 20,
                                   preloaded_telemetry=None) -> Optional[float]:
        """
        獲取彎道 apex 速度（使用原始 car_data，避免 FastF1 Distance 插值問題）
        
        修復說明（2025-12-13 v5 - 效能優化）：
        - v4: 使用原始 car_data 避免插值問題
        - v5: 支援預載遙測，避免重複調用 get_telemetry()
        
        原理：
        1. 從 get_telemetry() 或預載遙測獲取目標距離附近的時間區間
        2. 使用該時間區間從 session.car_data 提取原始速度數據
        3. 取最小速度作為 apex 速度
        
        Args:
            lap: FastF1 lap 物件
            target_distance: 目標距離（彎道 apex 位置）
            tolerance: 距離容差（預設 ±20m）
            preloaded_telemetry: 預載的遙測數據（效能優化，避免重複調用 get_telemetry）
        
        Returns:
            apex 速度（km/h）或 None
        """
        try:
            # 步驟 1: 從預載遙測或即時獲取目標距離附近的時間區間
            if preloaded_telemetry is not None and not preloaded_telemetry.empty:
                telemetry = preloaded_telemetry
            else:
                telemetry = lap.get_telemetry()
                
            if telemetry is None or telemetry.empty:
                return None
            
            nearby = telemetry[
                (telemetry['Distance'] >= target_distance - tolerance) &
                (telemetry['Distance'] <= target_distance + tolerance)
            ]
            
            if nearby.empty:
                return None
            
            # 獲取時間區間（使用 SessionTime 或 Time）
            if 'SessionTime' in nearby.columns:
                time_min = nearby['SessionTime'].min()
                time_max = nearby['SessionTime'].max()
            elif 'Time' in nearby.columns:
                time_min = nearby['Time'].min()
                time_max = nearby['Time'].max()
            else:
                # 無法獲取時間，回退到舊方法
                return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
            
            # 步驟 2: 從 session.car_data 獲取原始數據
            driver_number = str(lap['DriverNumber'])
            
            if not hasattr(self.session, 'car_data') or driver_number not in self.session.car_data:
                # car_data 不可用，回退到舊方法
                return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
            
            car_data = self.session.car_data[driver_number]
            
            # 篩選時間區間內的數據（擴展一點以確保覆蓋）
            time_buffer = pd.Timedelta(seconds=0.5)  # 0.5 秒緩衝
            
            if 'SessionTime' in car_data.columns:
                raw_nearby = car_data[
                    (car_data['SessionTime'] >= time_min - time_buffer) &
                    (car_data['SessionTime'] <= time_max + time_buffer)
                ]
            elif 'Time' in car_data.columns:
                raw_nearby = car_data[
                    (car_data['Time'] >= time_min - time_buffer) &
                    (car_data['Time'] <= time_max + time_buffer)
                ]
            else:
                return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
            
            # 步驟 3: 從原始數據取最小速度
            if raw_nearby.empty or 'Speed' not in raw_nearby.columns:
                return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
            
            min_speed = float(raw_nearby['Speed'].min())
            
            # 驗證：如果原始數據的最小速度比處理後的小很多，使用原始數據
            processed_min = float(nearby['Speed'].min()) if 'Speed' in nearby.columns else 999
            
            # 使用兩者中較小的值（更可能是真正的 apex 速度）
            return min(min_speed, processed_min)
            
        except Exception as e:
            # 出錯時回退到舊方法
            try:
                telemetry = lap.get_telemetry()
                if telemetry is not None and not telemetry.empty:
                    return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
            except Exception:
                pass
            return None
    
    def _get_corner_three_point_speeds(self, lap, apex_distance: float,
                                        entry_offset: float = -50,
                                        exit_offset: float = 50,
                                        tolerance: float = 20,
                                        preloaded_telemetry=None) -> Dict[str, Optional[float]]:
        """
        獲取彎道三個關鍵點的速度：Entry、Apex、Exit
        
        Args:
            lap: FastF1 lap 物件
            apex_distance: 彎道 apex 位置的距離
            entry_offset: 入彎點相對於 apex 的距離偏移（負值，默認 -50m）
            exit_offset: 出彎點相對於 apex 的距離偏移（正值，默認 +50m）
            tolerance: 距離容差
            preloaded_telemetry: 預載的遙測數據（效能優化）
        
        Returns:
            {
                'entry_speed': float or None,
                'apex_speed': float or None,
                'exit_speed': float or None
            }
        """
        try:
            entry_distance = apex_distance + entry_offset  # apex - 50m
            exit_distance = apex_distance + exit_offset    # apex + 50m
            
            # 獲取三個點的速度（使用預載遙測）
            entry_speed = self._get_speed_at_distance_v2(lap, entry_distance, tolerance, preloaded_telemetry)
            apex_speed = self._get_speed_at_distance_v2(lap, apex_distance, tolerance, preloaded_telemetry)
            exit_speed = self._get_speed_at_distance_v2(lap, exit_distance, tolerance, preloaded_telemetry)
            
            return {
                'entry_speed': entry_speed,
                'apex_speed': apex_speed,
                'exit_speed': exit_speed
            }
            
        except Exception as e:
            return {
                'entry_speed': None,
                'apex_speed': None,
                'exit_speed': None
            }
    
    def _get_speed_at_distance_fallback(self, telemetry: pd.DataFrame,
                                         target_distance: float,
                                         tolerance: float = 20) -> Optional[float]:
        """
        舊版方法（回退用）：從 get_telemetry() 獲取 apex 速度
        
        當 car_data 不可用時使用此方法
        """
        try:
            nearby = telemetry[
                (telemetry['Distance'] >= target_distance - tolerance) &
                (telemetry['Distance'] <= target_distance + tolerance)
            ].copy()
            
            if nearby.empty:
                return None
            
            # 計算速度變化率（減速 = 負值）
            nearby = nearby.sort_values('Distance')
            nearby['Speed_Delta'] = nearby['Speed'].diff()
            
            # 只保留減速階段的點
            braking_zone = nearby[
                (nearby['Speed_Delta'] <= 0) | 
                (nearby['Speed_Delta'].isna())
            ]
            
            if not braking_zone.empty:
                return float(braking_zone['Speed'].min())
            
            return float(nearby['Speed'].min())
            
        except Exception:
            return None
    
    def _get_speed_at_distance(self, telemetry: pd.DataFrame,
                               target_distance: float,
                               tolerance: float = 20) -> Optional[float]:
        """
        [已棄用] 舊版方法 - 保留向後兼容
        
        請使用 _get_speed_at_distance_v2(lap, target_distance, tolerance) 替代
        """
        return self._get_speed_at_distance_fallback(telemetry, target_distance, tolerance)
    
    def _is_yellow_flag_lap(self, lap) -> bool:
        """判斷該圈是否有黃旗"""
        try:
            if not hasattr(self.session, 'race_control_messages'):
                return False
            
            race_control = self.session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = str(msg.get('Message', '')).upper()
                if 'YELLOW FLAG' in message or 'DOUBLE YELLOW' in message:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_red_flag_lap(self, lap) -> bool:
        """判斷該圈是否有紅旗"""
        try:
            if not hasattr(self.session, 'race_control_messages'):
                return False
            
            race_control = self.session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = str(msg.get('Message', '')).upper()
                if 'RED FLAG' in message:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_safety_car_lap(self, lap) -> bool:
        """判斷該圈是否有安全車"""
        try:
            if not hasattr(self.session, 'race_control_messages'):
                return False
            
            race_control = self.session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = str(msg.get('Message', '')).upper()
                if 'SAFETY CAR' in message or 'VSC' in message or 'VIRTUAL SAFETY CAR' in message:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_pit_lap(self, lap) -> bool:
        """判斷是否為進站圈"""
        try:
            return (pd.notna(lap.get('PitOutTime')) or 
                   pd.notna(lap.get('PitInTime')))
        except Exception:
            return False


# ==================== 入口函數 ====================

def run_fp2_corner_all_laps_analysis(data_loader, year, race, session,
                                     show_detailed_output=True) -> Dict[str, Any]:
    """
    Function 120 入口函數
    
    Args:
        data_loader: F1 數據載入器
        year: 年份
        race: 賽事名稱
        session: 賽事類型（應為 "FP2"）
        show_detailed_output: 是否顯示詳細輸出
    
    Returns:
        分析結果字典
    """
    try:
        analyzer = FP2CornerAllLapsAnalysis(data_loader)
        result = analyzer.analyze(show_detailed_output)
        return result
        
    except Exception as e:
        print(f"[F120 ERROR] Function 120 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"執行失敗: {str(e)}",
            "function_id": "120"
        }
