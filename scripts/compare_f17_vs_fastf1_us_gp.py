"""
比較 CLI F17 動態檢測 vs FastF1 官方彎道
使用美國站數據進行分析
"""
import fastf1
import numpy as np
from scipy.signal import find_peaks
import pandas as pd

def classify_corner(min_speed):
    """彎道分類：根據最低速度"""
    if min_speed < 120:
        return "Low-speed"
    elif min_speed < 200:
        return "Medium-speed"
    else:
        return "High-speed"

def main():
    # 載入美國站數據
    print("Loading 2024 US GP data...")
    session = fastf1.get_session(2024, 'United States', 'R')
    session.load(telemetry=True, weather=False)
    
    # 1. FastF1 官方彎道
    circuit_info = session.get_circuit_info()
    official_corners = circuit_info.corners
    print(f"\n[FastF1] Official corners: {len(official_corners)}")
    
    # 2. F17 動態檢測
    fastest_lap = session.laps.pick_fastest()
    driver_code = fastest_lap['Driver']
    telemetry = fastest_lap.get_telemetry()
    
    print(f"[F17] Using fastest lap from {driver_code}")
    print(f"[F17] Telemetry points: {len(telemetry)}")
    
    # F17 彎道檢測
    speed = telemetry['Speed'].values
    peaks, properties = find_peaks(
        -speed,
        distance=30,
        prominence=15
    )
    
    # F17 檢測結果
    f17_corners = []
    for i, peak_idx in enumerate(peaks, 1):
        min_speed = float(speed[peak_idx])
        f17_corners.append({
            'number': i,
            'distance': float(telemetry.iloc[peak_idx]['Distance']),
            'min_speed': min_speed,
            'type': classify_corner(min_speed)
        })
    
    print(f"[F17] Detected corners: {len(f17_corners)}\n")
    
    # 統計 F17 彎道類型
    f17_types = {'Low-speed': 0, 'Medium-speed': 0, 'High-speed': 0}
    for c in f17_corners:
        f17_types[c['type']] += 1
    
    print("=== F17 Corner Type Distribution ===")
    for ctype, count in f17_types.items():
        print(f"  {ctype:15s}: {count}")
    
    # 3. 將 FastF1 官方彎道映射到 Distance
    print("\n=== Mapping FastF1 Official Corners to Distance ===")
    official_mapped = []
    for idx, corner in official_corners.iterrows():
        corner_num = int(corner['Number'])
        corner_x, corner_y = corner['X'], corner['Y']
        
        # 找最接近的遙測點
        distances_to_corner = np.sqrt(
            (telemetry['X'] - corner_x)**2 + 
            (telemetry['Y'] - corner_y)**2
        )
        closest_idx = distances_to_corner.idxmin()
        mapped_distance = float(telemetry.loc[closest_idx, 'Distance'])
        
        # 在彎道附近找最低速度
        search_range = 50
        start_idx = max(0, closest_idx - search_range)
        end_idx = min(len(telemetry), closest_idx + search_range)
        
        nearby_speeds = telemetry.iloc[start_idx:end_idx]['Speed']
        min_speed_nearby = float(nearby_speeds.min())
        
        official_mapped.append({
            'number': corner_num,
            'distance': mapped_distance,
            'min_speed': min_speed_nearby,
            'type': classify_corner(min_speed_nearby),
            'angle': float(corner['Angle'])
        })
    
    print(f"  Official corners mapped: {len(official_mapped)}")
    
    # 統計官方彎道類型
    official_types = {'Low-speed': 0, 'Medium-speed': 0, 'High-speed': 0}
    for c in official_mapped:
        official_types[c['type']] += 1
    
    print("\n=== FastF1 Official Corner Type Distribution ===")
    for ctype, count in official_types.items():
        print(f"  {ctype:15s}: {count}")
    
    # 4. 配對分析
    print("\n=== Corner Matching: F17 vs FastF1 Official ===\n")
    print(f"{'Official':^10} | {'Distance':>10} | {'Type':^15} | {'F17':^6} | {'Distance':>10} | {'Type':^15} | {'Diff':>8} | {'Status':^8}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*15}-+-{'-'*6}-+-{'-'*10}-+-{'-'*15}-+-{'-'*8}-+-{'-'*8}")
    
    matched_positions = 0
    matched_types = 0
    tolerance = 150  # 150m 容差
    
    for official in official_mapped:
        off_num = official['number']
        off_dist = official['distance']
        off_type = official['type']
        
        # 找最接近的 F17 彎道
        if f17_corners:
            f17_dists = [c['distance'] for c in f17_corners]
            closest_idx = np.argmin([abs(off_dist - d) for d in f17_dists])
            f17_match = f17_corners[closest_idx]
            
            f17_num = f17_match['number']
            f17_dist = f17_match['distance']
            f17_type = f17_match['type']
            
            diff = abs(off_dist - f17_dist)
            
            # 判斷配對狀態
            position_match = diff < tolerance
            type_match = off_type == f17_type
            
            if position_match:
                matched_positions += 1
                if type_match:
                    matched_types += 1
                    status = "PERFECT"
                else:
                    status = "POS_ONLY"
            else:
                status = "MISS"
            
            print(f"T{off_num:2d} {' ':6s} | {off_dist:8.1f}m | {off_type:^15s} | "
                  f"F17-{f17_num:2d} | {f17_dist:8.1f}m | {f17_type:^15s} | "
                  f"{diff:6.1f}m | {status:^8s}")
        else:
            print(f"T{off_num:2d} {' ':6s} | {off_dist:8.1f}m | {off_type:^15s} | "
                  f"{'N/A':^6s} | {'N/A':>10s} | {'N/A':^15s} | "
                  f"{'N/A':>8s} | {'NO_F17':^8s}")
    
    # 5. 總結
    print(f"\n=== Summary ===")
    print(f"FastF1 Official corners: {len(official_mapped)}")
    print(f"F17 Detected corners: {len(f17_corners)}")
    print(f"Position match rate: {matched_positions}/{len(official_mapped)} ({matched_positions/len(official_mapped)*100:.1f}%)")
    print(f"Position + Type match rate: {matched_types}/{len(official_mapped)} ({matched_types/len(official_mapped)*100:.1f}%)")
    print(f"Missing corners: {len(official_mapped) - matched_positions}")
    
    print(f"\n=== Corner Type Comparison ===")
    print(f"{'Type':^15s} | {'FastF1':^8s} | {'F17':^8s} | {'Diff':^8s}")
    print(f"{'-'*15}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")
    for ctype in ['Low-speed', 'Medium-speed', 'High-speed']:
        official_count = official_types[ctype]
        f17_count = f17_types.get(ctype, 0)
        diff = official_count - f17_count
        print(f"{ctype:^15s} | {official_count:^8d} | {f17_count:^8d} | {diff:^+8d}")
    
    print(f"\n=== Detailed F17 Detection Results ===")
    for corner in f17_corners:
        print(f"F17-{corner['number']:2d}: Distance={corner['distance']:7.1f}m, "
              f"Speed={corner['min_speed']:5.1f}km/h, Type={corner['type']}")

if __name__ == '__main__':
    main()
