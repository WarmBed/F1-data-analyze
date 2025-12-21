"""
生成基於 FastF1 原生坐標的日本電路 JSON
使用 FastF1 的 position_records 和 official_corners，確保坐標系統一致
並整合 GeoJSON 的高程數據

Author: GitHub Copilot
Date: 2025-10-XX
"""

import json
import numpy as np
import fastf1
from pathlib import Path
from scipy.interpolate import interp1d

def load_geojson_elevation_data():
    """
    從 GeoJSON 載入高程數據
    
    Returns:
        dict: 包含 distance 和 elevation 的字典
    """
    geojson_path = Path("json/f1-circuits-master/circuit_data/jp_1962_elevation_data.json")
    
    if not geojson_path.exists():
        print(f"   ⚠️  找不到 GeoJSON 高程檔案: {geojson_path}")
        return None
    
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        coordinates = data.get('coordinates', [])
        
        if not coordinates:
            print(f"   ⚠️  GeoJSON 無高程數據")
            return None
        
        # 提取距離和高程
        distances = []
        elevations = []
        
        for coord in coordinates:
            distance_km = coord.get('distance_km', 0.0)
            elevation = coord.get('elevation', 0.0)
            distances.append(distance_km * 1000)  # 轉換為米
            elevations.append(elevation)
        
        print(f"   ✅ GeoJSON 高程數據: {len(elevations)} 個點")
        print(f"      高程範圍: {min(elevations):.1f}m ~ {max(elevations):.1f}m")
        
        return {
            'distances': np.array(distances),
            'elevations': np.array(elevations),
            'min_elevation': float(min(elevations)),
            'max_elevation': float(max(elevations)),
            'elevation_change': float(max(elevations) - min(elevations))
        }
        
    except Exception as e:
        print(f"   ⚠️  載入 GeoJSON 高程失敗: {e}")
        return None


