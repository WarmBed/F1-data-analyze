"""
通用 F1 賽道數據生成器
支援任何賽道，整合 FastF1 + GeoJSON 高程數據

Author: GitHub Copilot
Date: 2025-11-09
"""

import json
import numpy as np
import fastf1
from pathlib import Path
from scipy.interpolate import interp1d
import sys


def find_geojson_file(country_code: str):
    """
    尋找對應國家的 GeoJSON 高程檔案
    
    Args:
        country_code: 國家代碼（如 'jp', 'mc', 'it' 等）
    
    Returns:
        Path 或 None
    """
    geo_path = Path("json/f1-circuits-master/circuit_data")
    
    if not geo_path.exists():
        return None
    
    # 尋找符合的檔案
    pattern = f"{country_code.lower()}_*_elevation_data.json"
    files = list(geo_path.glob(pattern))
    
    if files:
        return files[0]
    
    return None


def load_geojson_elevation_data(geojson_file: Path):
    """載入 GeoJSON 高程數據"""
    try:
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        coordinates = data.get('coordinates', [])
        
        if not coordinates:
            return None
        
        distances = []
        elevations = []
        
        for coord in coordinates:
            distance_km = coord.get('distance_km', 0.0)
            elevation = coord.get('elevation', 0.0)
            distances.append(distance_km * 1000)
            elevations.append(elevation)
        
        return {
            'distances': np.array(distances),
            'elevations': np.array(elevations),
            'min_elevation': float(min(elevations)),
            'max_elevation': float(max(elevations)),
            'elevation_change': float(max(elevations) - min(elevations))
        }
        
    except Exception as e:
        print(f"   ⚠️  載入 GeoJSON 失敗: {e}")
        return None


