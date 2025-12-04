"""
F1 Analysis API - 賽道位置分析模組 (功能2)
專門的賽道路線分析，包含位置數據表格顯示和Raw Data輸出
符合 copilot-instructions 開發核心要求
"""

import json
import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime, timedelta
from prettytable import PrettyTable


def run_track_position_analysis(data_loader, show_detailed_output=True):
    """主要功能：賽道位置分析 - 僅包含距離、位置X、位置Y (純FastF1/OpenF1數據)
    
    Args:
        data_loader: 數據載入器
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    print(f"[TEST] 開始執行賽道位置分析...")
    print(f"[TEST][TRACK] F1 賽道位置分析 (功能2)")
    print(f"[INFO] 分析目標：賽道位置座標、距離數據 (僅使用FastF1/OpenF1真實數據)")
    print("=" * 60)
    
    # 獲取賽事基本信息
    session_info = get_session_info(data_loader)
    print_session_summary(session_info)
    
    # 檢查緩存 - Function 15 標準實現
    cache_key = f"track_position_{session_info['year']}_{session_info['race']}_{session_info['session_type']}"
    cached_data = check_cache(cache_key)
    cache_used = cached_data is not None
    
    if cached_data and not show_detailed_output:
        print("[PACKAGE] 使用緩存數據")
        position_data = cached_data
        
        # 結果驗證和反饋
        if not report_analysis_results(position_data, "賽道位置分析"):
            return None
        
        print(f"\n[OK] 賽道位置分析分析完成！")
        return {
            "success": True,
            "data": position_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "2"
        }
        
    elif cached_data and show_detailed_output:
        print("[PACKAGE] 使用緩存數據 + [STATS] 顯示詳細分析結果")
        position_data = cached_data
        
        # 結果驗證和反饋
        if not report_analysis_results(position_data, "賽道位置分析"):
            return None
            
        # 顯示詳細輸出 - 即使使用緩存
        _display_cached_detailed_output(position_data, session_info)
        
        print(f"\n[OK] 賽道位置分析分析完成！")
        return {
            "success": True,
            "data": position_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "2"
        }
    else:
        print("[REFRESH] 重新計算 - 開始數據分析...")
        # 分析賽道位置數據
        position_data = analyze_track_position_data(data_loader)
        
        if not position_data:
            print("[ERROR] 賽道位置分析失敗：無可用數據")
            return None
        
        # 保存緩存
        save_cache(position_data, cache_key)
        print("[SAVE] 分析結果已緩存")
    
    # 結果驗證和反饋
    if not report_analysis_results(position_data, "賽道位置分析"):
        return None
    
    # 顯示位置數據表格
    display_position_table(position_data)
    
    # 顯示分析統計
    display_position_statistics(position_data)
    
    # 保存Raw Data
    save_position_raw_data(session_info, position_data)
    
    print(f"\n[OK] 賽道位置分析分析完成！")
    return {
        "success": True,
        "data": position_data,
        "cache_used": cache_used,
        "cache_key": cache_key,
        "function_id": "2"
    }


def check_cache(cache_key):
    """檢查緩存是否存在"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[WARNING] 緩存載入失敗: {e}")
            return None
    return None


def save_cache(data, cache_key):
    """保存數據到緩存"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"[WARNING] 緩存保存失敗: {e}")


def report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態"""
    if not data:
        print(f"[ERROR] {analysis_type}失敗：無可用數據")
        return False
    
    data_count = len(data.get('position_records', [])) if data else 0
    print(f"[STATS] {analysis_type}結果摘要：")
    print(f"   • 數據項目數量: {data_count}")
    print(f"   • 數據完整性: {'[OK] 良好' if data_count > 0 else '[ERROR] 不足'}")
    
    # 檢查關鍵欄位
    if data and 'position_records' in data:
        missing_coords = sum(1 for r in data['position_records'] if not (r.get('position_x') and r.get('position_y')))
        print(f"   • 缺失座標點: {missing_coords}")
    
    print(f"[OK] {analysis_type}分析完成！")
    return True


