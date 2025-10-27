"""
Function 47: 全車手彎道速度分析（多彎道模式）

功能：自動選擇低速/中速/高速彎各一個代表彎道，分析所有車手的：
1. 最速圈在三個彎道的表現（entry_50m, apex, exit_50m 速度）
2. 全圈數在三個彎道的速度分布（含圈狀態標註）

作者：AI Assistant
日期：2025-10-26
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any


class AllDriversCorneringAnalysis:
    """全車手彎道速度分析類別"""
    
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
    
    def analyze(self, show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行完整的全車手彎道分析
        
        Args:
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            分析結果字典（包含 selected_corners, fastest_lap_analysis, all_laps_analysis）
        """
        try:
            print("[START] 開始全車手彎道速度分析...")
            
            # 步驟 1: 獲取並分類所有彎道
            print("[STEP 1/5] 獲取賽道彎道資訊...")
            corners = self._get_circuit_corners()
            if corners is None or corners.empty:
                return {
                    "success": False,
                    "message": "無法獲取賽道彎道資訊",
                    "function_id": "47"
                }
            
            # 步驟 2: 分類彎道（低速/中速/高速）
            print("[STEP 2/5] 分析彎道速度特性...")
            classified_corners = self._classify_corners(corners)
            
            # 步驟 3: 選擇代表性彎道
            print("[STEP 3/5] 選擇代表性彎道（映射品質優先）...")
            selected_corners = self._select_representative_corners(classified_corners)
            
            if not selected_corners:
                return {
                    "success": False,
                    "message": "無法選擇代表性彎道",
                    "function_id": "47"
                }
            
            # 步驟 4: 分析所有車手最速圈
            print("[STEP 4/5] 分析所有車手最速圈表現...")
            fastest_lap_analysis = self._analyze_fastest_laps(selected_corners, show_detailed_output)
            
            # 步驟 5: 分析所有車手全圈數
            print("[STEP 5/5] 分析所有車手全圈數表現...")
            all_laps_analysis = self._analyze_all_laps(selected_corners, show_detailed_output)
            
            # 組裝結果
            result = {
                "success": True,
                "function_id": "47",
                "year": getattr(self.data_loader, 'year', None),
                "race": getattr(self.data_loader, 'race_name', None),
                "session": getattr(self.data_loader, 'session_type', None),
                "analysis_type": "multi_corner_speed_analysis",
                "selected_corners": selected_corners,
                "fastest_lap_analysis": fastest_lap_analysis,
                "all_laps_analysis": all_laps_analysis
            }
            
            print("[SUCCESS] 全車手彎道速度分析完成")
            return result
            
        except Exception as e:
            print(f"[ERROR] 全車手彎道速度分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"分析失敗: {str(e)}",
                "function_id": "47"
            }
    
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
        分類彎道為低速/中速/高速
        
        方法：計算所有車手在該彎道的平均 apex 速度
        - 低速彎：< 100 km/h
        - 中速彎：100-200 km/h
        - 高速彎：> 200 km/h
        
        Args:
            corners: 彎道 DataFrame（來自 circuit_info）
        
        Returns:
            分類結果 {"low_speed": [...], "mid_speed": [...], "high_speed": [...]}
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
                
                # 顯示進度條
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
        計算所有車手在指定彎道 apex 的平均速度
        
        優化版本：只使用前 5 位完成比賽的車手數據以加速處理
        
        Args:
            apex_distance: 彎道 apex 距離
        
        Returns:
            平均速度（km/h）或 None
        """
        try:
            speeds = []
            
            # 優化：只使用前 5 位完成比賽的車手
            # 這樣可以大幅減少數據處理時間，同時保持代表性
            all_drivers = self.laps['Driver'].unique()[:5]
            
            for driver in all_drivers:
                try:
                    driver_laps = self.laps.pick_driver(driver)
                    
                    # 選擇最快圈（避免異常圈影響）
                    fastest_lap = driver_laps.pick_fastest()
                    if fastest_lap is None:
                        continue
                    
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry is None or telemetry.empty:
                        continue
                    
                    # 獲取 apex 速度（使用較大的容差以加速查找）
                    apex_tel = telemetry[
                        (telemetry['Distance'] >= apex_distance - 15) &
                        (telemetry['Distance'] <= apex_distance + 15)
                    ]
                    
                    if not apex_tel.empty:
                        apex_speed = apex_tel['Speed'].min()
                        speeds.append(apex_speed)
                        
                except Exception as e:
                    # 靜默處理單個車手錯誤
                    pass
                    continue
            
            if not speeds:
                return None
            
            avg_speed = float(np.mean(speeds))
            return avg_speed
            
        except Exception as e:
            return None
    
    def _select_representative_corners(self, classified_corners: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        選擇代表性彎道（低速/中速/高速各一個）
        
        策略：在每種類型中，選擇「平均速度最慢」的彎道（更具挑戰性）
        
        注意：如果某類型沒有彎道，返回 None
        
        Args:
            classified_corners: 分類後的彎道
        
        Returns:
            選擇結果 {"low_speed": {...}, "mid_speed": {...}, "high_speed": {...}}
        """
        try:
            selected = {}
            
            for speed_type, corners in classified_corners.items():
                if not corners:
                    print(f"[WARNING] {speed_type} 類型沒有彎道，跳過")
                    selected[speed_type] = None
                    continue
                
                # 策略：選擇平均速度最慢的彎道（最具挑戰性）
                slowest_corner = min(corners, key=lambda c: c['avg_apex_speed'])
                
                selected[speed_type] = {
                    "corner_number": slowest_corner['corner_number'],
                    "corner_name": f"T{slowest_corner['corner_number']}",
                    "avg_apex_speed": round(slowest_corner['avg_apex_speed'], 1),
                    "apex_distance": slowest_corner['apex_distance'],
                    "classification": speed_type,
                    "angle": slowest_corner['angle'],
                    "x": slowest_corner['x'],
                    "y": slowest_corner['y']
                }
                
                print(f"[SELECT] {speed_type}: T{slowest_corner['corner_number']} "
                      f"(平均速度 {slowest_corner['avg_apex_speed']:.1f} km/h)")
            
            return selected
            
        except Exception as e:
            print(f"[ERROR] 選擇代表性彎道失敗: {e}")
            return {}
    
    def _analyze_fastest_laps(self, selected_corners: Dict[str, Any], 
                              show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        分析所有車手最速圈在三個彎道的表現
        
        Args:
            selected_corners: 選擇的代表性彎道
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            最速圈分析結果
        """
        try:
            drivers_data = []
            all_drivers = self.laps['Driver'].unique()
            
            print(f"[INFO] 分析 {len(all_drivers)} 位車手的最速圈...")
            print("[PROGRESS] 車手進度: ", end="", flush=True)
            
            for idx, driver in enumerate(all_drivers, 1):
                try:
                    print(f"{idx}/{len(all_drivers)}", end=" ", flush=True)
                    
                    driver_laps = self.laps.pick_driver(driver)
                    fastest_lap = driver_laps.pick_fastest()
                    
                    if fastest_lap is None:
                        continue
                    
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry is None or telemetry.empty:
                        continue
                    
                    # 分析三個彎道
                    corners_data = {}
                    for speed_type, corner_info in selected_corners.items():
                        if corner_info is None:
                            continue
                        
                        corner_speeds = self._get_corner_speeds(
                            telemetry,
                            corner_info['apex_distance']
                        )
                        
                        if corner_speeds:
                            key = f"{speed_type}_corner_{corner_info['corner_number']}"
                            corners_data[key] = corner_speeds
                    
                    if corners_data:
                        drivers_data.append({
                            "driver": driver,
                            "fastest_lap_number": int(fastest_lap['LapNumber']),
                            "lap_time": float(fastest_lap['LapTime'].total_seconds()) if pd.notna(fastest_lap['LapTime']) else None,
                            "corners": corners_data
                        })
                        
                        if show_detailed_output:
                            print(f"\n[DATA] {driver}: 最速圈 Lap {int(fastest_lap['LapNumber'])}", end="", flush=True)
                    
                except Exception as e:
                    # 靜默處理錯誤，不中斷整體分析
                    continue
            
            print()  # 換行
            print(f"[INFO] 最速圈分析完成 - 成功分析 {len(drivers_data)} 位車手")
            
            return {
                "description": "All drivers fastest lap corner analysis",
                "total_drivers": len(drivers_data),
                "drivers": drivers_data
            }
            
        except Exception as e:
            print(f"[ERROR] 最速圈分析失敗: {e}")
            return {"description": "Analysis failed", "total_drivers": 0, "drivers": []}
    
    def _analyze_all_laps(self, selected_corners: Dict[str, Any],
                          show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        分析所有車手全圈數在三個彎道的表現
        
        Args:
            selected_corners: 選擇的代表性彎道
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            全圈數分析結果
        """
        try:
            drivers_data = []
            all_drivers = self.laps['Driver'].unique()
            
            print(f"[INFO] 分析 {len(all_drivers)} 位車手的全圈數據...")
            print("[PROGRESS] 車手進度: ", end="", flush=True)
            
            for idx, driver in enumerate(all_drivers, 1):
                try:
                    print(f"{idx}/{len(all_drivers)}", end=" ", flush=True)
                    
                    driver_laps = self.laps.pick_driver(driver)
                    
                    # 分析每個彎道的所有圈數
                    corners_data = {}
                    for speed_type, corner_info in selected_corners.items():
                        if corner_info is None:
                            continue
                        
                        laps_list = []
                        apex_distance = corner_info['apex_distance']
                        
                        for _, lap in driver_laps.iterrows():
                            try:
                                telemetry = lap.get_telemetry()
                                if telemetry is None or telemetry.empty:
                                    continue
                                
                                # 只獲取 apex 速度（用於 Box Plot）
                                apex_speed = self._get_speed_at_distance(
                                    telemetry,
                                    apex_distance,
                                    tolerance=10
                                )
                                
                                if apex_speed is None:
                                    continue
                                
                                # 圈狀態標註
                                lap_data = {
                                    "lap_number": int(lap['LapNumber']),
                                    "apex_speed": round(apex_speed, 1),
                                    "yellow_flag": self._is_yellow_flag_lap(lap, self.session),
                                    "red_flag": self._is_red_flag_lap(lap, self.session),
                                    "safety_car": self._is_safety_car_lap(lap, self.session),
                                    "pit_lap": self._is_pit_lap(lap)
                                }
                                
                                laps_list.append(lap_data)
                                
                            except Exception:
                                continue
                        
                        if laps_list:
                            key = f"{speed_type}_corner_{corner_info['corner_number']}"
                            corners_data[key] = {"laps": laps_list}
                    
                    if corners_data:
                        drivers_data.append({
                            "driver": driver,
                            "total_laps": len(driver_laps),
                            "corners": corners_data
                        })
                        
                        if show_detailed_output:
                            print(f"\n[DATA] {driver}: 收集 {len(driver_laps)} 圈數據", end="", flush=True)
                    
                except Exception as e:
                    # 靜默處理錯誤
                    continue
            
            print()  # 換行
            print(f"[INFO] 全圈數分析完成 - 成功分析 {len(drivers_data)} 位車手")
            
            return {
                "description": "All laps corner performance distribution",
                "total_drivers": len(drivers_data),
                "drivers": drivers_data
            }
            
        except Exception as e:
            print(f"[ERROR] 全圈數分析失敗: {e}")
            return {"description": "Analysis failed", "total_drivers": 0, "drivers": []}
    
    def _get_corner_speeds(self, telemetry: pd.DataFrame, 
                           apex_distance: float) -> Optional[Dict[str, float]]:
        """
        獲取彎道三個位置的速度（entry_50m, apex, exit_50m）
        
        Args:
            telemetry: 遙測數據
            apex_distance: 彎道 apex 距離
        
        Returns:
            {"entry_50m_speed": ..., "apex_speed": ..., "exit_50m_speed": ...}
        """
        try:
            # Entry 50m (apex - 50m)
            entry_speed = self._get_speed_at_distance(
                telemetry,
                apex_distance - 50,
                tolerance=10
            )
            
            # Apex
            apex_speed = self._get_speed_at_distance(
                telemetry,
                apex_distance,
                tolerance=10
            )
            
            # Exit 50m (apex + 50m)
            exit_speed = self._get_speed_at_distance(
                telemetry,
                apex_distance + 50,
                tolerance=10
            )
            
            # 至少要有 apex 速度
            if apex_speed is None:
                return None
            
            return {
                "entry_50m_speed": round(entry_speed, 1) if entry_speed is not None else None,
                "apex_speed": round(apex_speed, 1),
                "exit_50m_speed": round(exit_speed, 1) if exit_speed is not None else None
            }
            
        except Exception as e:
            print(f"[WARNING] 獲取彎道速度失敗: {e}")
            return None
    
    def _get_speed_at_distance(self, telemetry: pd.DataFrame,
                               target_distance: float,
                               tolerance: float = 10) -> Optional[float]:
        """
        獲取最接近目標距離的速度
        
        Args:
            telemetry: 遙測數據
            target_distance: 目標距離
            tolerance: 容差範圍（公尺）
        
        Returns:
            速度（km/h）或 None
        """
        try:
            nearby = telemetry[
                (telemetry['Distance'] >= target_distance - tolerance) &
                (telemetry['Distance'] <= target_distance + tolerance)
            ]
            
            if nearby.empty:
                return None
            
            # 返回最接近的點
            closest_idx = (nearby['Distance'] - target_distance).abs().idxmin()
            return float(nearby.loc[closest_idx, 'Speed'])
            
        except Exception:
            return None
    
    def _is_yellow_flag_lap(self, lap, session) -> bool:
        """判斷該圈是否有黃旗"""
        try:
            if not hasattr(session, 'race_control_messages'):
                return False
            
            race_control = session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = msg.get('Message', '').upper()
                if 'YELLOW FLAG' in message or 'DOUBLE YELLOW' in message:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_red_flag_lap(self, lap, session) -> bool:
        """判斷該圈是否有紅旗"""
        try:
            if not hasattr(session, 'race_control_messages'):
                return False
            
            race_control = session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = msg.get('Message', '').upper()
                if 'RED FLAG' in message:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_safety_car_lap(self, lap, session) -> bool:
        """判斷該圈是否有安全車"""
        try:
            if not hasattr(session, 'race_control_messages'):
                return False
            
            race_control = session.race_control_messages
            if race_control is None or race_control.empty:
                return False
            
            lap_number = lap['LapNumber']
            lap_messages = race_control[race_control['Lap'] == lap_number]
            
            for _, msg in lap_messages.iterrows():
                message = msg.get('Message', '').upper()
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


def run_all_drivers_cornering_analysis(data_loader, year, race, session, 
                                       show_detailed_output=True) -> Dict[str, Any]:
    """
    Function 47 入口函數
    
    Args:
        data_loader: F1 數據載入器
        year: 年份
        race: 賽事名稱
        session: 賽事類型
        show_detailed_output: 是否顯示詳細輸出
    
    Returns:
        分析結果字典
    """
    try:
        analyzer = AllDriversCorneringAnalysis(data_loader)
        result = analyzer.analyze(show_detailed_output)
        return result
        
    except Exception as e:
        print(f"[ERROR] Function 47 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"執行失敗: {str(e)}",
            "function_id": "47"
        }