def generate_circuit_data(year: int, race: str, session: str = 'R', country_code: str = None, 
                         fix_elevation: bool = False, official_elevation_change: float = None):
    """
    生成賽道數據
    
    Args:
        year: 賽季年份
        race: 賽事名稱（如 'Monaco', 'Japan', 'Italy'）
        session: 賽事階段（'R', 'Q', 'FP1' 等）
        country_code: 國家代碼（如 'mc', 'jp'），用於尋找 GeoJSON
        fix_elevation: 是否修正高程數據（移除負值）
        official_elevation_change: F1 官方高程變化（用於驗證和修正）
    
    Returns:
        dict: 賽道數據
    """
    print(f"\n{'='*70}")
    print(f"🏎️  生成 {year} {race} 賽道數據")
    print(f"{'='*70}\n")
    
    # 啟用緩存
    cache_path = Path(__file__).parent / "f1_analysis_cache"
    cache_path.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))
    
    try:
        # 載入 FastF1 數據
        print(f"🔄 正在載入 FastF1 數據...")
        session_obj = fastf1.get_session(year, race, session)
        print(f"   ✅ {session_obj.event['EventName']} - {session_obj.name}")
        
        session_obj.load()
        print(f"   ✅ Session 數據載入完成")
        
        # 取得最快圈
        laps = session_obj.laps
        fastest_lap = laps.pick_fastest()
        
        if fastest_lap is None or fastest_lap.empty:
            print(f"   ❌ 找不到最快圈")
            return None
        
        driver_code = fastest_lap['Driver']
        lap_time = fastest_lap['LapTime']
        print(f"   ✅ 最快圈: {driver_code} - {lap_time}")
        
        # 取得位置數據
        pos_data = fastest_lap.get_pos_data()
        
        if pos_data is None or pos_data.empty:
            print(f"   ❌ 無法獲取位置數據")
            return None
        
        print(f"   ✅ 位置數據: {len(pos_data)} 個點")
        
        # 計算距離
        if 'Distance' in pos_data.columns:
            distances = pos_data['Distance'].values
        else:
            x_vals = pos_data['X'].values
            y_vals = pos_data['Y'].values
            dx = np.diff(x_vals)
            dy = np.diff(y_vals)
            segment_distances = np.sqrt(dx**2 + dy**2)
            distances = np.concatenate([[0], np.cumsum(segment_distances)])
        
        # 取樣
        sample_size = min(100, len(pos_data))
        sample_indices = np.linspace(0, len(pos_data)-1, sample_size, dtype=int)
        
        # 構建 track outline
        track_outline = []
        for idx in sample_indices:
            row = pos_data.iloc[idx]
            point = {
                "x": float(row['X']),
                "y": float(row['Y']),
                "distance_m": float(distances[idx])
            }
            track_outline.append(point)
        
        print(f"   ✅ Track outline: {len(track_outline)} 個點")
        
        # === 整合 GeoJSON 高程 ===
        elevation_data = None
        
        if country_code:
            geojson_file = find_geojson_file(country_code)
            
            if geojson_file:
                print(f"\n   🔄 載入 GeoJSON: {geojson_file.name}")
                elevation_data = load_geojson_elevation_data(geojson_file)
                
                if elevation_data:
                    print(f"      高程範圍: {elevation_data['min_elevation']:.1f}m ~ {elevation_data['max_elevation']:.1f}m")
                    print(f"      高程變化: {elevation_data['elevation_change']:.1f}m")
                    
                    # 修正負值高程（如果啟用）
                    if fix_elevation and elevation_data['min_elevation'] < 0:
                        offset = abs(elevation_data['min_elevation'])
                        print(f"      ⚠️  檢測到負值高程，向上偏移 {offset:.1f}m")
                        elevation_data['elevations'] += offset
                        elevation_data['min_elevation'] = float(np.min(elevation_data['elevations']))
                        elevation_data['max_elevation'] = float(np.max(elevation_data['elevations']))
                        elevation_data['elevation_change'] = elevation_data['max_elevation'] - elevation_data['min_elevation']
                        print(f"      ✅ 修正後: {elevation_data['min_elevation']:.1f}m ~ {elevation_data['max_elevation']:.1f}m (Δ{elevation_data['elevation_change']:.1f}m)")
                    
                    # 驗證官方數據（如果提供）
                    if official_elevation_change:
                        diff = abs(elevation_data['elevation_change'] - official_elevation_change)
                        if diff > 10:
                            print(f"      ⚠️  警告: 與 F1 官方數據差異 {diff:.1f}m (官方: {official_elevation_change:.0f}m)")
                        else:
                            print(f"      ✅ 與 F1 官方數據吻合 (官方: {official_elevation_change:.0f}m, 差異: {diff:.1f}m)")
                    
                    # 插值高程
                    track_length = elevation_data['distances'][-1]
                    print(f"      賽道長度: {track_length:.1f}m")
                    
                    interp_func = interp1d(
                        elevation_data['distances'],
                        elevation_data['elevations'],
                        kind='linear',
                        fill_value='extrapolate'
                    )
                    
                    for point in track_outline:
                        normalized_distance = point['distance_m'] % track_length
                        point['elevation'] = float(interp_func(normalized_distance))
                    
                    elevations = [p['elevation'] for p in track_outline]
                    print(f"   ✅ 插值後高程: {min(elevations):.1f}m ~ {max(elevations):.1f}m")
            else:
                print(f"   ⚠️  找不到 GeoJSON 檔案 (國家代碼: {country_code})")
        
        # 計算賽道邊界
        x_coords = pos_data['X'].values
        y_coords = pos_data['Y'].values
        track_bounds = {
            "x_min": float(np.min(x_coords)),
            "x_max": float(np.max(x_coords)),
            "y_min": float(np.min(y_coords)),
            "y_max": float(np.max(y_coords)),
            "width": float(np.max(x_coords) - np.min(x_coords)),
            "height": float(np.max(y_coords) - np.min(y_coords))
        }
        
        # 取得彎道資訊
        circuit_info = session_obj.get_circuit_info()
        official_corners = None
        
        if circuit_info and hasattr(circuit_info, 'corners'):
            corners_df = circuit_info.corners
            
            if corners_df is not None and len(corners_df) > 0:
                print(f"\n   🔄 處理 {len(corners_df)} 個彎道...")
                
                corners_list = []
                for idx, corner_row in corners_df.iterrows():
                    corner_x = float(corner_row['X'])
                    corner_y = float(corner_row['Y'])
                    
                    # 映射到最近的遙測點
                    dist_to_corner = np.sqrt(
                        (x_coords - corner_x)**2 + 
                        (y_coords - corner_y)**2
                    )
                    closest_idx = int(np.argmin(dist_to_corner))
                    
                    corner_data = {
                        "number": int(corner_row['Number']),
                        "x": corner_x,
                        "y": corner_y,
                        "angle": float(corner_row['Angle']),
                        "mapped_distance": float(distances[closest_idx]),
                        "mapping_error": float(dist_to_corner[closest_idx])
                    }
                    
                    if 'Letter' in corner_row.index and corner_row['Letter'] != '':
                        corner_data["letter"] = str(corner_row['Letter'])
                    
                    corners_list.append(corner_data)
                
                errors = [c['mapping_error'] for c in corners_list]
                
                official_corners = {
                    "available": True,
                    "count": len(corners_list),
                    "corners": corners_list,
                    "mapping_quality": {
                        "average_error_m": round(float(np.mean(errors)), 1),
                        "max_error_m": round(float(np.max(errors)), 1),
                        "min_error_m": round(float(np.min(errors)), 1)
                    }
                }
                
                print(f"   ✅ 彎道映射完成 (平均誤差: {np.mean(errors):.1f}m)")
        
        # 構建結果
        result = {
            "metadata": {
                "source": "FastF1 + GeoJSON",
                "year": year,
                "race": race,
                "session": session,
                "coordinate_system": "FastF1 Circuit Coordinates (X/Y meters)",
                "fastest_lap_driver": str(driver_code),
                "fastest_lap_time": str(lap_time),
                "total_distance_m": float(np.max(distances)),
                "data_points": len(pos_data),
                "sampled_points": len(track_outline)
            },
            "track_outline": {
                "coordinates": track_outline,
                "point_count": len(track_outline)
            },
            "track_bounds": track_bounds
        }
        
        if elevation_data:
            result["elevation_profile"] = {
                "available": True,
                "min_elevation": elevation_data['min_elevation'],
                "max_elevation": elevation_data['max_elevation'],
                "elevation_change": elevation_data['elevation_change'],
                "data_source": f"GeoJSON ({geojson_file.name})"
            }
        else:
            result["elevation_profile"] = {"available": False}
        
        if official_corners:
            result["official_corners"] = official_corners
        else:
            result["official_corners"] = {"available": False, "count": 0, "corners": []}
        
        return result
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主程式"""
    # 預設參數
    year = 2024
    race = "Monaco"
    session = "R"
    country_code = "mc"
    fix_elevation = False
    official_elevation_change = None
    
    # F1 官方高程數據（參考來源）
    official_elevations = {
        'Monaco': 42,      # https://www.formula1.com/
        'Spa': 103,        # Eau Rouge 爬升
        'COTA': 41,        # 德州
        'Interlagos': 30,  # 巴西
        'Suzuka': 50,      # 日本（估計）
    }
    
    # 命令列參數
    if len(sys.argv) > 1:
        race = sys.argv[1]
    if len(sys.argv) > 2:
        country_code = sys.argv[2]
    if len(sys.argv) > 3:
        year = int(sys.argv[3])
    if len(sys.argv) > 4:
        fix_elevation = sys.argv[4].lower() in ['true', '1', 'yes']
    
    # 設定官方高程數據
    if race in official_elevations:
        official_elevation_change = official_elevations[race]
    
    # 生成數據
    data = generate_circuit_data(year, race, session, country_code, fix_elevation, official_elevation_change)
    
    if data is None:
        print("\n❌ 數據生成失敗")
        return
    
    # 輸出摘要
    print(f"\n{'='*70}")
    print("📊 數據摘要")
    print(f"{'='*70}")
    print(f"   賽道輪廓: {data['track_outline']['point_count']} 點")
    print(f"   官方彎道: {data['official_corners']['count']} 個")
    print(f"   賽道範圍: {data['track_bounds']['width']:.1f}m × {data['track_bounds']['height']:.1f}m")
    print(f"   總距離: {data['metadata']['total_distance_m']:.1f}m")
    
    if data['elevation_profile']['available']:
        elev = data['elevation_profile']
        print(f"   高程範圍: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m (Δ{elev['elevation_change']:.1f}m)")
    else:
        print(f"   高程數據: 無")
    
    # 儲存
    output_file = f"{race.lower()}_circuit_{year}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已儲存至: {output_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
