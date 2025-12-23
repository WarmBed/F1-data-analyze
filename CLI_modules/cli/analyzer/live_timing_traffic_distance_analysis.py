#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Live Timing Traffic Analysis (Distance Threshold) - Function 127
===================================================================

以 Live Timing cache (PKL) 的 position + XY 路徑距離推導「前車距離(公尺)」，
並以距離門檻判定是否處於 traffic。

核心規則（距離門檻版）：
- traffic 判定：前車距離 <= traffic_distance_threshold_m (預設 50m)
- 單圈 traffic：traffic_ratio >= lap_traffic_ratio_threshold (預設 30%)
- SC/VSC 整圈排除：該圈任一時間點 TrackStatus 為 SC/VSC 時，整圈不計

數據來源：F1 Live Timing cache（由 F1APIDownloader 下載並快取）

作者: F1T Team
日期: 2025-12-23
"""

from __future__ import annotations

import os
import sys
import json
import math
from pathlib import Path
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_logger

# 延遲導入 F1APIDownloader 以避免 CLI 環境中 PyQt5 相關問題
F1APIDownloader = None


def _get_downloader():
    """延遲載入 F1APIDownloader"""
    global F1APIDownloader
    if F1APIDownloader is None:
        from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader as _F1APIDownloader

        F1APIDownloader = _F1APIDownloader
    return F1APIDownloader()


logger = get_logger("live_timing_traffic_distance_analysis", component="cli")

JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")


def _ensure_json_dir() -> Path:
    json_dir = Path(JSON_OUTPUT_DIR)
    json_dir.mkdir(parents=True, exist_ok=True)
    return json_dir


def _parse_timestamp_to_seconds(ts_str: str) -> float:
    """解析 Live Timing timestamp 字串 (HH:MM:SS(.mmm)) 為秒數。"""
    if not ts_str:
        return 0.0
    try:
        parts = ts_str.split(":")
        if len(parts) == 3:
            h, m, rest = parts
            if "." in rest:
                s_str, ms_str = rest.split(".", 1)
                return int(h) * 3600 + int(m) * 60 + int(s_str) + float("0." + ms_str)
            return int(h) * 3600 + int(m) * 60 + float(rest)
        if len(parts) == 2:
            m, rest = parts
            if "." in rest:
                s_str, ms_str = rest.split(".", 1)
                return int(m) * 60 + int(s_str) + float("0." + ms_str)
            return int(m) * 60 + float(rest)
    except Exception:
        return 0.0
    return 0.0


def _build_track_status_timeline(track_status_records: List[Dict[str, Any]]) -> List[Tuple[float, str]]:
    """回傳 [(time_seconds, status_code_str), ...] 已排序。"""
    timeline: List[Tuple[float, str]] = []
    for rec in track_status_records or []:
        if not isinstance(rec, dict):
            continue
        t = _parse_timestamp_to_seconds(rec.get("timestamp", ""))
        data = rec.get("data") or {}
        status = str(data.get("Status", "")).strip()
        if status:
            timeline.append((t, status))
    timeline.sort(key=lambda x: x[0])
    return timeline


def _build_lap_lookup_from_fastf1_cache(
    year: int,
    race: str,
    session: str,
) -> Dict[str, List[Tuple[float, float, int]]]:
    """
    從 FastF1 緩存的 _extended_timing_data 建立完整的圈數查詢表。
    
    返回: {driver_num: [(lap_start_time_s, lap_end_time_s, lap_num), ...]}
    """
    import pickle
    from pathlib import Path
    
    # 嘗試找到對應的緩存目錄
    cache_base = Path("cache") / str(year)
    if not cache_base.exists():
        return {}
    
    # 搜尋匹配的賽事目錄
    race_lower = race.lower().replace("_", " ").replace("-", " ")
    session_map = {"R": "Race", "Q": "Qualifying", "FP1": "Practice_1", "FP2": "Practice_2", "FP3": "Practice_3"}
    session_name = session_map.get(session, session)
    
    target_dir = None
    for subdir in cache_base.iterdir():
        if not subdir.is_dir():
            continue
        dir_name_lower = subdir.name.lower()
        if race_lower in dir_name_lower or race_lower.replace(" ", "_") in dir_name_lower:
            # 找到賽事目錄，現在找 session
            for sess_dir in subdir.iterdir():
                if sess_dir.is_dir() and session_name.lower() in sess_dir.name.lower():
                    target_dir = sess_dir
                    break
            if target_dir:
                break
    
    if not target_dir:
        print(f"  [LAP_LOOKUP] FastF1 cache not found for {year} {race} {session}")
        return {}
    
    # 載入 _extended_timing_data
    ext_timing_path = target_dir / "_extended_timing_data.ff1pkl"
    if not ext_timing_path.exists():
        print(f"  [LAP_LOOKUP] _extended_timing_data.ff1pkl not found")
        return {}
    
    try:
        with ext_timing_path.open("rb") as f:
            ext_data = pickle.load(f)
        
        # _extended_timing_data 結構: {'version': ..., 'data': (df0, df1, df2)}
        data_tuple = ext_data.get("data")
        if not data_tuple or not isinstance(data_tuple, tuple) or len(data_tuple) < 1:
            return {}
        
        df = data_tuple[0]  # 第一個 DataFrame 包含圈數資訊
        
        if not hasattr(df, 'columns'):
            return {}
        
        # 需要的欄位: Driver, Time, NumberOfLaps
        if 'Driver' not in df.columns or 'Time' not in df.columns or 'NumberOfLaps' not in df.columns:
            print(f"  [LAP_LOOKUP] Missing required columns")
            return {}
        
        # 建立查詢表
        # 重要：FastF1 和 Live Timing 的圈數編號有偏移！
        # - FastF1 Lap 1 = formation lap (暖胎圈)，結束於約 3592s
        # - Live Timing Lap 1 = 正式比賽第一圈，開始於約 3592s
        # - 因此：Live Timing Lap N 的時間範圍 = FastF1 Lap N+1 的時間範圍
        # 
        # 為了讓 lap_lookup 可以直接用於 Live Timing 的 race_time_seconds：
        # 我們把 FastF1 的 Lap 2 時間範圍對應到 lookup 的 Lap 1
        lap_lookup: Dict[str, List[Tuple[float, float, int]]] = {}
        
        for driver_num in df['Driver'].unique():
            driver_df = df[df['Driver'] == driver_num].copy()
            driver_df = driver_df.dropna(subset=['NumberOfLaps'])
            driver_df = driver_df.sort_values('Time')
            
            if len(driver_df) == 0:
                continue
            
            ranges: List[Tuple[float, float, int]] = []
            
            # 收集所有圈的結束時間（FastF1 編號）
            lap_end_times: Dict[int, float] = {}
            for _, row in driver_df.iterrows():
                ff1_lap_num = int(row['NumberOfLaps'])
                time_td = row['Time']
                if hasattr(time_td, 'total_seconds'):
                    time_s = time_td.total_seconds()
                else:
                    time_s = float(time_td)
                lap_end_times[ff1_lap_num] = time_s
            
            # 建立 Live Timing 圈數的時間範圍
            # Live Timing Lap 1 = FastF1 Lap 1 結束 → FastF1 Lap 2 結束
            # Live Timing Lap N = FastF1 Lap N 結束 → FastF1 Lap N+1 結束
            sorted_ff1_laps = sorted(lap_end_times.keys())
            max_ff1_lap = max(sorted_ff1_laps) if sorted_ff1_laps else 0
            
            for lt_lap_num in range(1, max_ff1_lap):  # Live Timing laps 1 to N-1
                ff1_lap_start_num = lt_lap_num       # FastF1 lap that ends at LT lap start
                ff1_lap_end_num = lt_lap_num + 1     # FastF1 lap that ends at LT lap end
                
                start_time = lap_end_times.get(ff1_lap_start_num)
                end_time = lap_end_times.get(ff1_lap_end_num)
                
                if start_time is not None and end_time is not None:
                    ranges.append((start_time, end_time, lt_lap_num))
            
            # 最後一圈延長 1 小時以捕獲比賽結束後的數據
            if ranges:
                last_lap = ranges[-1]
                ranges[-1] = (last_lap[0], last_lap[1] + 3600, last_lap[2])
            
            lap_lookup[str(driver_num)] = ranges
        
        total_drivers = len(lap_lookup)
        total_laps = sum(len(v) for v in lap_lookup.values())
        print(f"  [LAP_LOOKUP] Loaded {total_drivers} drivers, {total_laps} lap ranges from FastF1 cache")
        return lap_lookup
        
    except Exception as e:
        print(f"  [LAP_LOOKUP] Error loading FastF1 cache: {e}")
        return {}


def _get_lap_from_lookup(
    lap_lookup: Dict[str, List[Tuple[float, float, int]]],
    driver_num: str,
    time_s: float,
) -> Optional[int]:
    """根據時間查詢車手的圈數"""
    if not lap_lookup or driver_num not in lap_lookup:
        return None
    
    ranges = lap_lookup[driver_num]
    for start, end, lap_num in ranges:
        if start <= time_s < end:
            return lap_num
    
    # 如果超出範圍，返回最後一圈
    if ranges and time_s >= ranges[-1][0]:
        return ranges[-1][2]
    
    return None


def _get_track_status_at_time(timeline: List[Tuple[float, str]], t: float) -> str:
    """給定時間秒數，回傳該時間點最近的 TrackStatus（階梯函數）。"""
    if not timeline:
        return ""
    # 線性掃描已足夠（track_status 通常很少筆）
    current = timeline[0][1]
    for ts, status in timeline:
        if ts <= t:
            current = status
        else:
            break
    return current


def _estimate_meters_per_xy_unit(
    snapshots: List[Dict[str, Any]],
    *,
    max_snapshots: int = 8000,
    max_samples: int = 20000,
    max_dt_s: float = 2.0,
) -> Tuple[float, Dict[str, Any]]:
    """用 speed 與 dt 校準 XY 單位到「公尺」的換算比例。

    Live Timing cache 的 x/y 多半是「地圖座標」(類似像素/座標格)，不一定直接等於公尺。
    這裡用 (speed_mps * dt) / hypot(dx, dy) 的中位數估計 meters_per_xy_unit。
    """

    prev_by_driver: Dict[str, Tuple[float, float, float]] = {}
    ratios: List[float] = []
    used_snapshots = 0
    skipped = 0

    for snap in (snapshots or [])[:max_snapshots]:
        used_snapshots += 1
        t = float(snap.get("race_time_seconds") or 0.0)
        drivers: Dict[str, Any] = snap.get("drivers", {}) or {}
        if not drivers:
            continue

        for driver_num, d in drivers.items():
            if not isinstance(d, dict):
                continue

            x = d.get("x")
            y = d.get("y")
            speed = d.get("speed")
            if x is None or y is None or speed is None:
                skipped += 1
                continue

            try:
                x_f = float(x)
                y_f = float(y)
                speed_kmh = float(speed)
            except Exception:
                skipped += 1
                continue

            if speed_kmh <= 5.0 or speed_kmh > 450.0:
                skipped += 1
                continue

            prev = prev_by_driver.get(str(driver_num))
            prev_by_driver[str(driver_num)] = (x_f, y_f, t)
            if prev is None:
                continue

            px, py, pt = prev
            dt = t - pt
            if dt <= 0.0 or dt > max_dt_s:
                skipped += 1
                continue

            ds_xy = math.hypot(x_f - px, y_f - py)
            if ds_xy <= 1e-6 or ds_xy > 5000.0:
                skipped += 1
                continue

            ds_m = (speed_kmh / 3.6) * dt
            if ds_m <= 0.0:
                skipped += 1
                continue

            ratio = ds_m / ds_xy
            if 1e-4 <= ratio <= 10.0:
                ratios.append(ratio)
            else:
                skipped += 1

        if len(ratios) >= max_samples:
            break

    if not ratios:
        return 1.0, {
            "meters_per_xy_unit": 1.0,
            "ratio_samples": 0,
            "used_snapshots": used_snapshots,
            "skipped": skipped,
        }

    m_per_unit = float(median(ratios))
    return m_per_unit, {
        "meters_per_xy_unit": m_per_unit,
        "ratio_samples": len(ratios),
        "used_snapshots": used_snapshots,
        "skipped": skipped,
    }


def analyze_live_timing_traffic_distance(
    year: int,
    race: str,
    session: str = "R",
    traffic_distance_threshold_m: float = 50.0,
    lap_traffic_ratio_threshold: float = 0.3,
    exclude_track_status_codes: Optional[List[str]] = None,
    min_lap_time_s: float = 30.0,
    max_dt_s: float = 5.0,
) -> Dict[str, Any]:
    """主分析函數：回傳結果 dict（不直接寫檔）。"""

    exclude_set = set(exclude_track_status_codes or ["4", "6", "7"])  # 4=SC, 6=VSC, 7=VSC Ending

    print("\n" + "=" * 60)
    print("F127: Live Timing Traffic Analysis (Distance Threshold)")
    print("=" * 60)
    print(f"Year: {year}")
    print(f"Race: {race}")
    print(f"Session: {session}")
    print(f"Distance threshold (m): {traffic_distance_threshold_m}")
    print(f"Lap traffic ratio threshold: {lap_traffic_ratio_threshold}")
    print(f"Exclude TrackStatus codes: {sorted(exclude_set)}")
    print("=" * 60 + "\n")

    downloader = _get_downloader()

    print("[1/3] Loading Live Timing cache data...")
    cache_data = downloader.download_and_cache(year=year, race=race, session=session, force=False)
    if not cache_data:
        return {
            "success": False,
            "message": f"Failed to load Live Timing cache for {year} {race} {session}",
            "data": None,
        }

    snapshots: List[Dict[str, Any]] = cache_data.get("snapshots", []) or []
    if not snapshots:
        return {
            "success": False,
            "message": "No snapshots available in Live Timing cache",
            "data": None,
        }

    track_status_records = cache_data.get("track_status", []) or []
    status_timeline = _build_track_status_timeline(track_status_records)

    # driver_info 在 PKL 中通常存在，可提供顯示資訊
    driver_info = cache_data.get("driver_info", {}) or {}

    # 載入完整的圈數資訊（從 FastF1 _extended_timing_data）
    print("  Loading complete lap data from FastF1 cache...")
    lap_lookup = _build_lap_lookup_from_fastf1_cache(year, race, session)

    print("[2/3] Building distance model from XY...")

    # 先做一次 XY 單位→公尺的校準（避免把地圖座標當成公尺導致距離失真）
    meters_per_xy_unit, xy_scale_meta = _estimate_meters_per_xy_unit(
        snapshots,
        max_dt_s=min(2.0, max_dt_s),
    )
    print(
        f"  XY scale estimate: {meters_per_xy_unit:.6f} m/unit "
        f"(samples={xy_scale_meta.get('ratio_samples', 0)})"
    )

    # per-driver states
    class _State:
        __slots__ = (
            "prev_x",
            "prev_y",
            "prev_time",
            "prev_lap",
            "s_lap",
            "lap_point_count",
            "lap_distance_samples",
        )

        def __init__(self):
            self.prev_x: Optional[float] = None
            self.prev_y: Optional[float] = None
            self.prev_time: Optional[float] = None
            self.prev_lap: Optional[int] = None
            self.s_lap: float = 0.0
            self.lap_point_count: int = 0
            self.lap_distance_samples: List[float] = []

    states: Dict[str, _State] = {}

    # per-driver per-lap accumulation
    # keys are (driver_num, lap)
    lap_total_time: Dict[Tuple[str, int], float] = {}
    lap_traffic_time: Dict[Tuple[str, int], float] = {}
    lap_excluded: Dict[Tuple[str, int], bool] = {}

    track_length_est: Optional[float] = None

    def _get_state(driver_num: str) -> _State:
        st = states.get(driver_num)
        if st is None:
            st = _State()
            states[driver_num] = st
        return st

    def _safe_float(v: Any) -> Optional[float]:
        try:
            if v is None:
                return None
            return float(v)
        except Exception:
            return None

    def _safe_int(v: Any) -> Optional[int]:
        try:
            if v is None:
                return None
            return int(v)
        except Exception:
            return None

    # 逐快照更新
    # 注意：traffic_time 使用 (t_i -> t_{i+1}) 的 dt，歸屬於快照 i 的圈數
    for i in range(len(snapshots) - 1):
        snap = snapshots[i]
        snap_next = snapshots[i + 1]

        t = _safe_float(snap.get("race_time_seconds")) or 0.0
        t_next = _safe_float(snap_next.get("race_time_seconds")) or 0.0
        dt = t_next - t
        if dt <= 0 or dt > max_dt_s:
            continue

        drivers: Dict[str, Any] = snap.get("drivers", {}) or {}
        if not drivers:
            continue

        # 先更新各車手距離狀態，得到當前 s_lap
        s_lap_by_driver: Dict[str, float] = {}
        lap_by_driver: Dict[str, int] = {}
        in_pit_by_driver: Dict[str, bool] = {}
        position_by_driver: Dict[str, int] = {}

        for driver_num, d in drivers.items():
            if not isinstance(d, dict):
                continue

            x = _safe_float(d.get("x"))
            y = _safe_float(d.get("y"))
            
            # 優先使用 lap_lookup 的完整圈數資訊，fallback 到 snapshot 的 lap
            lap = _get_lap_from_lookup(lap_lookup, str(driver_num), t)
            if lap is None:
                lap = _safe_int(d.get("lap"))
            
            pos = _safe_int(d.get("position"))
            in_pit = bool(d.get("in_pit"))
            speed_kmh = _safe_float(d.get("speed"))

            if lap is None or lap <= 0:
                continue

            st = _get_state(str(driver_num))

            # lap change handling: record previous lap distance sample
            if st.prev_lap is not None and lap != st.prev_lap:
                if st.lap_point_count >= 50 and st.s_lap >= 1000:
                    st.lap_distance_samples.append(st.s_lap)
                    # 更新 track length 估計（足夠樣本後取中位數）
                    all_samples: List[float] = []
                    for sst in states.values():
                        all_samples.extend(sst.lap_distance_samples)
                    if len(all_samples) >= 10:
                        track_length_est = float(median(all_samples))

                st.s_lap = 0.0
                st.lap_point_count = 0

            # distance update
            if st.prev_x is not None and st.prev_y is not None and st.prev_time is not None:
                dt_prev = t - st.prev_time
                if dt_prev > 0 and x is not None and y is not None:
                    ds_xy = math.hypot(x - st.prev_x, y - st.prev_y)

                    # 把 XY delta 轉成公尺
                    ds_m = ds_xy * meters_per_xy_unit

                    # 基於速度的合理上限（用於偵測跳點；跳點不累積）
                    if speed_kmh is not None and 0.0 < speed_kmh <= 450.0:
                        expected_m = (speed_kmh / 3.6) * dt_prev
                        max_m = expected_m * 1.7 + 3.0
                        if ds_m > max_m:
                            ds_m = 0.0

                    if ds_m > 0.0:
                        st.s_lap += ds_m
                        st.lap_point_count += 1

            st.prev_x = x
            st.prev_y = y
            st.prev_time = t
            st.prev_lap = lap

            s_lap_by_driver[str(driver_num)] = st.s_lap
            lap_by_driver[str(driver_num)] = lap
            in_pit_by_driver[str(driver_num)] = in_pit
            if pos is not None and pos > 0:
                position_by_driver[str(driver_num)] = pos

        if track_length_est is None:
            # track length 尚未穩定估出前，先不做 traffic 判定
            continue

        # position -> driver map
        driver_by_position: Dict[int, str] = {}
        for drv, pos in position_by_driver.items():
            # 同名 position 取第一個即可
            if pos not in driver_by_position:
                driver_by_position[pos] = drv

        track_status = _get_track_status_at_time(status_timeline, t)
        is_excluded_segment = track_status in exclude_set

        # traffic 判定（以 position 的前車為準）
        for drv, pos in position_by_driver.items():
            lap = lap_by_driver.get(drv)
            if lap is None or lap <= 0:
                continue

            key = (drv, lap)

            if is_excluded_segment:
                lap_excluded[key] = True

            # pit 中不納入分母分子
            if in_pit_by_driver.get(drv, False):
                continue

            # 即使沒有前車，也要記錄圈數總時間（分母）
            # 這樣領先者的圈數也會被正確統計
            lap_total_time[key] = lap_total_time.get(key, 0.0) + dt

            ahead_drv = driver_by_position.get(pos - 1)
            if not ahead_drv:
                # 沒有前車（領先者），不累計 traffic_time，但圈數已記錄
                continue

            if in_pit_by_driver.get(ahead_drv, False):
                # 前車在 pit，不累計 traffic_time
                continue

            s_drv = s_lap_by_driver.get(drv)
            s_ahead = s_lap_by_driver.get(ahead_drv)
            if s_drv is None or s_ahead is None:
                continue

            lap_ahead = lap_by_driver.get(ahead_drv, lap)
            gap_m = (lap_ahead - lap) * track_length_est + (s_ahead - s_drv)

            # wrap 修正（位置/距離可能略有不一致）
            if gap_m < 0:
                gap_m += track_length_est

            if gap_m < 0 or gap_m > track_length_est * 2:
                continue

            if gap_m <= traffic_distance_threshold_m:
                lap_traffic_time[key] = lap_traffic_time.get(key, 0.0) + dt

    print("[3/3] Aggregating per-driver / per-lap traffic metrics...")

    # 建立 driver -> lap -> entry
    drivers_result: Dict[str, Any] = {}

    # 收集所有 driver/lap keys（以 total_time 為主）
    all_keys = set(lap_total_time.keys()) | set(lap_traffic_time.keys()) | set(lap_excluded.keys())

    # group by driver
    keys_by_driver: Dict[str, List[Tuple[str, int]]] = {}
    for drv, lap in all_keys:
        keys_by_driver.setdefault(drv, []).append((drv, lap))

    for drv, drv_keys in keys_by_driver.items():
        per_lap: List[Dict[str, Any]] = []
        analyzed_total = 0.0
        analyzed_traffic = 0.0
        laps_analyzed = 0
        laps_in_traffic = 0

        for _, lap in sorted(drv_keys, key=lambda x: x[1]):
            key = (drv, lap)
            total_t = float(lap_total_time.get(key, 0.0))
            traffic_t = float(lap_traffic_time.get(key, 0.0))
            excluded = bool(lap_excluded.get(key, False))

            ratio = (traffic_t / total_t) if total_t > 0 else 0.0
            is_valid_lap = (not excluded) and (total_t >= min_lap_time_s)

            if is_valid_lap:
                analyzed_total += total_t
                analyzed_traffic += traffic_t
                laps_analyzed += 1
                if ratio >= lap_traffic_ratio_threshold:
                    laps_in_traffic += 1

            per_lap.append(
                {
                    "lap": lap,
                    "total_time_s": round(total_t, 3),
                    "traffic_time_s": round(traffic_t, 3),
                    "traffic_ratio": round(ratio, 4),
                    "excluded_sc_vsc": excluded,
                    "included_in_summary": bool(is_valid_lap),
                    "lap_in_traffic": bool(is_valid_lap and ratio >= lap_traffic_ratio_threshold),
                }
            )

        time_ratio = (analyzed_traffic / analyzed_total) if analyzed_total > 0 else 0.0

        # driver display info
        info = driver_info.get(drv, {}) if isinstance(driver_info, dict) else {}
        drivers_result[drv] = {
            "driver_number": drv,
            "driver_tla": info.get("tla") or info.get("TLA") or "",
            "driver_name": info.get("name") or info.get("Name") or "",
            "team": info.get("team") or info.get("Team") or "",
            "laps_analyzed": laps_analyzed,
            "laps_in_traffic": laps_in_traffic,
            "time_in_traffic_ratio": round(time_ratio, 4),
            "per_lap": per_lap,
        }

    result = {
        "success": True,
        "metadata": {
            "year": year,
            "race": race,
            "session": session,
            "data_source": "F1 Live Timing cache (PKL)",
            "timestamp": datetime.now().isoformat(),
        },
        "parameters": {
            "traffic_distance_threshold_m": float(traffic_distance_threshold_m),
            "lap_traffic_ratio_threshold": float(lap_traffic_ratio_threshold),
            "exclude_track_status_codes": sorted(exclude_set),
            "min_lap_time_s": float(min_lap_time_s),
            "max_dt_s": float(max_dt_s),
        },
        "derived": {
            "track_length_est_m": round(float(track_length_est), 3) if track_length_est else None,
            "xy_scale": xy_scale_meta,
            "track_status_records": len(track_status_records),
        },
        "drivers": drivers_result,
    }

    return result


def generate_json_output(result: Dict[str, Any], year: int, race: str, session: str) -> str:
    json_dir = _ensure_json_dir()

    safe_race = str(race).replace(" ", "_")
    filename = f"live_timing_traffic_distance_{year}_{safe_race}_{session}.json"
    filepath = json_dir / filename

    json_result = {
        "function_id": 127,
        "function_name": "Live Timing Traffic Analysis (Distance Threshold)",
        "analysis_type": "live_timing_traffic_distance",
        "timestamp": datetime.now().isoformat(),
        "data": result,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)

        abs_filepath = filepath.absolute()
        print(f"\n[SUCCESS] JSON saved: {abs_filepath}")
        return str(abs_filepath)
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {type(e).__name__}: {e}")
        return ""


def run_live_timing_traffic_distance_analysis(
    year: int,
    race: str,
    session: str = "R",
    traffic_distance_threshold_m: float = 50.0,
    lap_traffic_ratio_threshold: float = 0.3,
    **kwargs,
) -> Dict[str, Any]:
    """FunctionMapper 入口：執行分析並輸出 JSON。"""

    print("[FUNCTION 127] Live Timing Traffic Analysis (Distance Threshold)")
    print(
        f"[PARAMS] Year={year}, Race={race}, Session={session}, "
        f"Distance={traffic_distance_threshold_m}m, LapRatio={lap_traffic_ratio_threshold}"
    )

    result = analyze_live_timing_traffic_distance(
        year=year,
        race=race,
        session=session,
        traffic_distance_threshold_m=traffic_distance_threshold_m,
        lap_traffic_ratio_threshold=lap_traffic_ratio_threshold,
    )

    if not result.get("success"):
        return {
            "success": False,
            "message": result.get("message", "Analysis failed"),
            "function_id": "127",
        }

    json_path = generate_json_output(result, year, race, session)

    # 摘要
    drivers = result.get("drivers", {}) or {}
    print("\n[SUMMARY] Traffic (distance) analysis")
    print(f"  Drivers: {len(drivers)}")
    track_len = (result.get("derived", {}) or {}).get("track_length_est_m")
    if track_len:
        print(f"  Track length estimate: {track_len} m")

    # 顯示前幾名 time_in_traffic_ratio
    top = []
    for drv, info in drivers.items():
        try:
            top.append((drv, float(info.get("time_in_traffic_ratio", 0.0)), int(info.get("laps_in_traffic", 0))))
        except Exception:
            continue
    top.sort(key=lambda x: x[1], reverse=True)

    for drv, ratio, laps_in_traf in top[:5]:
        print(f"  {drv}: time_in_traffic_ratio={ratio:.3f}, laps_in_traffic={laps_in_traf}")

    return {
        "success": True,
        "data": result,
        "json_path": json_path,
        "function_id": "127",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="F127: Live Timing Traffic Analysis (Distance Threshold)")
    parser.add_argument("-y", "--year", type=int, required=True, help="Year (2018+)")
    parser.add_argument("-r", "--race", type=str, required=True, help="Race name")
    parser.add_argument("-s", "--session", type=str, default="R", help="Session type (R/Q/FP1/FP2/FP3)")
    parser.add_argument("--distance", type=float, default=50.0, help="Traffic distance threshold (meters)")
    parser.add_argument("--lap-ratio", type=float, default=0.5, help="Lap traffic ratio threshold")

    args = parser.parse_args()

    run_live_timing_traffic_distance_analysis(
        year=args.year,
        race=args.race,
        session=args.session,
        traffic_distance_threshold_m=args.distance,
        lap_traffic_ratio_threshold=args.lap_ratio,
    )
