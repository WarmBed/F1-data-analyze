#!/usr/bin/env python3
"""
測試：使用 Open-Elevation API 獲取日本鈴鹿賽道的高程資料並繪製高程剖面圖
Test: Fetch elevation data for Suzuka Circuit using Open-Elevation API and plot elevation profile
"""

import json
import requests
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import time

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_suzuka_circuit_data():
    """載入鈴鹿賽道的 GeoJSON 資料"""
    geojson_path = Path("json/f1-circuits-master/circuits/jp-1962.geojson")
    
    if not geojson_path.exists():
        raise FileNotFoundError(f"找不到鈴鹿賽道資料檔案: {geojson_path}")
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 成功載入鈴鹿賽道資料")
    return data

def extract_coordinates(geojson_data):
    """從 GeoJSON 提取座標點"""
    features = geojson_data.get("features", [])
    if not features:
        raise ValueError("GeoJSON 沒有 features")
    
    geometry = features[0].get("geometry", {})
    coordinates = geometry.get("coordinates", [])
    
    if not coordinates:
        raise ValueError("找不到座標資料")
    
    print(f"✅ 提取到 {len(coordinates)} 個座標點")
    
    # 座標格式：[經度, 緯度]
    return coordinates

def fetch_elevation_batch(coordinates, batch_size=100):
    """
    批次查詢高程資料（Open-Elevation API 限制每次 100 個點）
    
    Args:
        coordinates: GPS 座標列表 [[lon, lat], ...]
        batch_size: 每批查詢的點數（預設 100）
    
    Returns:
        elevations: 高程列表（公尺）
    """
    url = "https://api.open-elevation.com/api/v1/lookup"
    
    elevations = []
    total_points = len(coordinates)
    
    print(f"\n🌐 開始查詢高程資料...")
    print(f"📍 總共 {total_points} 個點，將分 {(total_points + batch_size - 1) // batch_size} 批查詢")
    
    for i in range(0, total_points, batch_size):
        batch = coordinates[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_points + batch_size - 1) // batch_size
        
        # 轉換為 API 需要的格式：{"latitude": lat, "longitude": lon}
        locations = [
            {"latitude": lat, "longitude": lon}
            for lon, lat in batch
        ]
        
        payload = {"locations": locations}
        
        print(f"  [{batch_num}/{total_batches}] 查詢 {len(batch)} 個點...", end=" ")
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                batch_elevations = [point["elevation"] for point in result["results"]]
                elevations.extend(batch_elevations)
                print(f"✅ 成功（高度範圍: {min(batch_elevations):.1f}m - {max(batch_elevations):.1f}m）")
            else:
                print(f"❌ 失敗 (HTTP {response.status_code})")
                # 失敗時填充 None
                elevations.extend([None] * len(batch))
            
            # 避免 API 限流，稍微延遲
            if i + batch_size < total_points:
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            elevations.extend([None] * len(batch))
    
    print(f"\n✅ 高程查詢完成！共獲取 {len([e for e in elevations if e is not None])} 個有效高程值")
    
    return elevations

def calculate_track_distances(coordinates):
    """
    計算賽道累積距離（使用簡化的平面距離公式）
    
    Args:
        coordinates: GPS 座標列表 [[lon, lat], ...]
    
    Returns:
        distances: 累積距離列表（公里）
    """
    distances = [0.0]
    
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i-1]
        lon2, lat2 = coordinates[i]
        
        # 簡化的平面距離計算（適合小範圍）
        # 1 度緯度 ≈ 111 km
        # 1 度經度 ≈ 111 km * cos(緯度)
        lat_avg = (lat1 + lat2) / 2
        dx = (lon2 - lon1) * 111 * np.cos(np.radians(lat_avg))
        dy = (lat2 - lat1) * 111
        
        distance = np.sqrt(dx**2 + dy**2)
        distances.append(distances[-1] + distance)
    
    return distances

