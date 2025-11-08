#!/usr/bin/env python3
"""All drivers brake performance analysis module - Based on F48 straight-line speed architecture."""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

# 抑制 FastF1 的 FutureWarning (pick_driver/pick_lap 棄用警告)
warnings.filterwarnings('ignore', category=FutureWarning, module='fastf1')


@dataclass
class DriverBrakeRecord:
    """
    Container representing the brake performance details for a driver.
    
    使用加速度動態偵測邏輯（2025-10-XX 更新）：
    - brake_end_position: 從加速度最大負值自動偵測（取代硬編碼）
    - brake_start_position: 從終點往前找加速度 > -1 m/s² 的點
    
    新增欄位（2025-10-31）：
    - lap_time_s: 圈速時間（秒），用於計算煞車時間百分比
    - brake_time_percentage: 煞車時間占圈速時間的百分比（用於賽道分類）
    """

    driver: str
    driver_number: Optional[int]
    team: Optional[str]
    full_name: Optional[str]
    max_deceleration_ms2: float  # 最大減速度 (m/s²)
    brake_start_speed_kmh: float  # 煞車開始速度
    brake_end_speed_kmh: float    # 煞車結束速度
    brake_distance_m: float       # 煞車距離
    brake_time_s: float          # 煞車時間
    brake_end_position: float    # 煞車結束位置（動態偵測）
    brake_start_position: float  # 煞車開始位置（從終點往前計算）
    lap_number: Optional[int]
    session_time: Optional[str]
    # ✅ 新增：圈速與煞車時間百分比（用於賽道特徵分析）
    lap_time_s: Optional[float] = None          # 圈速時間（秒）
    brake_time_percentage: Optional[float] = None  # 煞車時間百分比 (%)
    # 位置標註欄位
    in_core_range: bool = True  # 是否在參考終點±50m 範圍內
    measurement_notes: Optional[str] = None  # 測量註記（偏離距離等）

    def as_dict(self) -> Dict[str, Any]:
        result = {
            "driver": self.driver,
            "driver_number": self.driver_number,
            "team": self.team,
            "full_name": self.full_name,
            "max_deceleration_ms2": round(float(self.max_deceleration_ms2), 2),
            "max_deceleration_g": round(float(self.max_deceleration_ms2) / 9.81, 2),
            "brake_start_speed_kmh": round(float(self.brake_start_speed_kmh), 1),
            "brake_end_speed_kmh": round(float(self.brake_end_speed_kmh), 1),
            "speed_reduction_kmh": round(float(self.brake_start_speed_kmh - self.brake_end_speed_kmh), 1),
            "brake_distance_m": round(float(self.brake_distance_m), 1),
            "brake_time_s": round(float(self.brake_time_s), 3),
            "brake_end_position": round(float(self.brake_end_position), 1),
            "brake_start_position": round(float(self.brake_start_position), 1),
            "lap_number": self.lap_number,
            "session_time": self.session_time,
            "in_core_range": self.in_core_range,
            "measurement_notes": self.measurement_notes,
        }
        
        # ✅ 新增：圈速與煞車時間百分比（保持 JSON 結構向後兼容）
        if self.lap_time_s is not None:
            result["lap_time_s"] = round(float(self.lap_time_s), 3)
        if self.brake_time_percentage is not None:
            result["brake_time_percentage"] = round(float(self.brake_time_percentage), 2)
        
        return result


