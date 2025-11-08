"""
測量賽道加速段起點距離工具

使用方法：
1. 執行此腳本，指定賽道、年份、會話
2. 腳本會顯示所有車手在哪個位置達到 110 km/h
3. 選擇最早的位置作為加速段起點
4. 複製建議的字典條目到 all_drivers_straight_line_speed.py 中的 TRACK_ACCELERATION_START_DISTANCE

範例：
    python tools/measure_track_acceleration_start.py --year 2025 --race China --session R
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, List

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_json_data(year: int, race: str, session: str) -> Optional[Dict]:
    """載入已生成的 JSON 數據"""
    json_dir = project_root / "json"
    json_pattern = f"all_drivers_straight_line_speed_{year}_{race}_{session}*.json"
    
    json_files = list(json_dir.glob(json_pattern))
    if not json_files:
        print(f"❌ 找不到數據檔案: {json_pattern}")
        print(f"💡 請先執行: python f1_analysis_modular_main.py -f 48 -y {year} -r {race} -s {session}")
        return None
    
    # 使用最新的檔案
    json_file = sorted(json_files)[-1]
    print(f"✅ 載入數據: {json_file.name}\n")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_acceleration_start(data: Dict, race: str) -> None:
    """分析加速段起點"""
    if not data or 'data' not in data or 'driver_speeds' not in data['data']:
        print("❌ 數據格式錯誤")
        return
    
    driver_speeds = data['data']['driver_speeds']
    
    print(f"🏁 賽道: {race}")
    print(f"📊 分析車手數量: {len(driver_speeds)}\n")
    print("=" * 80)
    print("【各車手加速段起點分析】")
    print("=" * 80)
    
    # 收集所有車手的加速起點位置
    start_positions = []
    
    for driver_data in driver_speeds:
        driver = driver_data.get('driver', 'N/A')
        
        # 檢查是否有加速度數據
        if 'acceleration_100_300_start_distance' in driver_data:
            start_distance = driver_data['acceleration_100_300_start_distance']
            start_speed = driver_data.get('acceleration_100_300_start_speed', 'N/A')
            
            start_positions.append({
                'driver': driver,
                'distance': start_distance,
                'speed': start_speed
            })
            
            print(f"  {driver:3s} | 起點: {start_distance:7.1f}m | 起始速度: {start_speed} km/h")
        else:
            print(f"  {driver:3s} | ❌ 無加速度數據")
    
    if not start_positions:
        print("\n❌ 沒有任何車手有加速度數據")
        return
    
    # 找出最早的起點（最小距離）
    min_position = min(start_positions, key=lambda x: x['distance'])
    max_position = max(start_positions, key=lambda x: x['distance'])
    avg_distance = sum(p['distance'] for p in start_positions) / len(start_positions)
    
    print("\n" + "=" * 80)
    print("【統計摘要】")
    print("=" * 80)
    print(f"  最早起點: {min_position['distance']:.1f}m ({min_position['driver']})")
    print(f"  最晚起點: {max_position['distance']:.1f}m ({max_position['driver']})")
    print(f"  平均起點: {avg_distance:.1f}m")
    print(f"  起點範圍: {max_position['distance'] - min_position['distance']:.1f}m")
    
    # 建議使用的起點（取最早的起點，並往前推 50m 作為緩衝）
    suggested_start = int(min_position['distance'] - 50)
    
    print("\n" + "=" * 80)
    print("【建議的加速段起點】")
    print("=" * 80)
    print(f"  建議起點: {suggested_start}m")
    print(f"  計算方式: 最早起點 ({min_position['distance']:.1f}m) - 50m 緩衝")
    print(f"  涵蓋範圍: 所有車手的加速段起點")
    
    print("\n" + "=" * 80)
    print("【複製到 TRACK_ACCELERATION_START_DISTANCE】")
    print("=" * 80)
    print(f'    "{race}": {suggested_start},  # 建議值：最早起點 - 50m 緩衝')
    print()
    
    # 檢查是否有異常值（距離差異超過 500m）
    if max_position['distance'] - min_position['distance'] > 500:
        print("⚠️  警告：起點位置差異過大（>500m），建議檢查數據是否正確")
        print(f"   最早: {min_position['driver']} @ {min_position['distance']:.1f}m")
        print(f"   最晚: {max_position['driver']} @ {max_position['distance']:.1f}m")
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='測量賽道加速段起點距離')
    parser.add_argument('-y', '--year', type=int, default=2025, help='年份（預設: 2025）')
    parser.add_argument('-r', '--race', type=str, required=True, help='賽道名稱（例如: China, Japan, Azerbaijan）')
    parser.add_argument('-s', '--session', type=str, default='R', help='會話類型（預設: R）')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🔍 F1 賽道加速段起點測量工具")
    print("=" * 80)
    print()
    
    # 載入數據
    data = load_json_data(args.year, args.race, args.session)
    if not data:
        return
    
    # 分析加速段起點
    analyze_acceleration_start(data, args.race)
    
    print("=" * 80)
    print("💡 下一步:")
    print("=" * 80)
    print("1. 複製上方的字典條目")
    print("2. 貼到 CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py")
    print("3. 找到 TRACK_ACCELERATION_START_DISTANCE 字典")
    print("4. 添加或取消註釋該賽道的條目")
    print(f"5. 重新執行: python f1_analysis_modular_main.py -f 48 -y {args.year} -r {args.race} -s {args.session} --force")
    print("6. 驗證加速度數據是否正確")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