def plot_elevation_profile(distances, elevations, circuit_info):
    """
    繪製高程剖面圖
    
    Args:
        distances: 距離列表（公里）
        elevations: 高程列表（公尺）
        circuit_info: 賽道資訊字典
    """
    # 過濾掉 None 值
    valid_data = [(d, e) for d, e in zip(distances, elevations) if e is not None]
    if not valid_data:
        print("❌ 沒有有效的高程資料可繪圖")
        return
    
    distances_valid, elevations_valid = zip(*valid_data)
    
    # 計算統計資訊
    min_elevation = min(elevations_valid)
    max_elevation = max(elevations_valid)
    elevation_change = max_elevation - min_elevation
    avg_elevation = np.mean(elevations_valid)
    
    # 創建圖表
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 繪製高程剖面（填充區域 + 線條）
    ax.fill_between(distances_valid, elevations_valid, alpha=0.3, color='#2E7D32', label='高程區域')
    ax.plot(distances_valid, elevations_valid, linewidth=2.5, color='#1B5E20', label='高程線')
    
    # 標註最高點和最低點
    max_idx = elevations_valid.index(max_elevation)
    min_idx = elevations_valid.index(min_elevation)
    
    ax.scatter([distances_valid[max_idx]], [max_elevation], 
              color='red', s=100, zorder=5, label=f'最高點 ({max_elevation:.1f}m)')
    ax.scatter([distances_valid[min_idx]], [min_elevation], 
              color='blue', s=100, zorder=5, label=f'最低點 ({min_elevation:.1f}m)')
    
    # 標註箭頭
    ax.annotate(f'最高點\n{max_elevation:.1f}m', 
               xy=(distances_valid[max_idx], max_elevation),
               xytext=(distances_valid[max_idx], max_elevation + 3),
               ha='center', fontsize=9, color='red',
               arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
    
    ax.annotate(f'最低點\n{min_elevation:.1f}m', 
               xy=(distances_valid[min_idx], min_elevation),
               xytext=(distances_valid[min_idx], min_elevation - 3),
               ha='center', fontsize=9, color='blue',
               arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    
    # 設定軸標籤
    ax.set_xlabel('賽道距離 (km)', fontsize=12, fontweight='bold')
    ax.set_ylabel('海拔高度 (m)', fontsize=12, fontweight='bold')
    
    # 標題
    circuit_name = circuit_info.get("name", "未知賽道")
    circuit_location = circuit_info.get("location", "")
    title = f'{circuit_name} - 高程剖面圖\n{circuit_location}'
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # 網格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 圖例
    ax.legend(loc='upper right', fontsize=10)
    
    # 添加統計資訊文字框
    stats_text = f'''
    賽道長度: {distances_valid[-1]:.2f} km
    平均海拔: {avg_elevation:.1f} m
    最高點: {max_elevation:.1f} m
    最低點: {min_elevation:.1f} m
    總高低差: {elevation_change:.1f} m
    '''
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, stats_text.strip(), transform=ax.transAxes, 
           fontsize=10, verticalalignment='top', bbox=props)
    
    # 調整布局
    plt.tight_layout()
    
    # 儲存圖表
    output_path = Path("elevation_profile_suzuka.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ 高程剖面圖已儲存至: {output_path.absolute()}")
    
    # 關閉圖表（不顯示視窗）
    plt.close()
    
    # 輸出統計摘要
    print(f"\n📊 高程統計摘要：")
    print(f"   賽道長度：{distances_valid[-1]:.2f} km")
    print(f"   平均海拔：{avg_elevation:.1f} m")
    print(f"   最高點：{max_elevation:.1f} m（位於 {distances_valid[max_idx]:.2f} km 處）")
    print(f"   最低點：{min_elevation:.1f} m（位於 {distances_valid[min_idx]:.2f} km 處）")
    print(f"   總高低差：{elevation_change:.1f} m")
    
    # 評估賽道高低差特性
    if elevation_change < 20:
        characteristic = "非常平坦的賽道 🟢"
    elif elevation_change < 50:
        characteristic = "輕微起伏的賽道 🟡"
    elif elevation_change < 100:
        characteristic = "中等高低差的賽道 🟠"
    else:
        characteristic = "極具挑戰性的高低差賽道 🔴"
    
    print(f"   賽道特性：{characteristic}")

def main():
    """主程式"""
    print("=" * 60)
    print("🏁 鈴鹿國際賽車場 (Suzuka Circuit) - 高程剖面分析")
    print("=" * 60)
    
    try:
        # 1. 載入賽道資料
        print("\n[步驟 1/4] 載入賽道 GeoJSON 資料...")
        geojson_data = load_suzuka_circuit_data()
        
        # 提取基本資訊
        circuit_info = geojson_data["features"][0]["properties"]
        print(f"   賽道名稱：{circuit_info.get('Name', 'N/A')}")
        print(f"   位置：{circuit_info.get('Location', 'N/A')}")
        print(f"   官方長度：{circuit_info.get('length', 'N/A')} 公尺")
        print(f"   起點海拔：{circuit_info.get('altitude', 'N/A')} 公尺")
        
        # 2. 提取座標
        print("\n[步驟 2/4] 提取賽道 GPS 座標...")
        coordinates = extract_coordinates(geojson_data)
        
        # 顯示前 3 個座標點
        print(f"   前 3 個座標點：")
        for i, (lon, lat) in enumerate(coordinates[:3]):
            print(f"     點 {i+1}: 經度={lon:.6f}, 緯度={lat:.6f}")
        
        # 3. 查詢高程資料
        print("\n[步驟 3/4] 查詢高程資料（Open-Elevation API）...")
        elevations = fetch_elevation_batch(coordinates, batch_size=100)
        
        # 4. 計算賽道距離
        print("\n[步驟 4/4] 計算賽道累積距離...")
        distances = calculate_track_distances(coordinates)
        print(f"   ✅ 計算完成，賽道總長度: {distances[-1]:.2f} km")
        
        # 5. 繪製高程剖面圖
        print("\n[繪製圖表] 生成高程剖面圖...")
        plot_elevation_profile(distances, elevations, circuit_info)
        
        print("\n" + "=" * 60)
        print("✅ 測試完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
