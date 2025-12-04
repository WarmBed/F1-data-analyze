"""
超車率訓練系統 - 2023-2024 數據

計算:
1. 賽道超車率 (每圈平均超車次數)
2. 車手超車能力 (超車/被超車比率)
3. 輪胎差異對超車的影響

輸出: 用於更新 predictor.py 的參數
"""
import fastf1
import numpy as np
import pandas as pd
from collections import defaultdict

fastf1.Cache.enable_cache('f1_analysis_cache')

print('='*70)
print('超車率訓練 - 2023-2024 數據')
print('='*70)

# 統計數據
circuit_overtakes = defaultdict(list)  # circuit -> [overtakes_per_lap, ...]
driver_overtakes = defaultdict(lambda: {'made': 0, 'received': 0, 'races': 0})
tyre_overtakes = defaultdict(lambda: {'overtakes': 0, 'opportunities': 0})

def count_overtakes(laps_df):
    """
    計算一場比賽的超車次數
    
    Returns:
        total_overtakes: 總超車數
        overtake_details: [(lap, overtaker, overtaken), ...]
    """
    if laps_df.empty:
        return 0, []
    
    # 按圈數排序
    laps_sorted = laps_df.sort_values(['LapNumber', 'Position'])
    
    # 追蹤位置變化
    prev_positions = {}  # driver -> position
    overtakes = []
    
    for lap_num in laps_sorted['LapNumber'].unique():
        lap_data = laps_sorted[laps_sorted['LapNumber'] == lap_num]
        current_positions = {}
        
        for _, row in lap_data.iterrows():
            driver = row['Driver']
            position = row.get('Position')
            if pd.isna(position):
                continue
            position = int(position)
            current_positions[driver] = position
        
        # 比較位置變化
        if prev_positions:
            for driver, curr_pos in current_positions.items():
                prev_pos = prev_positions.get(driver)
                if prev_pos is None:
                    continue
                
                # 位置提升 = 可能的超車
                if curr_pos < prev_pos:
                    positions_gained = prev_pos - curr_pos
                    
                    # 找出被超越的車手
                    for other_driver, other_curr in current_positions.items():
                        if other_driver == driver:
                            continue
                        other_prev = prev_positions.get(other_driver)
                        if other_prev is None:
                            continue
                        
                        # 檢測超車: A 從 prev_pos 到 curr_pos, B 從 other_prev 到 other_curr
                        # 如果 A 超越了 B: A.prev > B.prev AND A.curr < B.curr
                        if prev_pos > other_prev and curr_pos < other_curr:
                            overtakes.append({
                                'lap': lap_num,
                                'overtaker': driver,
                                'overtaken': other_driver,
                                'overtaker_new_pos': curr_pos,
                                'overtaken_new_pos': other_curr,
                            })
        
        prev_positions = current_positions.copy()
    
    # 去重 (同一圈同一對只算一次)
    unique_overtakes = []
    seen = set()
    for ot in overtakes:
        key = (ot['lap'], ot['overtaker'], ot['overtaken'])
        if key not in seen:
            seen.add(key)
            unique_overtakes.append(ot)
    
    return len(unique_overtakes), unique_overtakes