class BrakePerformanceAnalyzer:
    """Analyse brake performance for every driver in a session - Based on F48 architecture."""

    def __init__(
        self,
        data_loader: Any,
        *,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
    ) -> None:
        self.data_loader = data_loader
        self.year = year or getattr(data_loader, "year", None)
        self.race = race or getattr(data_loader, "race_name", None)
        self.session = session or getattr(data_loader, "session_type", None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *, top_n: Optional[int] = None, include_chart: bool = True) -> Dict[str, Any]:
        """執行全部車手煞車性能分析"""
        self._ensure_ready()
        
        print("\n" + "="*80)
        print("全部車手煞車性能分析 (Brake Performance Analysis)")
        print("="*80)
        
        # 檢查位置數據可用性
        print("\n[步驟 1/4] 檢查位置數據可用性...")
        position_available = self._check_position_data_availability()
        
        if not position_available:
            return {
                "success": False,
                "function_id": "34",
                "message": "位置數據不可用，無法執行煞車分析",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_brakes": [],
                },
            }
        
        # 找出最速車手和最速圈
        print("\n[步驟 2/4] 找出最速圈作為參考...")
        fastest_result = self._find_overall_fastest_lap()
        if fastest_result is None:
            return {
                "success": False,
                "function_id": "34",
                "message": "找不到有效的最速圈數據",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_brakes": [],
                },
            }
        
        fastest_driver, fastest_lap = fastest_result
        
        # 識別主煞車點位置（硬編碼終點 + Brake = 1 起點）
        print("\n[步驟 3/4] 識別主煞車點位置...")
        reference_segment = self._identify_main_brake_zone_position(fastest_driver, fastest_lap)
        
        if reference_segment is None:
            return {
                "success": False,
                "function_id": "34",
                "message": "無法識別主煞車點位置，請確認賽道已設定硬編碼終點",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_brakes": [],
                },
            }
        
        if reference_segment is None:
            print("\n[ERROR] ❌ 無法識別參考煞車區域，無法繼續分析")
            return {
                "success": False,
                "function_id": "34",
                "message": "無法識別參考煞車區域",
                "data": {
                    "analysis_type": "all_drivers_brake_performance",
                    "metadata": self._build_metadata(),
                    "driver_brakes": [],
                },
            }
        
        print("\n[參考煞車點資訊]")
        print(f"  參考車手: {reference_segment['driver']}")
        print(f"  參考圈數: {reference_segment['lap_number']}")
        print(f"  煞車起點: {reference_segment['brake_start_distance']:.1f}m @ {reference_segment['brake_start_speed']:.1f} km/h")
        print(f"  煞車終點: {reference_segment['brake_end_distance']:.1f}m @ {reference_segment['brake_end_speed']:.1f} km/h (硬編碼)")
        print(f"  煞車距離: {reference_segment['brake_distance']:.1f}m")
        print(f"  速度減少: {reference_segment['speed_reduction']:.1f} km/h")
        
        # 分析所有車手的煞車性能
        print("\n[步驟 4/4] 分析所有車手的煞車性能...")
        driver_records = []
        
        for driver_code in self._iter_drivers():
            print(f"\n  分析車手: {driver_code}")
            record = self._compute_driver_brake_record(driver_code, reference_segment)
            if record:
                driver_records.append(record)
                print(f"    ✅ 最大減速度: {record.max_deceleration_ms2:.2f} m/s² ({record.max_deceleration_ms2/9.81:.2f} G)")
            else:
                print(f"    ❌ 無法獲取煞車數據")
        
        if not driver_records:
            return {
                "success": False,
                "function_id": "34",
                "message": "沒有車手的煞車數據可用",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_brakes": [],
                },
            }
        
        # 按減速度排序
        driver_records.sort(key=lambda r: r.max_deceleration_ms2, reverse=True)
        
        # 限制返回數量
        if top_n is not None and top_n > 0:
            driver_records = driver_records[:top_n]
        
        print(f"\n[SUCCESS] 煞車分析完成，共 {len(driver_records)} 位車手")
        
        return {
            "success": True,
            "function_id": "34",
            "message": f"煞車分析完成，共 {len(driver_records)} 位車手",
            "data": {
                "metadata": self._build_metadata(),
                "reference_brake_zone": reference_segment,
                "driver_brakes": [r.as_dict() for r in driver_records],
                "total_drivers": len(driver_records),
            },
        }

    # ------------------------------------------------------------------
    # Private Helper Methods
    # ------------------------------------------------------------------

    def _check_position_data_availability(self) -> bool:
        """檢查位置數據是否可用（複製自 F48）"""
        try:
            session = getattr(self.data_loader, "session", None)
            if session is None:
                print("[WARNING] 無法獲取 session 對象")
                return False
            
            laps = getattr(session, "laps", None)
            if laps is None or laps.empty:
                print("[WARNING] 沒有圈速數據")
                return False
            
            valid_laps = laps[laps['LapTime'].notna()]
            if valid_laps.empty:
                print("[WARNING] 沒有有效圈速")
                return False
            
            fastest_lap_idx = valid_laps['LapTime'].idxmin()
            fastest_lap = valid_laps.loc[fastest_lap_idx]
            driver = fastest_lap['Driver']
            lap_number = int(fastest_lap['LapNumber'])
            
            driver_laps = session.laps.pick_driver(driver)
            if driver_laps.empty:
                print("[WARNING] 無法獲取車手圈速數據")
                return False
            
            lap_obj = driver_laps.pick_lap(lap_number)
            if lap_obj is None:
                print("[WARNING] 無法獲取圈對象")
                return False
            
            pos_data = lap_obj.get_pos_data()
            if pos_data is None or pos_data.empty:
                print("[WARNING] 位置數據為空")
                return False
            
            if 'X' not in pos_data.columns or 'Y' not in pos_data.columns:
                print("[WARNING] 位置數據缺少 X/Y 欄位")
                return False
            
            has_distance = 'Distance' in pos_data.columns
            
            if not has_distance:
                print("[INFO] 位置數據中沒有 Distance 欄位，將從 X/Y 座標計算")
                print("[INFO] 位置數據檢查通過 (將計算距離)")
                return True
            
            print("[INFO] 位置數據檢查通過 (Distance 可用)")
            return True
            
        except Exception as e:
            print(f"[WARNING] 位置數據檢查失敗: {e}")
            return False

    def _ensure_ready(self) -> None:
        if not self.data_loader:
            raise ValueError("data_loader 尚未初始化")
        if not getattr(self.data_loader, "session_loaded", False):
            raise ValueError("尚未載入任何賽事資料，無法執行分析")

    def _find_overall_fastest_lap(self) -> Optional[Tuple[str, Any]]:
        """找出整場賽事的最速圈和對應車手（複製自 F48）"""
        try:
            session = getattr(self.data_loader, "session", None)
            if session is None:
                print("[ERROR] 無法獲取 session 對象")
                return None
            
            laps = getattr(session, "laps", None)
            if laps is None or laps.empty:
                print("[ERROR] 沒有圈速數據")
                return None
            
            valid_laps = laps[laps['LapTime'].notna()]
            if valid_laps.empty:
                print("[ERROR] 沒有有效圈速")
                return None
            
            fastest_lap_idx = valid_laps['LapTime'].idxmin()
            fastest_lap = valid_laps.loc[fastest_lap_idx]
            
            driver = str(fastest_lap['Driver'])
            lap_number = int(fastest_lap['LapNumber'])
            lap_time = fastest_lap['LapTime']
            
            print(f"[INFO] 最速圈: {driver} - 第{lap_number}圈 - {lap_time}")
            
            driver_laps = session.laps.pick_driver(driver)
            if driver_laps.empty:
                print(f"[ERROR] 無法獲取 {driver} 的圈速數據")
                return None
            
            lap_obj = driver_laps.pick_lap(lap_number)
            if lap_obj is None:
                print(f"[ERROR] 無法獲取第{lap_number}圈對象")
                return None
            
            return (driver, lap_obj)
            
        except Exception as e:
            print(f"[ERROR] 找最速圈失敗: {e}")
            return None

    # ------------------------------------------------------------------
    # 加速度數據處理方法（新增）
    # ------------------------------------------------------------------
    
    def _get_or_calculate_acceleration(self, car_data: pd.DataFrame) -> pd.Series:
        """
        獲取或計算加速度數據
        
        優先使用 FastF1 的 Acceleration 欄位，
        如果不存在則從 Speed 差分計算
        
        Args:
            car_data: 車輛遙測數據 DataFrame
            
        Returns:
            pd.Series: 加速度數據 (m/s²)
        """
        if "Acceleration" in car_data.columns:
            accelerations = pd.to_numeric(car_data["Acceleration"], errors="coerce")
            print("[INFO] 使用 FastF1 內建 Acceleration 欄位")
        else:
            print("[WARNING] 缺少 Acceleration 欄位，從 Speed 計算")
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            speed_ms = speeds / 3.6  # km/h → m/s
            
            # 計算時間差
            if "Time" in car_data.columns:
                time_diffs = car_data["Time"].diff().dt.total_seconds()
            else:
                # 如果沒有 Time 欄位，假設採樣頻率為常數（通常 FastF1 是這樣）
                print("[WARNING] 缺少 Time 欄位，假設採樣頻率為 0.01 秒")
                time_diffs = pd.Series([0.01] * len(car_data), index=car_data.index)
            
            # 計算加速度 (m/s²)
            accelerations = speed_ms.diff() / time_diffs
            accelerations = accelerations.fillna(0.0)
        
        # NaN 處理
        accelerations = accelerations.fillna(0.0)
        
        # 可選：平滑處理（移動平均，避免雜訊）
        # accelerations = accelerations.rolling(window=3, center=True).mean().fillna(accelerations)
        
        return accelerations
    
    def _find_reference_brake_endpoint(self, car_data: pd.DataFrame) -> Tuple[float, float, int]:
        """
        從最速車手全圈找參考煞車終點（加速度最大負值位置）
        
        Args:
            car_data: 最速車手的車輛遙測數據
            
        Returns:
            Tuple[float, float, int]: (煞車終點距離, 最大負加速度, DataFrame索引)
        """
        accelerations = self._get_or_calculate_acceleration(car_data)
        distances = pd.to_numeric(car_data["Distance"], errors="coerce")
        
        # 找最小加速度（最大負值）
        max_neg_idx = accelerations.idxmin()
        max_neg_accel = accelerations[max_neg_idx]
        brake_end_distance = distances[max_neg_idx]
        
        print(f"[INFO] 參考煞車終點: {brake_end_distance:.1f}m @ 加速度 {max_neg_accel:.2f} m/s² ({max_neg_accel/9.81:.2f}g)")
        
        return brake_end_distance, max_neg_accel, max_neg_idx
    
    def _find_driver_brake_endpoint(self, car_data: pd.DataFrame, 
                                    reference_distance: float) -> Tuple[float, float, int]:
        """
        在參考終點±50m 範圍找該車手的最大負加速度點
        
        Args:
            car_data: 車手遙測數據
            reference_distance: 參考煞車終點距離
            
        Returns:
            Tuple[float, float, int]: (煞車終點距離, 最大負加速度, DataFrame索引)
        """
        accelerations = self._get_or_calculate_acceleration(car_data)
        distances = pd.to_numeric(car_data["Distance"], errors="coerce")
        
        # 定義搜尋範圍 ±50m
        SEARCH_RANGE = 50.0
        search_start = reference_distance - SEARCH_RANGE
        search_end = reference_distance + SEARCH_RANGE
        
        # 篩選範圍內的數據
        mask = (distances >= search_start) & (distances <= search_end)
        range_accelerations = accelerations[mask]
        range_distances = distances[mask]
        
        if range_accelerations.empty:
            print(f"[WARNING] 搜尋範圍 {search_start:.1f}m - {search_end:.1f}m 無數據，使用參考終點")
            # Fallback: 使用參考終點附近最接近的點
            distance_diff = (distances - reference_distance).abs()
            closest_idx = distance_diff.idxmin()
            return distances[closest_idx], accelerations[closest_idx], closest_idx
        
        # 找範圍內最小加速度
        max_neg_idx = range_accelerations.idxmin()
        max_neg_accel = range_accelerations[max_neg_idx]
        brake_end_distance = range_distances[max_neg_idx]
        
        print(f"[INFO] 個人煞車終點: {brake_end_distance:.1f}m @ 加速度 {max_neg_accel:.2f} m/s² ({max_neg_accel/9.81:.2f}g)")
        
        return brake_end_distance, max_neg_accel, max_neg_idx
    
    def _find_brake_start_from_endpoint(self, car_data: pd.DataFrame, 
                                         brake_end_idx: int) -> Tuple[float, int]:
        """
        從煞車終點往前找煞車起點（加速度 > -1 m/s² 的點）
        
        Args:
            car_data: 車手遙測數據
            brake_end_idx: 煞車終點的 DataFrame 索引
            
        Returns:
            Tuple[float, int]: (煞車起點距離, DataFrame索引)
        """
        accelerations = self._get_or_calculate_acceleration(car_data)
        distances = pd.to_numeric(car_data["Distance"], errors="coerce")
        
        ACCEL_THRESHOLD = -1.0
        
        print(f"[INFO] 從終點 {distances[brake_end_idx]:.1f}m 往前搜尋煞車起點（閥值: {ACCEL_THRESHOLD} m/s²）...")
        
        # 獲取所有索引並按距離排序（從大到小）
        all_indices = list(car_data.index)
        sorted_indices = sorted(all_indices, key=lambda idx: distances[idx] if pd.notna(distances[idx]) else 0, reverse=True)
        
        # 找到終點索引的位置
        try:
            end_idx_position = sorted_indices.index(brake_end_idx)
        except ValueError:
            print(f"[ERROR] 無法找到終點索引在排序列表中的位置")
            # Fallback: 使用第一個數據點
            return distances.iloc[0], car_data.index[0]
        
        # 從終點往前掃描
        in_brake_zone = False
        for i in range(end_idx_position, len(sorted_indices)):
            idx = sorted_indices[i]
            dist = distances[idx]
            accel = accelerations[idx]
            
            # 跳過 NaN 值
            if pd.isna(accel) or pd.isna(dist):
                continue
            
            # 狀態機：先進入煞車區（accel < -1），再離開煞車區（accel >= -1）
            if accel < ACCEL_THRESHOLD:
                in_brake_zone = True  # 正在煞車
            elif in_brake_zone and accel >= ACCEL_THRESHOLD:
                # 從煞車區離開（找到煞車起始邊界）
                brake_start_distance = dist
                searched_distance = abs(distances[brake_end_idx] - dist)
                print(f"[INFO] 煞車起點: {brake_start_distance:.1f}m @ 加速度 {accel:.2f} m/s² (往前搜尋 {searched_distance:.1f}m)")
                return brake_start_distance, idx
        
        # Fallback: 如果沒找到明確邊界，使用搜尋到的最遠煞車點
        if in_brake_zone:
            print(f"[WARNING] 未找到明確的煞車起始邊界，使用最遠煞車點")
            for i in range(len(sorted_indices) - 1, end_idx_position - 1, -1):
                idx = sorted_indices[i]
                dist = distances[idx]
                accel = accelerations[idx]
                
                if pd.isna(accel) or pd.isna(dist):
                    continue
                
                if accel < ACCEL_THRESHOLD:
                    searched_distance = abs(distances[brake_end_idx] - dist)
                    print(f"[INFO] 使用最遠煞車點: {dist:.1f}m @ 加速度 {accel:.2f} m/s² (往前搜尋 {searched_distance:.1f}m)")
                    return dist, idx
        
        # 最終 Fallback: 使用第一個數據點
        print(f"[WARNING] 無法找到煞車起點（加速度未超過 {ACCEL_THRESHOLD} m/s²），使用起始點")
        return distances.iloc[0], car_data.index[0]
    
    # ------------------------------------------------------------------
    # 主煞車點識別方法（重寫）
    # ------------------------------------------------------------------

    def _identify_main_brake_zone_position(self, driver_code: str, lap_obj: Any) -> Optional[Dict[str, Any]]:
        """
        從最速車手的最速圈中識別主煞車點位置 - 基於加速度動態偵測（新邏輯）
        
        流程：
        1. 從最速車手全圈找加速度最大負值 → 參考煞車終點
        2. 從終點往前找加速度 > -1 m/s² 的點 → 煞車起點
        3. 返回參考終點和相關數據
        
        Args:
            driver_code: 最速車手代碼
            lap_obj: 最速圈對象
            
        Returns:
            Dict 包含參考煞車終點和起點資訊，或 None（如果失敗）
        """
        try:
            car_data = self._extract_car_data(lap_obj)
            if car_data is None or car_data.empty:
                print(f"[ERROR] 無法獲取 {driver_code} 的車輛數據")
                return None
            
            if "Speed" not in car_data.columns or "Distance" not in car_data.columns:
                print(f"[ERROR] 缺少必要欄位: Speed={('Speed' in car_data.columns)}, Distance={('Distance' in car_data.columns)}")
                return None
            
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            
            if speeds.empty or distances.empty:
                print(f"[ERROR] 速度或距離數據為空")
                return None
            
            # ✅ 新邏輯：從最速車手找參考煞車終點（加速度最大負值）
            print(f"[INFO] 使用新的加速度動態偵測邏輯（取代硬編碼終點）")
            reference_brake_distance, reference_max_neg_accel, brake_end_idx = \
                self._find_reference_brake_endpoint(car_data)
            
            # 獲取終點速度
            brake_end_speed = speeds[brake_end_idx]
            
            # ✅ 從終點往前找煞車起點
            brake_start_distance, brake_start_idx = \
                self._find_brake_start_from_endpoint(car_data, brake_end_idx)
            
            # 獲取起點速度和加速度
            brake_start_speed = speeds[brake_start_idx]
            accelerations = self._get_or_calculate_acceleration(car_data)
            brake_start_accel = accelerations[brake_start_idx]
            
            # ✅ 計算煞車距離和速度減少
            brake_distance = float(reference_brake_distance - brake_start_distance)
            speed_reduction = float(brake_start_speed - brake_end_speed)
            
            print(f"[SUCCESS] 主煞車點已識別 (基於加速度動態偵測):")
            print(f"   起點: {brake_start_distance:.1f}m @ {brake_start_speed:.1f} km/h (加速度: {brake_start_accel:.2f} m/s²)")
            print(f"   終點: {reference_brake_distance:.1f}m @ {brake_end_speed:.1f} km/h (動態偵測)")
            print(f"   煞車距離: {brake_distance:.1f}m")
            print(f"   速度減少: {speed_reduction:.1f} km/h")
            print(f"   最大負加速度: {reference_max_neg_accel:.2f} m/s² ({reference_max_neg_accel/9.81:.2f}g)")

            lap_number = self._extract_lap_number(lap_obj)
            
            brake_zone_info = {
                "driver": driver_code,
                "lap_number": lap_number,
                "brake_start_distance": float(brake_start_distance),
                "brake_end_distance": float(reference_brake_distance),
                "brake_start_speed": float(brake_start_speed),
                "brake_end_speed": float(brake_end_speed),
                "brake_distance": brake_distance,
                "speed_reduction": speed_reduction,
                "reference_max_neg_accel": float(reference_max_neg_accel),
                "race_name": self.race
            }
            
            return brake_zone_info
            
        except Exception as e:
            print(f"[ERROR] 識別主煞車點失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _compute_driver_brake_record(
        self,
        driver_code: str,
        reference_segment: Dict[str, Any]
    ) -> Optional[DriverBrakeRecord]:
        """
        計算單一車手的煞車性能記錄 - 使用個人煞車終點偵測（新邏輯）
        
        流程：
        1. 在參考終點±50m 範圍找該車手的最大負加速度點 → 個人煞車終點
        2. 從終點往前找加速度 > -1 m/s² 的點 → 煞車起點
        3. 計算煞車性能數據
        """
        try:
            driver_laps = self._pick_driver_laps(driver_code)
            if driver_laps is None or getattr(driver_laps, "empty", False):
                print(f"      [DEBUG] {driver_code}: 無法獲取車手圈速數據")
                return None
            
            fastest_lap = self._find_fastest_lap(driver_laps)
            if fastest_lap is None:
                print(f"      [DEBUG] {driver_code}: 無法找到最速圈")
                return None
            
            car_data = self._extract_car_data(fastest_lap)
            if car_data is None or car_data.empty:
                print(f"      [DEBUG] {driver_code}: 無法提取車輛遙測數據")
                return None
            
            # ✅ 新邏輯：在參考終點±50m 找該車手的個人煞車終點
            reference_brake_distance = reference_segment["brake_end_distance"]
            driver_brake_distance, driver_max_neg_accel, brake_end_idx = \
                self._find_driver_brake_endpoint(car_data, reference_brake_distance)
            
            # ✅ 從終點往前找煞車起點
            brake_start_distance, brake_start_idx = \
                self._find_brake_start_from_endpoint(car_data, brake_end_idx)
            
            # 計算煞車減速度（使用新的個人煞車範圍）
            brake_data = self._calculate_brake_deceleration(
                car_data,
                brake_start_distance,
                driver_brake_distance
            )
            
            if brake_data is None:
                print(f"      [DEBUG] {driver_code}: 無法計算煞車減速度")
                return None
            
            # 獲取車手資訊
            driver_info = self._get_driver_info(fastest_lap)
            lap_number = self._extract_lap_number(fastest_lap)
            session_time = self._extract_session_time(fastest_lap)
            
            # ✅ 新增：提取圈速時間並計算煞車時間百分比（用於賽道特徵分析）
            lap_time_s = None
            brake_time_percentage = None
            try:
                if hasattr(fastest_lap, 'LapTime') and fastest_lap['LapTime'] is not None:
                    lap_time_timedelta = fastest_lap['LapTime']
                    if hasattr(lap_time_timedelta, 'total_seconds'):
                        lap_time_s = float(lap_time_timedelta.total_seconds())
                        # 計算煞車時間百分比
                        if lap_time_s > 0:
                            brake_time_percentage = (brake_data["time_seconds"] / lap_time_s) * 100
            except Exception as e:
                print(f"      [DEBUG] {driver_code}: 無法計算圈速時間或煞車百分比: {e}")
            
            # 檢查是否在核心範圍內（±50m）
            distance_from_reference = abs(driver_brake_distance - reference_brake_distance)
            in_core_range = distance_from_reference <= 50.0
            
            # 添加測量註解
            measurement_notes = None
            if not in_core_range:
                measurement_notes = f"煞車終點偏離參考終點 {distance_from_reference:.1f}m"
            
            return DriverBrakeRecord(
                driver=driver_code,
                driver_number=driver_info.get("driver_number"),
                team=driver_info.get("team"),
                full_name=driver_info.get("full_name"),
                max_deceleration_ms2=brake_data["avg_deceleration_ms2"],
                brake_start_speed_kmh=brake_data["start_speed_kmh"],
                brake_end_speed_kmh=brake_data["end_speed_kmh"],
                brake_distance_m=brake_data["distance_meters"],
                brake_time_s=brake_data["time_seconds"],
                brake_end_position=brake_data["actual_distance_end"],
                brake_start_position=brake_data["actual_distance_start"],
                lap_number=lap_number,
                session_time=session_time,
                lap_time_s=lap_time_s,  # ✅ 新增
                brake_time_percentage=brake_time_percentage,  # ✅ 新增
                in_core_range=in_core_range,
                measurement_notes=measurement_notes
            )
            
        except Exception as e:
            print(f"[WARNING] 計算車手 {driver_code} 煞車記錄失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_brake_deceleration(
        self,
        car_data: pd.DataFrame,
        brake_start_distance: float,
        brake_end_distance: float
    ) -> Optional[Dict[str, Any]]:
        """
        計算在指定距離範圍內的煞車減速度數據
        
        Args:
            car_data: 車手遙測數據 (包含 Speed, Distance, Time 欄位)
            brake_start_distance: 煞車起始距離 (米)
            brake_end_distance: 煞車終止距離 (米，硬編碼)
            
        Returns:
            包含減速時間、平均減速度、起始/結束速度的字典，失敗時返回 None
        """
        try:
            if car_data is None or car_data.empty:
                return None
            
            # 確保必要欄位存在
            if "Speed" not in car_data.columns or "Distance" not in car_data.columns or "Time" not in car_data.columns:
                return None
            
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            
            if speeds.empty or distances.empty:
                return None
            
            # ✅ 找到距離範圍內的起點和終點索引
            # 起點：最接近 brake_start_distance 的點
            start_distance_diff = (distances - brake_start_distance).abs()
            start_idx = start_distance_diff.idxmin()
            
            # 終點：最接近 brake_end_distance 的點（硬編碼）
            end_distance_diff = (distances - brake_end_distance).abs()
            end_idx = end_distance_diff.idxmin()
            
            # 確保起點在終點之前
            if start_idx >= end_idx:
                return None
            
            # 獲取速度值
            start_speed = speeds.loc[start_idx] if start_idx in speeds.index else None
            end_speed = speeds.loc[end_idx] if end_idx in speeds.index else None
            
            if start_speed is None or end_speed is None or pd.isna(start_speed) or pd.isna(end_speed):
                return None
            
            # 獲取實際測量到的距離
            actual_distance_start = distances[start_idx]
            actual_distance_end = distances[end_idx]
            brake_distance = float(actual_distance_end - actual_distance_start)
            
            # 計算時間差
            time_start = car_data.loc[start_idx, "Time"]
            time_end = car_data.loc[end_idx, "Time"]
            
            if hasattr(time_start, "total_seconds"):
                time_start_sec = time_start.total_seconds()
            else:
                time_start_sec = float(time_start)
            
            if hasattr(time_end, "total_seconds"):
                time_end_sec = time_end.total_seconds()
            else:
                time_end_sec = float(time_end)
            
            time_diff = time_end_sec - time_start_sec
            
            if time_diff <= 0:
                return None
            
            # 計算速度變化和平均減速度
            speed_change_kmh = float(end_speed - start_speed)  # 負值！
            speed_change_ms = speed_change_kmh / 3.6  # 轉換為 m/s（負值）
            avg_deceleration = speed_change_ms / time_diff  # 負值！
            
            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(brake_distance, 2),
                "avg_deceleration_ms2": round(abs(avg_deceleration), 2),  # 取絕對值
                "start_speed_kmh": round(float(start_speed), 1),
                "end_speed_kmh": round(float(end_speed), 1),
                "speed_reduction_kmh": round(abs(speed_change_kmh), 1),
                "actual_distance_start": round(float(actual_distance_start), 1),
                "actual_distance_end": round(float(actual_distance_end), 1)
            }
            
        except Exception as e:
            print(f"[WARNING] 計算煞車減速度失敗: {e}")
            return None

    # ------------------------------------------------------------------
    # Helper Methods (複製自 F48)
    # ------------------------------------------------------------------

    def _extract_car_data(self, lap_obj: Any) -> Optional[pd.DataFrame]:
        """提取車輛遙測數據並添加 Distance 欄位（完全複製 F48 邏輯）"""
        try:
            get_car_data = getattr(lap_obj, "get_car_data", None)
            if not callable(get_car_data):
                return None

            car_data = get_car_data()
            if car_data is None:
                return None
            
            # ✅ 關鍵修復：使用 add_distance() 方法添加 Distance 欄位
            if hasattr(car_data, "add_distance"):
                try:
                    car_data = car_data.add_distance()
                except Exception as e:
                    print(f"[WARNING] add_distance() 失敗: {e}")
            
            # 轉換為 DataFrame
            if isinstance(car_data, pd.DataFrame):
                return car_data
            elif hasattr(car_data, "to_pandas"):
                return car_data.to_pandas()
            else:
                return pd.DataFrame(car_data)
            
        except Exception as e:
            print(f"[WARNING] 提取車輛數據失敗: {e}")
            return None

    def _iter_drivers(self) -> Iterable[str]:
        """迭代所有車手代碼"""
        try:
            session = getattr(self.data_loader, "session", None)
            if session is None:
                return []
            
            laps = getattr(session, "laps", None)
            if laps is None or laps.empty:
                return []
            
            return laps["Driver"].unique()
            
        except Exception:
            return []

    def _pick_driver_laps(self, driver_code: str) -> Optional[Any]:
        """獲取指定車手的所有圈速"""
        try:
            session = getattr(self.data_loader, "session", None)
            if session is None:
                return None
            
            laps = getattr(session, "laps", None)
            if laps is None:
                return None
            
            return laps.pick_driver(driver_code)
            
        except Exception:
            return None

    def _find_fastest_lap(self, driver_laps: Any) -> Optional[Any]:
        """找出車手的最速圈"""
        try:
            if driver_laps is None or getattr(driver_laps, "empty", False):
                return None
            
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]
            if valid_laps.empty:
                return None
            
            fastest_idx = valid_laps['LapTime'].idxmin()
            return valid_laps.loc[fastest_idx]
            
        except Exception:
            return None

    def _extract_lap_number(self, lap_obj: Any) -> Optional[int]:
        """提取圈數"""
        try:
            if hasattr(lap_obj, "LapNumber"):
                lap_number = lap_obj.LapNumber
                # 修復 FutureWarning: 處理 Series 類型
                if hasattr(lap_number, "iloc"):
                    return int(lap_number.iloc[0])
                return int(lap_number)
            elif hasattr(lap_obj, "get") and callable(lap_obj.get):
                lap_num = lap_obj.get("LapNumber")
                if lap_num is not None:
                    return int(lap_num)
            return None
        except Exception:
            return None

    def _extract_session_time(self, lap_obj: Any) -> Optional[str]:
        """提取會話時間"""
        try:
            if hasattr(lap_obj, "Time"):
                time_val = lap_obj.Time
                if hasattr(time_val, "total_seconds"):
                    return str(time_val)
                return str(time_val)
            return None
        except Exception:
            return None

    def _get_driver_info(self, lap_obj: Any) -> Dict[str, Any]:
        """獲取車手資訊"""
        info = {
            "driver_number": None,
            "team": None,
            "full_name": None
        }
        
        try:
            if hasattr(lap_obj, "DriverNumber"):
                info["driver_number"] = int(lap_obj.DriverNumber)
            if hasattr(lap_obj, "Team"):
                info["team"] = str(lap_obj.Team)
            
            # 嘗試獲取完整姓名
            session = getattr(self.data_loader, "session", None)
            if session is not None:
                driver_code = str(lap_obj.Driver) if hasattr(lap_obj, "Driver") else None
                if driver_code:
                    drivers_info = getattr(session, "drivers", None)
                    if drivers_info is not None and driver_code in drivers_info:
                        driver_data = drivers_info[driver_code]
                        if hasattr(driver_data, "FullName"):
                            info["full_name"] = str(driver_data.FullName)
            
        except Exception:
            pass
        
        return info

    def _build_metadata(self) -> Dict[str, Any]:
        """建立元數據"""
        return {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "analysis_type": "brake_performance",
            "function_id": "34",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
