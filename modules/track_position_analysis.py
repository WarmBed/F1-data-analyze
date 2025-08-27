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
    print(f"� 開始執行賽道位置分析...")
    print(f"�🛣️ F1 賽道位置分析 (功能2)")
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
        print("📦 使用緩存數據")
        position_data = cached_data
        
        # 結果驗證和反饋
        if not report_analysis_results(position_data, "賽道位置分析"):
            return None
        
        print(f"\n✅ 賽道位置分析分析完成！")
        return {
            "success": True,
            "data": position_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "2"
        }
        
    elif cached_data and show_detailed_output:
        print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
        position_data = cached_data
        
        # 結果驗證和反饋
        if not report_analysis_results(position_data, "賽道位置分析"):
            return None
            
        # 顯示詳細輸出 - 即使使用緩存
        _display_cached_detailed_output(position_data, session_info)
        
        print(f"\n✅ 賽道位置分析分析完成！")
        return {
            "success": True,
            "data": position_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "2"
        }
    else:
        print("🔄 重新計算 - 開始數據分析...")
        # 分析賽道位置數據
        position_data = analyze_track_position_data(data_loader)
        
        if not position_data:
            print("❌ 賽道位置分析失敗：無可用數據")
            return None
        
        # 保存緩存
        save_cache(position_data, cache_key)
        print("💾 分析結果已緩存")
    
    # 結果驗證和反饋
    if not report_analysis_results(position_data, "賽道位置分析"):
        return None
    
    # 顯示位置數據表格
    display_position_table(position_data)
    
    # 顯示分析統計
    display_position_statistics(position_data)
    
    # 保存Raw Data
    save_position_raw_data(session_info, position_data)
    
    print(f"\n✅ 賽道位置分析分析完成！")
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
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    data_count = len(data.get('position_records', [])) if data else 0
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 數據項目數量: {data_count}")
    print(f"   • 數據完整性: {'✅ 良好' if data_count > 0 else '❌ 不足'}")
    
    # 檢查關鍵欄位
    if data and 'position_records' in data:
        missing_coords = sum(1 for r in data['position_records'] if not (r.get('position_x') and r.get('position_y')))
        print(f"   • 缺失座標點: {missing_coords}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True


def _display_cached_detailed_output(position_data, session_info):
    """當使用緩存數據但需要顯示詳細輸出時調用此函數"""
    print("\n📊 顯示緩存的詳細分析結果...")
    
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
    session_info = {
        "year": getattr(data_loader, 'year', 'Unknown'),
        "race": getattr(data_loader, 'race', 'Unknown'),
        "session_type": getattr(data_loader, 'session_type', 'Unknown'),
        "track_name": "Unknown",
        "date": "Unknown"
    }
    
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        try:
            session = data_loader.session
            session_info["track_name"] = getattr(session, 'event', {}).get('EventName', 'Unknown')
            session_info["date"] = str(getattr(session, 'date', 'Unknown'))
        except:
            pass
    
    return session_info


def print_session_summary(session_info):
    """顯示賽事摘要信息"""
    print(f"\n[LIST] 賽事信息摘要:")
    print(f"   📅 賽季: {session_info['year']}")
    print(f"   [FINISH] 賽事: {session_info['race']}")
    print(f"   🏎️ 賽段: {session_info['session_type']}")
    print(f"   🏟️ 賽道: {session_info['track_name']}")
    print(f"   📆 日期: {session_info['date']}")


def analyze_track_position_data(data_loader):
    """分析賽道位置數據 - 僅使用FastF1真實數據"""
    position_data = {
        "has_position_data": False,
        "position_records": [],
        "fastest_lap_info": None,
        "track_bounds": None,
        "distance_covered": 0
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
                            
                            # 處理位置記錄 - 取樣以避免過多數據
                            total_points = len(pos_data)
                            sample_size = min(50, total_points)  # 最多取50個點
                            sample_indices = np.linspace(0, total_points-1, sample_size, dtype=int)
                            
                            print(f"   [INFO] 處理 {total_points} 個賽道位置點，取樣 {sample_size} 個")
                            
                            for i, idx in enumerate(sample_indices):
                                row = pos_data.iloc[idx]
                                distance = distances[idx] if idx < len(distances) else 0
                                
                                # 僅包含距離、位置X、位置Y
                                record = {
                                    "point_index": i + 1,
                                    "distance_m": float(distance),
                                    "position_x": float(getattr(row, 'X', 0)),
                                    "position_y": float(getattr(row, 'Y', 0))
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
                            
                            print(f"   [SUCCESS] 成功獲取 {len(position_data['position_records'])} 個賽道位置點")
                        
                        else:
                            print("\n[ERROR] 位置數據中沒有 X, Y 座標")
                            # 嘗試備用方法：使用車輛數據中的位置信息
                            if not car_data.empty and 'X' in car_data.columns and 'Y' in car_data.columns:
                                print("🔄 嘗試使用車輛數據中的位置信息...")
                                return extract_position_from_car_data(car_data, position_data)
                            else:
                                return position_data
                    
                    except Exception as pos_error:
                        print(f"   [WARNING] 獲取位置數據失敗: {pos_error}")
                        # 嘗試備用方法：使用車輛數據
                        if not car_data.empty and 'X' in car_data.columns and 'Y' in car_data.columns:
                            print("🔄 嘗試使用車輛數據中的位置信息...")
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
        
        # 處理位置記錄 - 取樣以避免過多數據
        total_points = len(car_data)
        sample_size = min(50, total_points)  # 最多取50個點
        sample_indices = np.linspace(0, total_points-1, sample_size, dtype=int)
        
        print(f"   [INFO] 處理 {total_points} 個車輛位置點，取樣 {sample_size} 個")
        
        for i, idx in enumerate(sample_indices):
            row = car_data.iloc[idx]
            distance = distances[idx] if idx < len(distances) else 0
            
            # 僅包含距離、位置X、位置Y
            record = {
                "point_index": i + 1,
                "distance_m": float(distance),
                "position_x": float(getattr(row, 'X', 0)),
                "position_y": float(getattr(row, 'Y', 0))
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
    """顯示位置數據表格 - 僅顯示距離、位置X、位置Y"""
    if not position_data["has_position_data"] or not position_data["position_records"]:
        print("\n[ERROR] 沒有FastF1位置數據可顯示")
        return
    
    print(f"\n[INFO] FastF1賽道位置數據表格 (僅距離、X、Y座標):")
    
    table = PrettyTable()
    table.field_names = ["點", "距離(m)", "位置X", "位置Y"]
    table.align = "c"
    table.float_format = ".1"
    
    for record in position_data["position_records"]:
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
        print(f"   📍 X座標範圍: {bounds['x_min']:.1f}m ~ {bounds['x_max']:.1f}m")
        print(f"   📍 Y座標範圍: {bounds['y_min']:.1f}m ~ {bounds['y_max']:.1f}m")
    
    if position_data["distance_covered"]:
        print(f"   [FINISH] 圈長: {position_data['distance_covered']:.0f}m ({position_data['distance_covered']/1000:.3f}km)")
    
    if position_data["position_records"]:
        print(f"   [INFO] FastF1數據點數: {len(position_data['position_records'])} 個")
        distances = [r["distance_m"] for r in position_data["position_records"]]
        print(f"   � 距離範圍: {min(distances):.0f}m - {max(distances):.0f}m")


def save_position_raw_data(session_info, position_data):
    """保存位置分析Raw Data"""
    
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
    
    raw_data = {
        "analysis_type": "track_position_analysis",
        "function": "2",
        "timestamp": datetime.now().strftime("%Y%m%d"),
        "session_info": clean_for_json(session_info),
        "position_analysis": {
            "has_position_data": bool(position_data["has_position_data"]),
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
    
    raw_data_file = os.path.join(json_dir, f"raw_data_track_position_{session_info['year']}_{session_info['race']}_{datetime.now().strftime('%Y%m%d')}.json")
    
    try:
        with open(raw_data_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Raw Data 已保存: {raw_data_file}")
    except Exception as e:
        print(f"\n[ERROR] Raw Data 保存失敗: {e}")


if __name__ == "__main__":
    # 測試用途
    print("🛣️ 賽道位置分析模組 - 測試模式")
    run_track_position_analysis(None)