def analyze_tyre_overtakes(laps_df, overtakes):
    """分析輪胎對超車的影響"""
    results = []
    
    for ot in overtakes:
        lap = ot['lap']
        overtaker = ot['overtaker']
        overtaken = ot['overtaken']
        
        # 獲取雙方在該圈的輪胎資訊
        overtaker_lap = laps_df[(laps_df['Driver'] == overtaker) & (laps_df['LapNumber'] == lap)]
        overtaken_lap = laps_df[(laps_df['Driver'] == overtaken) & (laps_df['LapNumber'] == lap)]
        
        if overtaker_lap.empty or overtaken_lap.empty:
            continue
        
        overtaker_compound = overtaker_lap.iloc[0].get('Compound', '')
        overtaken_compound = overtaken_lap.iloc[0].get('Compound', '')
        overtaker_tyre_age = overtaker_lap.iloc[0].get('TyreLife', 0)
        overtaken_tyre_age = overtaken_lap.iloc[0].get('TyreLife', 0)
        
        if not overtaker_compound or not overtaken_compound:
            continue
        
        results.append({
            'overtaker_compound': overtaker_compound,
            'overtaken_compound': overtaken_compound,
            'overtaker_tyre_age': overtaker_tyre_age or 0,
            'overtaken_tyre_age': overtaken_tyre_age or 0,
            'tyre_age_diff': (overtaken_tyre_age or 0) - (overtaker_tyre_age or 0),  # 正值 = 超車者輪胎更新
        })
    
    return results


# 主訓練循環
total_races = 0
total_overtakes = 0
all_tyre_overtakes = []

for year in [2023, 2024]:
    print(f'\n[{year}] 載入賽程...')
    try:
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
    except Exception as e:
        print(f'  無法載入: {e}')
        continue
    
    for race in races[:24]:
        try:
            session = fastf1.get_session(year, race, 'R')
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            laps = session.laps
            
            if laps.empty:
                continue
            
            # 計算超車數
            overtake_count, overtake_details = count_overtakes(laps)
            total_laps = int(laps['LapNumber'].max())
            
            if total_laps > 0:
                overtakes_per_lap = overtake_count / total_laps
                
                # 取得賽道名稱
                circuit_name = session.event.get('CircuitShortName', race)
                circuit_overtakes[circuit_name].append({
                    'overtakes': overtake_count,
                    'total_laps': total_laps,
                    'per_lap': overtakes_per_lap,
                    'year': year,
                })
                
                # 車手統計
                for ot in overtake_details:
                    driver_overtakes[ot['overtaker']]['made'] += 1
                    driver_overtakes[ot['overtaken']]['received'] += 1
                
                for driver in laps['Driver'].unique():
                    driver_overtakes[driver]['races'] += 1
                
                # 輪胎分析
                tyre_details = analyze_tyre_overtakes(laps, overtake_details)
                all_tyre_overtakes.extend(tyre_details)
                
                total_races += 1
                total_overtakes += overtake_count
                
                print(f'  {race}: {overtake_count} 超車 / {total_laps} 圈 = {overtakes_per_lap:.2f}/圈')
            
        except Exception as e:
            print(f'  {race}: ERROR - {str(e)[:40]}')
            continue

# 結果分析
print(f'\n{"="*70}')
print(f'總計: {total_races} 場比賽, {total_overtakes} 次超車')
print(f'{"="*70}')

# 1. 賽道超車率排名
print(f'\n[賽道超車率排名]')
print(f'{"賽道":<20} {"平均超車/圈":<12} {"樣本數":<8} {"難度建議":<10}')
print('-'*55)

circuit_stats = {}
for circuit, data_list in circuit_overtakes.items():
    avg_per_lap = np.mean([d['per_lap'] for d in data_list])
    total_ot = sum(d['overtakes'] for d in data_list)
    circuit_stats[circuit] = {
        'avg_per_lap': avg_per_lap,
        'total_overtakes': total_ot,
        'samples': len(data_list),
    }

# 按超車率排序 (低 = 難超車 = 高難度)
sorted_circuits = sorted(circuit_stats.items(), key=lambda x: x[1]['avg_per_lap'])

# 計算難度係數 (0.3 ~ 0.8，低超車率 = 高難度)
min_rate = sorted_circuits[0][1]['avg_per_lap']
max_rate = sorted_circuits[-1][1]['avg_per_lap']

