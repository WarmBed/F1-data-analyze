#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Live Timing Weather Analysis - Function 126
===============================================

使用 F1 官方 Live Timing API 的 WeatherData.jsonStream 獲取逐圈天氣數據。

數據來源：F1 Live Timing API
- https://livetiming.formula1.com/static/{year}/{race}/{session}/WeatherData.jsonStream

輸出內容：
- 每圈的氣溫 (air_temperature)
- 每圈的賽道溫度 (track_temperature)
- 每圈的降雨狀態 (rainfall)
- 每圈的濕度 (humidity)
- 每圈的氣壓 (pressure)
- 每圈的風速/風向 (wind_speed, wind_direction)

作者: F1T Team
日期: 2025-12-21
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

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

logger = get_logger("live_timing_weather_analysis", component="cli")

# 全域設定
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")


def _ensure_json_dir() -> Path:
    """確保 JSON 輸出目錄存在"""
    json_dir = Path(JSON_OUTPUT_DIR)
    json_dir.mkdir(parents=True, exist_ok=True)
    return json_dir


def analyze_live_timing_weather(
    year: int,
    race: str,
    session: str = "R"
) -> Dict[str, Any]:
    """
    分析 Live Timing 天氣數據
    
    Args:
        year: 年份 (2018+)
        race: 賽事名稱 (例如 "Japan", "Abu Dhabi")
        session: 會話類型 (R/Q/FP1/FP2/FP3)
    
    Returns:
        分析結果字典
    """
    print(f"\n{'='*60}")
    print(f"F126: Live Timing Weather Analysis")
    print(f"{'='*60}")
    print(f"Year: {year}")
    print(f"Race: {race}")
    print(f"Session: {session}")
    print(f"{'='*60}\n")
    
    # 初始化下載器（延遲載入）
    downloader = _get_downloader()
    
    # 下載數據
    print("[1/3] Downloading Live Timing data...")
    cache_data = downloader.download_and_cache(
        year=year,
        race=race,
        session=session,
        force=False
    )
    
    if not cache_data:
        return {
            "success": False,
            "message": f"Failed to download Live Timing data for {year} {race} {session}",
            "data": None
        }
    
    # 提取天氣數據 (PKL 結構使用 weather_data 鍵，是一個 list)
    print("[2/3] Extracting weather data...")
    weather_records = cache_data.get('weather_data', [])
    
    if not weather_records:
        return {
            "success": False,
            "message": "No weather data available in Live Timing stream",
            "data": None
        }
    
    print(f"[INFO] Found {len(weather_records)} weather records")
    
    # 取最新一筆天氣數據作為 latest_weather
    if isinstance(weather_records, list) and weather_records:
        latest_record = weather_records[-1]
        latest_weather = latest_record.get('data', {}) if isinstance(latest_record, dict) else {}
    else:
        latest_weather = {}
    
    # 處理快照數據
    snapshots = cache_data.get('snapshots', [])
    race_info = cache_data.get('race_info', {})
    
    # 構建逐圈天氣數據
    print("[3/3] Building lap-by-lap weather analysis...")
    lap_weather = _build_lap_weather_data(snapshots, weather_records, race_info)
    
    # 計算統計數據
    stats = _calculate_weather_stats(lap_weather)
    
    # ✅ 構建兼容 rain_analysis GUI 的結果格式
    result = {
        "success": True,
        "metadata": {
            "year": year,
            "race": race,
            "session": session,
            "total_laps": len(lap_weather),
            "data_source": "F1 Live Timing API",
            "timestamp": datetime.now().isoformat()
        },
        "lap_weather_data": lap_weather,  # ✅ GUI 期望的欄位名稱
        "summary": stats,                  # ✅ GUI 期望的欄位名稱
        "latest_weather": latest_weather   # 最新的天氣快照
    }
    
    return result


