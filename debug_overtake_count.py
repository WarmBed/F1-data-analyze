# -*- coding: utf-8 -*-
"""
調試超車統計 - 檢查為什麼熱點次數這麼高
"""

import json
import os
from collections import defaultdict

BASE_DIR = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025\Abu_Dhabi_Race"

def load_json(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print(f"❌ 找不到: {filename}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 支援兩種格式: {metadata, records} 或 直接 list
    if isinstance(data, dict) and 'records' in data:
        return data['records']
    return data if isinstance(data, list) else []

def main():
    print("=" * 60)
    print("調試 Abu Dhabi 2025 超車統計")
    print("=" * 60)
    
    # 載入 TimingAppData
    timing_app = load_json("TimingAppData.json")
    print(f"TimingAppData 記錄數: {len(timing_app)}")
    
    # 追蹤位置變化
    last_positions = {}
    position_changes = []
    
    for record in timing_app:
        ts = record.get('timestamp', '')
        data = record.get('data', {})
        
        if 'Lines' not in data:
            continue
        
        for driver_num, line_data in data['Lines'].items():
            if driver_num in {'241', '242', '243'}:
                continue
            if not isinstance(line_data, dict):
                continue
            if 'Line' not in line_data:
                continue
            
            new_pos = line_data['Line']
            old_pos = last_positions.get(driver_num, new_pos)
            
            # 記錄位置變化
            if new_pos != old_pos:
                change = old_pos - new_pos
                position_changes.append({
                    'driver': driver_num,
                    'old': old_pos,
                    'new': new_pos,
                    'change': change,
                    'ts': ts
                })
            
            last_positions[driver_num] = new_pos
    
    print(f"\n總位置變化數: {len(position_changes)}")
    
    # 分析變化
    gains = [c for c in position_changes if c['change'] > 0]  # 超車
    losses = [c for c in position_changes if c['change'] < 0]  # 被超
    
    print(f"  - 超車 (gain): {len(gains)}")
    print(f"  - 被超 (loss): {len(losses)}")
    
    # 統計超過的位置數
    total_gain = sum(c['change'] for c in gains)
    total_loss = sum(abs(c['change']) for c in losses)
    
    print(f"\n總超過位置數: {total_gain}")
    print(f"總失去位置數: {total_loss}")
    
    # 分析多位超車
    multi_gains = [c for c in gains if c['change'] > 1]
    print(f"\n一次超多位 (change > 1): {len(multi_gains)}")
    for c in multi_gains[:20]:
        print(f"  {c['driver']}: P{c['old']} → P{c['new']} (gain {c['change']})")
    
    # 關鍵問題: 檢查同一超車事件是否被重複計算
    print("\n" + "=" * 60)
    print("問題分析: 超車計數方法")
    print("=" * 60)
    
    print("""
當前邏輯問題:
- 計算 total_overtakes += change (位置變化數)
- 例如: P5 → P3 會計算為 2 次超車
- 實際上只超越了 2 個車手，但可能是 1 次動作

熱點統計問題:
- 每次超車事件都會在 GPS 座標上標記
- 如果 P5 → P3 計為 2 次，那 GPS 熱點會增加 2 次
- 實際超車動作只有 1 次
""")
    
    # 正確的統計: 按事件計算
    unique_events = len(gains)  # 每次位置提升算一個事件
    print(f"正確統計 (按事件): {unique_events}")
    print(f"當前統計 (按位置): {total_gain}")
    print(f"差異: {total_gain - unique_events}")
    
    # 分析熱點問題: 檢查進站相關超車
    print("\n" + "=" * 60)
    print("進站相關超車分析")
    print("=" * 60)
    
    # 載入進站數據
    pit_data = load_json("PitLaneTimeCollection.json")
    pit_laps = defaultdict(set)
    for record in pit_data:
        pit_times = record.get('data', {}).get('PitTimes', {})
        for driver_num, pit_info in pit_times.items():
            if isinstance(pit_info, dict) and 'Lap' in pit_info:
                pit_laps[driver_num].add(int(pit_info['Lap']))
    
    all_pit_laps = set()
    for laps in pit_laps.values():
        all_pit_laps.update(laps)
    print(f"進站圈: {sorted(all_pit_laps)}")
    
    # 載入 TimingData 獲取圈數
    timing_data = load_json("TimingData.json")
    lap_updates = []
    for record in timing_data:
        ts = record.get('timestamp', '')
        data = record.get('data', {})
        if 'Lines' in data:
            for driver_num, line_data in data['Lines'].items():
                if isinstance(line_data, dict) and 'NumberOfLaps' in line_data:
                    lap_updates.append((ts, driver_num, line_data['NumberOfLaps']))
    
    # 分類超車
    current_laps = defaultdict(int)
    lap_update_idx = 0
    last_positions = {}
    
    on_track = 0
    pit_related = 0
    lap_one = 0
    
    for record in load_json("TimingAppData.json"):
        ts = record.get('timestamp', '')
        data = record.get('data', {})
        
        # 更新圈數
        while lap_update_idx < len(lap_updates) and lap_updates[lap_update_idx][0] <= ts:
            _, d_num, lap = lap_updates[lap_update_idx]
            current_laps[d_num] = lap
            lap_update_idx += 1
        
        if 'Lines' not in data:
            continue
        
        for driver_num, line_data in data['Lines'].items():
            if driver_num in {'241', '242', '243'}:
                continue
            if not isinstance(line_data, dict) or 'Line' not in line_data:
                continue
            
            new_pos = line_data['Line']
            old_pos = last_positions.get(driver_num, new_pos)
            
            if new_pos < old_pos:
                current_lap = current_laps.get(driver_num, 1)
                
                if current_lap <= 1:
                    lap_one += 1
                elif current_lap in all_pit_laps:
                    pit_related += 1
                else:
                    on_track += 1
            
            last_positions[driver_num] = new_pos
    
    print(f"\n按事件分類:")
    print(f"  第一圈: {lap_one}")
    print(f"  進站相關: {pit_related}")
    print(f"  賽道超車: {on_track}")
    print(f"  合計: {lap_one + pit_related + on_track}")

if __name__ == "__main__":
    main()