def load_fastf1_track_data(year: int = 2025):
    """
    從 FastF1 載入賽道輪廓和彎道數據
    
    Args:
        year: 賽季年份
    
    Returns:
        dict: 包含 track_outline 和 official_corners 的字典
    """
    print(f"\n🔄 正在載入 FastF1 {year} 年日本 GP 數據...")
    
    # 啟用緩存
    cache_path = Path(__file__).parent / "f1_analysis_cache"
    cache_path.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))
    
    try:
        # 載入賽事 session
        session = fastf1.get_session(year, 'Japan', 'R')
        print(f"   ✅ Session: {session.event['EventName']} - {session.name}")
        
        # 載入 session 數據
        print(f"   🔄 正在載入 session 數據...")
        session.load()
        print(f"   ✅ Session 數據載入完成")
        
        # 取得最快圈的 telemetry 作為 track outline
        print(f"\n   🔍 尋找最快圈...")
        laps = session.laps
        fastest_lap = laps.pick_fastest()
        
        if fastest_lap is None or fastest_lap.empty:
            print(f"   ❌ 找不到最快圈數據")
            return None
        
        driver_code = fastest_lap['Driver']
        lap_time = fastest_lap['LapTime']
        print(f"   ✅ 最快圈: {driver_code} - {lap_time}")
        
        # 取得位置數據
        print(f"\n   🔄 正在提取賽道輪廓 (X, Y 座標)...")
        pos_data = fastest_lap.get_pos_data()
        
        if pos_data is None or pos_data.empty:
            print(f"   ❌ 無法獲取位置數據")
            return None
        
        print(f"   ✅ 總共 {len(pos_data)} 個位置點")
        
        # 取樣以減少數據量（每 10 個點取 1 個）
        sample_size = len(pos_data) // 10
        if sample_size < 100:
            sample_size = min(100, len(pos_data))
        
        sample_indices = np.linspace(0, len(pos_data)-1, sample_size, dtype=int)
        print(f"   🔄 取樣 {sample_size} 個點...")
        
        # 計算距離（如果沒有 Distance 欄位）
        if 'Distance' in pos_data.columns:
            distances = pos_data['Distance'].values
            print(f"   ✅ 使用 FastF1 官方距離數據")
        else:
            # 計算累積距離
            x_vals = pos_data['X'].values
            y_vals = pos_data['Y'].values
            dx = np.diff(x_vals)
            dy = np.diff(y_vals)
            segment_distances = np.sqrt(dx**2 + dy**2)
            distances = np.concatenate([[0], np.cumsum(segment_distances)])
            print(f"   ⚠️  基於 X/Y 座標計算距離")
        
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
        
        # === 整合 GeoJSON 高程數據 ===
        print(f"\n   🔄 整合 GeoJSON 高程數據...")
        elevation_data = load_geojson_elevation_data()
        
        if elevation_data:
            # 創建插值函數（基於距離映射高程）
            try:
                # 取得賽道一圈的長度
                track_length = elevation_data['distances'][-1]
                print(f"   🔍 賽道長度: {track_length:.1f}m")
                
                interp_func = interp1d(
                    elevation_data['distances'],
                    elevation_data['elevations'],
                    kind='linear',
                    fill_value='extrapolate'
                )
                
                # 為每個 track outline 點添加高程
                # 使用模運算將 FastF1 的累積距離映射回一圈內
                for point in track_outline:
                    # 將距離映射到 [0, track_length] 範圍
                    normalized_distance = point['distance_m'] % track_length
                    point['elevation'] = float(interp_func(normalized_distance))
                
                print(f"   ✅ 成功為 {len(track_outline)} 個點添加高程數據")
                
                # 驗證高程範圍
                elevations = [p['elevation'] for p in track_outline]
                print(f"   🔍 插值後高程範圍: {min(elevations):.1f}m ~ {max(elevations):.1f}m")
                
            except Exception as e:
                print(f"   ⚠️  高程插值失敗: {e}")
                elevation_data = None
        
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
        print(f"   ✅ Track bounds: X({track_bounds['x_min']:.1f} ~ {track_bounds['x_max']:.1f}), "
              f"Y({track_bounds['y_min']:.1f} ~ {track_bounds['y_max']:.1f})")
        
        # 取得官方彎道資訊
        print(f"\n   🔄 正在提取官方彎道資訊...")
        circuit_info = session.get_circuit_info()
        
        if circuit_info is None or not hasattr(circuit_info, 'corners'):
            print(f"   ⚠️  無法獲取彎道資訊")
            official_corners = None
        else:
            corners_df = circuit_info.corners
            
            if corners_df is None or len(corners_df) == 0:
                print(f"   ⚠️  彎道資訊為空")
                official_corners = None
            else:
                print(f"   ✅ 找到 {len(corners_df)} 個彎道")
                
                # 映射彎道到遙測距離（找最近的位置點）
                corners_list = []
                for idx, corner_row in corners_df.iterrows():
                    corner_x = float(corner_row['X'])
                    corner_y = float(corner_row['Y'])
                    corner_num = int(corner_row['Number'])
                    corner_angle = float(corner_row['Angle'])
                    
                    # 計算到每個遙測點的距離
                    dist_to_corner = np.sqrt(
                        (x_coords - corner_x)**2 + 
                        (y_coords - corner_y)**2
                    )
                    closest_idx = int(np.argmin(dist_to_corner))
                    mapping_error = float(dist_to_corner[closest_idx])
                    mapped_distance = float(distances[closest_idx])
                    
                    corner_data = {
                        "number": corner_num,
                        "x": corner_x,
                        "y": corner_y,
                        "angle": corner_angle,
                        "mapped_distance": mapped_distance,
                        "mapping_error": mapping_error
                    }
                    
                    # 添加 Letter 欄位（如果有）
                    if 'Letter' in corner_row.index and corner_row['Letter'] != '':
                        corner_data["letter"] = str(corner_row['Letter'])
                    
                    corners_list.append(corner_data)
                    print(f"      彎道 {corner_num}: X={corner_x:.1f}, Y={corner_y:.1f}, "
                          f"Distance={mapped_distance:.1f}m (誤差: {mapping_error:.1f}m)")
                
                # 計算映射品質
                errors = [c['mapping_error'] for c in corners_list]
                avg_error = np.mean(errors)
                max_error = np.max(errors)
                
                official_corners = {
                    "available": True,
                    "count": len(corners_list),
                    "corners": corners_list,
                    "mapping_quality": {
                        "average_error_m": round(float(avg_error), 1),
                        "max_error_m": round(float(max_error), 1),
                        "min_error_m": round(float(np.min(errors)), 1)
                    }
                }
                
                print(f"   ✅ 映射品質: 平均誤差 {avg_error:.1f}m, 最大誤差 {max_error:.1f}m")
        
        # 構建完整數據
        result = {
            "metadata": {
                "source": "FastF1 + GeoJSON Elevation",
                "year": year,
                "race": "Japan",
                "session": "R",
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
        
        # 添加高程資訊（如果有）
        if elevation_data:
            result["elevation_profile"] = {
                "available": True,
                "min_elevation": elevation_data['min_elevation'],
                "max_elevation": elevation_data['max_elevation'],
                "elevation_change": elevation_data['elevation_change'],
                "data_source": "GeoJSON (jp_1962)"
            }
        else:
            result["elevation_profile"] = {
                "available": False
            }
        
        if official_corners:
            result["official_corners"] = official_corners
        else:
            result["official_corners"] = {
                "available": False,
                "count": 0,
                "corners": []
            }
        
        return result
        
    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_json(data: dict, output_path: str):
    """
    儲存 JSON 檔案
    
    Args:
        data: 數據字典
        output_path: 輸出路徑
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON 已儲存至: {output_path}")


def main():
    """主程式"""
    print("=" * 70)
    print("🏎️  FastF1 日本電路數據生成器")
    print("=" * 70)
    
    # 載入 FastF1 數據
    data = load_fastf1_track_data(year=2025)
    
    if data is None:
        print("\n❌ 數據載入失敗")
        return
    
    # 輸出摘要
    print("\n" + "=" * 70)
    print("📊 數據摘要")
    print("=" * 70)
    print(f"   賽道輪廓點數: {data['track_outline']['point_count']}")
    print(f"   官方彎道數量: {data['official_corners']['count']}")
    print(f"   賽道範圍: {data['track_bounds']['width']:.1f}m × {data['track_bounds']['height']:.1f}m")
    print(f"   總距離: {data['metadata']['total_distance_m']:.1f}m")
    
    # 顯示高程資訊
    if data['elevation_profile']['available']:
        elev = data['elevation_profile']
        print(f"   高程範圍: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m")
        print(f"   高程變化: {elev['elevation_change']:.1f}m")
    else:
        print(f"   高程數據: 不可用")
    
    # 儲存 JSON
    output_path = "japan_circuit_fastf1_2025.json"
    save_json(data, output_path)
    
    print("\n" + "=" * 70)
    print("✅ 完成！")
    print("=" * 70)
    print(f"\n💡 提示: 此 JSON 使用 FastF1 原生坐標系統")
    print(f"   - track_outline 和 official_corners 使用相同的 X/Y 座標系")
    print(f"   - 可直接用於 TrackMapWidget 顯示")
    print(f"   - 彎道標註將正確對齊賽道輪廓")


if __name__ == "__main__":
    main()
