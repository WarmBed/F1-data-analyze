#!/usr/bin/env python3
"""
F1 Analysis API - 分析相關路由
處理所有分析執行相關的端點

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import time

# 導入服務
from api.services.simple_analysis_service import SimpleF1AnalysisService
from api.models.function_specs import (
    FUNCTION_SPECS,
    function_id_sort_key,
    normalize_function_id,
)


def _merge_cross_event_telemetry(
    data1: Dict[str, Any],
    data2: Dict[str, Any],
    driver1: str,
    driver2: str,
    year1: int,
    race1: str,
    session1: str,
    lap1: int,
    year2: int,
    race2: str,
    session2: str,
    lap2: int
) -> Dict[str, Any]:
    """
    合併兩組 Function 13 JSON 數據為跨賽事比較格式
    
    策略：
    - 提取 data1 中車手1的遙測數據 (driver1_data)
    - 提取 data2 中車手2的遙測數據 (driver1_data，因為是占位符調用)
    - 合併為標準 Function 13 格式
    - ✅ 計算 Speed Diff / Distance Diff / Time Diff（參考 CLI Function 13 邏輯）
    
    Args:
        data1: 車手1的 Function 13 結果 (year1, race1, session1)
        data2: 車手2的 Function 13 結果 (year2, race2, session2)
        其他參數用於構建 metadata
    
    Returns:
        合併後的 JSON，格式與 Function 13 相同
    """
    
    import numpy as np
    
    # 提取遙測數據（從 results 內部）
    telemetry_comp1 = data1.get("results", {}).get("telemetry_comparison", {})
    telemetry_comp2 = data2.get("results", {}).get("telemetry_comparison", {})
    
    print(f"[MERGE] 🔍 data1 鍵值: {list(data1.keys())}")
    print(f"[MERGE] 🔍 data2 鍵值: {list(data2.keys())}")
    print(f"[MERGE] 🔍 telemetry_comp1 鍵值: {list(telemetry_comp1.keys())}")
    print(f"[MERGE] 🔍 telemetry_comp2 鍵值: {list(telemetry_comp2.keys())}")
    
    # 構建合併後的遙測比較數據
    merged_telemetry = {}
    
    # 遍歷所有遙測參數 (Speed, RPM, Brake, nGear, Throttle, Acceleration)
    for param in telemetry_comp1.keys():
        print(f"[MERGE] 處理參數: {param}")
        if param not in telemetry_comp2:
            print(f"[MERGE] ⚠️ 參數 {param} 在車手2數據中不存在，跳過")
            continue
        
        # 提取車手1的數據 (data1 中的 driver1_data)
        driver1_data = telemetry_comp1[param].get("driver1_data", [])
        distance1 = telemetry_comp1[param].get("distance", [])
        time1 = telemetry_comp1[param].get("driver1_time_seconds", None)
        
        # 提取車手2的數據 (data2 中的 driver1_data，因為是占位符)
        driver2_data = telemetry_comp2[param].get("driver1_data", [])
        distance2 = telemetry_comp2[param].get("distance", [])
        time2 = telemetry_comp2[param].get("driver1_time_seconds", None)
        
        # 統一距離基準 (使用較短的距離範圍)
        min_length = min(len(driver1_data), len(driver2_data))
        
        merged_telemetry[param] = {
            "name": telemetry_comp1[param].get("name", param),
            "driver1_data": driver1_data[:min_length],
            "driver2_data": driver2_data[:min_length],
            "distance": distance1[:min_length],  # 使用車手1的距離
        }
        
        # 添加時間數據 (如果存在)
        if time1 and time2:
            merged_telemetry[param]["driver1_time_seconds"] = time1[:min_length]
            merged_telemetry[param]["driver2_time_seconds"] = time2[:min_length]
            merged_telemetry[param]["time_reference"] = "seconds_from_lap_start"
    
    # 提取 comparison_info
    info1 = data1.get("comparison_info", {})
    info2 = data2.get("comparison_info", {})
    
    # 構建合併後的 comparison_info
    merged_comparison_info = {
        "driver1": driver1,
        "driver2": driver2,
        "act_lap1_number": lap1,
        "act_lap2_number": lap2,
        "lap_time1": info1.get("lap_time1", "N/A"),
        "lap_time2": info2.get("lap_time1", "N/A"),  # 注意：data2 的 driver1 就是我們的 driver2
        "compound1": info1.get("compound1", "Unknown"),
        "compound2": info2.get("compound1", "Unknown"),
        "tyre_life1": info1.get("tyre_life1", "Unknown"),
        "tyre_life2": info2.get("tyre_life1", "Unknown"),
    }
    
    # ========== ✅ 計算 Speed Difference（參考 CLI Function 13 邏輯）==========
    print(f"[MERGE] 🔄 開始計算跨賽事速度差異...")
    merged_speed_difference = {}
    
    if "Speed" in telemetry_comp1 and "Speed" in telemetry_comp2:
        try:
            # 提取速度數據
            driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
            driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
            distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
            distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))
            time1 = telemetry_comp1["Speed"].get("driver1_time_seconds", None)
            time2 = telemetry_comp2["Speed"].get("driver1_time_seconds", None)
            
            print(f"[MERGE] 車手1速度數據點數: {len(driver1_speed)}, 距離範圍: {distance1.min():.2f}-{distance1.max():.2f}m")
            print(f"[MERGE] 車手2速度數據點數: {len(driver2_speed)}, 距離範圍: {distance2.min():.2f}-{distance2.max():.2f}m")
            
            # 找出共同的距離範圍
            common_min = max(distance1.min(), distance2.min())
            common_max = min(distance1.max(), distance2.max())
            
            if common_min < common_max:
                # 創建共同的距離數組（500個採樣點）
                common_distance = np.linspace(common_min, common_max, 500)
                
                # 插值速度數據到共同距離
                speed1_interp = np.interp(common_distance, distance1, driver1_speed)
                speed2_interp = np.interp(common_distance, distance2, driver2_speed)
                
                # 計算速度差（driver1 - driver2）
                speed_diff = speed1_interp - speed2_interp
                
                merged_speed_difference = {
                    'distance': common_distance.tolist(),
                    'speed_difference': speed_diff.tolist(),
                    'max_diff': float(np.max(speed_diff)),
                    'min_diff': float(np.min(speed_diff)),
                    'mean_diff': float(np.mean(speed_diff)),
                    'reference': f"{driver1} - {driver2}"
                }
                
                # 插值時間數據（如果存在）
                if time1 and time2:
                    time1_array = np.array(time1)
                    time2_array = np.array(time2)
                    
                    # 插值時間到共同距離
                    time1_interp = np.interp(common_distance, distance1, time1_array)
                    time2_interp = np.interp(common_distance, distance2, time2_array)
                    
                    merged_speed_difference['driver1_time_seconds'] = time1_interp.tolist()
                    merged_speed_difference['driver2_time_seconds'] = time2_interp.tolist()
                    merged_speed_difference['time_reference'] = 'seconds_from_lap_start'
                    print(f"[MERGE] ✅ 速度差時間數據已添加（{len(time1_interp)} 點）")
                
                print(f"[MERGE] ✅ 速度差計算完成：{len(speed_diff)} 點，範圍 {merged_speed_difference['min_diff']:.2f} ~ {merged_speed_difference['max_diff']:.2f} km/h")
            else:
                print(f"[MERGE] ❌ 無共同距離範圍: [{common_min:.2f}, {common_max:.2f}]")
        except Exception as e:
            print(f"[MERGE] ❌ 速度差計算失敗: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[MERGE] ⚠️ Speed 數據不完整，跳過速度差計算")
    
    # ========== 構建 Speeddiff 遙測參數（用於 Speed Diff Analysis）==========
    if merged_speed_difference:
        merged_telemetry["Speeddiff"] = {
            "name": "Speed Difference",
            "distance": merged_speed_difference["distance"],
            "speed_difference": merged_speed_difference["speed_difference"],  # ✅ 已計算的差異
            "driver1_time_seconds": merged_speed_difference.get("driver1_time_seconds", []),
            "driver2_time_seconds": merged_speed_difference.get("driver2_time_seconds", []),
            "time_reference": merged_speed_difference.get("time_reference", "")
        }
        print(f"[MERGE] ✅ Speeddiff 遙測參數已添加")
    
    # ========== ✅ 計算 Distance Difference（參考 Speeddiff 邏輯）==========
    print(f"[MERGE] 🔄 開始計算跨賽事距離差異...")
    merged_distance_difference = {}
    
    # 檢查是否有 Distance 參數（在某些情況下可能沒有獨立的 Distance 參數）
    # 嘗試從 Speed 參數中提取距離信息
    if "Speed" in telemetry_comp1 and "Speed" in telemetry_comp2:
        try:
            # 使用速度數據的距離作為參考
            distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
            distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))
            time1 = telemetry_comp1["Speed"].get("driver1_time_seconds", None)
            time2 = telemetry_comp2["Speed"].get("driver1_time_seconds", None)
            
            print(f"[MERGE] 車手1距離數據點數: {len(distance1)}, 範圍: {distance1.min():.2f}-{distance1.max():.2f}m")
            print(f"[MERGE] 車手2距離數據點數: {len(distance2)}, 範圍: {distance2.min():.2f}-{distance2.max():.2f}m")
            
            # 找出共同的距離範圍
            common_min = max(distance1.min(), distance2.min())
            common_max = min(distance1.max(), distance2.max())
            
            if common_min < common_max:
                # 創建共同的距離數組（500個採樣點）
                common_distance = np.linspace(common_min, common_max, 500)
                
                # 對於距離差異，我們需要計算在相同賽道位置上的時間差異
                # 然後根據速度估算距離差異
                # 簡化版本：假設兩位車手在相同距離上的累積距離差
                
                # 計算每位車手到達每個距離點的時間
                if time1 and time2:
                    time1_array = np.array(time1)
                    time2_array = np.array(time2)
                    
                    # 插值時間到共同距離
                    time1_interp = np.interp(common_distance, distance1, time1_array)
                    time2_interp = np.interp(common_distance, distance2, time2_array)
                    
                    # 計算時間差（driver1 - driver2）
                    time_diff = time1_interp - time2_interp
                    
                    # 使用速度和時間差計算距離差
                    # 簡化假設：使用速度插值估算距離差
                    driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
                    driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
                    
                    speed1_interp = np.interp(common_distance, distance1, driver1_speed)
                    speed2_interp = np.interp(common_distance, distance2, driver2_speed)
                    
                    # 估算距離差：使用平均速度 * 時間差 / 3.6 (km/h -> m/s)
                    avg_speed = (speed1_interp + speed2_interp) / 2
                    distance_diff = (avg_speed / 3.6) * time_diff  # 轉換為米
                    
                    merged_distance_difference = {
                        'distance': common_distance.tolist(),
                        'distance_difference': distance_diff.tolist(),
                        'max_diff': float(np.max(distance_diff)),
                        'min_diff': float(np.min(distance_diff)),
                        'mean_diff': float(np.mean(distance_diff)),
                        'reference': f"{driver1} - {driver2}",
                        'driver1_time_seconds': time1_interp.tolist(),
                        'driver2_time_seconds': time2_interp.tolist(),
                        'time_reference': 'seconds_from_lap_start'
                    }
                    
                    print(f"[MERGE] ✅ 距離差計算完成：{len(distance_diff)} 點，範圍 {merged_distance_difference['min_diff']:.2f} ~ {merged_distance_difference['max_diff']:.2f} m")
                else:
                    print(f"[MERGE] ⚠️ 缺少時間數據，無法計算距離差")
            else:
                print(f"[MERGE] ❌ 無共同距離範圍: [{common_min:.2f}, {common_max:.2f}]")
        except Exception as e:
            print(f"[MERGE] ❌ 距離差計算失敗: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[MERGE] ⚠️ Speed 數據不完整，跳過距離差計算")
    
    # ========== 構建 Distancediff 遙測參數（用於 Distance Diff Analysis）==========
    if merged_distance_difference:
        merged_telemetry["Distancediff"] = {
            "name": "Distance Difference",
            "distance": merged_distance_difference["distance"],
            "distance_difference": merged_distance_difference["distance_difference"],  # ✅ 已計算的距離差
            "driver1_time_seconds": merged_distance_difference.get("driver1_time_seconds", []),
            "driver2_time_seconds": merged_distance_difference.get("driver2_time_seconds", []),
            "time_reference": merged_distance_difference.get("time_reference", "")
        }
        print(f"[MERGE] ✅ Distancediff 遙測參數已添加")
    
    # ========== ✅ 計算 Time Difference（參考 CLI Function 13 Line 641-721）==========
    print(f"[MERGE] 🔄 開始計算跨賽事時間差異...")
    merged_time_difference = {}
    
    if "Speed" in telemetry_comp1 and "Speed" in telemetry_comp2:
        try:
            # 提取距離和時間數據
            distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
            distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))
            time1 = telemetry_comp1["Speed"].get("driver1_time_seconds", None)
            time2 = telemetry_comp2["Speed"].get("driver1_time_seconds", None)
            
            if time1 and time2 and len(distance1) > 0 and len(distance2) > 0:
                time1_array = np.array(time1)
                time2_array = np.array(time2)
                
                # 找出共同的時間範圍
                common_time_min = max(time1_array.min(), time2_array.min())
                common_time_max = min(time1_array.max(), time2_array.max())
                
                if common_time_min < common_time_max:
                    # 創建共同的時間數組（500個採樣點）
                    common_time = np.linspace(common_time_min, common_time_max, 500)
                    
                    # 插值距離數據到共同時間
                    distance1_interp = np.interp(common_time, time1_array, distance1)
                    distance2_interp = np.interp(common_time, time2_array, distance2)
                    
                    # 計算距離差（driver1 - driver2，正值表示 driver1 領先）
                    distance_gap = distance1_interp - distance2_interp
                    
                    # 提取速度數據並插值到共同時間
                    driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
                    driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
                    
                    speed1_interp = np.interp(common_time, time1_array, driver1_speed)
                    speed2_interp = np.interp(common_time, time2_array, driver2_speed)
                    
                    # 轉換速度 km/h → m/s
                    speed1_ms = speed1_interp / 3.6
                    speed2_ms = speed2_interp / 3.6
                    
                    # 計算平均速度並避免除以零
                    avg_speed_ms = (speed1_ms + speed2_ms) / 2
                    avg_speed_ms = np.where(avg_speed_ms > 0.1, avg_speed_ms, 0.1)  # 最小速度 0.1 m/s
                    
                    # 計算時間差：距離差 / 平均速度
                    cumulative_time_diff = distance_gap / avg_speed_ms
                    
                    # 構建合併後的時間差數據
                    merged_time_difference = {
                        'time': common_time.tolist(),  # X軸：時間（秒）
                        'distance_gap': distance_gap.tolist(),  # 距離差（米）
                        'time_difference': cumulative_time_diff.tolist(),  # Y軸：時間差（秒）
                        'driver1_distance': distance1_interp.tolist(),  # 車手1在各時間點的距離
                        'driver2_distance': distance2_interp.tolist(),  # 車手2在各時間點的距離
                        'max_time_diff': float(np.max(cumulative_time_diff)),
                        'min_time_diff': float(np.min(cumulative_time_diff)),
                        'mean_time_diff': float(np.mean(cumulative_time_diff)),
                        'reference': f"{driver1} - {driver2}"
                    }
                    
                    print(f"[MERGE] ✅ 時間差計算完成：{len(cumulative_time_diff)} 點")
                    print(f"[MERGE]    - 時間範圍: {common_time_min:.2f} ~ {common_time_max:.2f} s")
                    print(f"[MERGE]    - 時間差範圍: {merged_time_difference['min_time_diff']:.3f} ~ {merged_time_difference['max_time_diff']:.3f} s")
                else:
                    print(f"[MERGE] ⚠️ 時間範圍不重疊，跳過時間差計算")
            else:
                print(f"[MERGE] ⚠️ 時間或距離數據缺失，跳過時間差計算")
        except Exception as e:
            print(f"[MERGE] ❌ 時間差計算失敗: {e}")
            traceback.print_exc()
    else:
        print(f"[MERGE] ⚠️ Speed 數據不完整，跳過時間差計算")
    
    # ========== 構建 Timediff 遙測參數（用於 Time Diff Analysis）==========
    if merged_time_difference:
        merged_telemetry["Timediff"] = {
            "name": "Time Difference",
            "time": merged_time_difference["time"],  # X軸：時間（秒）
            "time_difference": merged_time_difference["time_difference"],  # Y軸：時間差（秒）
            "distance_gap": merged_time_difference.get("distance_gap", []),  # 額外資訊：距離差
            "driver1_distance": merged_time_difference.get("driver1_distance", []),  # 車手1距離
            "driver2_distance": merged_time_difference.get("driver2_distance", [])   # 車手2距離
        }
        print(f"[MERGE] ✅ Timediff 遙測參數已添加")
    
    # 提取速度差數據 (使用計算好的跨賽事速度差)
    speed_diff1 = data1.get("speed_difference", {})
    speed_diff2 = data2.get("speed_difference", {})
    
    # 構建合併後的結果
    merged_result = {
        "comparison_info": merged_comparison_info,
        "telemetry_comparison": merged_telemetry,
        "speed_difference": merged_speed_difference if merged_speed_difference else speed_diff1,  # ✅ 使用跨賽事計算的速度差
        "distance_difference": merged_distance_difference if merged_distance_difference else data1.get("distance_difference", {}),  # ✅ 使用跨賽事計算的距離差
        "time_difference": merged_time_difference if merged_time_difference else data1.get("time_difference", {}),  # ✅ 使用跨賽事計算的時間差
        "statistics": data1.get("statistics", {}),
        "charts_generated": [],
        "disable_charts": True,
        # 🆕 跨賽事元數據
        "cross_event_metadata": {
            "driver1_event": {
                "year": year1,
                "race": race1,
                "session": session1,
                "lap": lap1
            },
            "driver2_event": {
                "year": year2,
                "race": race2,
                "session": session2,
                "lap": lap2
            },
            "comparison_mode": "cross_event"
        }
    }
    
    print(f"[MERGE] ✅ 合併完成，參數數量: {len(merged_telemetry)}")
    print(f"[MERGE] ✅ 速度差數據: {'已計算' if merged_speed_difference else '未計算'}")
    print(f"[MERGE] ✅ 距離差數據: {'已計算' if merged_distance_difference else '未計算'}")
    print(f"[MERGE] ✅ 時間差數據: {'已計算' if merged_time_difference else '未計算'}")
    return merged_result


# 創建路由器
router = APIRouter(
    prefix="/analysis",
    tags=["分析執行"],
    responses={
        404: {"description": "分析功能不存在"},
        500: {"description": "服務器內部錯誤"}
    }
)

# 初始化服務
analysis_service = SimpleF1AnalysisService()


SUPPORTED_FUNCTION_IDS = sorted(FUNCTION_SPECS.keys(), key=function_id_sort_key)


@router.post("/execute")
async def execute_analysis(
    function_id: str = Query(..., description="分析功能 ID"),
    year: Optional[int] = Query(None, ge=2020, le=2025, description="賽季年份 (2020-2025，Function 100 可選)"),
    race: Optional[str] = Query(None, min_length=3, description="賽事名稱"),
    session: Optional[str] = Query(None, description="會話類型 (R/Q/FP1/FP2/FP3)"),
    driver1: Optional[str] = Query(None, min_length=3, max_length=3, description="主要車手代碼"),
    driver2: Optional[str] = Query(None, min_length=3, max_length=3, description="比較車手代碼"),
    force_refresh: bool = Query(False, description="強制重新執行分析"),
    lap: Optional[int] = Query(None, ge=1, description="統一圈數參數 (單圈分析)"),
    lap1: Optional[int] = Query(None, ge=1, description="車手1圈數 (遙測比較)"),
    lap2: Optional[int] = Query(None, ge=1, description="車手2圈數 (遙測比較)"),
    team: Optional[str] = Query(None, description="車隊名稱 (Function 29 - FIA Parts Analysis)"),
    change_type: Optional[str] = Query(None, description="變更類型 (Function 29)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="最低信心度 (Function 29)"),
    exclude_noise: Optional[bool] = Query(None, description="排除噪音記錄 (Function 29)")
) -> Dict[str, Any]:
    """
    執行 F1 分析功能
    
    - **function_id**: 分析功能 ID (1-200)
    - **year**: 賽季年份 (2020-2025，Function 100 不需要此參數)
    - **race**: 賽事名稱 (例如: Japan, Italy)
    - **session**: 會話類型 (R=正賽, Q=排位賽, FP1/2/3=練習賽)
    - **driver1**: 主要車手代碼 (3字母, 例如: VER)
    - **driver2**: 比較車手代碼 (用於車手比較分析)
    - **force_refresh**: 是否強制重新執行 (忽略緩存)
    """
    
    try:
        normalized_id = normalize_function_id(function_id)

        if normalized_id not in FUNCTION_SPECS:
            raise HTTPException(status_code=400, detail={
                "error": "unsupported_function",
                "message": f"function_id {function_id} 尚未透過 API 支援",
                "supported": SUPPORTED_FUNCTION_IDS,
            })

        # 建構參數（year 為可選）
        params = {}
        
        if year is not None:
            params["year"] = year

        if race:
            params["race"] = race
        if session:
            params["session"] = session
        
        if driver1:
            params["driver1"] = driver1.upper()
        if driver2:
            params["driver2"] = driver2.upper()
        if force_refresh:
            params["force_refresh"] = True
        if lap:
            params["lap"] = lap
        if lap1:
            params["lap1"] = lap1
        if lap2:
            params["lap2"] = lap2
        
        # Function 29 (FIA Parts Analysis) 專用參數
        if team:
            params["team"] = team
        if change_type:
            params["change_type"] = change_type
        if min_confidence is not None:
            params["min_confidence"] = min_confidence
        if exclude_noise is not None:
            params["exclude_noise"] = exclude_noise
            
        # 執行分析
        result = await analysis_service.execute_analysis(normalized_id, **params)

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameters",
                "message": str(exc),
                "function_id": function_id,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "分析執行失敗",
                "message": str(e),
                "function_id": function_id,
                "timestamp": time.time()
            }
        )


@router.get("/functions")
async def get_supported_functions() -> Dict[str, Any]:
    """
    獲取支持的分析功能列表
    
    返回所有可用的分析功能及其描述
    """
    try:
        functions = {
            spec.function_id: {
                "name": spec.name,
                "description": spec.description,
                "required_params": spec.required_params,
                "optional_params": spec.optional_params,
                "cache_patterns": spec.cache_patterns,
                "notes": spec.notes,
            }
            for spec in FUNCTION_SPECS.values()
        }

        return {
            "success": True,
            "message": "目前 API 支援的分析功能",
            "total_functions": len(functions),
            "functions": functions,
            "supported_function_ids": SUPPORTED_FUNCTION_IDS,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "功能列表獲取失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )


@router.post("/cross-event-comparison")
async def cross_event_comparison(
    driver1: str = Query(..., min_length=3, max_length=3, description="車手1代碼"),
    year1: int = Query(..., ge=2020, le=2025, description="車手1賽季年份"),
    race1: str = Query(..., min_length=3, description="車手1賽事名稱"),
    session1: str = Query(..., description="車手1會話類型 (R/Q/FP1/FP2/FP3)"),
    lap1: int = Query(..., ge=1, description="車手1圈數"),
    driver2: str = Query(..., min_length=3, max_length=3, description="車手2代碼"),
    year2: int = Query(..., ge=2020, le=2025, description="車手2賽季年份"),
    race2: str = Query(..., min_length=3, description="車手2賽事名稱"),
    session2: str = Query(..., description="車手2會話類型 (R/Q/FP1/FP2/FP3)"),
    lap2: int = Query(..., ge=1, description="車手2圈數"),
    force_refresh: bool = Query(False, description="強制重新執行分析"),
) -> Dict[str, Any]:
    """
    跨年度/跨賽事遙測比較
    
    支援比較不同年份、不同賽事、不同會話的兩位車手遙測數據
    例如：2024 Brazil R VER Lap1 vs 2025 Japan Q LEC Lap1
    
    內部流程：
    1. 檢查是否為跨賽事比較 (year1 != year2 或 race1 != race2 或 session1 != session2)
    2. 分別調用 Function 13 獲取兩組遙測數據
    3. 合併兩組 JSON 為統一格式
    4. 返回合併後的結果
    
    返回格式與 Function 13 相同，但 metadata 包含兩組賽事信息
    """
    
    try:
        # 檢查是否為跨賽事比較
        is_cross_event = (year1 != year2) or (race1 != race2) or (session1 != session2)
        
        if not is_cross_event:
            # 標準模式：直接調用 Function 13
            params = {
                "year": year1,
                "race": race1,
                "session": session1,
                "driver1": driver1.upper(),
                "driver2": driver2.upper(),
                "lap1": lap1,
                "lap2": lap2,
                "force_refresh": force_refresh,
            }
            return await analysis_service.execute_analysis("13", **params)
        
        # 跨賽事模式：分別獲取兩組數據
        print(f"[CROSS-EVENT] 開始跨賽事比較...")
        print(f"[CROSS-EVENT]   車手1: {year1} {race1} {session1} - {driver1} Lap {lap1}")
        print(f"[CROSS-EVENT]   車手2: {year2} {race2} {session2} - {driver2} Lap {lap2}")
        
        # 步驟 1: 獲取車手1的遙測數據 (使用最速圈作為比較對象)
        # 由於 Function 13 需要兩個車手，這裡使用同一車手的不同圈數作為占位符
        params1 = {
            "year": year1,
            "race": race1,
            "session": session1,
            "driver1": driver1.upper(),
            "driver2": driver1.upper(),  # 占位符：使用相同車手
            "lap1": lap1,
            "lap2": lap1,  # 占位符：使用相同圈數
            "force_refresh": force_refresh,
        }
        
        print(f"[CROSS-EVENT] 步驟 1/3: 獲取車手1數據...")
        result1 = await analysis_service.execute_analysis("13", **params1)
        
        if not result1.get("success"):
            raise ValueError(f"車手1數據獲取失敗: {result1.get('message', '未知錯誤')}")
        
        # 步驟 2: 獲取車手2的遙測數據
        params2 = {
            "year": year2,
            "race": race2,
            "session": session2,
            "driver1": driver2.upper(),
            "driver2": driver2.upper(),  # 占位符：使用相同車手
            "lap1": lap2,
            "lap2": lap2,  # 占位符：使用相同圈數
            "force_refresh": force_refresh,
        }
        
        print(f"[CROSS-EVENT] 步驟 2/3: 獲取車手2數據...")
        result2 = await analysis_service.execute_analysis("13", **params2)
        
        if not result2.get("success"):
            raise ValueError(f"車手2數據獲取失敗: {result2.get('message', '未知錯誤')}")
        
        # 步驟 3: 合併兩組數據
        print(f"[CROSS-EVENT] 步驟 3/3: 合併遙測數據...")
        merged_result = _merge_cross_event_telemetry(
            result1["data"], result2["data"],
            driver1, driver2, year1, race1, session1, lap1,
            year2, race2, session2, lap2
        )
        
        print(f"[CROSS-EVENT] ✅ 跨賽事比較完成")
        
        return {
            "success": True,
            "message": f"跨賽事遙測比較完成 ({year1} {race1} {session1} vs {year2} {race2} {session2})",
            "data": merged_result,
            "cross_event": True,
            "function_id": "13",
            "timestamp": time.time()
        }
        
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameters",
                "message": str(exc),
                "timestamp": time.time()
            }
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "跨賽事比較執行失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/status")
async def get_analysis_status() -> Dict[str, Any]:
    """
    獲取分析服務狀態
    
    返回服務健康狀態和性能指標
    """
    
    try:
        health_result = await analysis_service.health_check()
        cache_result = await analysis_service.get_cache_status()
        runtime_state = analysis_service.get_runtime_state()
        service_status = "busy" if runtime_state.get("busy") else health_result.get("status", "unknown")
        
        return {
            "success": True,
            "message": "分析服務狀態",
            "status": service_status,
            "service_health": health_result,
            "cache_status": cache_result,
            "runtime": runtime_state,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "狀態檢查失敗",
            "error": str(e),
            "timestamp": time.time()
        }
