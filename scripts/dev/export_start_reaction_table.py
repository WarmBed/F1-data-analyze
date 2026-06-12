#!/usr/bin/env python3
"""
導出 2025 全賽季起跑反應數據表格 (用於影片驗證)
輸出格式: CSV
"""
import json
import csv
from pathlib import Path
from collections import defaultdict

# 設置
DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'LAW', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}


def parse_timestamp(ts):
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def interpolate_time(t1, v1, t2, v2, target_v):
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


def analyze_race(race_dir):
    """分析單場賽事，返回所有車手的 T10/T20 數據（不過濾）"""
    results = {}
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return results, None
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        race_start_ts = None
        race_start_raw = None
        for rec in session_data.get('records', []):
            status = rec.get('data', {}).get('StatusSeries', {})
            if isinstance(status, dict):
                for key, val in status.items():
                    if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                        race_start_ts = parse_timestamp(rec.get('timestamp', ''))
                        race_start_raw = rec.get('timestamp', '')
                        break
            if race_start_ts:
                break
        
        if not race_start_ts:
            return results, None
        
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        driver_speeds = defaultdict(list)
        
        for rec in cardata.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            if ts < race_start_ts or ts > race_start_ts + 30:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    driver_speeds[name].append((ts - race_start_ts, speed, rec.get('timestamp', '')))
        
        for name, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            speeds.sort(key=lambda x: x[0])
            t10, t20 = None, None
            t10_raw, t20_raw = None, None
            
            for i in range(1, len(speeds)):
                t_prev, v_prev, ts_prev = speeds[i-1]
                t_curr, v_curr, ts_curr = speeds[i]
                
                if t10 is None and v_prev < 10 <= v_curr:
                    t10 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 10)
                    t10_raw = ts_curr
                
                if t20 is None and v_prev < 20 <= v_curr:
                    t20 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 20)
                    t20_raw = ts_curr
            
            if t10:
                results[name] = {
                    't10': t10, 
                    't20': t20,
                    't10_timestamp': t10_raw,
                    't20_timestamp': t20_raw
                }
                
    except Exception as e:
        print(f"Error: {e}")
    
    return results, race_start_raw


def main():
    base_dir = Path(__file__).parent / "json" / "LiveF1" / "2025"
    race_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.endswith('_Race')])
    
    print(f"掃描到 {len(race_dirs)} 場賽事")
    
    # 收集所有數據
    all_rows = []
    
    for race_dir in race_dirs:
        race_name = race_dir.name.replace('_Race', '').replace('_', ' ')
        results, race_start = analyze_race(race_dir)
        
        if results:
            print(f"  {race_name}: {len(results)} 位車手")
            
            for driver, times in sorted(results.items()):
                t10 = times.get('t10')
                t20 = times.get('t20')
                
                # 判斷是否為異常值
                is_outlier = ""
                if t10 and t10 > 2.5:
                    is_outlier = "異常"
                
                all_rows.append({
                    'race': race_name,
                    'race_start': race_start or '',
                    'driver': driver,
                    't10': f"{t10:.3f}" if t10 else '',
                    't20': f"{t20:.3f}" if t20 else '',
                    'outlier': is_outlier
                })
    
    # 輸出 CSV (加上時間戳避免檔案被鎖定)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent / f"start_reaction_verification_table_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['race', 'race_start', 'driver', 't10', 't20', 'outlier'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\n✅ 已導出到: {output_file}")
    print(f"   共 {len(all_rows)} 筆數據")
    
    # 同時顯示摘要表格
    print("\n" + "="*80)
    print("數據摘要 (按賽事排序)")
    print("="*80)
    print(f"{'賽事':<20} {'車手':<6} {'T10(s)':<10} {'T20(s)':<10} {'備註':<10}")
    print("-"*80)
    
    for row in all_rows:
        print(f"{row['race']:<20} {row['driver']:<6} {row['t10']:<10} {row['t20']:<10} {row['outlier']:<10}")
    
    print("="*80)


if __name__ == "__main__":
    main()