def _display_cached_detailed_output(position_data, session_info):
    """當使用緩存數據但需要顯示詳細輸出時調用此函數"""
    print("\n[STATS] 顯示緩存的詳細分析結果...")
    
    # 顯示位置數據表格
    display_position_table(position_data)
    
    # 顯示分析統計
    display_position_statistics(position_data)
    
    # 保存Raw Data（如果需要）
    save_position_raw_data(session_info, position_data)


def format_time(time_obj):
    """標準時間格式化函數 - 禁止包含 day 或 days"""
    if pd.isna(time_obj) or time_obj is None:
        return "N/A"
    
    # 轉換為字符串並移除 days
    time_str = str(time_obj)
    
    # 移除 "0 days " 和任何 "days " 前綴
    if "days" in time_str:
        time_str = time_str.split("days ")[-1]
    
    # 處理 pandas Timedelta 或 datetime
    if hasattr(time_obj, 'total_seconds'):
        total_seconds = time_obj.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:06.3f}"
        else:
            return f"{minutes}:{seconds:06.3f}"
    
    return time_str


def get_session_info(data_loader):
    """獲取賽事基本信息"""
    # 使用賽事全名映射
    race_full_names = {
        "Bahrain": "Bahrain Grand Prix",
        "Saudi Arabia": "Saudi Arabian Grand Prix", 
        "Australia": "Australian Grand Prix",
        "Japan": "Japanese Grand Prix",
        "China": "Chinese Grand Prix",
        "Miami": "Miami Grand Prix",
        "Emilia Romagna": "Emilia Romagna Grand Prix",
        "Monaco": "Monaco Grand Prix",
        "Canada": "Canadian Grand Prix",
        "Spain": "Spanish Grand Prix", 
        "Austria": "Austrian Grand Prix",
        "Great Britain": "British Grand Prix",
        "Hungary": "Hungarian Grand Prix",
        "Belgium": "Belgian Grand Prix",
        "Netherlands": "Dutch Grand Prix",
        "Italy": "Italian Grand Prix",
        "Azerbaijan": "Azerbaijan Grand Prix",
        "Singapore": "Singapore Grand Prix",
        "United States": "United States Grand Prix",
        "Mexico": "Mexican Grand Prix",
        "Brazil": "Brazilian Grand Prix",
        "Las Vegas": "Las Vegas Grand Prix",
        "Qatar": "Qatar Grand Prix",
        "Abu Dhabi": "Abu Dhabi Grand Prix"
    }
    
    # 先嘗試從 data_loader 獲取簡短賽事名稱，然後映射到完整名稱
    race_short = getattr(data_loader, 'race', 'Unknown')
    race_full = race_full_names.get(race_short, race_short)
    
    session_info = {
        "year": getattr(data_loader, 'year', 'Unknown'),
        "race": race_full,  # 使用完整賽事名稱
        "session_type": getattr(data_loader, 'session_type', 'Unknown'),
        "date": "Unknown"
    }
    
    # 優先從 FastF1 Session 獲取正確的賽事名稱
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        try:
            session = data_loader.session
            # 從 FastF1 session 獲取正確的賽事名稱
            event_name = getattr(session, 'event', {}).get('EventName', None)
            if event_name and event_name != 'Unknown':
                session_info["race"] = event_name
            
            session_info["date"] = str(getattr(session, 'date', 'Unknown'))
        except:
            pass
    
    return session_info


def print_session_summary(session_info):
    """顯示賽事摘要信息"""
    print(f"\n[LIST] 賽事信息摘要:")
    print(f"   [CALENDAR] 賽季: {session_info['year']}")
    print(f"   [FINISH] 賽事: {session_info['race']}")
    print(f"   [F1] 賽段: {session_info['session_type']}")
    print(f"   📆 日期: {session_info['date']}")


