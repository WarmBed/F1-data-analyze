"""
Function 121: 直線速度全圈數分析（官方 API 版本 + F48 完整加速邏輯）

功能：分析所有會話（FP1/FP2/FP3/Q/R）所有車手在直線區段的全圈數速度表現
1. 使用官方 API car_data（避免 FastF1 插值問題）
2. 完整複製 F48 加速邏輯：100->300 km/h 加速時間 + 線性推算到最高速度
3. 統一分析所有有效圈（包含完整統計分佈）
4. 中位數異常值過濾
5. 支援所有會話類型：FP1, FP2, FP3, Q, R（正賽）

參照：
- F120: 架構模式、官方 API 數據獲取方法
- F48: 直線速度分析邏輯（完整複製加速性能計算）

作者：AI Assistant
日期：2025-12-14
版本：2.1 - 支援所有會話類型（包括正賽 R）
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


class FP2StraightLineAllLapsAnalysis:
    """直線速度全圈數分析類別（支援所有會話類型）"""
    
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
        
        # 記錄會話類型（支援所有會話）
        session_type = getattr(data_loader, 'session_type', None)
        print(f"[INFO] 分析會話類型: {session_type}")
    
    def analyze(self, show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行完整的直線速度全圈數分析（支援所有會話類型）
        
        Args:
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            分析結果字典（統一分析所有有效圈）
        """
        try:
            session_type = getattr(self.data_loader, 'session_type', 'Unknown')
            print(f"[F121 START] 開始直線速度全圈數分析 ({session_type})...")
            
            # 步驟 1: 識別直線區段
            print("[STEP 1/6] 識別賽道直線區段...")
            straight_segments = self._identify_straight_segments()
            if not straight_segments:
                return {
                    "success": False,
                    "message": "無法識別直線區段",
                    "function_id": "121"
                }
            
            # 步驟 2: 選擇主要直線
            print("[STEP 2/6] 選擇主要直線區段...")
            main_straight = self._select_main_straight(straight_segments)
            
            # 步驟 3: 獲取所有車手數據
            print("[STEP 3/6] 獲取所有車手圈數...")
            all_drivers = self.laps['Driver'].unique()
            print(f"[INFO] 找到 {len(all_drivers)} 位車手")
            
            # 步驟 4: 統一分析（所有有效圈）
            print("[STEP 4/5] 執行統一分析...")
            analysis_result = self._analyze_unified_mode(main_straight, all_drivers, show_detailed_output)
            
            # 步驟 5: 組裝結果
            print("[STEP 5/5] 組裝分析結果...")
            result = {
                "success": True,
                "function_id": "121",
                "year": getattr(self.data_loader, 'year', None),
                "race": getattr(self.data_loader, 'race_name', None),
                "session": getattr(self.data_loader, 'session_type', None),
                "analysis_type": "straight_line_all_laps_analysis",
                "main_straight": main_straight,
                "drivers": analysis_result.get("drivers", []),
                "summary": analysis_result.get("summary", {}),
            }
            
            print(f"[F121 SUCCESS] 直線速度全圈數分析完成 ({session_type})\n")
            return result
            
        except Exception as e:
            print(f"[F121 ERROR] 分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"分析失敗: {e}",
                "function_id": "121"
            }
    
    # ===== 直線區段識別 =====
    
    def _identify_straight_segments(self) -> List[Dict[str, Any]]:
        """
        識別賽道中的直線區段
        
        邏輯：使用最快圈的速度分布，找到持續高速區域
        """
        try:
            # 獲取最快圈
            valid_laps = self.laps[self.laps['LapTime'].notna()]
            if valid_laps.empty:
                print("[ERROR] 沒有有效圈速")
                return []
            
            fastest_lap_idx = valid_laps['LapTime'].idxmin()
            fastest_lap = valid_laps.loc[fastest_lap_idx]
            driver = fastest_lap['Driver']
            
            # 獲取遙測數據
            driver_laps = self.session.laps.pick_driver(driver)
            lap_number = int(fastest_lap['LapNumber'])
            lap_mask = driver_laps['LapNumber'] == lap_number
            
            if not lap_mask.any():
                print(f"[ERROR] 無法找到圈數 {lap_number}")
                return []
            
            lap_obj = driver_laps[lap_mask].iloc[0]
            
            # 使用 car_data 獲取速度（避免插值問題）
            try:
                lap_start_time = lap_obj['LapStartTime']
                lap_time = lap_obj['LapTime']
                lap_end_time = lap_start_time + lap_time
                
                # session.car_data 是字典，key 是車手號碼（字串格式）
                driver_number = str(lap_obj['DriverNumber'])
                
                if not hasattr(self.session, 'car_data') or driver_number not in self.session.car_data:
                    print(f"[ERROR] 車手 {driver} (#{driver_number}) 沒有 car_data")
                    return []
                
                all_car_data = self.session.car_data[driver_number]
                
                # 使用 SessionTime 或 Time 過濾
                if 'SessionTime' in all_car_data.columns:
                    car_data = all_car_data[
                        (all_car_data['SessionTime'] >= lap_start_time) &
                        (all_car_data['SessionTime'] <= lap_end_time)
                    ].copy()
                elif 'Time' in all_car_data.columns:
                    car_data = all_car_data[
                        (all_car_data['Time'] >= lap_start_time) &
                        (all_car_data['Time'] <= lap_end_time)
                    ].copy()
                else:
                    print(f"[ERROR] car_data 缺少時間欄位")
                    return []
                
            except Exception as e:
                print(f"[ERROR] 獲取 car_data 失敗: {e}")
                import traceback
                traceback.print_exc()
                return []
            
            if 'Speed' not in car_data.columns:
                print("[ERROR] car_data 缺少 Speed 欄位")
                return []
            
            # 計算累積距離
            car_data = car_data.copy()
            if 'Distance' not in car_data.columns:
                car_data['Distance'] = self._calculate_distance_from_car_data(car_data)
            
            # 識別直線：速度 > 250 km/h 且持續 > 300m
            straight_threshold = 250  # km/h
            min_length = 300  # meters
            
            straights = []
            in_straight = False
            straight_start = None
            
            for idx, row in car_data.iterrows():
                speed = row['Speed']
                distance = row['Distance']
                
                if speed >= straight_threshold:
                    if not in_straight:
                        in_straight = True
                        straight_start = distance
                else:
                    if in_straight:
                        straight_length = distance - straight_start
                        if straight_length >= min_length:
                            straights.append({
                                'start_distance': straight_start,
                                'end_distance': distance,
                                'length': straight_length
                            })
                        in_straight = False
            
            # 按長度排序
            straights.sort(key=lambda x: x['length'], reverse=True)
            
            print(f"[INFO] 識別到 {len(straights)} 個直線區段")
            for i, s in enumerate(straights[:3]):
                print(f"  直線 {i+1}: {s['start_distance']:.0f}m - {s['end_distance']:.0f}m (長度: {s['length']:.0f}m)")
            
            return straights
            
        except Exception as e:
            print(f"[ERROR] 識別直線區段失敗: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _select_main_straight(self, straights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """選擇主直線（最長的直線）"""
        if not straights:
            return {}
        
        main = straights[0]
        print(f"[INFO] 選擇主直線: {main['start_distance']:.0f}m - {main['end_distance']:.0f}m (長度: {main['length']:.0f}m)")
        return main
    
    # ===== 統一分析 =====
    
    def _analyze_unified_mode(self, main_straight: Dict[str, Any], all_drivers: List[str], 
                              show_detailed: bool = True) -> Dict[str, Any]:
        """
        統一分析所有有效圈
        """
        print("[MODE A] 開始統一分析...")
        
        driver_results = []
        
        for driver in all_drivers:
            driver_stats = self._analyze_driver_straight_speed(
                driver, main_straight, mode='unified'
            )
            if driver_stats:
                driver_results.append(driver_stats)
        
        print(f"[MODE A] 統一分析完成 - 成功分析 {len(driver_results)} 位車手")
        
        return {
            "mode": "unified",
            "description": "所有有效圈統一分析",
            "total_drivers": len(driver_results),
            "drivers": driver_results
        }
    
    # ===== 車手直線速度分析 =====
    
    def _analyze_driver_straight_speed(self, driver: str, main_straight: Dict[str, Any],
                                       mode: str = 'unified') -> Optional[Dict[str, Any]]:
        """
        分析單一車手的直線速度和加速性能（✅ 完整複製 F48 邏輯）
        
        Args:
            driver: 車手代碼
            main_straight: 主直線區段信息
            mode: 統一分析模式（保留參數以維持向後兼容）
        """
        try:
            driver_laps = self.laps[self.laps['Driver'] == driver].copy()
            
            # 過濾圈數
            driver_laps = self._filter_laps_by_mode(driver_laps, mode)
            
            if driver_laps.empty:
                return None
            
            # 收集所有圈的最高速度和加速性能
            max_speeds = []
            valid_lap_numbers = []  # ✅ 記錄有效圈數
            acceleration_times = []  # ✅ 新增：100→300 km/h 加速時間
            times_to_max = []  # ✅ 新增：100 km/h → 最高速度的時間（線性推算）
            
            for _, lap in driver_laps.iterrows():
                lap_number = int(lap['LapNumber'])
                lap_obj = self._get_lap_object(driver, lap_number)
                if lap_obj is None:
                    continue
                
                # 獲取該圈的 car_data（官方 API 靜態數據）
                car_data = self._get_lap_car_data(lap_obj)
                if car_data is None or car_data.empty:
                    continue
                
                # 計算距離
                if 'Distance' not in car_data.columns:
                    car_data['Distance'] = self._calculate_distance_from_car_data(car_data)
                
                # 獲取最高速度
                max_speed = self._get_max_speed_in_straight_from_car_data(car_data, main_straight)
                if max_speed is not None:
                    max_speeds.append(max_speed)
                    valid_lap_numbers.append(lap_number)  # ✅ 記錄圈數
                    
                    # ✅ 計算加速性能（100→300 km/h）
                    accel_data = self._calculate_acceleration_in_segment(car_data, main_straight)
                    if accel_data is not None:
                        accel_time = accel_data['time_seconds']
                        acceleration_times.append(accel_time)
                        
                        # ✅ 線性推算到最高速度的時間
                        time_to_max = self._calculate_time_to_max_speed(max_speed, accel_time)
                        times_to_max.append(time_to_max)
            
            if not max_speeds:
                return None
            
            # ✅ 找出最高速度點（所有圈中的絕對最高值）
            absolute_max_speed = max(max_speeds)
            absolute_max_speed_lap = None
            
            # 找到達到最高速度的圈數
            for i, (lap_num, speed) in enumerate(zip(valid_lap_numbers, max_speeds)):
                if speed == absolute_max_speed:
                    absolute_max_speed_lap = lap_num
                    break
            
            # 中位數過濾異常值（速度）
            filtered_speeds, num_outliers = self._filter_outliers_by_median(max_speeds, driver)
            
            if not filtered_speeds:
                return None
            
            # 速度統計
            speed_stats = self._calculate_speed_stats(filtered_speeds)
            
            # ✅ 加速性能統計
            accel_stats = None
            time_to_max_stats = None
            
            if acceleration_times:
                # 過濾加速時間異常值
                filtered_accel_times, _ = self._filter_outliers_by_median(acceleration_times, driver, threshold=0.5)
                if filtered_accel_times:
                    accel_stats = self._calculate_acceleration_stats(filtered_accel_times)
            
            if times_to_max:
                # 過濾推算時間異常值
                filtered_times_to_max, _ = self._filter_outliers_by_median(times_to_max, driver, threshold=0.5)
                if filtered_times_to_max:
                    time_to_max_stats = self._calculate_acceleration_stats(filtered_times_to_max)
            
            return {
                "driver": driver,
                "total_laps": len(driver_laps),
                "valid_speed_laps": len(max_speeds),
                "filtered_laps": num_outliers,
                "speed_stats": speed_stats,
                "speeds_raw": filtered_speeds,
                # ✅ 新增：最高速度點數據
                "absolute_max_speed_kmh": absolute_max_speed,
                "absolute_max_speed_lap": absolute_max_speed_lap,
                # ✅ 新增：加速性能數據
                "acceleration_100_300_stats": accel_stats,
                "time_to_max_speed_stats": time_to_max_stats,
                "acceleration_times_raw": acceleration_times if acceleration_times else [],
                "times_to_max_raw": times_to_max if times_to_max else []
            }
            
        except Exception as e:
            print(f"[WARNING] 分析 {driver} 失敗: {e}")
            return None
    
    def _filter_laps_by_mode(self, driver_laps: pd.DataFrame, mode: str) -> pd.DataFrame:
        """過濾有效圈數"""
        # 基礎過濾：排除無效圈、被刪除的圈
        driver_laps = driver_laps[
            (driver_laps['LapTime'].notna()) &
            (~driver_laps['Deleted']) &
            (~driver_laps['IsPersonalBest'].isna())  # 有競爭力的圈
        ].copy()
        
        # 統一模式：不進行額外的分組過濾
        return driver_laps
    
    def _get_max_speed_in_straight(self, lap_obj, main_straight: Dict[str, Any]) -> Optional[float]:
        """獲取該圈在直線區段的最高速度（向後兼容方法）"""
        try:
            car_data = self._get_lap_car_data(lap_obj)
            if car_data is None or car_data.empty:
                return None
            
            # 計算距離
            if 'Distance' not in car_data.columns:
                car_data['Distance'] = self._calculate_distance_from_car_data(car_data)
            
            return self._get_max_speed_in_straight_from_car_data(car_data, main_straight)
            
        except Exception as e:
            return None
    
    def _get_max_speed_in_straight_from_car_data(self, car_data: pd.DataFrame, 
                                                  main_straight: Dict[str, Any]) -> Optional[float]:
        """從 car_data 獲取直線區段的最高速度"""
        try:
            # 篩選直線區段
            start_dist = main_straight['start_distance']
            end_dist = main_straight['end_distance']
            
            straight_data = car_data[
                (car_data['Distance'] >= start_dist) &
                (car_data['Distance'] <= end_dist)
            ]
            
            if straight_data.empty or 'Speed' not in straight_data.columns:
                return None
            
            return float(straight_data['Speed'].max())
            
        except Exception as e:
            return None
    
    # ===== 輔助方法 =====
    
    def _get_lap_object(self, driver: str, lap_number: int):
        """獲取圈對象"""
        try:
            driver_laps = self.session.laps.pick_driver(driver)
            lap_mask = driver_laps['LapNumber'] == lap_number
            if not lap_mask.any():
                return None
            return driver_laps[lap_mask].iloc[0]
        except:
            return None
    
    def _get_lap_car_data(self, lap_obj) -> Optional[pd.DataFrame]:
        """獲取圈的 car_data"""
        try:
            driver_number = str(lap_obj['DriverNumber'])
            lap_start = lap_obj['LapStartTime']
            lap_end = lap_start + lap_obj['LapTime']
            
            # session.car_data 是字典，key 是車手號碼
            if not hasattr(self.session, 'car_data') or driver_number not in self.session.car_data:
                return None
            
            car_data = self.session.car_data[driver_number]
            
            # 使用 SessionTime 或 Time
            if 'SessionTime' in car_data.columns:
                lap_car_data = car_data[
                    (car_data['SessionTime'] >= lap_start) &
                    (car_data['SessionTime'] <= lap_end)
                ].copy()
            elif 'Time' in car_data.columns:
                lap_car_data = car_data[
                    (car_data['Time'] >= lap_start) &
                    (car_data['Time'] <= lap_end)
                ].copy()
            else:
                return None
            
            return lap_car_data
            
        except Exception as e:
            return None
    
    def _calculate_distance_from_car_data(self, car_data: pd.DataFrame) -> pd.Series:
        """從 car_data 計算累積距離"""
        if 'Speed' not in car_data.columns:
            return pd.Series([0] * len(car_data), index=car_data.index)
        
        # 計算時間差（秒）
        time_diff = car_data['Time'].diff().dt.total_seconds()
        time_diff.iloc[0] = 0
        
        # 速度 (km/h) -> m/s
        speed_ms = car_data['Speed'] / 3.6
        
        # 距離 = 速度 × 時間
        distance_increment = speed_ms * time_diff
        cumulative_distance = distance_increment.cumsum()
        
        return cumulative_distance
    
    def _filter_outliers_by_median(self, speeds: List[float], driver: str,
                                   threshold: float = 2.0) -> Tuple[List[float], int]:
        """
        中位數異常值過濾（繼承自 F120）
        """
        if not speeds or len(speeds) < 3:
            return speeds, 0
        
        median = np.median(speeds)
        filtered = []
        outliers = []
        
        for speed in speeds:
            deviation = abs(speed - median)
            if deviation <= threshold * median:
                filtered.append(speed)
            else:
                outliers.append(speed)
        
        if outliers:
            print(f"[MEDIAN-FILTER] {driver}: 移除 {len(outliers)} 個異常值 "
                  f"(median={median:.1f}, outliers={[round(x, 1) for x in outliers]})")
        
        return filtered, len(outliers)
    
    def _calculate_speed_stats(self, speeds: List[float]) -> Dict[str, float]:
        """計算速度統計指標"""
        speeds_array = np.array(speeds)
        
        return {
            "median": float(np.median(speeds_array)),
            "mean": float(np.mean(speeds_array)),
            "std_dev": float(np.std(speeds_array, ddof=1)) if len(speeds) > 1 else 0.0,
            "min": float(np.min(speeds_array)),
            "max": float(np.max(speeds_array)),
            "q1": float(np.percentile(speeds_array, 25)),
            "q3": float(np.percentile(speeds_array, 75)),
            "iqr": float(np.percentile(speeds_array, 75) - np.percentile(speeds_array, 25)),
            "cv": float((np.std(speeds_array, ddof=1) / np.mean(speeds_array) * 100)) if len(speeds) > 1 and np.mean(speeds_array) != 0 else 0.0,
            "count": len(speeds)
        }
    
    # ===== F48 加速性能計算方法（完整複製）=====
    
    def _calculate_acceleration_in_segment(self, car_data: pd.DataFrame,
                                           main_straight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        計算直線段內的加速性能（100→目標速度）
        
        ⚠️ 統一後備速度標準：
        - 優先使用 300 km/h
        - 若無法達到 300，使用 280 km/h
        - 若無法達到 280，使用 270 km/h
        
        Args:
            car_data: 官方 API 的遙測數據（已包含 Distance）
            main_straight: 主直線區段信息
        
        Returns:
            {
                "time_seconds": 加速時間（秒）,
                "distance_meters": 加速距離（米）,
                "avg_acceleration_ms2": 平均加速度（m/s²）,
                "speed_100_kmh": 起始速度,
                "speed_target_kmh": 終點速度,
                "target_speed_used": 實際使用的目標速度（300/280/270）,
                ...
            }
        """
        try:
            # 篩選直線區段
            start_dist = main_straight['start_distance']
            end_dist = main_straight['end_distance']
            
            segment_data = car_data[
                (car_data['Distance'] >= start_dist) &
                (car_data['Distance'] <= end_dist)
            ].copy()
            
            if segment_data.empty or 'Speed' not in segment_data.columns:
                return None
            
            speeds = pd.to_numeric(segment_data['Speed'], errors='coerce').dropna()
            
            if speeds.empty or 'Time' not in segment_data.columns:
                return None
            
            # 在該段內找到 100 km/h 和目標速度的點
            # ⚠️ 統一後備速度標準：300 → 280 → 270 km/h
            speed_100_idx = None
            speed_target_idx = None
            target_speed_value = None
            
            # 嘗試找到 100 km/h 起點
            for idx in speeds.index:
                speed = speeds[idx]
                if speed >= 100 and speed_100_idx is None:
                    speed_100_idx = idx
                    break
            
            # 按優先級嘗試找到目標速度：300 → 280 → 270
            for target_speed in [300, 280, 270]:
                for idx in speeds.index:
                    speed = speeds[idx]
                    if speed >= target_speed and speed_target_idx is None:
                        speed_target_idx = idx
                        target_speed_value = target_speed
                        break
                if speed_target_idx is not None:
                    break
            
            # 檢查是否找到兩個速度點
            if speed_100_idx is None or speed_target_idx is None:
                return None
            
            # 獲取實際速度值
            actual_speed_100 = speeds[speed_100_idx]
            actual_speed_target = speeds[speed_target_idx]
            
            # 計算時間差
            time_100 = segment_data.loc[speed_100_idx, 'Time']
            time_target = segment_data.loc[speed_target_idx, 'Time']
            
            if hasattr(time_100, 'total_seconds'):
                time_100_sec = time_100.total_seconds()
            else:
                time_100_sec = float(time_100)
            
            if hasattr(time_target, 'total_seconds'):
                time_target_sec = time_target.total_seconds()
            else:
                time_target_sec = float(time_target)
            
            time_diff = time_target_sec - time_100_sec
            
            # 驗證時間差合理性（100→目標速度 應在 1-15 秒範圍）
            if time_diff <= 0 or time_diff > 15:
                return None
            
            # 計算距離差
            distance_diff = None
            if 'Distance' in segment_data.columns:
                try:
                    dist_100 = segment_data.loc[speed_100_idx, 'Distance']
                    dist_target = segment_data.loc[speed_target_idx, 'Distance']
                    distance_diff = float(dist_target) - float(dist_100)
                except (KeyError, TypeError, ValueError):
                    distance_diff = None
            
            # 計算平均加速度
            velocity_change = (actual_speed_target - actual_speed_100) / 3.6  # 轉換為 m/s
            avg_acceleration = velocity_change / time_diff
            
            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(distance_diff, 2) if distance_diff else None,
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "speed_100_kmh": round(actual_speed_100, 1),
                "speed_target_kmh": round(actual_speed_target, 1),
                "target_speed_used": target_speed_value,  # 記錄使用的目標速度（300/280/270）
                "speed_100_index": int(speed_100_idx),
                "speed_target_index": int(speed_target_idx)
            }
            
        except Exception as e:
            return None
    
    def _calculate_time_to_max_speed(self, max_speed: float, accel_100_300_time: float) -> float:
        """
        計算從 100 km/h 加速到最高速度所需時間（線性推算）
        ✅ 完整複製 F48 公式
        
        假設線性加速:
        time_to_max = (max_speed - 100) / (300 - 100) × accel_100_300_time
        
        Args:
            max_speed: 車手最高速度 (km/h)
            accel_100_300_time: 100→300 km/h 加速時間 (秒)
            
        Returns:
            float: 100 km/h → max_speed 所需時間 (秒)
        """
        if max_speed <= 100:
            return 0.0
        
        speed_range_100_300 = 300 - 100  # 200 km/h
        speed_range_100_max = max_speed - 100
        
        # 線性加速假設
        time_to_max = (speed_range_100_max / speed_range_100_300) * accel_100_300_time
        
        return round(time_to_max, 3)
    
    def _calculate_acceleration_stats(self, times: List[float]) -> Dict[str, float]:
        """計算加速時間統計指標（與速度統計格式一致）"""
        times_array = np.array(times)
        
        return {
            "median": float(np.median(times_array)),
            "mean": float(np.mean(times_array)),
            "std_dev": float(np.std(times_array, ddof=1)) if len(times) > 1 else 0.0,
            "min": float(np.min(times_array)),
            "max": float(np.max(times_array)),
            "q1": float(np.percentile(times_array, 25)),
            "q3": float(np.percentile(times_array, 75)),
            "iqr": float(np.percentile(times_array, 75) - np.percentile(times_array, 25)),
            "cv": float((np.std(times_array, ddof=1) / np.mean(times_array) * 100)) if len(times) > 1 and np.mean(times_array) != 0 else 0.0,
            "count": len(times)
        }
