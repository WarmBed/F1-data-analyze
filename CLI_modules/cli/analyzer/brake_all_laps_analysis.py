"""
Function 122: 煞車性能全圈數分析（官方 API 版本）

功能：分析所有會話（FP1/FP2/FP3/Q/R）所有車手在煞車點的全圈數性能表現
1. 使用官方 API car_data（避免 FastF1 插值問題）
2. 自動偵測所有煞車點（多數決方式統一位置）
3. 自行計算減速度值（官方 API 無直接提供）
4. 統一分析所有有效圈在主煞車點的表現
5. 中位數異常值過濾 + 統計指標（median/mean/std/CV）
6. 原始圈數趨勢（未過濾的每圈減速度值）
7. 支援所有會話類型：FP1, FP2, FP3, Q, R

參照：
- F121: 架構模式、官方 API car_data 使用方法
- F34: 煞車點偵測邏輯（改為多數決統一位置）

技術規格：
- 偵測閾值：-20 m/s^2 → -15 → -10（遞減嘗試）
- 主煞車點標準：最大減速度
- 統一位置方案：多數決（所有車手投票，選出最常見的煞車點）
- 異常值過濾：中位數法（threshold=2.0）
- 趨勢數據：原始每圈減速度值（未過濾）

作者：AI Assistant
日期：2025-12-14
版本：1.0 - 初始實作
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
from collections import defaultdict, Counter


class BrakeAllLapsAnalysis:
    """煞車性能全圈數分析類別（支援所有會話類型）"""
    
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
        
        # 煞車偵測閾值（遞減嘗試）
        self.decel_thresholds = [-20, -15, -10]  # m/s^2²
    
    def analyze(self, show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行完整的煞車性能全圈數分析（支援所有會話類型）
        
        Args:
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            分析結果字典（統一分析所有有效圈在主煞車點的性能）
        """
        try:
            session_type = getattr(self.data_loader, 'session_type', 'Unknown')
            print(f"[F122 START] 開始煞車性能全圈數分析 ({session_type})...")
            
            # 步驟 1: 獲取所有車手
            print("[STEP 1/6] 獲取所有車手圈數...")
            all_drivers = self.laps['Driver'].unique()
            print(f"[INFO] 找到 {len(all_drivers)} 位車手")
            
            # 步驟 2: 多數決偵測統一煞車點位置
            print("[STEP 2/6] 多數決偵測統一煞車點位置...")
            unified_brake_zones = self._detect_unified_brake_zones_via_majority_vote(
                all_drivers, show_detailed_output
            )
            
            if not unified_brake_zones:
                return {
                    "success": False,
                    "message": "無法偵測到統一煞車點",
                    "function_id": "122"
                }
            
            print(f"[INFO] 多數決找到 {len(unified_brake_zones)} 個統一煞車點")
            
            # 步驟 3: 選擇主煞車點（最大減速度）
            print("[STEP 3/6] 選擇主煞車點（最大減速度標準）...")
            main_brake_zone = self._select_main_brake_zone(unified_brake_zones)
            
            print(f"[INFO] 主煞車點: 距離 {main_brake_zone['distance']:.0f}m, "
                  f"平均最大減速度 {main_brake_zone['avg_max_decel']:.2f} m/s^2")
            
            # 步驟 4: 統一分析（所有有效圈在主煞車點）
            print("[STEP 4/6] 執行統一分析（所有有效圈）...")
            analysis_result = self._analyze_unified_mode(
                main_brake_zone, all_drivers, show_detailed_output
            )
            
            # 步驟 5: 組裝結果
            print("[STEP 5/6] 組裝分析結果...")
            result = {
                "success": True,
                "function_id": "122",
                "year": getattr(self.data_loader, 'year', None),
                "race": getattr(self.data_loader, 'race_name', None),
                "session": session_type,
                "analysis_type": "brake_all_laps_analysis",
                "main_brake_zone": {
                    "distance": round(main_brake_zone['distance'], 2),
                    "avg_max_decel": round(main_brake_zone['avg_max_decel'], 2),
                    "detection_threshold": main_brake_zone.get('threshold_used', -20),
                    "voter_count": main_brake_zone.get('voter_count', 0)
                },
                "drivers": analysis_result.get("drivers", []),
                "summary": analysis_result.get("summary", {}),
            }
            
            print(f"[F122 SUCCESS] 煞車性能全圈數分析完成 ({session_type})\n")
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"分析失敗: {str(e)}",
                "function_id": "122"
            }
    
    # ===== 多數決統一煞車點偵測（方案 B）=====
    
    def _detect_unified_brake_zones_via_majority_vote(self, 
                                                       all_drivers: List[str],
                                                       show_detailed: bool = True) -> List[Dict[str, Any]]:
        """
        多數決方式偵測統一煞車點位置
        
        流程：
        1. 為每位車手偵測煞車點（使用最快圈）
        2. 將所有車手的煞車點按距離聚類（容差 ±50m）
        3. 選出投票數最多的聚類作為統一煞車點
        
        Args:
            all_drivers: 所有車手代碼列表
            show_detailed: 是否顯示詳細輸出
        
        Returns:
            統一煞車點列表，按投票數排序
            [{
                "distance": 煞車點距離（聚類中心）,
                "avg_max_decel": 平均最大減速度,
                "voter_count": 投票數（多少車手在此煞車）,
                "voters": 投票車手列表,
                "threshold_used": 使用的偵測閾值
            }, ...]
        """
        print("[INFO] 多數決方式偵測統一煞車點...")
        
        # 步驟 1: 為每位車手偵測煞車點（使用最快圈）
        all_brake_zones = []  # [(driver, distance, max_decel, threshold), ...]
        
        for driver in all_drivers:
            driver_zones = self._detect_brake_zones_for_driver(driver)
            if driver_zones:
                all_brake_zones.extend([
                    (driver, zone['distance'], zone['max_decel'], zone['threshold_used'])
                    for zone in driver_zones
                ])
        
        if not all_brake_zones:
            print("[ERROR] 無法為任何車手偵測到煞車點")
            return []
        
        print(f"[INFO] 共偵測到 {len(all_brake_zones)} 個車手煞車點")
        
        # 步驟 2: 按距離聚類（容差 ±50m）
        clusters = self._cluster_brake_zones_by_distance(all_brake_zones, tolerance=50)
        
        if not clusters:
            print("[ERROR] 無法聚類煞車點")
            return []
        
        print(f"[INFO] 聚類結果: {len(clusters)} 個煞車點群組")
        
        # 步驟 3: 將聚類轉換為統一煞車點
        unified_zones = []
        for cluster_center, cluster_members in clusters.items():
            voters = [member[0] for member in cluster_members]
            decels = [member[2] for member in cluster_members]
            thresholds = [member[3] for member in cluster_members]
            
            unified_zones.append({
                "distance": cluster_center,
                "avg_max_decel": np.mean(decels),
                "voter_count": len(voters),
                "voters": voters,
                "threshold_used": thresholds[0] if thresholds else -20
            })
        
        # 按投票數排序（投票數多的優先）
        unified_zones.sort(key=lambda x: x['voter_count'], reverse=True)
        
        if show_detailed:
            print("\n[多數決投票結果]")
            for idx, zone in enumerate(unified_zones, 1):
                print(f"  煞車點 #{idx}: 距離 {zone['distance']:.0f}m, "
                      f"投票數 {zone['voter_count']}, "
                      f"平均減速 {zone['avg_max_decel']:.2f} m/s^2")
        
        return unified_zones
    
    def _cluster_brake_zones_by_distance(self, 
                                         brake_zones: List[Tuple[str, float, float, float]], 
                                         tolerance: float = 50) -> Dict[float, List[Tuple]]:
        """
        按距離聚類煞車點
        
        Args:
            brake_zones: [(driver, distance, max_decel, threshold), ...]
            tolerance: 距離容差（米），±50m 內視為同一煞車點
        
        Returns:
            {cluster_center: [members], ...}
        """
        if not brake_zones:
            return {}
        
        # 排序所有煞車點距離
        sorted_zones = sorted(brake_zones, key=lambda x: x[1])
        
        clusters = {}
        for zone in sorted_zones:
            driver, distance, max_decel, threshold = zone
            
            # 尋找匹配的聚類
            matched_cluster = None
            for cluster_center in clusters.keys():
                if abs(distance - cluster_center) <= tolerance:
                    matched_cluster = cluster_center
                    break
            
            if matched_cluster is not None:
                # 加入現有聚類
                clusters[matched_cluster].append(zone)
            else:
                # 創建新聚類
                clusters[distance] = [zone]
        
        # 重新計算聚類中心（使用成員平均距離）
        recalculated_clusters = {}
        for cluster_center, members in clusters.items():
            avg_distance = np.mean([m[1] for m in members])
            recalculated_clusters[avg_distance] = members
        
        return recalculated_clusters
    
    def _detect_brake_zones_for_driver(self, driver: str) -> List[Dict[str, Any]]:
        """
        為單一車手偵測煞車點（使用最快圈）
        
        Args:
            driver: 車手代碼
        
        Returns:
            煞車點列表 [{
                "distance": 煞車點距離,
                "max_decel": 最大減速度,
                "threshold_used": 使用的閾值
            }, ...]
        """
        # 獲取車手最快圈
        driver_laps = self.laps[self.laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            return []
        
        # 排除異常圈（基礎過濾：有效圈時、未被刪除）
        valid_laps = driver_laps[
            (driver_laps['LapTime'].notna()) &
            (~driver_laps['Deleted'])
        ].copy()
        
        if valid_laps.empty:
            return []
        
        # 找最快圈
        fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
        
        # 獲取最快圈的 car_data
        try:
            lap_start_time = fastest_lap['LapStartTime']
            lap_time = fastest_lap['LapTime']
            lap_end_time = lap_start_time + lap_time
            
            driver_number = str(fastest_lap['DriverNumber'])
            
            if not hasattr(self.session, 'car_data') or driver_number not in self.session.car_data:
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
                return []
            
        except Exception as e:
            return []
        
        if car_data.empty or 'Speed' not in car_data.columns:
            return []
        
        # 計算累積距離（如果沒有）
        if 'Distance' not in car_data.columns:
            car_data['Distance'] = self._calculate_distance_from_car_data(car_data)
        
        # 計算減速度
        car_data = self._calculate_deceleration(car_data)
        
        if 'Deceleration' not in car_data.columns:
            return []
        
        # 遞減嘗試閾值偵測煞車點
        for threshold in self.decel_thresholds:
            brake_zones = self._identify_brake_zones_with_threshold(car_data, threshold)
            if brake_zones:
                # 標記使用的閾值
                for zone in brake_zones:
                    zone['threshold_used'] = threshold
                return brake_zones
        
        # 所有閾值都失敗
        return []
    
    def _calculate_deceleration(self, car_data: pd.DataFrame) -> pd.DataFrame:
        """
        計算減速度（m/s^2²）
        
        公式：decel = (v2 - v1) / (t2 - t1)
        其中 v 單位為 m/s^2，t 單位為秒
        
        Args:
            car_data: 官方 API car_data（包含 Speed, Time）
        
        Returns:
            添加了 Deceleration 欄位的 car_data
        """
        if 'Speed' not in car_data.columns or 'Time' not in car_data.columns:
            return car_data
        
        car_data = car_data.copy()
        
        # 將速度從 km/h 轉換為 m/s^2
        speeds_ms = car_data['Speed'].values / 3.6
        
        # 提取時間（處理 Timedelta 和 numpy.timedelta64）
        times = car_data['Time'].values
        
        # 轉換為秒數（支援多種時間類型）
        times_sec = np.zeros(len(times))
        for i, t in enumerate(times):
            if hasattr(t, 'total_seconds'):
                # Python timedelta
                times_sec[i] = t.total_seconds()
            elif isinstance(t, (np.timedelta64, pd.Timedelta)):
                # numpy.timedelta64 或 pandas.Timedelta
                times_sec[i] = t / np.timedelta64(1, 's')
            else:
                # 直接是數值
                times_sec[i] = float(t)
        
        # 計算減速度（差分）
        decel = np.zeros(len(speeds_ms))
        for i in range(1, len(speeds_ms)):
            delta_v = speeds_ms[i] - speeds_ms[i-1]
            delta_t = times_sec[i] - times_sec[i-1]
            
            if delta_t > 0:
                decel[i] = delta_v / delta_t
            else:
                decel[i] = 0.0
        
        car_data['Deceleration'] = decel
        
        return car_data
    
    def _identify_brake_zones_with_threshold(self, 
                                             car_data: pd.DataFrame, 
                                             threshold: float) -> List[Dict[str, Any]]:
        """
        使用指定閾值識別煞車點
        
        Args:
            car_data: 包含 Deceleration, Distance 的數據
            threshold: 減速度閾值（m/s^2²），例如 -20
        
        Returns:
            煞車點列表 [{
                "distance": 煞車點距離,
                "max_decel": 最大減速度
            }, ...]
        """
        if 'Deceleration' not in car_data.columns or 'Distance' not in car_data.columns:
            return []
        
        brake_zones = []
        in_brake = False
        brake_start_idx = None
        
        for idx, row in car_data.iterrows():
            decel = row['Deceleration']
            
            if decel <= threshold:  # 減速度超過閾值（負值更小）
                if not in_brake:
                    # 進入煞車區
                    in_brake = True
                    brake_start_idx = idx
            else:
                if in_brake:
                    # 離開煞車區
                    in_brake = False
                    
                    # 分析此煞車區
                    brake_segment = car_data.loc[brake_start_idx:idx]
                    
                    if not brake_segment.empty and len(brake_segment) >= 3:
                        max_decel = brake_segment['Deceleration'].min()  # 最大減速度（最小值）
                        max_decel_idx = brake_segment['Deceleration'].idxmin()
                        brake_distance = brake_segment.loc[max_decel_idx, 'Distance']
                        
                        brake_zones.append({
                            "distance": float(brake_distance),
                            "max_decel": float(max_decel)
                        })
        
        return brake_zones
    
    def _select_main_brake_zone(self, unified_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        選擇主煞車點（使用最大減速度標準）
        
        Args:
            unified_zones: 統一煞車點列表（已按投票數排序）
        
        Returns:
            主煞車點字典
        """
        # 在投票數最高的前 3 個煞車點中，選擇最大減速度的
        top_zones = unified_zones[:3]
        
        main_zone = max(top_zones, key=lambda x: abs(x['avg_max_decel']))
        
        return main_zone
    
    # ===== 全圈數統一分析 =====
    
    def _analyze_unified_mode(self, 
                              main_brake_zone: Dict[str, Any],
                              all_drivers: List[str],
                              show_detailed: bool = True) -> Dict[str, Any]:
        """
        統一分析模式：所有車手在主煞車點的全圈數性能
        
        Args:
            main_brake_zone: 主煞車點信息
            all_drivers: 所有車手代碼
            show_detailed: 是否顯示詳細輸出
        
        Returns:
            {
                "drivers": [{
                    "driver": 車手代碼,
                    "brake_decel_stats": 減速度統計,
                    "raw_decel_trend": 原始每圈減速度值（未過濾）,
                    "valid_laps_count": 有效圈數
                }, ...],
                "summary": 整體摘要
            }
        """
        drivers_results = []
        brake_zone_distance = main_brake_zone['distance']
        distance_tolerance = 100  # ±100m 容差
        
        for driver in all_drivers:
            if show_detailed:
                print(f"\n[分析車手] {driver}")
            
            # 獲取車手所有有效圈
            driver_laps = self.laps[self.laps['Driver'] == driver].copy()
            
            valid_laps = driver_laps[
                (driver_laps['LapTime'].notna()) &
                (~driver_laps['Deleted'])
            ].copy()
            
            if valid_laps.empty:
                if show_detailed:
                    print(f"  [SKIP] 無有效圈")
                continue
            
            # 分析每一圈在煞車點的減速度
            raw_decel_trend = []  # 原始趨勢（未過濾）
            all_decels = []  # 用於統計
            all_entry_speeds = []  # 🆕 用於煞車前速度統計
            
            for lap_num in valid_laps['LapNumber']:
                brake_perf = self._analyze_brake_performance_in_zone(
                    driver, lap_num, brake_zone_distance, distance_tolerance
                )
                
                if brake_perf is not None:
                    max_decel = brake_perf['max_decel']
                    entry_speed = brake_perf.get('entry_speed')  # 🆕 煞車前速度
                    
                    raw_decel_trend.append({
                        "lap_number": int(lap_num),
                        "max_decel": round(max_decel, 2),
                        "entry_speed": round(entry_speed, 1) if entry_speed else None  # 🆕
                    })
                    all_decels.append(max_decel)
                    
                    # 🆕 收集有效的煞車前速度
                    if entry_speed is not None and entry_speed > 0:
                        all_entry_speeds.append(entry_speed)
            
            if not all_decels:
                if show_detailed:
                    print(f"  [SKIP] 無法在煞車點獲取數據")
                continue
            
            # 異常值過濾（中位數法）
            filtered_decels, outlier_flags = self._filter_outliers_by_median(
                all_decels, driver, threshold=2.0
            )
            
            # 計算統計指標
            brake_stats = self._calculate_brake_stats(filtered_decels)
            
            # 🆕 計算煞車前速度統計
            entry_speed_stats = self._calculate_entry_speed_stats(all_entry_speeds) if all_entry_speeds else {}
            
            if show_detailed:
                print(f"  有效圈數: {len(all_decels)} 圈")
                print(f"  減速度中位數: {brake_stats['median']:.2f} m/s^2")
                print(f"  減速度平均: {brake_stats['mean']:.2f} m/s^2")
                print(f"  一致性 (CV): {brake_stats['cv']:.2f}%")
                if entry_speed_stats:
                    print(f"  煞車前速度中位數: {entry_speed_stats.get('median', 0):.1f} km/h")
            
            drivers_results.append({
                "driver": driver,
                "brake_decel_stats": brake_stats,
                "entry_speed_stats": entry_speed_stats,  # 🆕 煞車前速度統計
                "raw_decel_trend": raw_decel_trend,
                "valid_laps_count": len(all_decels),
                "outlier_count": sum(outlier_flags)
            })
        
        # 生成摘要
        summary = self._generate_summary(drivers_results)
        
        return {
            "drivers": drivers_results,
            "summary": summary
        }
    
    def _analyze_brake_performance_in_zone(self,
                                           driver: str,
                                           lap_number: int,
                                           target_distance: float,
                                           tolerance: float = 100) -> Optional[Dict[str, Any]]:
        """
        分析單圈在指定煞車點的性能
        
        Args:
            driver: 車手代碼
            lap_number: 圈數
            target_distance: 目標煞車點距離
            tolerance: 距離容差（米）
        
        Returns:
            {
                "max_decel": 最大減速度,
                "brake_distance": 煞車距離,
                ...
            } 或 None（如果無法分析）
        """
        # 獲取該圈 car_data
        driver_laps = self.laps[self.laps['Driver'] == driver].copy()
        lap_mask = driver_laps['LapNumber'] == lap_number
        
        if not lap_mask.any():
            return None
        
        lap_obj = driver_laps[lap_mask].iloc[0]
        
        try:
            lap_start_time = lap_obj['LapStartTime']
            lap_time = lap_obj['LapTime']
            lap_end_time = lap_start_time + lap_time
            
            driver_number = str(lap_obj['DriverNumber'])
            
            if not hasattr(self.session, 'car_data') or driver_number not in self.session.car_data:
                return None
            
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
                return None
            
        except Exception as e:
            return None
        
        if car_data.empty or 'Speed' not in car_data.columns:
            return None
        
        # 計算距離和減速度
        if 'Distance' not in car_data.columns:
            car_data['Distance'] = self._calculate_distance_from_car_data(car_data)
        
        car_data = self._calculate_deceleration(car_data)
        
        if 'Deceleration' not in car_data.columns:
            return None
        
        # 篩選目標煞車點範圍
        brake_zone_data = car_data[
            (car_data['Distance'] >= target_distance - tolerance) &
            (car_data['Distance'] <= target_distance + tolerance)
        ]
        
        if brake_zone_data.empty:
            return None
        
        # 找最大減速度
        max_decel = brake_zone_data['Deceleration'].min()  # 最小值 = 最大減速度
        max_decel_idx = brake_zone_data['Deceleration'].idxmin()
        brake_distance = brake_zone_data.loc[max_decel_idx, 'Distance']
        
        # 🆕 獲取煞車前速度（進入煞車區的最高速度）
        # 煞車前速度 = 煞車區開始附近的最高速度
        entry_zone_data = car_data[
            (car_data['Distance'] >= target_distance - tolerance) &
            (car_data['Distance'] <= target_distance - 10)  # 煞車點前 10-100m
        ]
        
        if entry_zone_data.empty:
            # 如果前置區域沒有數據，使用煞車區前半部分的最高速度
            entry_zone_data = brake_zone_data.head(len(brake_zone_data) // 3 + 1)
        
        entry_speed = float(entry_zone_data['Speed'].max()) if not entry_zone_data.empty else None
        
        return {
            "max_decel": float(max_decel),
            "brake_distance": float(brake_distance),
            "entry_speed": entry_speed  # 🆕 煞車前速度 (km/h)
        }
    
    # ===== 輔助方法 =====
    
    def _calculate_distance_from_car_data(self, car_data: pd.DataFrame) -> pd.Series:
        """
        從 car_data 計算累積距離
        
        公式：distance = speed × time
        
        Args:
            car_data: 官方 API car_data（包含 Speed, Time）
        
        Returns:
            累積距離 Series（米）
        """
        if 'Speed' not in car_data.columns or 'Time' not in car_data.columns:
            return pd.Series([0] * len(car_data), index=car_data.index)
        
        speeds_ms = car_data['Speed'].values / 3.6  # km/h → m/s^2
        
        # 提取時間（支援多種時間類型）
        times = car_data['Time'].values
        times_sec = np.zeros(len(times))
        for i, t in enumerate(times):
            if hasattr(t, 'total_seconds'):
                times_sec[i] = t.total_seconds()
            elif isinstance(t, (np.timedelta64, pd.Timedelta)):
                times_sec[i] = t / np.timedelta64(1, 's')
            else:
                times_sec[i] = float(t)
        
        # 計算距離增量
        distances = np.zeros(len(speeds_ms))
        for i in range(1, len(speeds_ms)):
            delta_t = times_sec[i] - times_sec[i-1]
            avg_speed = (speeds_ms[i] + speeds_ms[i-1]) / 2
            distances[i] = distances[i-1] + avg_speed * delta_t
        
        return pd.Series(distances, index=car_data.index)
    
    def _filter_outliers_by_median(self, 
                                   values: List[float], 
                                   driver: str,
                                   threshold: float = 2.0) -> Tuple[List[float], List[bool]]:
        """
        中位數法過濾異常值
        
        Args:
            values: 數值列表
            driver: 車手代碼（用於日誌）
            threshold: 異常值閾值（標準差倍數）
        
        Returns:
            (filtered_values, outlier_flags)
        """
        if not values:
            return [], []
        
        values_array = np.array(values)
        median = np.median(values_array)
        mad = np.median(np.abs(values_array - median))
        
        if mad == 0:
            # 所有值相同，無異常值
            return values, [False] * len(values)
        
        # 計算 z-score
        z_scores = np.abs((values_array - median) / mad)
        outlier_flags = z_scores > threshold
        
        filtered_values = values_array[~outlier_flags].tolist()
        
        return filtered_values, outlier_flags.tolist()
    
    def _calculate_entry_speed_stats(self, speeds: List[float]) -> Dict[str, float]:
        """
        計算煞車前速度統計指標
        
        Args:
            speeds: 煞車前速度列表 (km/h)
        
        Returns:
            統計字典 {median, mean, std_dev, min, max}
        """
        if not speeds:
            return {}
        
        speeds_array = np.array(speeds)
        
        return {
            "median": round(float(np.median(speeds_array)), 1),
            "mean": round(float(np.mean(speeds_array)), 1),
            "std_dev": round(float(np.std(speeds_array, ddof=1)), 2) if len(speeds) > 1 else 0.0,
            "min": round(float(np.min(speeds_array)), 1),
            "max": round(float(np.max(speeds_array)), 1),
            "count": len(speeds)
        }
    
    def _calculate_brake_stats(self, decels: List[float]) -> Dict[str, float]:
        """
        計算減速度統計指標
        
        Args:
            decels: 減速度列表（已過濾異常值）
        
        Returns:
            統計字典
        """
        if not decels:
            return {
                "median": 0.0,
                "mean": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0,
                "cv": 0.0,
                "count": 0
            }
        
        decels_array = np.array(decels)
        
        return {
            "median": float(np.median(decels_array)),
            "mean": float(np.mean(decels_array)),
            "std_dev": float(np.std(decels_array, ddof=1)) if len(decels) > 1 else 0.0,
            "min": float(np.min(decels_array)),
            "max": float(np.max(decels_array)),
            "q1": float(np.percentile(decels_array, 25)),
            "q3": float(np.percentile(decels_array, 75)),
            "iqr": float(np.percentile(decels_array, 75) - np.percentile(decels_array, 25)),
            "cv": float((np.std(decels_array, ddof=1) / abs(np.mean(decels_array)) * 100)) if len(decels) > 1 and np.mean(decels_array) != 0 else 0.0,
            "count": len(decels)
        }
    
    def _generate_summary(self, drivers_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成整體摘要
        
        Args:
            drivers_results: 所有車手結果
        
        Returns:
            摘要字典
        """
        if not drivers_results:
            return {}
        
        # 找出最佳煞車性能（最大減速度絕對值）
        best_braker = max(drivers_results, key=lambda x: abs(x['brake_decel_stats']['median']))
        
        # 找出最一致的煞車（最小 CV）
        most_consistent = min(drivers_results, key=lambda x: x['brake_decel_stats']['cv'])
        
        # 計算平均統計
        all_medians = [d['brake_decel_stats']['median'] for d in drivers_results]
        
        return {
            "total_drivers": len(drivers_results),
            "best_braker": {
                "driver": best_braker['driver'],
                "median_decel": round(best_braker['brake_decel_stats']['median'], 2)
            },
            "most_consistent_braker": {
                "driver": most_consistent['driver'],
                "cv": round(most_consistent['brake_decel_stats']['cv'], 2)
            },
            "avg_median_decel": round(float(np.mean(all_medians)), 2)
        }