def _build_lap_weather_data(
    snapshots: List[Dict],
    weather_records: List[Dict],
    race_info: Dict
) -> Dict[str, Dict[str, Any]]:
    """
    從快照和天氣記錄構建逐圈天氣數據（兼容 rain_analysis GUI 格式）
    
    Args:
        snapshots: 時間序列快照 (包含 race_time_seconds 和 current_lap)
        weather_records: 天氣數據記錄列表 (每個記錄包含 timestamp 和 data)
        race_info: 賽事資訊
    
    Returns:
        逐圈天氣數據字典 {圈數字串: 天氣數據}
    """
    lap_weather = {}
    
    # 解析天氣記錄的時間戳為秒數
    def parse_timestamp(ts_str: str) -> float:
        """解析 HH:MM:SS.mmm 格式為秒數"""
        try:
            parts = ts_str.split(':')
            if len(parts) == 3:
                h, m, rest = parts
                s_parts = rest.split('.')
                s = float(s_parts[0])
                ms = float(s_parts[1]) / 1000 if len(s_parts) > 1 else 0
                return int(h) * 3600 + int(m) * 60 + s + ms
        except Exception:
            pass
        return 0.0
    
    # 建立時間排序的天氣記錄
    sorted_weather = sorted(
        weather_records,
        key=lambda r: parse_timestamp(r.get('timestamp', '00:00:00.000'))
    )
    
    # 如果快照為空，使用最新天氣數據構建單個記錄
    if not snapshots or not sorted_weather:
        if sorted_weather:
            latest = sorted_weather[-1].get('data', {})
            lap_weather["1"] = _format_weather_record(latest, "N/A")
        return lap_weather
    
    # 獲取每圈開始的時間點
    lap_start_times = {}  # {lap_num: race_time_seconds}
    
    for snapshot in snapshots:
        current_lap = snapshot.get('current_lap', 0)
        race_time = snapshot.get('race_time_seconds', 0)
        
        if current_lap and current_lap > 0:
            if current_lap not in lap_start_times:
                lap_start_times[current_lap] = race_time
    
    # 為每圈找到對應的天氣記錄
    total_laps = race_info.get('total_laps', max(lap_start_times.keys()) if lap_start_times else 0)
    
    for lap in range(1, total_laps + 1):
        lap_time = lap_start_times.get(lap, 0)
        
        # 找到最接近該圈開始時間的天氣記錄
        best_weather = None
        best_diff = float('inf')
        
        for record in sorted_weather:
            record_time = parse_timestamp(record.get('timestamp', '00:00:00.000'))
            diff = abs(record_time - lap_time)
            if diff < best_diff:
                best_diff = diff
                best_weather = record.get('data', {})
        
        if best_weather:
            lap_weather[str(lap)] = _format_weather_record(best_weather, f"Lap {lap}")
    
    return lap_weather


def _format_weather_record(weather_data: Dict, timestamp: str) -> Dict[str, Any]:
    """格式化單條天氣記錄為 GUI 格式"""
    # 處理 Rainfall: 可能是 "0", "1", True, False
    rainfall_val = weather_data.get('Rainfall', False)
    if isinstance(rainfall_val, str):
        rainfall = rainfall_val == '1' or rainfall_val.lower() == 'true'
    else:
        rainfall = bool(rainfall_val)
    
    # 安全轉換數值
    def safe_float(val, default=0.0):
        try:
            return float(val) if val else default
        except (ValueError, TypeError):
            return default
    
    return {
        "weather": {
            "rainfall": rainfall
        },
        "temperature": {
            "air_temp": safe_float(weather_data.get('AirTemp')),
            "track_temp": safe_float(weather_data.get('TrackTemp'))
        },
        "humidity": safe_float(weather_data.get('Humidity')),
        "pressure": safe_float(weather_data.get('Pressure')),
        "wind": {
            "speed": safe_float(weather_data.get('WindSpeed')),
            "direction": safe_float(weather_data.get('WindDirection'))
        },
        "timestamp": timestamp
    }


def _calculate_weather_stats(lap_weather: Dict[str, Dict]) -> Dict[str, Any]:
    """
    計算天氣統計數據（兼容 rain_analysis GUI 格式）
    
    Args:
        lap_weather: 逐圈天氣數據字典
    
    Returns:
        統計數據字典（包含 has_rain_data 標記）
    """
    if not lap_weather:
        return {"has_rain_data": False}
    
    air_temps = []
    track_temps = []
    humidities = []
    pressures = []
    wind_speeds = []
    rainfall_laps = []
    
    for lap_str, lap_data in lap_weather.items():
        temp_data = lap_data.get("temperature", {})
        air_temp = temp_data.get("air_temp", 0)
        track_temp = temp_data.get("track_temp", 0)
        
        if air_temp > 0:
            air_temps.append(air_temp)
        if track_temp > 0:
            track_temps.append(track_temp)
        
        humidity = lap_data.get("humidity", 0)
        if humidity > 0:
            humidities.append(humidity)
        
        pressure = lap_data.get("pressure", 0)
        if pressure > 0:
            pressures.append(pressure)
        
        wind_data = lap_data.get("wind", {})
        wind_speed = wind_data.get("speed", 0)
        if wind_speed > 0:
            wind_speeds.append(wind_speed)
        
        weather_data = lap_data.get("weather", {})
        if weather_data.get("rainfall", False):
            rainfall_laps.append(int(lap_str))
    
    stats = {
        "has_rain_data": len(rainfall_laps) > 0,  # ✅ GUI 檢查此標記
        "air_temperature": {
            "min": min(air_temps) if air_temps else None,
            "max": max(air_temps) if air_temps else None,
            "avg": sum(air_temps) / len(air_temps) if air_temps else None,
            "range": max(air_temps) - min(air_temps) if air_temps else None
        },
        "track_temperature": {
            "min": min(track_temps) if track_temps else None,
            "max": max(track_temps) if track_temps else None,
            "avg": sum(track_temps) / len(track_temps) if track_temps else None,
            "range": max(track_temps) - min(track_temps) if track_temps else None
        },
        "humidity": {
            "min": min(humidities) if humidities else None,
            "max": max(humidities) if humidities else None,
            "avg": sum(humidities) / len(humidities) if humidities else None
        },
        "pressure": {
            "min": min(pressures) if pressures else None,
            "max": max(pressures) if pressures else None,
            "avg": sum(pressures) / len(pressures) if pressures else None
        },
        "wind_speed": {
            "min": min(wind_speeds) if wind_speeds else None,
            "max": max(wind_speeds) if wind_speeds else None,
            "avg": sum(wind_speeds) / len(wind_speeds) if wind_speeds else None
        },
        "rainfall": {
            "occurred": len(rainfall_laps) > 0,
            "affected_laps": rainfall_laps,
            "total_laps": len(rainfall_laps)
        }
    }
    
    return stats


