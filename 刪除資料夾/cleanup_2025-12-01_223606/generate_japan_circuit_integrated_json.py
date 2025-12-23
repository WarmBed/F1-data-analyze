#!/usr/bin/env python3
"""
生成整合型 Japan 賽道 JSON
整合 f1-circuits-master GeoJSON + FastF1 官方彎道數據

輸出：japan_circuit_integrated_2025.json
- GeoJSON 賽道輪廓（GPS 座標 + 高程）
- FastF1 官方彎道標註（X/Y 座標 + 編號）
"""

import json
import fastf1
from pathlib import Path
from datetime import datetime
import numpy as np

def load_geojson_data():
    """載入 f1-circuits-master 的 Japan 賽道 GeoJSON 數據"""
    geojson_path = Path("json/f1-circuits-master/circuit_data/jp_1962_elevation_data.json")
    
    print(f"📁 載入 GeoJSON 數據: {geojson_path}")
    
    if not geojson_path.exists():
        print(f"❌ 找不到檔案: {geojson_path}")
        return None
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 載入成功: {len(data.get('coordinates', []))} 個座標點")
    return data


def load_fastf1_corners(year=2025):
    """載入 FastF1 的 Japan 官方彎道數據"""
    print(f"\n🏁 載入 FastF1{year} Japan 彎道數據...")
    
    try:
        # 啟用緩存
        fastf1.Cache.enable_cache('f1_analysis_cache')
        
        # 載入 2025 Japan 賽事
        session = fastf1.get_session(year, 'Japan', 'R')
        print(f"📊 載入 Session: {session.event['EventName']} - {session.name}")
        
        # 載入 Session 數據
        session.load()
        print(f"✅ Session 數據載入完成")
        
        # 獲取賽道資訊
        circuit_info = session.get_circuit_info()
        
        if circuit_info is None or not hasattr(circuit_info, 'corners'):
            print(f"❌ 無法獲取賽道彎道資訊")
            return None, None
        
        corners = circuit_info.corners
        
        if corners is None or corners.empty:
            print(f"❌ 彎道數據為空")
            return None, None
        
        print(f"✅ 成功載入 {len(corners)} 個官方彎道")
        print(f"📋 彎道欄位: {list(corners.columns)}")
        
        # 顯示前 3 個彎道
        print(f"\n前 3 個彎道範例:")
        for idx, corner in corners.head(3).iterrows():
            print(f"  Turn {corner['Number']}: Distance={corner['Distance']:.1f}m, "
                  f"X={corner['X']:.1f}, Y={corner['Y']:.1f}, Angle={corner['Angle']:.1f}°")
        
        return corners, session.event
        
    except Exception as e:
        print(f"❌ 載入 FastF1 數據失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def convert_gps_to_xy(geojson_coords):
    """
    將 GPS 座標（經緯度）轉換為 X/Y 平面座標（米）
    使用簡單的墨卡托投影
    
    注意：這是近似轉換，適用於小範圍區域（賽道）
    """
    print(f"\n🔄 轉換 GPS 座標到 X/Y 平面座標...")
    
    if not geojson_coords:
        return []
    
    # 提取經緯度
    lons = [coord['lon'] for coord in geojson_coords]
    lats = [coord['lat'] for coord in geojson_coords]
    
    # 計算中心點
    center_lon = np.mean(lons)
    center_lat = np.mean(lats)
    
    print(f"📍 賽道中心點: ({center_lat:.6f}, {center_lon:.6f})")
    
    # 轉換為平面座標（米）
    # 使用簡單的墨卡托投影公式
    xy_coords = []
    
    for coord in geojson_coords:
        lon = coord['lon']
        lat = coord['lat']
        
        # 轉換為米（簡化公式）
        # 1 度經度 ≈ 111,320 * cos(lat) 米
        # 1 度緯度 ≈ 111,320 米
        x = (lon - center_lon) * 111320 * np.cos(np.radians(center_lat))
        y = (lat - center_lat) * 111320
        
        xy_coords.append({
            'x': round(x, 2),
            'y': round(y, 2),
            'elevation': coord.get('elevation', 0),
            'distance_km': coord.get('distance_km', 0)
        })
    
    print(f"✅ 轉換完成: {len(xy_coords)} 個座標點")
    
    # 計算邊界
    xs = [c['x'] for c in xy_coords]
    ys = [c['y'] for c in xy_coords]
    
    bounds = {
        'x_min': min(xs),
        'x_max': max(xs),
        'y_min': min(ys),
        'y_max': max(ys)
    }
    
    print(f"📐 賽道範圍: X({bounds['x_min']:.0f} ~ {bounds['x_max']:.0f}), "
          f"Y({bounds['y_min']:.0f} ~ {bounds['y_max']:.0f})")
    
    return xy_coords, bounds


def generate_integrated_json(geojson_data, corners_df, event_info, output_path):
    """生成整合型 JSON 檔案"""
    print(f"\n🔨 生成整合型 JSON...")
    
    # 轉換 GeoJSON 座標為 X/Y
    xy_coords, track_bounds = convert_gps_to_xy(geojson_data['coordinates'])
    
    # 轉換 FastF1 彎道數據
    corners_list = []
    if corners_df is not None:
        for idx, corner in corners_df.iterrows():
            corners_list.append({
                'number': int(corner['Number']),
                'distance': float(corner['Distance']),
                'x': float(corner['X']),
                'y': float(corner['Y']),
                'angle': float(corner['Angle']),
                'letter': str(corner.get('Letter', '')),
                'name': f"Turn {int(corner['Number'])}"
            })
    
    # 建立整合型 JSON 結構
    integrated_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_sources': [
                'f1-circuits-master (GeoJSON + Elevation)',
                'FastF1 Official Circuit Info'
            ],
            'coordinate_system': 'X/Y Plane (meters)',
            'description': 'Integrated circuit data with GeoJSON track outline and FastF1 official corners'
        },
        'circuit_info': {
            'name': event_info['EventName'] if event_info is not None else 'Suzuka International Racing Course',
            'country': 'Japan',
            'location': event_info['Location'] if event_info is not None else 'Suzuka',
            'year': 2025,
            'track_length_km': geojson_data.get('track_length_km', 5.807)
        },
        'track_outline': {
            'description': 'Track outline in X/Y coordinates (converted from GPS)',
            'coordinate_count': len(xy_coords),
            'coordinates': xy_coords
        },
        'fastf1_corners': {
            'available': len(corners_list) > 0,
            'count': len(corners_list),
            'description': 'Official corners from FastF1 circuit_info',
            'corners': corners_list
        },
        'track_bounds': track_bounds,
        'elevation_profile': {
            'available': True,
            'min_elevation': min(c['elevation'] for c in xy_coords),
            'max_elevation': max(c['elevation'] for c in xy_coords),
            'elevation_change': max(c['elevation'] for c in xy_coords) - min(c['elevation'] for c in xy_coords)
        }
    }
    
    # 儲存 JSON
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(integrated_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 檔案已生成: {output_path}")
    print(f"📊 統計資訊:")
    print(f"   - 賽道輪廓點數: {len(xy_coords)}")
    print(f"   - 官方彎道數: {len(corners_list)}")
    print(f"   - 高程變化: {integrated_data['elevation_profile']['elevation_change']:.1f}m")
    
    return integrated_data


def main():
    """主函數"""
    print("=" * 80)
    print("Japan 賽道整合型 JSON 生成工具")
    print("整合 f1-circuits-master GeoJSON + FastF1 官方彎道數據")
    print("=" * 80)
    
    # 1. 載入 GeoJSON 數據
    geojson_data = load_geojson_data()
    if not geojson_data:
        print("\n❌ 無法載入 GeoJSON 數據，終止執行")
        return
    
    # 2. 載入 FastF1 彎道數據
    corners_df, event_info = load_fastf1_corners(year=2025)
    if corners_df is None:
        print("\n⚠️  無法載入 FastF1 彎道數據，將只包含 GeoJSON 數據")
    
    # 3. 生成整合型 JSON
    output_path = "json/japan_circuit_integrated_2025.json"
    integrated_data = generate_integrated_json(geojson_data, corners_df, event_info, output_path)
    
    # 4. 顯示摘要
    print("\n" + "=" * 80)
    print("✅ 整合型 JSON 生成完成！")
    print("=" * 80)
    print(f"📄 輸出檔案: {output_path}")
    print(f"📊 內容摘要:")
    print(f"   - 賽道: {integrated_data['circuit_info']['name']}")
    print(f"   - 年份: {integrated_data['circuit_info']['year']}")
    print(f"   - 座標點: {integrated_data['track_outline']['coordinate_count']}")
    print(f"   - 彎道數: {integrated_data['fastf1_corners']['count']}")
    print(f"   - 高程範圍: {integrated_data['elevation_profile']['min_elevation']:.1f}m ~ "
          f"{integrated_data['elevation_profile']['max_elevation']:.1f}m")
    print("\n💡 下一步: 執行 demo_japan_circuit_trackmap.py 查看視覺化效果")


if __name__ == "__main__":
    main()
