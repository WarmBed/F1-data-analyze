#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""All drivers straight-line speed analysis module."""

from __future__ import annotations

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import math
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

# 抑制 FastF1 的 FutureWarning (pick_driver/pick_lap 棄用警告)
# 這些 API 目前仍可用，與項目中其他分析器保持一致
warnings.filterwarnings('ignore', category=FutureWarning, module='fastf1')


@dataclass
class DriverSpeedRecord:
    """Container representing the maximum speed details and acceleration performance for a driver."""

    driver: str
    driver_number: Optional[int]
    team: Optional[str]
    full_name: Optional[str]
    max_speed_kmh: float
    lap_number: Optional[int]
    distance_m: Optional[float]
    session_time: Optional[str]
    throttle: Optional[float]
    drs: Optional[int]
    # 新增加速性能數據
    acceleration_100_300: Optional[Dict[str, float]] = None
    # ✅ 新增：基於 reference_segment 距離範圍的加速數據
    segment_acceleration: Optional[Dict[str, Any]] = None
    # 新增位置標註欄位
    in_core_range: bool = True  # 是否在核心參考範圍內測得
    measurement_notes: Optional[str] = None  # 測量備註

    def as_dict(self) -> Dict[str, Any]:
        result = {
            "driver": self.driver,
            "driver_number": self.driver_number,
            "team": self.team,
            "full_name": self.full_name,
            "max_speed_kmh": round(float(self.max_speed_kmh), 3),
            "lap_number": self.lap_number,
            "distance_m": round(float(self.distance_m), 3) if self.distance_m is not None else None,
            "session_time": self.session_time,
            "throttle_percent": round(float(self.throttle), 2) if self.throttle is not None else None,
            "drs": self.drs,
            # ✅ 新增位置標註
            "in_core_range": self.in_core_range,
            "measurement_notes": self.measurement_notes,
        }
        
        # ✅ 展開加速性能數據為獨立欄位（GUI 兼容格式）
        if self.acceleration_100_300 is not None:
            # 展開為 GUI 期望的欄位名稱
            result["acceleration_time_100_300_seconds"] = self.acceleration_100_300.get("time_seconds", 0.0)
            result["acceleration_distance_100_300_meters"] = self.acceleration_100_300.get("distance_meters", 0.0)
            result["avg_acceleration_100_300_ms2"] = self.acceleration_100_300.get("avg_acceleration_ms2", 0.0)
            result["acceleration_continuous_time_seconds"] = self.acceleration_100_300.get("time_seconds", 0.0)
        else:
            # 沒有加速數據時設為 None
            result["acceleration_time_100_300_seconds"] = None
            result["acceleration_distance_100_300_meters"] = None
            result["avg_acceleration_100_300_ms2"] = None
            result["acceleration_continuous_time_seconds"] = None
        
        # ✅ 新增：基於 reference_segment 的加速數據
        if self.segment_acceleration is not None:
            # 統一終點速度的加速數據
            result["segment_accel_time_seconds"] = self.segment_acceleration.get("time_seconds")
            result["segment_accel_distance_meters"] = self.segment_acceleration.get("distance_meters")
            result["segment_avg_acceleration_ms2"] = self.segment_acceleration.get("avg_acceleration_ms2")
            result["segment_start_speed_kmh"] = self.segment_acceleration.get("start_speed_kmh")
            result["segment_end_speed_kmh"] = self.segment_acceleration.get("end_speed_kmh")
            result["segment_speed_gain_kmh"] = self.segment_acceleration.get("speed_gain_kmh")
            
            # ⭐ v3.3 新增：個人最高速度數據
            result["max_speed_time_seconds"] = self.segment_acceleration.get("max_speed_time_seconds")
            result["max_speed_distance_meters"] = self.segment_acceleration.get("max_speed_distance_meters")
            result["segment_unified_end_speed_kmh"] = self.segment_acceleration.get("unified_end_speed_kmh")
            result["segment_personal_max_speed_kmh"] = self.segment_acceleration.get("personal_max_speed_kmh")
        else:
            result["segment_accel_time_seconds"] = None
            result["segment_accel_distance_meters"] = None
            result["segment_avg_acceleration_ms2"] = None
            result["segment_start_speed_kmh"] = None
            result["segment_end_speed_kmh"] = None
            result["segment_speed_gain_kmh"] = None
            
            # ⭐ v3.3 新增欄位
            result["max_speed_time_seconds"] = None
            result["max_speed_distance_meters"] = None
            result["segment_unified_end_speed_kmh"] = None
            result["segment_personal_max_speed_kmh"] = None
            
        return result