def generate_json_output(
    result: Dict[str, Any],
    year: int,
    race: str,
    session: str
) -> str:
    """
    生成 JSON 輸出檔案
    
    Args:
        result: 分析結果
        year: 年份
        race: 賽事名稱
        session: 會話類型
    
    Returns:
        JSON 檔案路徑
    """
    json_dir = _ensure_json_dir()
    
    # 標準化賽事名稱
    race_token = race.replace(" ", "_")
    
    # 檔案命名：live_timing_weather_{year}_{race}_{session}.json
    filename = f"live_timing_weather_{year}_{race_token}_{session}.json"
    filepath = json_dir / filename
    
    json_result = {
        "function_id": 126,
        "function_name": "Live Timing Weather Analysis",
        "analysis_type": "live_timing_weather",
        "timestamp": datetime.now().isoformat(),
        "data": result
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        abs_filepath = filepath.absolute()
        print(f"\n[SUCCESS] JSON saved: {abs_filepath}")
        return str(abs_filepath)
        
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")
        return ""


def run_live_timing_weather_analysis(
    year: int,
    race: str,
    session: str = "R",
    **kwargs
) -> Dict[str, Any]:
    """
    執行 Live Timing 天氣分析（JSON 模式）
    
    此函數被 function_mapper.py 調用
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型
        **kwargs: 其他參數
    
    Returns:
        標準化結果字典
    """
    print(f"[FUNCTION 126] Live Timing Weather Analysis")
    print(f"[PARAMS] Year={year}, Race={race}, Session={session}")
    
    # 執行分析
    result = analyze_live_timing_weather(year, race, session)
    
    if not result.get('success'):
        return {
            "success": False,
            "message": result.get('message', 'Analysis failed'),
            "function_id": "126"
        }
    
    # 生成 JSON 輸出
    json_path = generate_json_output(result, year, race, session)
    
    # 顯示摘要
    print(f"\n[SUMMARY] Weather Analysis:")
    print(f"  Race: {year} {race} {session}")
    print(f"  Total Laps: {result['metadata']['total_laps']}")
    
    stats = result.get('statistics', {})
    air_temp_stats = stats.get('air_temperature', {})
    track_temp_stats = stats.get('track_temperature', {})
    rainfall_stats = stats.get('rainfall', {})
    
    if air_temp_stats.get('avg'):
        print(f"  Air Temperature: {air_temp_stats['avg']:.1f}°C (range: {air_temp_stats['min']:.1f}-{air_temp_stats['max']:.1f}°C)")
    
    if track_temp_stats.get('avg'):
        print(f"  Track Temperature: {track_temp_stats['avg']:.1f}°C (range: {track_temp_stats['min']:.1f}-{track_temp_stats['max']:.1f}°C)")
    
    if rainfall_stats.get('occurred'):
        print(f"  Rainfall: Yes (laps: {rainfall_stats['affected_laps']})")
    else:
        print(f"  Rainfall: No")
    
    return {
        "success": True,
        "data": result,
        "json_path": json_path,
        "function_id": "126"
    }


if __name__ == "__main__":
    # 測試範例
    import argparse
    
    parser = argparse.ArgumentParser(description="F126: Live Timing Weather Analysis")
    parser.add_argument("-y", "--year", type=int, required=True, help="Year (2018+)")
    parser.add_argument("-r", "--race", type=str, required=True, help="Race name")
    parser.add_argument("-s", "--session", type=str, default="R", help="Session type (R/Q/FP1/FP2/FP3)")
    
    args = parser.parse_args()
    
    result = run_live_timing_weather_analysis(
        year=args.year,
        race=args.race,
        session=args.session
    )
    
    print(f"\nResult: {'✅ Success' if result['success'] else '❌ Failed'}")