def _map_official_corners_to_telemetry(session, telemetry_data, telemetry_distances):
    """
    將 FastF1 官方彎道映射到遙測距離
    
    Args:
        session: FastF1 session 對象
        telemetry_data: 遙測數據 DataFrame (包含 X, Y)
        telemetry_distances: 遙測距離數組
    
    Returns:
        dict: 官方彎道資訊，包含映射後的距離
    """
    try:
        # 獲取賽道彎道資訊
        circuit_info = session.get_circuit_info()
        
        if circuit_info is None or not hasattr(circuit_info, 'corners'):
            return None
        
        official_corners = circuit_info.corners
        
        if official_corners is None or len(official_corners) == 0:
            return None
        
        print(f"   [INFO] FastF1 官方彎道數量: {len(official_corners)}")
        
        # 提取遙測座標
        telemetry_x = telemetry_data['X'].values
        telemetry_y = telemetry_data['Y'].values
        
        mapped_corners = []
        
        for idx, corner_row in official_corners.iterrows():
            corner_num = int(corner_row['Number'])
            corner_x = float(corner_row['X'])
            corner_y = float(corner_row['Y'])
            corner_angle = float(corner_row['Angle'])
            
            # 計算遙測中每個點到彎道的歐幾里得距離
            distances_to_corner = np.sqrt(
                (telemetry_x - corner_x)**2 + 
                (telemetry_y - corner_y)**2
            )
            
            # 找到最接近的遙測點
            closest_idx = int(np.argmin(distances_to_corner))
            mapping_error = float(distances_to_corner[closest_idx])
            
            # 獲取該點的距離
            if closest_idx < len(telemetry_distances):
                mapped_distance = float(telemetry_distances[closest_idx])
            else:
                mapped_distance = 0.0
            
            # 獲取 FastF1 原始的單圈距離 (Distance 欄位)
            fastf1_distance = 0.0
            if 'Distance' in corner_row.index and pd.notna(corner_row['Distance']):
                fastf1_distance = float(corner_row['Distance'])
            
            # 構建彎道資料
            corner_data = {
                "number": corner_num,
                "x": corner_x,
                "y": corner_y,
                "angle": corner_angle,
                "distance": fastf1_distance,  # FastF1 原始單圈距離
                "mapped_distance": mapped_distance,  # 多圈累積距離 (保留向後相容)
                "mapping_error": mapping_error
            }
            
            # 如果有 Letter 欄位，也加入
            if 'Letter' in corner_row.index and pd.notna(corner_row['Letter']):
                corner_data["letter"] = str(corner_row['Letter'])
            
            mapped_corners.append(corner_data)
        
        # 按彎道編號排序
        mapped_corners.sort(key=lambda x: x['number'])
        
        # 計算映射品質統計
        errors = [c['mapping_error'] for c in mapped_corners]
        avg_error = float(np.mean(errors))
        max_error = float(np.max(errors))
        
        result = {
            "available": True,
            "count": len(mapped_corners),
            "corners": mapped_corners,
            "mapping_quality": {
                "average_error_m": round(avg_error, 1),
                "max_error_m": round(max_error, 1),
                "min_error_m": round(float(np.min(errors)), 1)
            }
        }
        
        print(f"   [INFO] 映射品質 - 平均誤差: {avg_error:.1f}m, 最大誤差: {max_error:.1f}m")
        
        return result
        
    except Exception as e:
        print(f"   [ERROR] 官方彎道映射異常: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_track_position_data(data_loader):
    """分析賽道位置數據 - 僅使用FastF1真實數據"""
    position_data = {
        "has_position_data": False,
        "position_records": [],
        "fastest_lap_info": None,
        "track_bounds": None,
        "distance_covered": 0,
        # 新增：FastF1 官方彎道資訊 (向後相容)
        "official_corners": {
            "available": False,
            "count": 0,
            "corners": []
        }
    }
    
    if not hasattr(data_loader, 'session') or data_loader.session is None:
        print("\n[ERROR] 無法獲取賽事數據")
        return position_data
    
    try:
        session = data_loader.session
        laps = session.laps
        
        if laps is None or laps.empty:
            print("\n[ERROR] 沒有圈速數據")
            return position_data
        
        # 找到最快圈
        valid_laps = laps[laps['LapTime'].notna()]
        if valid_laps.empty:
            print("\n[ERROR] 沒有有效圈速數據")
            return position_data
        
        # 獲取最快圈信息
        fastest_lap_idx = valid_laps['LapTime'].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        
        position_data["fastest_lap_info"] = {
            "driver": str(fastest_lap['Driver']),
            "lap_number": int(fastest_lap['LapNumber']),
            "lap_time": str(fastest_lap['LapTime'])
        }
        
        # 嘗試獲取位置數據 - 僅使用FastF1真實數據
        try:
            # 獲取該圈的原始FastF1 Lap對象
            driver = fastest_lap['Driver']
            lap_number = int(fastest_lap['LapNumber'])
            
            print(f"\n[DEBUG] 嘗試獲取 {driver} 第{lap_number}圈的真實位置數據...")
            
            # 從session獲取原始lap對象
            driver_laps = session.laps.pick_driver(driver)
            if not driver_laps.empty:
                lap_obj = driver_laps.pick_lap(lap_number)
                
                if lap_obj is not None:
                    # 獲取車輛數據和位置數據
                    car_data = lap_obj.get_car_data()
                    
                    print(f"[INFO] FastF1數據檢查:")
                    print(f"   車輛數據點數: {len(car_data)}")
                    print(f"   可用欄位: {list(car_data.columns)}")
                    
                    # 嘗試獲取賽道位置數據
                    try:
                        # 從lap對象獲取位置數據
                        pos_data = lap_obj.get_pos_data()
                        print(f"   位置數據點數: {len(pos_data)}")
                        print(f"   位置數據欄位: {list(pos_data.columns)}")
                        
                        if not pos_data.empty and 'X' in pos_data.columns and 'Y' in pos_data.columns:
                            position_data["has_position_data"] = True
                            print(f"   [SUCCESS] 賽道位置數據 (X, Y): 可用")
                            
                            # 檢查距離數據
                            has_distance = 'Distance' in pos_data.columns
                            print(f"   [SUCCESS] 距離數據: {'可用' if has_distance else '需計算'}")
                            
                            # 計算距離
                            if has_distance:
                                distances = pos_data['Distance'].values
                                print(f"   [SUCCESS] 使用FastF1官方距離數據")
                            else:
                                # 基於位置計算累積距離
                                distances = calculate_distances_from_positions(
                                    pos_data['X'].values, 
                                    pos_data['Y'].values
                                )
                                print(f"   [WARNING] 基於位置計算距離")
                            
                            # ✅ 使用完整位置數據（不再限制採樣）
                            total_points = len(pos_data)
                            
                            print(f"   [INFO] 處理 {total_points} 個賽道位置點（使用完整數據）")
                            
                            # 檢查是否有時間數據
                            has_time = 'Time' in pos_data.columns or 'SessionTime' in pos_data.columns
                            time_column = 'Time' if 'Time' in pos_data.columns else 'SessionTime' if 'SessionTime' in pos_data.columns else None
                            
                            if has_time and time_column:
                                print(f"   [SUCCESS] 時間數據: 可用 (使用 {time_column} 欄位)")
                            else:
                                print(f"   [WARNING] 時間數據: 不可用，將使用點索引")
                            
                            for i in range(total_points):
                                row = pos_data.iloc[i]
                                distance = distances[i] if i < len(distances) else 0
                                
                                # 提取時間數據（秒為單位）
                                time_seconds = 0.0
                                if has_time and time_column:
                                    try:
                                        time_val = getattr(row, time_column, 0)
                                        # 處理 pandas Timedelta
                                        if hasattr(time_val, 'total_seconds'):
                                            time_seconds = float(time_val.total_seconds())
                                        else:
                                            time_seconds = float(time_val)
                                    except:
                                        time_seconds = 0.0
                                
                                # 包含距離、位置X、位置Y、時間戳
                                record = {
                                    "point_index": i + 1,
                                    "distance_m": float(distance),
                                    "position_x": float(getattr(row, 'X', 0)),
                                    "position_y": float(getattr(row, 'Y', 0)),
                                    "time_seconds": time_seconds
                                }
                                position_data["position_records"].append(record)
                            
                            # 計算賽道邊界
                            x_coords = pos_data['X'].values
                            y_coords = pos_data['Y'].values
                            position_data["track_bounds"] = {
                                "x_min": float(np.min(x_coords)),
                                "x_max": float(np.max(x_coords)),
                                "y_min": float(np.min(y_coords)),
                                "y_max": float(np.max(y_coords))
                            }
                            
                            # 計算總距離
                            if len(distances) > 0:
                                position_data["distance_covered"] = float(np.max(distances))
                            
                            # 新增：映射 FastF1 官方彎道到遙測距離
                            try:
                                print(f"\n   [INFO] 嘗試獲取 FastF1 官方彎道資訊...")
                                official_corners_data = _map_official_corners_to_telemetry(
                                    session, pos_data, distances
                                )
                                if official_corners_data:
                                    position_data["official_corners"] = official_corners_data
                                    print(f"   [SUCCESS] 成功映射 {official_corners_data['count']} 個官方彎道")
                                else:
                                    print(f"   [WARNING] 無法獲取官方彎道資訊")
                            except Exception as corner_error:
                                print(f"   [WARNING] 官方彎道映射失敗: {corner_error}")
                            
                            print(f"   [SUCCESS] 成功獲取 {len(position_data['position_records'])} 個賽道位置點")
                        
                        else:
                            print("\n[ERROR] 位置數據中沒有 X, Y 座標")
                            # 嘗試備用方法：使用車輛數據中的位置信息
                            if not car_data.empty and 'X' in car_data.columns and 'Y' in car_data.columns:
                                print("[REFRESH] 嘗試使用車輛數據中的位置信息...")
                                return extract_position_from_car_data(car_data, position_data)
                            else:
                                return position_data
                    
                    except Exception as pos_error:
                        print(f"   [WARNING] 獲取位置數據失敗: {pos_error}")
                        # 嘗試備用方法：使用車輛數據
                        if not car_data.empty and 'X' in car_data.columns and 'Y' in car_data.columns:
                            print("[REFRESH] 嘗試使用車輛數據中的位置信息...")
                            return extract_position_from_car_data(car_data, position_data)
                        else:
                            return position_data
                
                else:
                    print("\n[ERROR] 無法獲取最快圈的FastF1詳細數據")
                    return position_data
            
            else:
                print("\n[ERROR] 無法找到該車手的FastF1圈速數據")
                return position_data
        
        except Exception as e:
            print(f"\n[ERROR] FastF1位置數據獲取失敗: {e}")
            return position_data
            
    except Exception as e:
        print(f"\n[ERROR] 賽道位置數據分析失敗: {e}")
        return position_data
    
    return position_data


def calculate_distances_from_positions(x_coords, y_coords):
    """從位置座標計算累積距離"""
    distances = [0]
    for i in range(1, len(x_coords)):
        dx = x_coords[i] - x_coords[i-1]
        dy = y_coords[i] - y_coords[i-1]
        distance_delta = np.sqrt(dx**2 + dy**2)
        distances.append(distances[-1] + distance_delta)
    return np.array(distances)


def extract_position_from_car_data(car_data, position_data):
    """從車輛數據中提取位置信息的輔助函數"""
    try:
        position_data["has_position_data"] = True
        print(f"   [SUCCESS] 車輛位置數據 (X, Y): 可用")
        
        # 檢查距離數據
        has_distance = 'Distance' in car_data.columns
        print(f"   [SUCCESS] 距離數據: {'可用' if has_distance else '需計算'}")
        
        # 計算距離
        if has_distance:
            distances = car_data['Distance'].values
            print(f"   [SUCCESS] 使用FastF1官方距離數據")
        else:
            # 基於位置計算累積距離
            distances = calculate_distances_from_positions(
                car_data['X'].values, 
                car_data['Y'].values
            )
            print(f"   [WARNING] 基於位置計算距離")
        
        # 檢查是否有時間數據
        has_time = 'Time' in car_data.columns or 'SessionTime' in car_data.columns
        time_column = 'Time' if 'Time' in car_data.columns else 'SessionTime' if 'SessionTime' in car_data.columns else None
        
        if has_time and time_column:
            print(f"   [SUCCESS] 時間數據: 可用 (使用 {time_column} 欄位)")
        else:
            print(f"   [WARNING] 時間數據: 不可用，將使用點索引")
        
        # ✅ 使用完整車輛位置數據（不再限制採樣）
        total_points = len(car_data)
        
        print(f"   [INFO] 處理 {total_points} 個車輛位置點（使用完整數據）")
        
        for i in range(total_points):
            row = car_data.iloc[i]
            distance = distances[i] if i < len(distances) else 0
            
            # 提取時間數據（秒為單位）
            time_seconds = 0.0
            if has_time and time_column:
                try:
                    time_val = getattr(row, time_column, 0)
                    # 處理 pandas Timedelta
                    if hasattr(time_val, 'total_seconds'):
                        time_seconds = float(time_val.total_seconds())
                    else:
                        time_seconds = float(time_val)
                except:
                    time_seconds = 0.0
            
            # 包含距離、位置X、位置Y、時間戳
            record = {
                "point_index": i + 1,
                "distance_m": float(distance),
                "position_x": float(getattr(row, 'X', 0)),
                "position_y": float(getattr(row, 'Y', 0)),
                "time_seconds": time_seconds
            }
            position_data["position_records"].append(record)
        
        # 計算賽道邊界
        x_coords = car_data['X'].values
        y_coords = car_data['Y'].values
        position_data["track_bounds"] = {
            "x_min": float(np.min(x_coords)),
            "x_max": float(np.max(x_coords)),
            "y_min": float(np.min(y_coords)),
            "y_max": float(np.max(y_coords))
        }
        
        # 計算總距離
        if len(distances) > 0:
            position_data["distance_covered"] = float(np.max(distances))
        
        print(f"   [SUCCESS] 成功獲取 {len(position_data['position_records'])} 個位置點")
        return position_data
        
    except Exception as e:
        print(f"   [ERROR] 車輛位置數據提取失敗: {e}")
        return position_data


def display_position_table(position_data):
    """顯示位置數據表格 - 包含距離、位置X、位置Y、時間戳"""
    if not position_data["has_position_data"] or not position_data["position_records"]:
        print("\n[ERROR] 沒有FastF1位置數據可顯示")
        return
    
    # 檢查是否有時間數據
    has_time = any(record.get('time_seconds', 0) > 0 for record in position_data["position_records"])
    
    print(f"\n[INFO] FastF1賽道位置數據表格 ({'包含時間戳' if has_time else '僅座標資料'}):")
    
    table = PrettyTable()
    if has_time:
        table.field_names = ["點", "距離(m)", "位置X", "位置Y", "時間(s)"]
    else:
        table.field_names = ["點", "距離(m)", "位置X", "位置Y"]
    table.align = "c"
    table.float_format = ".1"
    
    for record in position_data["position_records"]:
        if has_time:
            table.add_row([
                record["point_index"],
                f"{record['distance_m']:.0f}",
                f"{record['position_x']:.1f}",
                f"{record['position_y']:.1f}",
                f"{record.get('time_seconds', 0.0):.3f}"
            ])
        else:
            table.add_row([
                record["point_index"],
                f"{record['distance_m']:.0f}",
                f"{record['position_x']:.1f}",
                f"{record['position_y']:.1f}"
            ])
    
    print(table)


def display_position_statistics(position_data):
    """顯示位置統計分析 - 僅基於FastF1真實數據"""
    print(f"\n[STATS] FastF1賽道位置統計分析:")
    
    if position_data["fastest_lap_info"]:
        lap_info = position_data["fastest_lap_info"]
        formatted_time = format_time(lap_info['lap_time'])
        print(f"   🏆 最快圈: {lap_info['driver']} - 第{lap_info['lap_number']}圈 ({formatted_time})")
    
    if position_data["track_bounds"]:
        bounds = position_data["track_bounds"]
        track_width = bounds["x_max"] - bounds["x_min"]
        track_height = bounds["y_max"] - bounds["y_min"]
        print(f"   📏 賽道尺寸: {track_width:.0f}m × {track_height:.0f}m")
        print(f"   [PIN] X座標範圍: {bounds['x_min']:.1f}m ~ {bounds['x_max']:.1f}m")
        print(f"   [PIN] Y座標範圍: {bounds['y_min']:.1f}m ~ {bounds['y_max']:.1f}m")
    
    if position_data["distance_covered"]:
        print(f"   [FINISH] 圈長: {position_data['distance_covered']:.0f}m ({position_data['distance_covered']/1000:.3f}km)")
    
    if position_data["position_records"]:
        print(f"   [INFO] FastF1數據點數: {len(position_data['position_records'])} 個")
        distances = [r["distance_m"] for r in position_data["position_records"]]
        print(f"   [TEST] 距離範圍: {min(distances):.0f}m - {max(distances):.0f}m")


def save_position_raw_data(session_info, position_data):
    """保存位置分析Raw Data - 包含時間戳資訊"""
    
    # 清理不能序列化的數據類型
    def clean_for_json(obj):
        if isinstance(obj, (list, tuple)):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, bool):
            return bool(obj)
        elif obj is None or isinstance(obj, (str, int, float)):
            return obj
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return str(obj)
    
    # 檢查是否有時間數據
    has_time_data = any(record.get('time_seconds', 0) > 0 for record in position_data["position_records"])
    
    raw_data = {
        "analysis_type": "track_position_analysis",
        "function": "2",
        "timestamp": datetime.now().strftime("%Y%m%d"),
        "session_info": clean_for_json(session_info),
        "position_analysis": {
            "has_position_data": bool(position_data["has_position_data"]),
            "has_time_data": has_time_data,
            "time_reference": "seconds_from_lap_start" if has_time_data else "none",
            "fastest_lap_info": clean_for_json(position_data["fastest_lap_info"]),
            "track_bounds": clean_for_json(position_data["track_bounds"]),
            "distance_covered_m": float(position_data["distance_covered"]),
            "total_position_records": len(position_data["position_records"])
        },
        "detailed_position_records": clean_for_json(position_data["position_records"])
    }
    
    # 確保json資料夾存在
    import os
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    # 檔案命名格式：raw_data_track_position_YYYY_賽事.json
    # 使用賽事名稱（如 "Chinese Grand Prix"）
    year = session_info.get('year', 2025)
    race_name = session_info.get('race', 'Unknown')
    
    raw_data_file = os.path.join(json_dir, f"raw_data_track_position_{year}_{race_name}.json")
    
    try:
        with open(raw_data_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVE] Raw Data 已保存: {raw_data_file}")
        if has_time_data:
            print(f"[INFO] 時間戳資訊已包含於 JSON 檔案中")
    except Exception as e:
        print(f"\n[ERROR] Raw Data 保存失敗: {e}")


if __name__ == "__main__":
    # 測試用途
    print("[TRACK] 賽道位置分析模組 - 測試模式")
    run_track_position_analysis(None)