class AllDriversStraightLineSpeedAnalysis:
    """Analyse maximum straight-line speeds for every driver in a session."""

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
    
    def _check_position_data_availability(self) -> bool:
        """檢查位置數據是否可用
        
        根據 -f2 (track_position_analysis) 的實現:
        - Distance 欄位從 pos_data 獲取，不是 car_data
        - 如果 pos_data 沒有 Distance，可以從 X/Y 座標計算
        """
        try:
            session = getattr(self.data_loader, "session", None)
            if session is None:
                print("[WARNING] 無法獲取 session 對象")
                return False
            
            laps = getattr(session, "laps", None)
            if laps is None or laps.empty:
                print("[WARNING] 沒有圈速數據")
                return False
            
            # 測試獲取一個樣本圈的位置數據
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
            
            # ✅ 修正: 使用索引方式獲取圈對象，而不是 pick_lap
            lap_mask = driver_laps['LapNumber'] == lap_number
            if not lap_mask.any():
                print(f"[WARNING] 無法找到圈數 {lap_number}")
                return False
            
            lap_obj = driver_laps[lap_mask].iloc[0]
            
            # 嘗試獲取位置數據
            pos_data = lap_obj.get_pos_data()
            if pos_data is None or pos_data.empty:
                print("[WARNING] 位置數據為空")
                return False
            
            if 'X' not in pos_data.columns or 'Y' not in pos_data.columns:
                print("[WARNING] 位置數據缺少 X/Y 欄位")
                return False
            
            # ✅ 關鍵修正: Distance 從 pos_data 檢查，不是 car_data
            # 參考 -f2: has_distance = 'Distance' in pos_data.columns
            has_distance = 'Distance' in pos_data.columns
            
            if not has_distance:
                print("[INFO] 位置數據中沒有 Distance 欄位，將從 X/Y 座標計算")
                # 可以計算距離，所以仍然可用
                print("[INFO] 位置數據檢查通過 (將計算距離)")
                return True
            
            print("[INFO] 位置數據檢查通過 (Distance 可用)")
            return True
            
        except Exception as e:
            print(f"[WARNING] 位置數據檢查失敗: {e}")
            import traceback
            traceback.print_exc()  # ✅ 添加完整錯誤追蹤
            return False

    def run(self, *, top_n: Optional[int] = None, include_chart: bool = True) -> Dict[str, Any]:
        """執行全部車手直線速度分析（位置標準化版）"""
        self._ensure_ready()
        
        print("\n" + "="*80)
        print("全部車手直線速度分析 (位置標準化版本)")
        print("="*80)
        
        # 檢查位置數據可用性
        print("\n[步驟 1/4] 檢查位置數據可用性...")
        position_available = self._check_position_data_availability()
        
        if not position_available:
            return {
                "success": False,
                "function_id": "48",
                "message": "位置數據不可用，無法執行位置標準化分析",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                },
            }
        
        # 找出最速車手和最速圈
        print("\n[步驟 2/4] 找出最速車手和最速圈...")
        fastest_result = self._find_overall_fastest_lap()
        if fastest_result is None:
            return {
                "success": False,
                "function_id": "48",
                "message": "無法找到最速圈",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                },
            }
        
        fastest_driver, fastest_lap = fastest_result
        
        # 從最速圈識別主直線段位置
        print("\n[步驟 3/4] 從最速圈識別主直線段位置...")
        reference_segment = self._identify_main_straight_position(fastest_driver, fastest_lap)
        
        if reference_segment is None:
            return {
                "success": False,
                "function_id": "48",
                "message": "無法識別主直線段位置",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                },
            }
        
        print(f"\n主直線段位置已確定:")
        print(f"  參考車手: {reference_segment['driver']}")
        print(f"  參考圈數: {reference_segment['lap_number']}")
        print(f"  位置範圍: {reference_segment['segment_distance_start']:.1f}m - {reference_segment['segment_distance_end']:.1f}m")
        print(f"  直線長度: {reference_segment['segment_length']:.1f}m")
        print(f"  速度範圍: {reference_segment['segment_start_speed']:.1f} - {reference_segment['segment_max_speed']:.1f} km/h")
        
        # ✅ v3.3 步驟 1: 預掃描所有車手，獲取個人最高速度數據
        print(f"\n[步驟 4A/5] 預掃描所有車手，獲取個人最高速度數據...")
        print(f"  核心測量範圍: {reference_segment['segment_distance_start']:.1f}m - {reference_segment['segment_distance_end']:.1f}m")
        print(f"  加速測量邏輯: 從硬編碼起點到油門降低前最高速度點\n")
        
        temp_records: List[DriverSpeedRecord] = []
        driver_count = 0
        success_count = 0
        
        for driver_code in self._iter_drivers():
            driver_count += 1
            record = self._compute_driver_record_with_position(driver_code, reference_segment)
            if record:
                temp_records.append(record)
                success_count += 1
                
                # 顯示個人最高速度數據
                range_marker = "" if record.in_core_range else " [擴展範圍]"
                segment_end_speed = record.segment_acceleration.get('end_speed_kmh') if record.segment_acceleration else None
                if segment_end_speed:
                    print(f"  {driver_code}: 最高速度 {record.max_speed_kmh:.1f} km/h, 範圍內最高 {segment_end_speed:.1f} km/h{range_marker}")
                else:
                    print(f"  {driver_code}: 最高速度 {record.max_speed_kmh:.1f} km/h (無加速數據){range_marker}")
        
        print(f"\n預掃描完成: {success_count}/{driver_count} 車手")
        
        if not temp_records:
            return {
                "success": False,
                "function_id": "48",
                "message": "無法計算任何車手的直線最高速度 (缺少遙測資料)",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                    "reference_segment": reference_segment,
                },
            }
        
        # ✅ v3.3 步驟 2: 從核心範圍車手中找出最低的終點速度
        print(f"\n[步驟 4B/5] 確定統一終點速度...")
        core_range_records = [r for r in temp_records if r.in_core_range and r.segment_acceleration]
        
        if core_range_records:
            # 從核心範圍車手的終點速度中選最低值
            end_speeds = [r.segment_acceleration['end_speed_kmh'] for r in core_range_records]
            unified_end_speed = min(end_speeds)
            print(f"  ✅ 使用核心範圍車手的最低終點速度: {unified_end_speed:.1f} km/h")
            print(f"  核心範圍車手數: {len(core_range_records)}")
        else:
            # 如果沒有核心範圍車手，使用所有車手
            records_with_accel = [r for r in temp_records if r.segment_acceleration]
            if records_with_accel:
                end_speeds = [r.segment_acceleration['end_speed_kmh'] for r in records_with_accel]
                unified_end_speed = min(end_speeds)
                print(f"  ⚠️  無核心範圍車手，使用所有車手的最低終點速度: {unified_end_speed:.1f} km/h")
            else:
                print(f"  ❌ 無任何車手有加速數據，無法確定統一終點速度")
                unified_end_speed = None
        
        # ✅ v3.3 步驟 3: 使用統一終點速度重新計算所有車手的加速時間
        if unified_end_speed is not None:
            print(f"\n[步驟 4C/5] 使用統一終點速度 ({unified_end_speed:.1f} km/h) 重新計算加速時間...\n")
        else:
            print(f"\n[步驟 4C/5] ⚠️  無法確定統一終點速度，使用原始數據...\n")
        
        records: List[DriverSpeedRecord] = []
        for temp_record in temp_records:
            # 重新計算到統一速度的加速時間
            updated_record = self._recompute_driver_record_with_unified_endpoint(
                temp_record, 
                reference_segment, 
                unified_end_speed
            )
            if updated_record:
                records.append(updated_record)
                
                # 顯示更新後的數據
                range_marker = "" if updated_record.in_core_range else " [擴展範圍]"
                seg = updated_record.segment_acceleration
                if seg:
                    # ✅ 修正: 處理 None 值
                    max_speed_time = seg.get('max_speed_time_seconds')
                    if max_speed_time is not None:
                        max_speed_time_str = f"{max_speed_time:.2f}s"
                    else:
                        max_speed_time_str = "N/A"
                    
                    print(f"  {updated_record.driver}: 加速 {seg['time_seconds']:.2f}s " +
                          f"({seg['start_speed_kmh']:.0f}→{seg['end_speed_kmh']:.0f} km/h), " +
                          f"最高速度時間 {max_speed_time_str}{range_marker}")
                else:
                    print(f"  {updated_record.driver}: 無加速數據{range_marker}")
        
        print(f"\n重新計算完成: {len(records)} 車手")
        
        if not records:
            return {
                "success": False,
                "function_id": "48",
                "message": "無法計算任何車手的直線最高速度 (缺少遙測資料)",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                    "reference_segment": reference_segment,
                },
            }

        records.sort(key=lambda item: item.max_speed_kmh, reverse=True)
        if top_n is not None and isinstance(top_n, int) and top_n > 0:
            sliced_records = records[:top_n]
        else:
            sliced_records = records

        # ✅ 更新 reference_segment 為實際加速測量範圍
        # 使用所有車手的最大加速終點距離作為 segment_distance_end
        if temp_records:
            actual_end_distances = []
            for r in temp_records:
                if r.segment_acceleration and "actual_distance_end" in r.segment_acceleration:
                    actual_end_distances.append(r.segment_acceleration["actual_distance_end"])
            
            if actual_end_distances:
                # 使用最大加速終點距離（涵蓋所有車手的測量範圍）
                max_end_distance = max(actual_end_distances)
                reference_segment["segment_distance_end"] = max_end_distance
                reference_segment["segment_length"] = max_end_distance - reference_segment["segment_distance_start"]
                print(f"\n✅ 更新分析範圍為實際加速測量範圍:")
                print(f"   起點: {reference_segment['segment_distance_start']:.1f}m")
                print(f"   終點: {max_end_distance:.1f}m (最遠車手的加速終點)")
                print(f"   長度: {reference_segment['segment_length']:.1f}m")
        
        # ❌ [已移除] 添加統一速度範圍到 metadata
        # 原因：不再使用統一速度範圍，完全依賴硬編碼距離
        metadata = self._build_metadata(total_drivers=len(records))
        
        data_payload = {
            "metadata": metadata,
            "driver_speeds": [record.as_dict() for record in sliced_records],
            "summary": self._build_summary(records),
            "reference_segment": reference_segment,  # 添加參考直線段信息（已更新為實際測量範圍）
            "algorithm_version": "3.3_unified_endpoint_with_max_speed",  # ✅ 更新版本號（2025-10-18）
            "unified_end_speed_kmh": unified_end_speed  # ⭐ 添加統一終點速度
        }

        if include_chart:
            data_payload["chart_data"] = self._build_chart_data(records)

        # ✅ 修正: 處理 unified_end_speed 為 None 的情況
        if unified_end_speed is not None:
            success_message = f"全部車手直線速度與加速性能分析完成 (統一終點速度: {unified_end_speed:.1f} km/h)"
        else:
            success_message = "全部車手直線速度與加速性能分析完成 (部分車手無加速數據)"

        return {
            "success": True,
            "function_id": "48",
            "message": success_message,
            "data": data_payload,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _determine_unified_speed_range(self, reference_segment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ❌ DEPRECATED - 此函數已廢棄 (2025-10-18)
        
        原因：系統已改為完全依賴硬編碼距離範圍 (TRACK_ACCELERATION_START_DISTANCE)
        不再使用統一速度範圍限制
        
        保留此函數僅供參考，請勿調用！
        
        ---
        
        預掃描所有車手，確定統一的加速測量速度範圍
        
        ✅ 新邏輯（2025-10-15）：
        1. 起始速度：取所有車手在錨點搜索範圍內的最小速度的最小值，向上取整到 10 km/h，上限 200 km/h
        2. 終點速度：取所有車手最高速度的最小值，向下取整到 10 km/h，下限 200 km/h
        
        Returns:
            {
                "start_speed": float,  # 統一起始速度 (km/h)
                "end_speed": float,    # 統一終點速度 (km/h)
                "adjustment_reason": str,  # 調整原因說明
                "scanned_drivers": int  # 掃描的車手數量
            }
        """
        raise DeprecationWarning(
            "❌ _determine_unified_speed_range() 已廢棄！"
            "系統已改為完全依賴硬編碼距離範圍，不再使用統一速度限制。"
            "請檢查調用此函數的代碼並移除！"
        )
        print("  預掃描所有車手的速度範圍（基於錨點搜索範圍）...")
        
        distance_start = reference_segment["segment_distance_start"]
        distance_end = reference_segment["segment_distance_end"]
        race_name = reference_segment.get("race_name")  # ✅ 獲取賽道名稱
        
        # ✅ 賽道主直線段長度硬編碼（米）
        TRACK_STRAIGHT_LENGTHS = {
            "Monaco": 400,
            "Singapore": 800,
            "Hungary": 600,
            "Zandvoort": 700,
            "Azerbaijan": 2200,
            "Saudi Arabia": 1000,
            "Jeddah": 1000,
            "Monza": 1100,
            "Spa": 850,
            "Silverstone": 800,
            "Austria": 750,
            "Canada": 900,
            "Miami": 850,
            "Las Vegas": 1800,
            "Qatar": 1000,
            "Abu Dhabi": 1200,
            "Bahrain": 1100,
            "China": 1200,
            "Australia": 850,
            "Japan": 1000,
            "United States": 1000,
            "Mexico": 900,
            "Brazil": 950,
            "Italy": 1100,
            "Great Britain": 800,
            "Netherlands": 700,
            "Belgium": 850,
            "Spain": 1050,
            "Emilia Romagna": 800,
        }
        
        track_straight_length = TRACK_STRAIGHT_LENGTHS.get(race_name, 800) if race_name else 800
        print(f"    賽道: {race_name or '未知'}, 主直線長度: {track_straight_length}m")
        
        # 收集所有車手的速度範圍
        driver_speed_ranges = []
        
        for driver_code in self._iter_drivers():
            driver_laps = self._pick_driver_laps(driver_code)
            if driver_laps is None or getattr(driver_laps, "empty", False):
                continue
            
            fastest_lap = self._find_fastest_lap(driver_laps)
            if fastest_lap is None:
                continue
            
            car_data = self._extract_car_data(fastest_lap)
            if car_data is None or "Speed" not in car_data.columns:
                continue
            
            # ✅ 步驟 1: 在擴展範圍內找最高速度點
            speed_result = self._find_speed_in_position_range(
                car_data,
                distance_start,
                distance_end,
                position_tolerance=200.0
            )
            
            if not speed_result or not speed_result["can_calculate_acceleration"]:
                continue
            
            max_speed = speed_result["max_speed"]
            max_speed_idx = speed_result["max_speed_idx"]
            
            # ✅ 步驟 2: 計算錨點搜索範圍
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            
            max_speed_distance = distances[max_speed_idx] if max_speed_idx in distances.index else distance_end
            calculated_start = max_speed_distance - (track_straight_length - 100)  # ✅ 修正公式：減去 100m
            search_distance_start = calculated_start
            search_distance_end = max_speed_distance + 200
            
            # ✅ 步驟 3: 在錨點搜索範圍內找最小速度
            search_mask = (distances >= search_distance_start) & (distances <= search_distance_end)
            search_indices = car_data[search_mask].index
            
            if len(search_indices) == 0:
                continue
            
            # 只在最高速度點之前搜索
            search_indices_before_max = [idx for idx in search_indices if idx <= max_speed_idx]
            if len(search_indices_before_max) == 0:
                continue
            
            search_speeds_before_max = speeds.loc[speeds.index.intersection(search_indices_before_max)]
            if search_speeds_before_max.empty:
                continue
            
            min_speed_in_range = float(search_speeds_before_max.min())
            
            driver_speed_ranges.append({
                "driver": driver_code,
                "min_speed_in_search_range": min_speed_in_range,  # ✅ 搜索範圍內最小速度
                "max_speed": max_speed  # ✅ 擴展範圍內最高速度
            })
        
        if not driver_speed_ranges:
            print("  ⚠️  沒有車手數據可用於確定速度範圍")
            return None
        
        # ✅ 新邏輯：收集所有車手的最小速度和最高速度
        min_speeds_in_search = [d["min_speed_in_search_range"] for d in driver_speed_ranges]
        max_speeds = [d["max_speed"] for d in driver_speed_ranges]
        
        # 取所有車手的最小速度的最小值
        min_of_all_min_speeds = min(min_speeds_in_search)
        # 取所有車手的最高速度的最小值
        min_of_all_max_speeds = min(max_speeds)
        max_of_all_max_speeds = max(max_speeds)
        
        print(f"  掃描結果: {len(driver_speed_ranges)} 個車手")
        print(f"    所有車手最小速度的最小值: {min_of_all_min_speeds:.0f} km/h")
        print(f"    所有車手最高速度範圍: {min_of_all_max_speeds:.0f} - {max_of_all_max_speeds:.0f} km/h")
        
        # ✅ 確定統一起始速度：向上取整到 10 km/h，上限 200 km/h
        import math
        unified_start_raw = math.ceil(min_of_all_min_speeds / 10) * 10  # 向上取整到 10 km/h
        unified_start = min(unified_start_raw, 200.0)  # 上限 200 km/h
        
        if unified_start == unified_start_raw:
            start_adjustment = f"所有車手最低能達到 {unified_start:.0f} km/h（向上取整）"
        else:
            start_adjustment = f"所有車手最低能達到 {unified_start_raw:.0f} km/h，但已限制在上限 {unified_start:.0f} km/h"
        
        print(f"    統一起始速度: {unified_start:.0f} km/h ({start_adjustment})")
        
        # ✅ 確定統一終點速度：向下取整到 10 km/h，下限 200 km/h
        unified_end_raw = (int(min_of_all_max_speeds) // 10) * 10  # 向下取整到 10 km/h
        unified_end = max(unified_end_raw, 200.0)  # 下限 200 km/h
        
        if unified_end == unified_end_raw:
            end_adjustment = f"所有車手最高能達到 {unified_end:.0f} km/h（向下取整）"
        else:
            end_adjustment = f"所有車手最高能達到 {unified_end_raw:.0f} km/h，但已提升至下限 {unified_end:.0f} km/h"
        
        print(f"    統一終點速度: {unified_end:.0f} km/h ({end_adjustment})")
        
        adjustment_reason = f"起始: {start_adjustment}; 終點: {end_adjustment}"
        
        print(f"  ✅ 統一速度範圍確定完成: {unified_start:.0f} → {unified_end:.0f} km/h")
        
        return {
            "start_speed": unified_start,
            "end_speed": unified_end,
            "adjustment_reason": adjustment_reason,
            "scanned_drivers": len(driver_speed_ranges)
        }

    def _ensure_ready(self) -> None:
        if not self.data_loader:
            raise ValueError("data_loader 尚未初始化")
        if not getattr(self.data_loader, "session_loaded", False):
            raise ValueError("尚未載入任何賽事資料，無法執行分析")

    def _find_overall_fastest_lap(self) -> Optional[Tuple[str, Any]]:
        """找出整場賽事的最速圈和對應車手"""
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
            
            # 獲取該圈對象
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
    
    def _identify_main_straight_position(self, driver_code: str, lap_obj: Any) -> Optional[Dict[str, Any]]:
        """從最速車手的最速圈中識別主直線段位置 - 使用硬編碼起點 + throttle 100% 終點"""
        try:
            # ✅ 使用 _extract_car_data() 自動添加 Distance 欄位
            car_data = self._extract_car_data(lap_obj)
            if car_data is None or car_data.empty:
                print(f"[ERROR] 無法獲取 {driver_code} 的車輛數據")
                return None
            
            # ⭐ 嘗試獲取下一圈數據（用於處理跨越終點線的情況）
            lap_number = self._extract_lap_number(lap_obj)
            driver_laps = self._pick_driver_laps(driver_code)
            if driver_laps is not None and lap_number is not None:
                next_lap_data = self._extract_next_lap_data(driver_laps, lap_number)
                if next_lap_data is not None:
                    # 合併當前圈和下一圈的前段數據（0-1000m）
                    car_data = self._merge_lap_data_for_finish_line_crossing(car_data, next_lap_data)
            
            if "Speed" not in car_data.columns or "Distance" not in car_data.columns:
                print(f"[ERROR] 缺少必要欄位: Speed={('Speed' in car_data.columns)}, Distance={('Distance' in car_data.columns)}")
                return None
            
            # ⚠️ 檢查是否有 Throttle 欄位
            has_throttle = "Throttle" in car_data.columns
            if not has_throttle:
                print(f"[WARNING] 缺少 Throttle 欄位，將使用速度最高點作為終點")
            
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            
            if speeds.empty or distances.empty:
                print(f"[ERROR] 速度或距離數據為空")
                return None
            
            # ✅ 硬編碼起點字典
            TRACK_ACCELERATION_START_DISTANCE = {
                "China": 3544,
                "Japan": 0,
                "Monaco": 200,
                "Singapore": 3550,
                "Hungary": 0,
                "Zandvoort": 3840,
                "Saudi Arabia": 5584,
                "Monza": 4216,
                "Spa": 4997,
                "Silverstone": 1288,
                "Great Britain": 1288,  # Silverstone 別名
                "Austria": 4857,
                "Canada": 2725,
                "Miami": 3600,
                "Las Vegas": 5190,
                "Qatar": 5076,
                "Abu Dhabi": 1452,
                "United Arab Emirates": 1452,  # Abu Dhabi 別名
                "Bahrain": 4850,
                "Australia": 4807,
                "United States": 3625,
                "Mexico": 0,
                "Brazil": 823,
                "Spain": 4333,
                "Emilia Romagna": 3600,
                "Italy": 4216,  # Monza 別名
                "Belgium": 4997,  # Spa 別名
                "Netherlands": 3840,  # Zandvoort 別名
                "Germany": 0,  # Hockenheimring (系統自動計算)
                "Russia": 0,  # Sochi (系統自動計算)
                "Azerbaijan": 0,  # Baku (系統自動計算)
                "France": 0,  # Paul Ricard (系統自動計算)
            }
            
            race_name = self.race
            
            # ✅ 標準化賽道名稱（支援不區分大小寫）
            if race_name:
                # 將賽道名稱標準化為首字母大寫（Japan, China, Saudi Arabia 等）
                race_name = race_name.title()
                print(f"[INFO] 標準化賽道名稱: '{self.race}' → '{race_name}'")
            
            # ✅ 步驟 1: 使用硬編碼起點
            if race_name and race_name in TRACK_ACCELERATION_START_DISTANCE:
                hardcoded_start_distance = TRACK_ACCELERATION_START_DISTANCE[race_name]
                print(f"[INFO] 使用硬編碼起點: {hardcoded_start_distance:.1f}m (賽道: {race_name})")
            else:
                print(f"[ERROR] 賽道 '{race_name}' 未設定硬編碼起點，無法分析")
                return None
            
            # ✅ 步驟 2: 找到最接近硬編碼起點的數據點
            distance_diff = (distances - hardcoded_start_distance).abs()
            segment_start_idx = distance_diff.idxmin()
            segment_start_distance = distances[segment_start_idx]
            segment_start_speed = speeds[segment_start_idx]
            
            print(f"[INFO] 起點位置: {segment_start_distance:.1f}m @ {segment_start_speed:.1f} km/h")
            
            # ✅ 步驟 3: 從起點往後找 throttle 100% 區間中速度最高的點（作為終點）
            segment_end_idx = None
            segment_end_distance = None
            segment_end_speed = None
            
            if has_throttle:
                throttles = pd.to_numeric(car_data["Throttle"], errors="coerce")
                
                # 從起點往後掃描，找到所有 throttle >= 99% 的點
                full_throttle_indices = []
                for idx in car_data.index:
                    if idx < segment_start_idx:
                        continue
                    
                    if idx in throttles.index and not pd.isna(throttles[idx]):
                        if throttles[idx] >= 99:  # throttle >= 99% 視為全油門
                            full_throttle_indices.append(idx)
                
                if full_throttle_indices:
                    # ✅ 在全油門區間中找速度最高的點作為終點
                    max_speed_in_full_throttle = -1
                    for idx in full_throttle_indices:
                        if idx in speeds.index and not pd.isna(speeds[idx]):
                            if speeds[idx] > max_speed_in_full_throttle:
                                max_speed_in_full_throttle = speeds[idx]
                                segment_end_idx = idx
                    
                    if segment_end_idx is not None:
                        segment_end_distance = distances[segment_end_idx]
                        segment_end_speed = speeds[segment_end_idx]
                        print(f"[INFO] 找到 {len(full_throttle_indices)} 個全油門點，使用速度最高點 ({segment_end_speed:.1f} km/h) 作為終點")
                    else:
                        print(f"[WARNING] 全油門區間無有效速度數據")
                else:
                    print(f"[WARNING] 從起點往後未找到全油門點，使用速度最高點")
            
            # ✅ 回退方案: 如果沒有 throttle 或找不到全油門點，使用速度最高點
            if segment_end_idx is None:
                # 從起點往後找速度最高點
                speeds_after_start = speeds[speeds.index >= segment_start_idx]
                if not speeds_after_start.empty:
                    segment_end_idx = speeds_after_start.idxmax()
                    segment_end_distance = distances[segment_end_idx]
                    segment_end_speed = speeds[segment_end_idx]
                    print(f"[INFO] 使用速度最高點作為終點")
                else:
                    print(f"[ERROR] 起點之後無速度數據")
                    return None
            
            print(f"[INFO] 終點位置: {segment_end_distance:.1f}m @ {segment_end_speed:.1f} km/h")
            
            # ✅ 計算直線段長度和速度增益
            segment_length = float(segment_end_distance - segment_start_distance)
            speed_gain = float(segment_end_speed - segment_start_speed)
            
            print(f"[SUCCESS] 主直線段已識別:")
            print(f"   起點: {segment_start_distance:.1f}m @ {segment_start_speed:.1f} km/h (硬編碼)")
            print(f"   終點: {segment_end_distance:.1f}m @ {segment_end_speed:.1f} km/h (throttle 100% 最後點)")
            print(f"   長度: {segment_length:.1f}m")
            print(f"   速度增益: {speed_gain:.1f} km/h")

            # ✅ 檢測跨越終點線（保留用於兼容性）
            crosses_finish_line = False
            try:
                max_distance_in_lap = float(distances.max())
                if segment_start_distance > max_distance_in_lap or segment_end_distance > max_distance_in_lap:
                    crosses_finish_line = True
                    print(f"[INFO] 檢測到可能的跨圈計算 (segment_start={segment_start_distance:.1f}, segment_end={segment_end_distance:.1f}, lap_max={max_distance_in_lap:.1f})")
            except Exception:
                crosses_finish_line = False
            
            lap_number = self._extract_lap_number(lap_obj)
            
            segment_info = {
                "driver": driver_code,
                "lap_number": lap_number,
                "segment_distance_start": float(segment_start_distance),
                "segment_distance_end": float(segment_end_distance),
                "segment_start_speed": float(segment_start_speed),
                "segment_max_speed": float(segment_end_speed),
                "segment_length": segment_length,
                "speed_gain": speed_gain,
                "race_name": self.race
            }
            
            return segment_info
            
        except Exception as e:
            print(f"[ERROR] 識別主直線段失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_segment_acceleration(
        self,
        car_data: pd.DataFrame,
        segment_distance_start: float,
        segment_distance_end: float
    ) -> Optional[Dict[str, Any]]:
        """
        計算在指定距離範圍內的加速性能數據
        
        Args:
            car_data: 車手遙測數據 (包含 Speed, Distance, Time 欄位)
            segment_distance_start: 起始距離 (米)
            segment_distance_end: 終止距離 (米)
            
        Returns:
            包含加速時間、平均加速度、起始/最高速度的字典，失敗時返回 None
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
            # 起點：最接近 segment_distance_start 的點
            start_distance_diff = (distances - segment_distance_start).abs()
            start_idx = start_distance_diff.idxmin()
            
            # 終點：最接近 segment_distance_end 的點
            end_distance_diff = (distances - segment_distance_end).abs()
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
            segment_length = float(actual_distance_end - actual_distance_start)
            
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
            
            # 計算速度變化和平均加速度
            speed_change_kmh = float(end_speed - start_speed)
            speed_change_ms = speed_change_kmh / 3.6  # 轉換為 m/s
            avg_acceleration = speed_change_ms / time_diff
            
            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(segment_length, 2),
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "start_speed_kmh": round(float(start_speed), 1),
                "end_speed_kmh": round(float(end_speed), 1),
                "speed_gain_kmh": round(speed_change_kmh, 1),
                "actual_distance_start": round(float(actual_distance_start), 1),
                "actual_distance_end": round(float(actual_distance_end), 1)
            }
            
        except Exception as e:
            print(f"[WARNING] 計算 segment 加速度失敗: {e}")
            return None
    
    def _calculate_segment_acceleration_improved(
        self,
        car_data: pd.DataFrame,
        hardcoded_start_distance: float,
        track_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        計算從硬編碼起點到油門降低前最高速度點的加速性能（改進版 v3.2）
        
        ✅ 核心邏輯（2025-10-18 更新）：
        1. 起點：硬編碼的固定距離（例如 3544m），往後看找最接近的點
        2. 計算範圍：從起點到油門從 >= 95% 降到 < 95% 之前的所有點
        3. 終點選擇：在計算範圍內找到速度最高的點作為最終點
        4. 原因：
           - 油門降低代表車手開始鬆油門準備剎車
           - 使用最高速度點確保捕捉到最佳加速性能
           - 避免因短暫的油門降低（換檔、打滑）而提前終止測量
        5. 最高速度：全圈最高速度（不限於加速區間）
        
        Args:
            car_data: 車手遙測數據（必須包含 Speed, Distance, Time, Throttle 欄位）
            hardcoded_start_distance: 硬編碼起點距離（米）
            track_name: 賽道名稱（用於日誌，可選）
            
        Returns:
            包含加速時間、平均加速度、起始/終點速度的字典，失敗時返回 None
        """
        try:
            debug = True  # ✅ 啟用調試模式
            
            if debug:
                print(f"\n[DEBUG] === 開始計算 Segment 加速 ===")
                print(f"[DEBUG] 硬編碼起點: {hardcoded_start_distance}m")
                print(f"[DEBUG] 賽道: {track_name}")
            
            if car_data is None or car_data.empty:
                if debug:
                    print(f"[DEBUG] ❌ 步驟 0: car_data 為空")
                return None
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 0: car_data 有 {len(car_data)} 個數據點")
                print(f"[DEBUG]    欄位: {list(car_data.columns)}")
            
            # ✅ 確保必要欄位存在
            required_columns = ["Speed", "Distance", "Time"]
            for col in required_columns:
                if col not in car_data.columns:
                    if debug:
                        print(f"[DEBUG] ❌ 缺少必要欄位: {col}")
                    print(f"[WARNING] 缺少必要欄位: {col}")
                    return None
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 1: 所有必要欄位存在")
            
            # 提取數據
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            times = car_data["Time"]
            
            # ✅ 步驟 2: 檢查並提取油門數據（Throttle）
            if "Throttle" not in car_data.columns:
                if debug:
                    print(f"[DEBUG] ❌ 步驟 2: 缺少 Throttle 欄位")
                print(f"[WARNING] 缺少 Throttle 欄位，無法使用油門作為終點判斷")
                return None
            
            throttles = pd.to_numeric(car_data["Throttle"], errors="coerce")
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 2: 成功提取 Throttle 數據")
                print(f"[DEBUG]    油門範圍: {throttles.min():.1f}% - {throttles.max():.1f}%")
            
            # 移除 NaN 值
            valid_mask = ~(speeds.isna() | distances.isna() | throttles.isna())
            if not valid_mask.any():
                if debug:
                    print(f"[DEBUG] ❌ 步驟 3: 所有數據都是 NaN")
                return None
            
            speeds = speeds[valid_mask]
            distances = distances[valid_mask]
            times = times[valid_mask]
            throttles = throttles[valid_mask]
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 3: 移除 NaN 後剩餘 {len(speeds)} 個有效點")
                print(f"[DEBUG]    距離範圍: {distances.min():.1f}m - {distances.max():.1f}m")
                print(f"[DEBUG]    速度範圍: {speeds.min():.1f} - {speeds.max():.1f} km/h")
                print(f"[DEBUG]    油門範圍: {throttles.min():.1f}% - {throttles.max():.1f}%")
            
            # ✅ 步驟 4: 找到硬編碼起點（往後看，最接近且 >= hardcoded_start_distance）
            valid_start_indices = distances >= hardcoded_start_distance
            if not valid_start_indices.any():
                if debug:
                    print(f"[DEBUG] ❌ 步驟 4: 沒有數據在硬編碼起點 {hardcoded_start_distance}m 之後")
                return None  # 沒有數據在硬編碼起點之後
            
            # 找最接近的點（往後看）
            start_candidates = distances[valid_start_indices]
            distance_diffs = (start_candidates - hardcoded_start_distance).abs()
            start_idx = distance_diffs.idxmin()
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 4: 找到起點候選")
                print(f"[DEBUG]    起點索引: {start_idx}")
                print(f"[DEBUG]    起點距離: {distances[start_idx]:.1f}m")
                print(f"[DEBUG]    起點速度: {speeds[start_idx]:.1f} km/h")
                print(f"[DEBUG]    起點油門: {throttles[start_idx]:.1f}%")
            
            # ✅ 步驟 5: 檢查起點油門，如果 <= 50% 則往前找第一個 > 50% 的點
            # 理由：油門小於 50% 表示車手尚未全力加速
            THROTTLE_START_MIN = 50  # 百分比
            if throttles[start_idx] <= THROTTLE_START_MIN:
                if debug:
                    print(f"[DEBUG] 步驟 5: 起點油門 <= {THROTTLE_START_MIN}%，往前搜尋高油門點...")
                future_high_throttle = throttles.loc[start_idx:] > THROTTLE_START_MIN
                if not future_high_throttle.any():
                    if debug:
                        print(f"[DEBUG] ❌ 步驟 5: 沒有找到高油門區間 (> {THROTTLE_START_MIN}%)")
                    return None  # 沒有高油門區間
                start_idx = future_high_throttle[future_high_throttle].index[0]
                if debug:
                    print(f"[DEBUG] ✅ 步驟 5: 調整起點")
                    print(f"[DEBUG]    新起點距離: {distances[start_idx]:.1f}m")
                    print(f"[DEBUG]    新起點油門: {throttles[start_idx]:.1f}%")
            else:
                if debug:
                    print(f"[DEBUG] ✅ 步驟 5: 起點油門 > {THROTTLE_START_MIN}%，無需調整")
            
            # ✅ 步驟 6: 找到油門降低的點，並在降低之前的範圍內找最高速度點作為終點
            # 新邏輯（2025-10-18 v3.3.1）：
            # 1. 如果起點油門 < 95%，往後搜索第一個油門 ≥ 95% 的點作為真正的起點
            # 2. 從該高油門起點開始，找油門降低（< 95%）的點
            # 3. 在高油門範圍內找速度最高的點作為終點
            
            THROTTLE_HIGH_THRESHOLD = 95  # 百分比
            actual_start_idx = start_idx  # 實際起點
            
            # 如果當前起點油門 < 95%，往後找第一個 ≥ 95% 的點
            if throttles[start_idx] < THROTTLE_HIGH_THRESHOLD:
                if debug:
                    print(f"[DEBUG] 步驟 6: 起點油門 {throttles[start_idx]:.1f}% < {THROTTLE_HIGH_THRESHOLD}%")
                    print(f"[DEBUG]    往後搜索第一個 ≥ {THROTTLE_HIGH_THRESHOLD}% 的點...")
                
                future_throttles = throttles.loc[start_idx:]
                high_throttle_mask = future_throttles >= THROTTLE_HIGH_THRESHOLD
                
                if high_throttle_mask.any():
                    # 找到第一個高油門點，作為實際起點
                    actual_start_idx = high_throttle_mask[high_throttle_mask].index[0]
                    if debug:
                        print(f"[DEBUG] ✅ 找到高油門起點")
                        print(f"[DEBUG]    距離: {distances[actual_start_idx]:.1f}m")
                        print(f"[DEBUG]    油門: {throttles[actual_start_idx]:.1f}%")
                        print(f"[DEBUG]    速度: {speeds[actual_start_idx]:.1f} km/h")
                else:
                    if debug:
                        print(f"[DEBUG] ❌ 沒有找到 ≥ {THROTTLE_HIGH_THRESHOLD}% 的油門點")
                    return None  # 沒有高油門區間，無法計算
            
            # 從實際起點開始，找油門降低的點
            future_throttles = throttles.loc[actual_start_idx:]
            low_throttle_mask = future_throttles < THROTTLE_HIGH_THRESHOLD
            
            if debug:
                print(f"[DEBUG] 步驟 6: 從實際起點搜索油門 < {THROTTLE_HIGH_THRESHOLD}% 的點...")
            
            end_idx = None
            if low_throttle_mask.any():
                # 找到第一個低於閾值的點
                first_low_throttle_idx = low_throttle_mask[low_throttle_mask].index[0]
                
                # 計算範圍：從實際起點到油門降低之前
                loc_in_future = future_throttles.index.get_loc(first_low_throttle_idx)
                if loc_in_future > 0:
                    # 油門降低前的最後一個高油門點
                    last_high_throttle_idx = future_throttles.index[loc_in_future - 1]
                    
                    # 在實際起點到最後高油門點的範圍內，找速度最高的點
                    speed_range = speeds.loc[actual_start_idx:last_high_throttle_idx]
                    if len(speed_range) > 0:
                        end_idx = speed_range.idxmax()
                        
                        if debug:
                            print(f"[DEBUG] ✅ 步驟 6: 找到油門降低點並確定終點")
                            print(f"[DEBUG]    終點距離: {distances[end_idx]:.1f}m")
                            print(f"[DEBUG]    終點速度: {speeds[end_idx]:.1f} km/h")
                            print(f"[DEBUG]    終點油門: {throttles[end_idx]:.1f}%")
            
            # 如果沒有找到，使用全範圍最高速度點
            if end_idx is None:
                speed_range = speeds.loc[actual_start_idx:]
                if len(speed_range) > 0:
                    end_idx = speed_range.idxmax()
                    if debug:
                        print(f"[DEBUG] ⚠️  步驟 6: 沒有找到油門降低點，使用全範圍最高速度")
                        print(f"[DEBUG]    終點距離: {distances[end_idx]:.1f}m")
                        print(f"[DEBUG]    終點速度: {speeds[end_idx]:.1f} km/h")
                else:
                    if debug:
                        print(f"[DEBUG] ❌ 步驟 6: 無有效數據")
                    return None
            
            # 使用實際起點替換原始起點
            start_idx = actual_start_idx
            
            # ✅ 步驟 7: 確保終點在起點之後
            if start_idx >= end_idx:
                if debug:
                    print(f"[DEBUG] ❌ 步驟 7: 終點不在起點之後（start_idx={start_idx}, end_idx={end_idx}）")
                return None
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 7: 終點在起點之後")
            
            # ✅ 步驟 8: 提取起點和終點的數據
            start_speed = float(speeds[start_idx])
            end_speed = float(speeds[end_idx])
            start_distance = float(distances[start_idx])
            end_distance = float(distances[end_idx])
            start_time = times[start_idx]
            end_time = times[end_idx]
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 8: 提取數據完成")
                print(f"[DEBUG]    加速區間: {start_distance:.1f}m - {end_distance:.1f}m ({end_distance - start_distance:.1f}m)")
                print(f"[DEBUG]    速度變化: {start_speed:.1f} - {end_speed:.1f} km/h ({end_speed - start_speed:.1f} km/h)")
            
            # 先計算距離差（用於時間估算）
            distance_diff = end_distance - start_distance
            
            # ✅ 步驟 9: 計算時間差（處理跨越終點線的情況）
            if hasattr(start_time, "total_seconds"):
                time_start_sec = start_time.total_seconds()
            else:
                time_start_sec = float(start_time)
            
            if hasattr(end_time, "total_seconds"):
                time_end_sec = end_time.total_seconds()
            else:
                time_end_sec = float(end_time)
            
            time_diff = time_end_sec - time_start_sec
            
            # ⚠️ 處理跨越終點線的情況（時間反轉）
            if time_diff < 0:
                if debug:
                    print(f"[DEBUG] ⚠️  檢測到時間反轉（跨越終點線）")
                    print(f"[DEBUG]    原始時間差: {time_diff:.3f}秒")
                    print(f"[DEBUG]    起點時間: {time_start_sec:.3f}秒")
                    print(f"[DEBUG]    終點時間: {time_end_sec:.3f}秒")
                
                # 使用距離和平均速度估算時間
                avg_speed_ms = ((start_speed + end_speed) / 2) / 3.6  # 平均速度 (m/s)
                if avg_speed_ms > 0:
                    time_diff = distance_diff / avg_speed_ms
                    if debug:
                        print(f"[DEBUG]    使用距離估算時間: {time_diff:.3f}秒")
                else:
                    if debug:
                        print(f"[DEBUG] ❌ 無法估算時間（平均速度 = 0）")
                    return None
            
            if time_diff <= 0:
                if debug:
                    print(f"[DEBUG] ❌ 步驟 9: 時間差仍然 <= 0 ({time_diff})")
                return None
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 9: 時間差計算完成: {time_diff:.3f}秒")
            
            # ✅ 步驟 10: 計算性能指標
            speed_gain_kmh = end_speed - start_speed
            speed_gain_ms = speed_gain_kmh / 3.6  # 轉為 m/s
            avg_acceleration = speed_gain_ms / time_diff
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 10: 性能指標計算完成")
                print(f"[DEBUG]    加速時間: {time_diff:.3f}秒")
                print(f"[DEBUG]    加速距離: {distance_diff:.2f}m")
                print(f"[DEBUG]    速度增益: {speed_gain_kmh:.1f} km/h")
                print(f"[DEBUG]    平均加速度: {avg_acceleration:.2f} m/s²")
            
            # ✅ 步驟 11: 返回完整的加速性能數據
            result = {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(distance_diff, 2),
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "start_speed_kmh": round(start_speed, 1),
                "end_speed_kmh": round(end_speed, 1),
                "speed_gain_kmh": round(speed_gain_kmh, 1),
                "actual_distance_start": round(start_distance, 1),
                "actual_distance_end": round(end_distance, 1)
            }
            
            if debug:
                print(f"[DEBUG] ✅ 步驟 11: 返回結果")
                print(f"[DEBUG] === Segment 加速計算完成 ===\n")
            
            return result
            
        except Exception as e:
            print(f"[WARNING] 計算改進版 segment 加速度失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_segment_acceleration_to_target_speed(
        self,
        car_data: pd.DataFrame,
        hardcoded_start_distance: float,
        target_end_speed_kmh: float,
        track_name: Optional[str] = None,
        debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        計算從硬編碼起點到達指定目標速度的加速性能（v3.3 新增）
        
        ✅ 核心邏輯（2025-10-18）：
        1. 起點：硬編碼的固定距離（例如 3544m）
        2. 終點：找到速度達到或最接近目標速度（例如 310 km/h）的點
        3. 用途：統一所有車手的加速測量終點，使數據具有可比性
        
        Args:
            car_data: 車手遙測數據（必須包含 Speed, Distance, Time 欄位）
            hardcoded_start_distance: 硬編碼起點距離（米）
            target_end_speed_kmh: 目標終點速度（km/h）
            track_name: 賽道名稱（用於日誌，可選）
            debug: 是否啟用調試輸出
            
        Returns:
            包含加速時間、平均加速度、起始/終點速度的字典，失敗時返回 None
        """
        try:
            if debug:
                print(f"\n[DEBUG] === 計算到目標速度的加速 ===")
                print(f"[DEBUG] 目標速度: {target_end_speed_kmh} km/h")
            
            if car_data is None or car_data.empty:
                return None
            
            # 提取數據
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            times = car_data["Time"]
            
            # 移除 NaN
            valid_mask = ~(speeds.isna() | distances.isna())
            if not valid_mask.any():
                return None
            
            speeds = speeds[valid_mask]
            distances = distances[valid_mask]
            times = times[valid_mask]
            
            # 找到起點
            valid_start_indices = distances[distances >= hardcoded_start_distance].index
            if len(valid_start_indices) == 0:
                return None
            
            start_candidates = distances[valid_start_indices]
            distance_diffs = (start_candidates - hardcoded_start_distance).abs()
            start_idx = distance_diffs.idxmin()
            
            start_speed = float(speeds[start_idx])
            start_distance = float(distances[start_idx])
            start_time = times[start_idx]
            
            if debug:
                print(f"[DEBUG] 起點: {start_distance:.1f}m, 速度 {start_speed:.1f} km/h")
            
            # 找到目標速度點（從起點開始搜尋）
            future_speeds = speeds.loc[start_idx:]
            
            # 找到第一個 >= 目標速度的點
            target_mask = future_speeds >= target_end_speed_kmh
            
            if target_mask.any():
                end_idx = target_mask[target_mask].index[0]
            else:
                # 如果無法達到目標速度，使用最高速度點
                end_idx = future_speeds.idxmax()
                if debug:
                    print(f"[DEBUG] ⚠️  無法達到目標速度 {target_end_speed_kmh} km/h，使用最高速度點")
            
            end_speed = float(speeds[end_idx])
            end_distance = float(distances[end_idx])
            end_time = times[end_idx]
            
            if debug:
                print(f"[DEBUG] 終點: {end_distance:.1f}m, 速度 {end_speed:.1f} km/h")
            
            # 確保終點在起點之後
            if start_idx >= end_idx:
                return None
            
            # 計算時間差
            if hasattr(start_time, "total_seconds"):
                time_start_sec = start_time.total_seconds()
            else:
                time_start_sec = float(start_time)
            
            if hasattr(end_time, "total_seconds"):
                time_end_sec = end_time.total_seconds()
            else:
                time_end_sec = float(end_time)
            
            time_diff = time_end_sec - time_start_sec
            
            # 處理跨越終點線的情況
            if time_diff < 0:
                avg_speed_ms = ((start_speed + end_speed) / 2) / 3.6
                if avg_speed_ms > 0:
                    time_diff = (end_distance - start_distance) / avg_speed_ms
                else:
                    return None
            
            if time_diff <= 0:
                return None
            
            # 計算距離差
            distance_diff = end_distance - start_distance
            
            # 計算性能指標
            speed_gain_kmh = end_speed - start_speed
            speed_gain_ms = speed_gain_kmh / 3.6
            avg_acceleration = speed_gain_ms / time_diff
            
            if debug:
                print(f"[DEBUG] 加速時間: {time_diff:.3f}秒")
                print(f"[DEBUG] 加速距離: {distance_diff:.2f}m")
                print(f"[DEBUG] 速度增益: {speed_gain_kmh:.1f} km/h")
                print(f"[DEBUG] === 完成 ===\n")
            
            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(distance_diff, 2),
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "start_speed_kmh": round(start_speed, 1),
                "end_speed_kmh": round(end_speed, 1),
                "speed_gain_kmh": round(speed_gain_kmh, 1),
                "actual_distance_start": round(start_distance, 1),
                "actual_distance_end": round(end_distance, 1)
            }
            
        except Exception as e:
            if debug:
                print(f"[WARNING] 計算到目標速度的加速失敗: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def _find_closest_distance_index(
        self,
        distances: pd.Series,
        target_distance: float
    ) -> Optional[int]:
        """
        輔助方法：找到最接近目標距離的索引
        
        Args:
            distances: 距離數據序列
            target_distance: 目標距離（米）
            
        Returns:
            最接近目標距離的索引，失敗時返回 None
        """
        try:
            if distances is None or distances.empty:
                return None
            
            distance_diff = (distances - target_distance).abs()
            closest_idx = distance_diff.idxmin()
            
            return closest_idx
            
        except Exception as e:
            print(f"[WARNING] 找尋最接近距離的索引失敗: {e}")
            return None
    
    def _find_speed_in_position_range(
        self,
        car_data: pd.DataFrame,
        distance_start: float,
        distance_end: float,
        position_tolerance: float = 200.0
    ) -> Optional[Dict[str, Any]]:
        """在指定位置範圍內找到最高速度點
        
        Args:
            car_data: 車手遙測數據
            distance_start: 參考直線段起點（米）
            distance_end: 參考直線段終點（米）
            position_tolerance: 位置容差（米），預設 ±200m
                例如：參考範圍 1000-1500m，實際搜尋範圍 800-1700m
        
        Returns:
            包含最高速度點信息的字典，額外標註是否在擴展範圍內測得
        """
        try:
            if "Distance" not in car_data.columns or "Speed" not in car_data.columns:
                return None
            
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            
            # ✅ 擴展測量範圍（參考範圍 ± 容差）
            extended_start = distance_start - position_tolerance
            extended_end = distance_end + position_tolerance
            
            # 過濾出擴展位置範圍內的數據
            mask = (distances >= extended_start) & (distances <= extended_end)
            range_indices = car_data[mask].index
            
            if len(range_indices) == 0:
                return None
            
            range_speeds = speeds[mask]
            if range_speeds.empty:
                return None
            
            # 找到範圍內的最高速度點
            max_speed_idx = range_speeds.idxmax()
            max_speed = range_speeds[max_speed_idx]
            max_speed_distance = distances[max_speed_idx]
            
            # ✅ 檢查是否在核心範圍內（參考直線段）
            in_core_range = (max_speed_distance >= distance_start) and (max_speed_distance <= distance_end)
            in_extended_range = not in_core_range  # 在擴展範圍但不在核心範圍
            
            # ✅ 加速測量邏輯：從整個最速圈數據中往前推找起點（不限於擴展範圍！）
            # 擴展範圍僅用於確定最高速度點位置，加速測量需要搜索整個圈
            can_calculate_acceleration = False
            speed_100_found = False
            speed_150_found = False
            start_speed_threshold = None
            start_speed_idx = None
            
            # ✅ 關鍵修正：從整個遙測數據（整個最速圈）中搜索，不限於擴展範圍
            # 找到在最高速度點之前的所有數據點
            max_speed_pos_in_full_data = car_data.index.get_loc(max_speed_idx)
            all_indices_before_max = car_data.index[:max_speed_pos_in_full_data + 1]
            
            # 優先尋找 100 km/h（在整個最速圈中搜索）
            for idx in reversed(all_indices_before_max):
                if idx in speeds.index and speeds[idx] <= 100:
                    speed_100_found = True
                    can_calculate_acceleration = True
                    start_speed_threshold = 100
                    start_speed_idx = idx
                    break
            
            # 如果找不到 100 km/h，嘗試 150 km/h（在整個最速圈中搜索）
            if not speed_100_found:
                for idx in reversed(all_indices_before_max):
                    if idx in speeds.index and speeds[idx] <= 150:
                        speed_150_found = True
                        can_calculate_acceleration = True
                        start_speed_threshold = 150
                        start_speed_idx = idx
                        break
            
            # 如果都找不到，使用整個最速圈中最高速度點之前的最小速度
            if not can_calculate_acceleration and len(all_indices_before_max) > 0:
                full_speeds_before_max = speeds.loc[speeds.index.intersection(all_indices_before_max)]
                if not full_speeds_before_max.empty:
                    min_speed_idx = full_speeds_before_max.idxmin()
                    min_speed = full_speeds_before_max[min_speed_idx]
                    
                    # ✅ 降低要求：只要有顯著速度增益就計算（20 km/h）
                    if max_speed - min_speed >= 20:
                        can_calculate_acceleration = True
                        start_speed_threshold = float(min_speed)
                        start_speed_idx = min_speed_idx
            
            return {
                "max_speed_idx": max_speed_idx,
                "max_speed": float(max_speed),
                "distance": float(max_speed_distance),
                "can_calculate_acceleration": can_calculate_acceleration,
                "speed_100_found": speed_100_found,
                "speed_150_found": speed_150_found,
                "start_speed_threshold": start_speed_threshold,
                "start_speed_idx": start_speed_idx,
                "range_indices": range_indices,
                # ✅ 新增：標註測量位置
                "in_core_range": in_core_range,
                "in_extended_range": in_extended_range,
                "core_range_start": distance_start,
                "core_range_end": distance_end,
                "extended_range_start": extended_start,
                "extended_range_end": extended_end,
                "position_tolerance": position_tolerance
            }
            
        except Exception as e:
            print(f"[WARNING] 在位置範圍內查找速度失敗: {e}")
            return None

    def _collect_speed_records(self) -> List[DriverSpeedRecord]:
        records: List[DriverSpeedRecord] = []
        for driver_code in self._iter_drivers():
            record = self._compute_driver_record(driver_code)
            if record:
                records.append(record)
        return records

    # Driver iteration -------------------------------------------------

    def _iter_drivers(self) -> Iterable[str]:
        results = getattr(self.data_loader, "results", None)
        if isinstance(results, pd.DataFrame) and not results.empty:
            return results["Abbreviation"].dropna().unique()

        # fallback to synchronized data if available
        loaded = getattr(self.data_loader, "loaded_data", {}) or {}
        sync_map = loaded.get("synchronized_driver_data", {})
        if isinstance(sync_map, dict):
            return list(sync_map.keys())

        # final fallback: try laps dataframe columns
        laps = getattr(self.data_loader, "laps", None)
        if hasattr(laps, "drivers"):
            return list(laps.drivers)
        if isinstance(laps, pd.DataFrame) and "Driver" in laps.columns:
            return laps["Driver"].dropna().unique()

        return []

    # Single driver computation ---------------------------------------

    def _find_fastest_lap(self, driver_laps: Any) -> Optional[Any]:
        """找到最速圈（LapTime 最小的圈）"""
        if driver_laps is None or getattr(driver_laps, "empty", False):
            return None

        # 嘗試轉換為 DataFrame
        if hasattr(driver_laps, "to_pandas"):
            laps_df = driver_laps.to_pandas()
        elif isinstance(driver_laps, pd.DataFrame):
            laps_df = driver_laps
        else:
            # 無法轉換，嘗試直接迭代
            laps_df = None

        if laps_df is not None:
            # 過濾有效圈（有圈速的圈）
            valid_laps = laps_df[laps_df["LapTime"].notna()].copy()

            if valid_laps.empty:
                return None

            # 找到最速圈
            fastest_idx = valid_laps["LapTime"].idxmin()
            fastest_lap_num = int(valid_laps.loc[fastest_idx, "LapNumber"])

            # 從原始 driver_laps 中取得該圈
            for _, lap in self._iter_lap_rows(driver_laps):
                if self._extract_lap_number(lap) == fastest_lap_num:
                    return lap

        # 回退：返回第一圈
        for _, lap in self._iter_lap_rows(driver_laps):
            return lap

        return None

    def _identify_straight_line_segments(self, car_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """識別所有直線段（基於最高速度點回推）
        
        新邏輯：
        1. 找到整圈的最高速度點
        2. 從最高速度點向前回推，找到加速起點
        3. 這樣可以捕捉到真實的直線段（包含加速減緩階段）
        """
        if car_data is None or car_data.empty or "Speed" not in car_data.columns:
            return []

        speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
        if speeds.empty or len(speeds) < 10:
            return []

        # ✅ 步驟 1: 找到整圈的最高速度點
        max_speed_idx = speeds.idxmax()
        max_speed = speeds[max_speed_idx]
        
        # ✅ 步驟 2: 從最高速度點向前回推，找到直線段起點
        # 起點定義：速度持續上升的區間起點（允許輕微波動）
        segment_start_idx = None
        segment_start_speed = None
        
        speeds_list = list(speeds.items())
        max_speed_pos = None
        
        # 找到最高速度點在列表中的位置
        for i, (idx, speed) in enumerate(speeds_list):
            if idx == max_speed_idx:
                max_speed_pos = i
                break
        
        if max_speed_pos is None or max_speed_pos < 3:
            # 最高速度點太靠前，無法回推
            return []
        
        # 從最高速度點向前掃描，允許數據波動
        consecutive_decreases = 0  # 連續下降計數器
        temp_start_idx = max_speed_idx
        temp_start_speed = max_speed
        
        for i in range(max_speed_pos - 1, -1, -1):
            idx, speed = speeds_list[i]
            next_idx, next_speed = speeds_list[i + 1]
            
            # 檢查速度是否在合理範圍（> 60 km/h）
            if speed <= 60:
                # 速度過低，停止回推
                break
            
            # 檢查速度趨勢
            if next_speed > speed:
                # 速度上升，繼續回推
                temp_start_idx = idx
                temp_start_speed = speed
                consecutive_decreases = 0  # 重置下降計數器
            elif next_speed >= speed - 5:
                # 輕微下降（≤5 km/h），容忍並繼續
                temp_start_idx = idx
                temp_start_speed = speed
                consecutive_decreases = 0
            else:
                # 速度明顯下降
                consecutive_decreases += 1
                if consecutive_decreases >= 3:
                    # 連續 3 次明顯下降，停止回推
                    break
        
        segment_start_idx = temp_start_idx
        segment_start_speed = temp_start_speed
        
        # ✅ 步驟 3: 檢查直線段是否有效（速度增益 > 80 km/h，降低要求）
        speed_gain = max_speed - segment_start_speed
        if speed_gain < 80:
            # 速度增益不足，可能不是有效的直線段
            return []
        
        # ✅ 步驟 4: 從最高速度點向後延伸，找到終點（速度開始明顯下降）
        segment_end_idx = max_speed_idx
        segment_end_speed = max_speed
        
        for i in range(max_speed_pos + 1, len(speeds_list)):
            idx, speed = speeds_list[i]
            prev_idx, prev_speed = speeds_list[i - 1]
            
            # 如果速度下降不超過 5 km/h，仍算直線段
            if speed >= prev_speed - 5:
                segment_end_idx = idx
                segment_end_speed = speed
                # 更新最高速度（可能在減速前還有更高點）
                if speed > max_speed:
                    max_speed = speed
                    max_speed_idx = idx
            else:
                # 速度明顯下降，直線段結束
                break
        
        # ✅ 返回直線段（只有一個，包含最高速度點）
        segment = {
            "start_idx": segment_start_idx,
            "end_idx": segment_end_idx,
            "start_speed": segment_start_speed,
            "max_speed": max_speed,
            "max_speed_idx": max_speed_idx
        }
        
        return [segment]  # 返回包含最高速度點的直線段

    def _calculate_acceleration_in_segment(
        self,
        car_data: pd.DataFrame,
        segment: Dict[str, Any]
    ) -> Optional[Dict[str, float]]:
        """在指定直線段內計算 100→300 km/h 加速時間"""
        try:
            # 只在該直線段的範圍內搜索
            segment_start = segment["start_idx"]
            segment_end = segment["end_idx"]

            # 獲取該段的速度數據
            segment_data = car_data.loc[segment_start:segment_end].copy()
            speeds = pd.to_numeric(segment_data["Speed"], errors="coerce").dropna()

            if speeds.empty or "Time" not in segment_data.columns:
                return None

            # 在該段內找到 100 km/h 和 250 km/h 的點
            speed_100_idx = None
            speed_250_idx = None
            
            # ✅ 統一標準：計算 100→250 km/h 的加速時間
            # 優點：所有賽道都能達到 250 km/h，便於比較
            target_speed = 250

            for idx in speeds.index:
                speed = speeds[idx]
                if speed >= 100 and speed_100_idx is None:
                    speed_100_idx = idx
                if speed >= target_speed and speed_250_idx is None:
                    speed_250_idx = idx
                    break

            # 檢查是否找到兩個速度點
            if speed_100_idx is None or speed_250_idx is None:
                return None
            
            # 獲取實際速度值
            actual_speed_100 = speeds[speed_100_idx]
            actual_speed_250 = speeds[speed_250_idx]

            # 計算時間差
            time_100 = segment_data.loc[speed_100_idx, "Time"]
            time_250 = segment_data.loc[speed_250_idx, "Time"]

            if hasattr(time_100, "total_seconds"):
                time_100_sec = time_100.total_seconds()
            else:
                time_100_sec = float(time_100)

            if hasattr(time_250, "total_seconds"):
                time_250_sec = time_250.total_seconds()
            else:
                time_250_sec = float(time_250)

            time_diff = time_250_sec - time_100_sec

            # 驗證時間差合理性（100→250 km/h 應在 2-10 秒範圍）
            if time_diff <= 0 or time_diff > 12:
                return None

            # 計算距離差
            distance_diff = None
            if "Distance" in segment_data.columns:
                try:
                    dist_100 = segment_data.loc[speed_100_idx, "Distance"]
                    dist_250 = segment_data.loc[speed_250_idx, "Distance"]
                    distance_diff = float(dist_250) - float(dist_100)
                except (KeyError, TypeError, ValueError):
                    distance_diff = None

            # 計算平均加速度 (100→250 km/h)
            velocity_change = (250 - 100) / 3.6  # 轉換為 m/s = 41.67 m/s
            avg_acceleration = velocity_change / time_diff

            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(distance_diff, 2) if distance_diff else None,
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "speed_100_kmh": 100.0,
                "speed_250_kmh": 250.0,
                "speed_100_index": int(speed_100_idx),
                "speed_250_index": int(speed_250_idx),
                "segment_start_speed": round(segment["start_speed"], 1),
                "segment_max_speed": round(segment["max_speed"], 1)
            }

        except Exception:
            return None
    
    def _calculate_acceleration_in_position_range(
        self,
        car_data: pd.DataFrame,
        max_speed_idx: int,
        distance_start: float,
        distance_end: float,
        range_indices: Any,
        start_speed_threshold: Optional[float] = None,
        start_speed_idx: Optional[int] = None,
        unified_start_speed: Optional[float] = None,  # ⚠️ DEPRECATED 參數
        unified_end_speed: Optional[float] = None,    # ⚠️ DEPRECATED 參數
        race_name: Optional[str] = None
    ) -> Optional[Dict[str, float]]:
        """
        ⚠️ DEPRECATED - 此函數使用舊邏輯（統一速度範圍）
        
        建議使用：_calculate_segment_acceleration_improved()
        
        原因：此函數基於統一速度範圍（unified_start_speed, unified_end_speed），
        新邏輯已改為完全依賴硬編碼距離範圍。
        
        保留此函數僅用於計算 100-300 km/h 固定速度範圍的加速性能。
        若需要賽道段加速性能，請使用 _calculate_segment_acceleration_improved()。
        
        ---
        
        計算加速性能（基於統一速度範圍）
        
        ✅ 關鍵修正：
        - 最高速度點：在擴展範圍（range_indices）內找
        - 加速起點：在整個最速圈（car_data）中往前推找
        - 加速終點：統一終點速度（unified_end_speed）
        """
        try:
            # ✅ 使用整個最速圈的數據（不限於擴展範圍）
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
            distances = pd.to_numeric(car_data["Distance"], errors="coerce")

            if speeds.empty or "Time" not in car_data.columns:
                return None

            # ✅ 使用統一的起始和終點速度
            target_speed_low = unified_start_speed if unified_start_speed is not None else 100.0
            target_speed_high = unified_end_speed if unified_end_speed is not None else 250.0

            # ✅ 基於賽道主直線長度的智能搜索範圍（硬編碼賽道特性）
            # 從最快車手的最高速度位置往前推算起點：max_speed_distance - (直線長度 + 100m)
            
            # 賽道主直線段長度硬編碼（米）
            TRACK_STRAIGHT_LENGTHS = {
                "Monaco": 400,
                "Singapore": 800,
                "Hungary": 600,
                "Zandvoort": 700,
                "Azerbaijan": 2200,  # Baku 有超長直線
                "Saudi Arabia": 1000,
                "Jeddah": 1000,
                "Monza": 1100,
                "Spa": 850,
                "Silverstone": 800,
                "Austria": 750,
                "Canada": 900,
                "Miami": 850,
                "Las Vegas": 1800,
                "Qatar": 1000,
                "Abu Dhabi": 1200,
                "Bahrain": 1100,
                "China": 1200,
                "Australia": 850,
                "Japan": 1000,
                "United States": 1000,
                "Mexico": 900,
                "Brazil": 950,
                "Italy": 1100,  # Monza 別名
                "Great Britain": 800,  # Silverstone 別名
                "Netherlands": 700,  # Zandvoort 別名
                "Belgium": 850,  # Spa 別名
                "Spain": 1050,
                "Emilia Romagna": 800,  # Imola
            }
            
            # ⭐ 硬編碼賽道加速段起點距離（絕對位置，單位：米）
            # 使用方法：
            # 1. 在 GUI 速度圖中找到主直線段的起點（速度開始上升的位置）
            # 2. 記錄該位置的距離值（綠色虛線標註）
            # 3. 填入下方字典，格式：賽道名稱: 起點距離（米）
            # 4. 如果沒有填入，系統會自動使用公式計算（可能不準確）
            TRACK_ACCELERATION_START_DISTANCE = {
                # 格式範例：
                # "China": 3096,        # 中國站：從 3096m 開始加速（從 GUI 圖表測量）
                # "Azerbaijan": 3385,   # Baku：從 3385m 開始（超長直線）
                # "Japan": 3800,        # 日本站：從 3800m 開始
                
                # ⚠️ 請在此填入您測試過的賽道起點距離 ⚠️
                # 測試步驟：
                #   1. 執行 CLI 生成 JSON：python f1_analysis_modular_main.py -f 48 -y 2025 -r [賽道] -s R
                #   2. 在 GUI 中查看速度圖，找到加速段起點
                #   3. 填入距離值到下方
                #   4. 重新執行 CLI 驗證加速度是否正確
                
                # 已測試賽道（填入實際值）：
                "China": 3544,           #260km/h算起
                "Azerbaijan": 683,      # 待填入
                 "Japan": 5432,          #由 5650m->529m #230km/h算起
                
                # 未測試賽道（暫時空白）：
                 "Monaco": 200, #110km/h算起
                 "Singapore": 3447,
                 "Hungary": 0,
                 "Zandvoort": 3840,#由 3840m->100m 
                 "Saudi Arabia": 5584, #由 5584m->220m #170km/h算起
                 "Monza": 4216,
                 "Spa": 4997, #由 5584m->403m #202km/h算起
                 "Silverstone": 1288,
                 "Austria": 4857,  #由 4857m->160m #230km/h算起
                 "Canada": 2725,
                 "Miami": 3600, #164km/h算起
                 "Las Vegas": 5190,
                 "Qatar": 5076,
                 "Abu Dhabi": 1452,
                 "Bahrain": 4850, #由 5650m->510m #115km/h算起 
                 "Australia": 4807,
                 "United States": 3589,
                 "Mexico": 0,
                 "Brazil": 823,
                 "Spain": 4333, #由4333m到589m
                 "Emilia Romagna": 3600, #115km/h算起
            }
            
            # 獲取當前賽道的直線長度（預設 800m）
            track_straight_length = TRACK_STRAIGHT_LENGTHS.get(race_name, 800) if race_name else 800
            
            # ✅ 計算搜索起點：優先使用硬編碼起點，沒有則用公式計算
            max_speed_distance = distances[max_speed_idx] if max_speed_idx in distances.index else distance_end
            
            # ⭐ 新邏輯：優先使用硬編碼的加速段起點
            if race_name and race_name in TRACK_ACCELERATION_START_DISTANCE:
                # 使用硬編碼起點（用戶手動測量的準確值）
                calculated_start = TRACK_ACCELERATION_START_DISTANCE[race_name]
                start_source = "硬編碼"
                print(f"      ✅ 使用硬編碼起點: {calculated_start:.1f}m")
            else:
                # 回退到公式計算（可能不準確）
                calculated_start = max_speed_distance - (track_straight_length - 100)
                start_source = "公式計算"
                print(f"      ⚠️  使用公式計算起點: {calculated_start:.1f}m")
                print(f"      💡 建議: 在 TRACK_ACCELERATION_START_DISTANCE 中添加 '{race_name}' 的硬編碼值")
            
            # 搜索範圍：從計算起點到最高速度點後 200m
            search_distance_start = calculated_start
            search_distance_end = max_speed_distance + 200
            
            print(f"      📍 加速段搜索範圍: {search_distance_start:.1f}m → {search_distance_end:.1f}m (來源: {start_source})")
            print(f"      🏁 最高速度位置: {max_speed_distance:.1f}m")
            
            # ⭐ 檢測是否跨越終點線（起點 > 最高速度位置，且差異 > 1000m）
            # 注意：如果數據已經合併了下一圈，距離會是連續的（例如：5650m → 6650m）
            crosses_finish_line = (search_distance_start > max_speed_distance and 
                                   search_distance_start - max_speed_distance > 1000)
            
            if crosses_finish_line:
                print(f"      🔄 檢測到跨越終點線！")
                print(f"      📋 數據已合併下一圈，距離為連續值")
            
            # 無論是否跨越終點線，都使用統一的範圍搜索（因為數據已合併）
            search_mask = (distances >= search_distance_start) & (distances <= search_distance_end)
            
            # 過濾出搜索範圍內的數據點
            search_indices = car_data[search_mask].index
            
            if len(search_indices) == 0:
                # 如果搜索範圍內沒有數據，回退到整個最速圈
                search_indices = car_data.index
            
            # 只在最高速度點之前搜索
            search_indices_before_max = [idx for idx in search_indices if idx <= max_speed_idx]
            
            speed_start_idx = None
            best_speed_diff = float('inf')
            
            # 優先找到最接近統一起始速度的點
            for idx in reversed(search_indices_before_max):
                if idx not in speeds.index:
                    continue
                speed = speeds[idx]
                if math.isnan(speed):
                    continue
                
                # 找到速度最接近目標起始速度的點（允許 ±10 km/h 容差）
                if speed <= target_speed_low + 10:
                    speed_diff = abs(speed - target_speed_low)
                    if speed_diff < best_speed_diff:
                        best_speed_diff = speed_diff
                        speed_start_idx = idx
                        # 如果找到非常接近的點（誤差 < 2 km/h），就使用它
                        if speed_diff < 2:
                            break
            
            # ✅ 強制全車手模式：如果找不到理想起點，使用搜索範圍內最高速度點之前的最小速度
            if speed_start_idx is None and len(search_indices_before_max) > 0:
                search_speeds_before_max = speeds.loc[speeds.index.intersection(search_indices_before_max)]
                if not search_speeds_before_max.empty:
                    speed_start_idx = search_speeds_before_max.idxmin()
                    actual_start_speed = search_speeds_before_max[speed_start_idx]
                    # 更新目標起始速度為實際值
                    target_speed_low = float(actual_start_speed)
            
            if speed_start_idx is None:
                return None
            
            # ✅ 尋找終點速度：從起始點向後找第一個 >= 目標終點速度的點
            # 搜索範圍：從起始點到最高速度點（在整個最速圈中）
            speed_end_idx = None
            for idx in car_data.index:
                if idx < speed_start_idx or idx > max_speed_idx:
                    continue
                
                if idx not in speeds.index:
                    continue
                    
                speed = speeds[idx]
                if math.isnan(speed):
                    continue
                
                # 找到第一個 >= 目標終點速度的點
                if speed >= target_speed_high:
                    speed_end_idx = idx
                    break

            # ✅ 強制全車手模式：如果找不到理想終點，使用最高速度點作為終點
            if speed_end_idx is None:
                speed_end_idx = max_speed_idx
                # 更新目標終點速度為實際最高速度
                target_speed_high = float(speeds[max_speed_idx])
            
            # 獲取實際速度值
            actual_speed_start = speeds[speed_start_idx]
            actual_speed_end = speeds[speed_end_idx]

            # 計算時間差
            time_start = car_data.loc[speed_start_idx, "Time"]
            time_end = car_data.loc[speed_end_idx, "Time"]

            if hasattr(time_start, "total_seconds"):
                time_start_sec = time_start.total_seconds()
            else:
                time_start_sec = float(time_start)

            if hasattr(time_end, "total_seconds"):
                time_end_sec = time_end.total_seconds()
            else:
                time_end_sec = float(time_end)

            time_diff = time_end_sec - time_start_sec

            # ✅ 取消時間差上限限制：強制全車手模式，無論加速需要多長時間都接受
            if time_diff <= 0:
                return None

            # 計算距離差
            distance_diff = None
            if "Distance" in car_data.columns:
                try:
                    dist_start = distances[speed_start_idx]
                    dist_end = distances[speed_end_idx]
                    distance_diff = float(dist_end) - float(dist_start)
                except (KeyError, TypeError, ValueError):
                    distance_diff = None

            # 計算平均加速度（使用統一速度範圍）
            velocity_change = (target_speed_high - target_speed_low) / 3.6  # 轉換為 m/s
            avg_acceleration = velocity_change / time_diff

            return {
                "time_seconds": round(time_diff, 3),
                "distance_meters": round(distance_diff, 2) if distance_diff else None,
                "avg_acceleration_ms2": round(avg_acceleration, 2),
                "speed_start_kmh": round(target_speed_low, 1),  # ✅ 使用統一起始速度
                "speed_end_kmh": round(target_speed_high, 1),    # ✅ 使用統一終點速度
                "actual_speed_start_kmh": round(actual_speed_start, 1),  # 實際測量到的起始速度
                "actual_speed_end_kmh": round(actual_speed_end, 1),      # 實際測量到的終點速度
                "speed_start_index": int(speed_start_idx),
                "speed_end_index": int(speed_end_idx),
                "measurement_position_start": round(distance_start, 1),
                "measurement_position_end": round(distance_end, 1)
            }

        except Exception as e:
            print(f"[WARNING] 計算加速性能失敗: {e}")
            return None

    def _compute_driver_record(self, driver_code: str) -> Optional[DriverSpeedRecord]:
        """計算車手的速度記錄（基於最速圈的最佳直線段）"""
        driver_laps = self._pick_driver_laps(driver_code)
        if driver_laps is None or getattr(driver_laps, "empty", False):
            return None

        # ✅ 步驟 1: 找到最速圈
        fastest_lap = self._find_fastest_lap(driver_laps)
        if fastest_lap is None:
            return None

        lap_number = self._extract_lap_number(fastest_lap)
        if lap_number is None:
            return None

        # ✅ 步驟 2: 獲取最速圈的遙測數據
        car_data = self._extract_car_data(fastest_lap)
        if car_data is None or "Speed" not in car_data.columns:
            return None

        # ✅ 步驟 3: 識別所有直線段
        straight_segments = self._identify_straight_line_segments(car_data)
        if not straight_segments:
            return None

        # ✅ 步驟 4: 找到尾速最高的直線段
        best_segment = max(straight_segments, key=lambda s: s["max_speed"])

        # ✅ 步驟 5: 在該直線段內計算加速性能
        acceleration_data = self._calculate_acceleration_in_segment(car_data, best_segment)

        # ✅ 步驟 6: 獲取該直線段尾速點的其他數據
        max_speed_idx = best_segment["max_speed_idx"]
        max_speed = best_segment["max_speed"]

        distance_m = self._safe_float(car_data, max_speed_idx, "Distance")
        throttle = self._safe_float(car_data, max_speed_idx, "Throttle")
        drs = self._safe_int(car_data, max_speed_idx, "DRS")
        session_time = self._format_time(car_data, max_speed_idx, "Time")

        # ✅ 創建記錄
        record = DriverSpeedRecord(
            driver=driver_code,
            driver_number=self._lookup_driver_number(driver_code),
            team=self._lookup_driver_team(driver_code),
            full_name=self._lookup_driver_name(driver_code),
            max_speed_kmh=max_speed,
            lap_number=lap_number,
            distance_m=distance_m,
            session_time=session_time,
            throttle=throttle,
            drs=drs,
            acceleration_100_300=acceleration_data,
        )

        return record
    
    def _compute_driver_record_with_position(
        self, 
        driver_code: str, 
        reference_segment: Dict[str, Any]
    ) -> Optional[DriverSpeedRecord]:
        """
        計算車手的速度記錄（基於位置標準化）
        
        Args:
            driver_code: 車手代碼
            reference_segment: 參考直線段位置信息
        """
        driver_laps = self._pick_driver_laps(driver_code)
        if driver_laps is None or getattr(driver_laps, "empty", False):
            return None

        # 找到最速圈
        fastest_lap = self._find_fastest_lap(driver_laps)
        if fastest_lap is None:
            return None

        lap_number = self._extract_lap_number(fastest_lap)
        if lap_number is None:
            return None

        # 獲取最速圈的遙測數據
        car_data = self._extract_car_data(fastest_lap)
        if car_data is None or "Speed" not in car_data.columns:
            return None
        
        # ⭐ 嘗試獲取下一圈的數據（用於處理跨越終點線的情況）
        next_lap_data = self._extract_next_lap_data(driver_laps, lap_number)
        if next_lap_data is not None:
            # 合併當前圈和下一圈的前段數據（0-1000m）
            car_data = self._merge_lap_data_for_finish_line_crossing(car_data, next_lap_data)

        # 在指定位置範圍內找最高速度點（使用擴展範圍 ±200m）
        distance_start = reference_segment["segment_distance_start"]
        distance_end = reference_segment["segment_distance_end"]
        
        speed_result = self._find_speed_in_position_range(
            car_data,
            distance_start,
            distance_end,
            position_tolerance=200.0  # ✅ 擴展範圍 ±200m
        )
        
        if speed_result is None:
            print(f"[WARNING] {driver_code}: 無法在擴展位置範圍內找到速度數據")
            return None
        
        max_speed_idx = speed_result["max_speed_idx"]
        max_speed = speed_result["max_speed"]
        
        # ✅ 提取位置標註信息
        in_core_range = speed_result.get("in_core_range", True)
        in_extended_range = speed_result.get("in_extended_range", False)
        measured_distance = speed_result.get("distance")
        
        # 計算加速性能（在同一位置範圍內，使用統一速度範圍）
        acceleration_data = None
        if speed_result["can_calculate_acceleration"]:
            # ⚠️ DEPRECATED 調用：此函數使用舊邏輯（統一速度範圍）
            # 保留僅用於計算 100-300 km/h 固定速度範圍的加速性能
            acceleration_data = self._calculate_acceleration_in_position_range(
                car_data,
                max_speed_idx,
                distance_start,
                distance_end,
                speed_result["range_indices"],
                start_speed_threshold=speed_result.get("start_speed_threshold"),
                start_speed_idx=speed_result.get("start_speed_idx"),
                unified_start_speed=None,  # ❌ 已移除統一速度範圍
                unified_end_speed=None,    # ❌ 已移除統一速度範圍
                race_name=reference_segment.get("race_name")
            )
        
        # ⭐ 計算基於硬編碼起點的賽道段加速性能（改進版 v3）
        # 核心邏輯：從硬編碼起點開始，直到油門 <= 5% 之前的所有點
        segment_acceleration_data = self._calculate_segment_acceleration_improved(
            car_data=car_data,
            hardcoded_start_distance=distance_start,  # 使用參考起點作為硬編碼起點
            track_name=reference_segment.get("race_name")  # 賽道名稱（用於日誌）
        )
        
        # ✅ 使用加速終點距離作為顯示距離（專注於直線段分析）
        # 優先使用 segment_acceleration_data 的終點距離，回退到最高速度點距離
        if segment_acceleration_data and "actual_distance_end" in segment_acceleration_data:
            distance_m = segment_acceleration_data["actual_distance_end"]
        else:
            # 回退方案：使用全圈最高速度點的距離
            distance_m = self._safe_float(car_data, max_speed_idx, "Distance")
        
        # 獲取其他數據
        throttle = self._safe_float(car_data, max_speed_idx, "Throttle")
        drs = self._safe_int(car_data, max_speed_idx, "DRS")
        session_time = self._format_time(car_data, max_speed_idx, "Time")

        # ✅ 生成測量備註
        measurement_notes = None
        if in_extended_range:
            core_diff = None
            if measured_distance < distance_start:
                core_diff = f"{distance_start - measured_distance:.1f}m before core"
            elif measured_distance > distance_end:
                core_diff = f"{measured_distance - distance_end:.1f}m after core"
            
            measurement_notes = f"Extended range measurement ({core_diff})"

        # 創建記錄
        record = DriverSpeedRecord(
            driver=driver_code,
            driver_number=self._lookup_driver_number(driver_code),
            team=self._lookup_driver_team(driver_code),
            full_name=self._lookup_driver_name(driver_code),
            max_speed_kmh=max_speed,
            lap_number=lap_number,
            distance_m=distance_m,
            session_time=session_time,
            throttle=throttle,
            drs=drs,
            acceleration_100_300=acceleration_data,
            segment_acceleration=segment_acceleration_data,  # ⭐ 新增：賽道段加速性能
            in_core_range=in_core_range,  # ✅ 新增
            measurement_notes=measurement_notes,  # ✅ 新增
        )

        return record

    def _recompute_driver_record_with_unified_endpoint(
        self,
        temp_record: DriverSpeedRecord,
        reference_segment: Dict[str, Any],
        unified_end_speed_kmh: float
    ) -> Optional[DriverSpeedRecord]:
        """
        使用統一終點速度重新計算車手的加速數據（v3.3）
        
        保留原始的個人最高速度數據，同時添加到統一速度的加速時間
        
        Args:
            temp_record: 預掃描階段獲取的車手記錄（包含個人最高速度數據）
            reference_segment: 參考直線段信息
            unified_end_speed_kmh: 統一的終點速度（km/h）
            
        Returns:
            更新後的車手記錄，失敗時返回 None
        """
        try:
            # 獲取車手的最快單圈遙測數據
            driver_laps = self._pick_driver_laps(temp_record.driver)
            if driver_laps is None or getattr(driver_laps, "empty", False):
                return temp_record  # 無法重新計算，返回原記錄
            
            fastest_lap = self._find_fastest_lap(driver_laps)
            if fastest_lap is None:
                return temp_record
            
            car_data = self._extract_car_data(fastest_lap)
            if car_data is None or "Speed" not in car_data.columns:
                return temp_record
            
            # 保存個人最高速度數據
            personal_max_speed_data = temp_record.segment_acceleration.copy() if temp_record.segment_acceleration else {}
            
            # 計算到統一速度的加速時間
            distance_start = reference_segment.get("segment_distance_start")
            unified_accel_data = self._calculate_segment_acceleration_to_target_speed(
                car_data=car_data,
                hardcoded_start_distance=distance_start,
                target_end_speed_kmh=unified_end_speed_kmh,
                track_name=reference_segment.get("race_name"),
                debug=False
            )
            
            if unified_accel_data is None:
                # 無法計算到統一速度，保留原數據
                return temp_record
            
            # ⭐ v3.3 修正：處理個人最高速度數據
            # 如果預掃描階段有個人數據，使用之；否則使用統一速度數據作為個人極限
            personal_time = personal_max_speed_data.get("time_seconds")
            personal_distance = personal_max_speed_data.get("distance_meters")
            personal_max_speed = personal_max_speed_data.get("end_speed_kmh")
            
            if personal_time is None:
                # 預掃描時找不到個人最高速度（油門一直很低），使用統一速度作為極限
                personal_time = unified_accel_data["time_seconds"]
                personal_distance = unified_accel_data["distance_meters"]
                personal_max_speed = unified_accel_data["end_speed_kmh"]
            
            # ✅ v3.4 修正賦值邏輯（2025-10-19）
            # 問題：之前 time_seconds 和 max_speed_time_seconds 的賦值反轉了
            # 正確邏輯：
            #   - time_seconds（導出為 segment_accel_time_seconds）= 到個人最高速度的時間（較長）
            #   - max_speed_time_seconds = 到統一終點速度的時間（較短）
            # 原因：
            #   - personal_max_speed_data 來自預掃描的 segment_acceleration，使用 _calculate_segment_acceleration_improved
            #   - _calculate_segment_acceleration_improved 計算到油門降低前的最高速度點（個人最高速度）
            #   - unified_accel_data 使用 _calculate_segment_acceleration_to_target_speed 計算到統一速度
            #   - 所以 personal_time > unified_time
            merged_segment_data = {
                # ✅ 修正：個人最高速度的加速數據（時間較長，用於主要排序）
                "time_seconds": personal_time,  # ← 到個人最高速度（較長）
                "distance_meters": personal_distance,
                "avg_acceleration_ms2": unified_accel_data["avg_acceleration_ms2"],  # 使用統一數據的加速度
                "start_speed_kmh": unified_accel_data["start_speed_kmh"],
                "end_speed_kmh": personal_max_speed,  # ← 個人最高速度
                "speed_gain_kmh": personal_max_speed - unified_accel_data["start_speed_kmh"],
                
                # ✅ 修正：統一終點速度數據（時間較短，用於公平比較）
                "max_speed_time_seconds": unified_accel_data["time_seconds"],  # ← 到統一速度（較短）
                "max_speed_distance_meters": unified_accel_data["distance_meters"],
                "unified_end_speed_kmh": unified_end_speed_kmh,  # 統一終點速度
                "personal_max_speed_kmh": personal_max_speed,  # 個人最高速度
            }
            
            # 創建新的記錄
            updated_record = DriverSpeedRecord(
                driver=temp_record.driver,
                driver_number=temp_record.driver_number,
                team=temp_record.team,
                full_name=temp_record.full_name,
                max_speed_kmh=temp_record.max_speed_kmh,
                lap_number=temp_record.lap_number,
                distance_m=temp_record.distance_m,
                session_time=temp_record.session_time,
                throttle=temp_record.throttle,
                drs=temp_record.drs,
                acceleration_100_300=temp_record.acceleration_100_300,
                segment_acceleration=merged_segment_data,  # ⭐ 合併後的數據
                in_core_range=temp_record.in_core_range,
                measurement_notes=temp_record.measurement_notes,
            )
            
            return updated_record
            
        except Exception as e:
            print(f"[WARNING] 重新計算 {temp_record.driver} 的加速數據失敗: {e}")
            return temp_record  # 失敗時返回原記錄

    def _pick_driver_laps(self, driver_code: str) -> Any:
        laps = getattr(self.data_loader, "laps", None)
        if laps is None:
            return None
        if hasattr(laps, "pick_driver"):
            return laps.pick_driver(driver_code)
        return None

    def _iter_lap_rows(self, driver_laps: Any) -> Iterable[Tuple[Any, Any]]:
        if hasattr(driver_laps, "iterlaps"):
            yield from driver_laps.iterlaps()
        elif hasattr(driver_laps, "iterrows"):
            yield from driver_laps.iterrows()
        elif isinstance(driver_laps, list):
            for idx, lap in enumerate(driver_laps):
                yield idx, lap
        else:
            return []

    def _extract_lap_number(self, lap: Any) -> Optional[int]:
        for attr in ("LapNumber", "lap_number"):
            if hasattr(lap, attr):
                value = getattr(lap, attr)
                if value is not None:
                    try:
                        # ✅ 修正 FutureWarning: 檢查是否為 Series 並使用 .iloc[0]
                        if isinstance(value, pd.Series):
                            return int(value.iloc[0])
                        else:
                            return int(value)
                    except (TypeError, ValueError, IndexError):
                        return None
        if isinstance(lap, pd.Series) and "LapNumber" in lap:
            try:
                # ✅ 修正 FutureWarning: 使用 .iloc[0] 而不是直接 int()
                return int(lap["LapNumber"].iloc[0]) if isinstance(lap["LapNumber"], pd.Series) else int(lap["LapNumber"])
            except (TypeError, ValueError, IndexError):
                return None
        return None

    def _extract_car_data(self, lap: Any) -> Optional[pd.DataFrame]:
        get_car_data = getattr(lap, "get_car_data", None)
        if not callable(get_car_data):
            return None

        try:
            car_data = get_car_data()
            if car_data is None:
                return None
            if hasattr(car_data, "add_distance"):
                try:
                    car_data = car_data.add_distance()
                except Exception:
                    pass
            return self._to_dataframe(car_data)
        except Exception:
            return None

    def _extract_next_lap_data(self, driver_laps: Any, current_lap_number: int) -> Optional[pd.DataFrame]:
        """獲取下一圈的遙測數據（用於處理跨越終點線的情況）"""
        try:
            next_lap_number = current_lap_number + 1
            
            # 嘗試找到下一圈
            if hasattr(driver_laps, 'iloc'):
                # driver_laps 是 DataFrame
                next_lap_mask = driver_laps["LapNumber"] == next_lap_number
                if next_lap_mask.any():
                    next_lap = driver_laps[next_lap_mask].iloc[0]
                    return self._extract_car_data(next_lap)
            elif hasattr(driver_laps, 'pick_lap'):
                # driver_laps 是 Laps 對象
                next_lap = driver_laps.pick_lap(next_lap_number)
                if next_lap is not None:
                    return self._extract_car_data(next_lap)
        except Exception as e:
            print(f"      ⚠️  無法獲取下一圈數據: {e}")
        
        return None

    def _merge_lap_data_for_finish_line_crossing(
        self, 
        current_lap: pd.DataFrame, 
        next_lap: pd.DataFrame,
        next_lap_distance_threshold: float = 1000.0
    ) -> pd.DataFrame:
        """
        合併當前圈和下一圈的數據（用於處理跨越終點線的情況）
        
        Args:
            current_lap: 當前圈的遙測數據
            next_lap: 下一圈的遙測數據
            next_lap_distance_threshold: 下一圈要保留的最大距離（預設 1000m）
        
        Returns:
            合併後的數據（當前圈 + 下一圈前段）
        """
        if next_lap is None or "Distance" not in next_lap.columns:
            return current_lap
        
        try:
            # 只保留下一圈的前段數據（0-1000m）
            next_lap_front = next_lap[next_lap["Distance"] <= next_lap_distance_threshold].copy()
            
            if next_lap_front.empty:
                return current_lap
            
            # 調整下一圈的距離（加上賽道總長度，使其連續）
            # 例如：當前圈最大距離 5650m，下一圈 0-1000m → 調整為 5650-6650m
            current_lap_max_distance = current_lap["Distance"].max()
            next_lap_front["Distance"] = next_lap_front["Distance"] + current_lap_max_distance
            
            # 合併數據
            merged_data = pd.concat([current_lap, next_lap_front], ignore_index=True)
            
            print(f"      ✅ 已合併下一圈數據: {len(next_lap_front)} 個點 (0-{next_lap_distance_threshold}m)")
            
            return merged_data
        except Exception as e:
            print(f"      ⚠️  合併下一圈數據失敗: {e}")
            return current_lap

    def _to_dataframe(self, telemetry: Any) -> Optional[pd.DataFrame]:
        if telemetry is None:
            return None
        if isinstance(telemetry, pd.DataFrame):
            return telemetry
        if hasattr(telemetry, "to_pandas"):
            return telemetry.to_pandas()
        if hasattr(telemetry, "data"):
            try:
                return pd.DataFrame(telemetry.data)
            except Exception:
                pass
        try:
            return pd.DataFrame(telemetry)
        except Exception:
            return None



    # Metadata lookups -----------------------------------------------

    def _lookup_driver_number(self, driver_code: str) -> Optional[int]:
        row = self._get_driver_row(driver_code)
        if row is not None and "DriverNumber" in row:
            value = row["DriverNumber"]
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _lookup_driver_team(self, driver_code: str) -> Optional[str]:
        row = self._get_driver_row(driver_code)
        if row is not None:
            for key in ("TeamName", "Team", "Constructor", "team_reconciled"):
                if key in row and pd.notna(row[key]):
                    return str(row[key])
        sync_data = self._get_sync_driver_data(driver_code)
        if sync_data:
            return sync_data.get("team_reconciled") or sync_data.get("team_fastf1") or sync_data.get("team_openf1")
        return None

    def _lookup_driver_name(self, driver_code: str) -> Optional[str]:
        row = self._get_driver_row(driver_code)
        if row is not None:
            for key in ("FullName", "Driver", "Name"):
                if key in row and pd.notna(row[key]):
                    return str(row[key])
        sync_data = self._get_sync_driver_data(driver_code)
        if sync_data:
            return sync_data.get("name")
        return None

    def _get_driver_row(self, driver_code: str) -> Optional[pd.Series]:
        results = getattr(self.data_loader, "results", None)
        if isinstance(results, pd.DataFrame) and not results.empty:
            matches = results[results["Abbreviation"] == driver_code]
            if not matches.empty:
                return matches.iloc[0]
        return None

    def _get_sync_driver_data(self, driver_code: str) -> Optional[Dict[str, Any]]:
        loaded = getattr(self.data_loader, "loaded_data", {}) or {}
        sync_map = loaded.get("synchronized_driver_data", {})
        if isinstance(sync_map, dict):
            entry = sync_map.get(driver_code)
            if isinstance(entry, dict):
                return entry.get("reconciled_data") or entry
        return None

    # Utility helpers -------------------------------------------------

    def _safe_float(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[float]:
        if column in df.columns:
            value = df.loc[idx, column]
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return None

    def _safe_int(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[int]:
        if column in df.columns:
            value = df.loc[idx, column]
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _format_time(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[str]:
        if column not in df.columns:
            return None
        value = df.loc[idx, column]
        if pd.isna(value):
            return None
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        if isinstance(value, pd.Timedelta):
            return self._timedelta_to_string(value)
        return str(value)

    def _timedelta_to_string(self, td: pd.Timedelta) -> str:
        total_seconds = td.total_seconds()
        return f"{total_seconds:.3f}s"

    # Summary & chart -------------------------------------------------

    def _build_summary(self, records: List[DriverSpeedRecord]) -> Dict[str, Any]:
        speeds = [rec.max_speed_kmh for rec in records]
        highest = max(records, key=lambda rec: rec.max_speed_kmh)
        summary = {
            "fastest_driver": highest.driver,
            "fastest_driver_number": highest.driver_number,
            "fastest_speed_kmh": round(highest.max_speed_kmh, 3),
            "fastest_lap": highest.lap_number,
            "drivers_analysed": len(records),
            "average_speed_kmh": round(float(sum(speeds) / len(speeds)), 3),
            "max_minus_min_delta_kmh": round(float(max(speeds) - min(speeds)), 3),
        }
        if len(speeds) > 1:
            sorted_speeds = sorted(speeds)
            median = sorted_speeds[len(sorted_speeds) // 2]
            summary["median_speed_kmh"] = round(float(median), 3)
        
        # ✅ 新增：從最快圈提取整體賽道速度統計（用於賽道分類）
        track_speed_stats = self._calculate_track_speed_statistics(records)
        if track_speed_stats:
            summary["track_speed_statistics"] = track_speed_stats
            
        # 添加加速性能摘要
        acceleration_summary = self._build_acceleration_summary(records)
        if acceleration_summary:
            summary["acceleration_performance"] = acceleration_summary
            
        return summary

    def _calculate_track_speed_statistics(self, records: List[DriverSpeedRecord]) -> Optional[Dict[str, Any]]:
        """
        從最快圈遙測數據計算整體賽道速度統計（用於賽道分類建模）
        
        新增功能 (2025-10-31): 支援賽道特徵提取
        - avg_speed_kmh: 全圈平均速度
        - min_speed_kmh: 全圈最低速度（彎道最慢點）
        - speed_std_kmh: 速度標準差（反映賽道速度變化）
        """
        if not records:
            return None
        
        try:
            # 找出最快車手的最快圈
            fastest_record = max(records, key=lambda rec: rec.max_speed_kmh)
            driver_code = fastest_record.driver
            lap_number = fastest_record.lap_number
            
            # 獲取該圈的完整遙測數據
            driver_laps = self._pick_driver_laps(driver_code)
            if driver_laps is None or getattr(driver_laps, "empty", False):
                return None
            
            # 找到對應的圈
            target_lap = driver_laps[driver_laps['LapNumber'] == lap_number]
            if target_lap.empty:
                return None
            
            fastest_lap = target_lap.iloc[0]
            car_data = self._extract_car_data(fastest_lap)
            
            if car_data is None or "Speed" not in car_data.columns:
                return None
            
            # 提取速度數據並移除 NaN
            speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
            speeds = speeds.dropna()
            
            if len(speeds) == 0:
                return None
            
            # 計算統計值
            import numpy as np
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

            return {
                "avg_speed_kmh": round(float(speeds.mean()), 3),
                "min_speed_kmh": round(float(speeds.min()), 3),
                "max_speed_kmh": round(float(speeds.max()), 3),  # 與 fastest_speed_kmh 應該一致
                "speed_std_kmh": round(float(speeds.std()), 3),
                "reference_driver": driver_code,
                "reference_lap": int(lap_number),
                "data_points": len(speeds)
            }
            
        except Exception as e:
            print(f"[WARNING] 計算賽道速度統計失敗: {e}")
            return None

    def _build_acceleration_summary(self, records: List[DriverSpeedRecord]) -> Optional[Dict[str, Any]]:
        """構建加速性能摘要"""
        acceleration_records = [rec for rec in records if rec.acceleration_100_300 is not None]
        
        if not acceleration_records:
            return None
            
        acceleration_times = [rec.acceleration_100_300["time_seconds"] for rec in acceleration_records]
        
        # 找到最快加速的車手
        fastest_acceleration = min(acceleration_records, key=lambda rec: rec.acceleration_100_300["time_seconds"])
        
        return {
            "fastest_acceleration_driver": fastest_acceleration.driver,
            "fastest_acceleration_time": fastest_acceleration.acceleration_100_300["time_seconds"],
            "drivers_with_acceleration_data": len(acceleration_records),
            "average_acceleration_time": round(sum(acceleration_times) / len(acceleration_times), 3),
            "best_worst_delta": round(max(acceleration_times) - min(acceleration_times), 3)
        }

    def _build_chart_data(self, records: List[DriverSpeedRecord]) -> Dict[str, Any]:
        speed_chart = {
            "type": "bar",
            "title": "最高速度",
            "x": [rec.driver for rec in records],
            "values": [round(float(rec.max_speed_kmh), 3) for rec in records],
            "unit": "km/h",
            "highlight": records[0].driver if records else None,
        }
        
        # 添加加速性能圖表數據
        acceleration_records = [rec for rec in records if rec.acceleration_100_300 is not None]
        acceleration_chart = None
        
        if acceleration_records:
            # 按加速時間排序（越小越好）
            acceleration_records.sort(key=lambda rec: rec.acceleration_100_300["time_seconds"])
            
            acceleration_chart = {
                "type": "horizontal_bar",
                "title": "加速性能 (100-300 km/h)",
                "y": [rec.driver for rec in acceleration_records],
                "values": [rec.acceleration_100_300["time_seconds"] for rec in acceleration_records],
                "unit": "秒",
                "highlight": acceleration_records[0].driver if acceleration_records else None,
                "max_speeds": [rec.max_speed_kmh for rec in acceleration_records]  # 用於在圖表右側顯示最高速度
            }
        
        chart_data = {
            "speed_chart": speed_chart
        }
        
        if acceleration_chart:
            chart_data["acceleration_chart"] = acceleration_chart
            
        return chart_data

    def _build_metadata(self, *, total_drivers: Optional[int] = None) -> Dict[str, Any]:
        return {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "analysis_type": "enhanced_straight_line_speed_with_acceleration",
            "features": [
                "max_speed_analysis",
                "acceleration_100_300_analysis",
                "fastest_lap_based",
                "telemetry_based"
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "drivers_total": total_drivers,
        }


__all__ = [
    "AllDriversStraightLineSpeedAnalysis",
    "DriverSpeedRecord",
]