for circuit, stats in sorted_circuits:
    # 正規化到 0.3 ~ 0.8 (低超車率 = 高難度)
    if max_rate > min_rate:
        normalized = (stats['avg_per_lap'] - min_rate) / (max_rate - min_rate)
        difficulty = 0.80 - (normalized * 0.50)  # 高超車率 → 低難度 0.30
    else:
        difficulty = 0.55
    
    stats['difficulty'] = difficulty
    print(f'{circuit:<20} {stats["avg_per_lap"]:>8.2f}      {stats["samples"]:>4}      {difficulty:.2f}')

# 2. 車手超車能力排名
print(f'\n[車手超車能力排名] (至少參加 10 場)')
print(f'{"車手":<8} {"超車":<8} {"被超":<8} {"淨超車":<10} {"超車率":<10}')
print('-'*50)

driver_stats = []
for driver, stats in driver_overtakes.items():
    if stats['races'] >= 10:
        net = stats['made'] - stats['received']
        ratio = stats['made'] / max(1, stats['received'])
        driver_stats.append({
            'driver': driver,
            'made': stats['made'],
            'received': stats['received'],
            'net': net,
            'ratio': ratio,
            'races': stats['races'],
        })

driver_stats.sort(key=lambda x: x['net'], reverse=True)
for d in driver_stats[:15]:
    print(f'{d["driver"]:<8} {d["made"]:>6}    {d["received"]:>6}    {d["net"]:>+6}      {d["ratio"]:>6.2f}')

# 3. 輪胎對超車的影響
print(f'\n[輪胎對超車的影響] (樣本: {len(all_tyre_overtakes)})')
print('-'*50)

if all_tyre_overtakes:
    df_tyre = pd.DataFrame(all_tyre_overtakes)
    
    # 輪胎年齡差異分析
    age_diff_groups = [
        ('新胎優勢 (>10圈)', df_tyre[df_tyre['tyre_age_diff'] > 10]),
        ('中等優勢 (5-10圈)', df_tyre[(df_tyre['tyre_age_diff'] >= 5) & (df_tyre['tyre_age_diff'] <= 10)]),
        ('相近 (-5~5圈)', df_tyre[(df_tyre['tyre_age_diff'] > -5) & (df_tyre['tyre_age_diff'] < 5)]),
        ('舊胎超車 (<-5圈)', df_tyre[df_tyre['tyre_age_diff'] <= -5]),
    ]
    
    print(f'{"輪胎差異":<20} {"超車次數":<12} {"比例":<10}')
    total = len(df_tyre)
    for name, group in age_diff_groups:
        count = len(group)
        pct = count / total * 100 if total > 0 else 0
        print(f'{name:<20} {count:>8}      {pct:>5.1f}%')
    
    # 輪胎組合分析
    print(f'\n[超車者 vs 被超者輪胎組合]')
    combo_stats = df_tyre.groupby(['overtaker_compound', 'overtaken_compound']).size()
    combo_stats = combo_stats.sort_values(ascending=False)
    print(combo_stats.head(10))

# 輸出 Python 格式
print(f'\n{"="*70}')
print('predictor.py 更新建議 - CIRCUIT_OVERTAKE_DIFFICULTY')
print(f'{"="*70}')
print('# 基於 2023-2024 真實超車數據訓練')
print('# 低超車率 = 高難度值')
print('CIRCUIT_OVERTAKE_DIFFICULTY = {')
for circuit, stats in sorted_circuits:
    print(f'    "{circuit}": {stats["difficulty"]:.2f},  # {stats["avg_per_lap"]:.2f} 超車/圈')
print('}')

# 車手超車能力係數
print(f'\n# 車手超車能力修正 (基於淨超車數)')
print('# ratio > 1.5 = 優秀超車手, < 0.8 = 易被超')
print('DRIVER_OVERTAKE_ABILITY = {')
for d in driver_stats[:10]:
    ability = min(1.3, max(0.7, 0.9 + (d['ratio'] - 1.0) * 0.2))
    print(f'    "{d["driver"]}": {ability:.2f},  # 淨超車 {d["net"]:+d}, 比率 {d["ratio"]:.2f}')
print('}')
