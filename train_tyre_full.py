"""
輪胎性能完整訓練 - 2023-2024 所有比賽
用於更新 predictor.py 的 TYRE_PERFORMANCE
"""
import fastf1
import numpy as np
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print('='*70)
print('輪胎性能完整訓練 - 2023-2024 所有比賽')
print('='*70)

# 收集數據
all_stints = []

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
            
            stint_count = 0
            # 按車手分析
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber')
                
                prev_compound = None
                stint_laps = []
                
                for _, lap in driver_laps.iterrows():
                    compound = lap.get('Compound', '')
                    tyre_life = lap.get('TyreLife', 0)
                    
                    # 新 stint 檢測
                    if compound != prev_compound or (len(stint_laps) > 0 and tyre_life < 3):
                        if len(stint_laps) >= 5 and prev_compound:
                            all_stints.append({
                                'year': year,
                                'race': race,
                                'compound': prev_compound,
                                'laps': stint_laps.copy()
                            })
                        stint_laps = []
                    
                    # 收集圈時
                    lt = lap.get('LapTime')
                    if pd.notna(lt):
                        if hasattr(lt, 'total_seconds'):
                            lt_sec = lt.total_seconds()
                        else:
                            lt_sec = float(lt)
                        if 60 < lt_sec < 180:
                            stint_laps.append(lt_sec)
                    
                    prev_compound = compound
                
                # 最後一個 stint
                if len(stint_laps) >= 5 and prev_compound:
                        all_stints.append({
                            'year': year,
                            'race': race,
                            'compound': prev_compound,
                            'laps': stint_laps
                        })
                        stint_count += 1
            
            print(f'  {race}: {stint_count} stints')
        except Exception as e:
            print(f'  {race}: ERROR - {str(e)[:40]}')
            continue

print(f'\n總計收集: {len(all_stints)} stints')

# 分析輪胎性能
print('\n' + '='*70)
print('輪胎性能分析結果')
print('='*70)

results = {}

# 計算 SOFT 基準
soft_stints = [s for s in all_stints if s['compound'] == 'SOFT']
if soft_stints:
    soft_new_paces = [np.mean(s['laps'][:3]) for s in soft_stints if len(s['laps']) >= 3]
    soft_baseline = np.median(soft_new_paces)
else:
    soft_baseline = 90.0

for compound in ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']:
    stints = [s for s in all_stints if s['compound'] == compound]
    
    if len(stints) < 10:
        print(f'{compound}: 樣本不足 ({len(stints)})')
        continue
    
    # 新胎速度 (前3圈)
    new_paces = [np.mean(s['laps'][:3]) for s in stints if len(s['laps']) >= 3]
    avg_new = np.median(new_paces)
    relative_speed = soft_baseline / avg_new
    
    # 衰退率 (線性迴歸)
    deg_rates = []
    for s in stints:
        if len(s['laps']) >= 10:
            x = np.arange(len(s['laps']))
            slope, _ = np.polyfit(x, s['laps'], 1)
            deg_rates.append(slope)
    
    avg_deg = np.median(deg_rates) if deg_rates else 0.03
    
    # cliff 檢測 (圈時突然增加 >1.5秒)
    cliff_laps = []
    for s in stints:
        for i in range(5, len(s['laps'])):
            if s['laps'][i] - s['laps'][i-1] > 1.5:
                cliff_laps.append(i)
                break
    
    avg_cliff = np.median(cliff_laps) if cliff_laps else 35
    cliff_rate = len(cliff_laps) / len(stints)
    
    # 轉換為係數
    deg_coef = avg_deg / avg_new  # 相對衰退
    
    results[compound] = {
        'speed': round(relative_speed, 4),
        'deg_per_lap': round(max(0.0001, deg_coef), 5),
        'ideal_laps': int(avg_cliff * 0.7),
        'cliff_lap': int(avg_cliff),
        'samples': len(stints),
        'avg_deg_sec': round(avg_deg, 4),
    }
    
    print(f'\n{compound} ({len(stints)} stints):')
    print(f'  相對速度: {relative_speed:.4f} (vs SOFT)')
    print(f'  衰退率:   {avg_deg:.4f} s/lap → 係數 {deg_coef:.5f}')
    print(f'  cliff:    第 {int(avg_cliff)} 圈 (檢測率 {cliff_rate*100:.1f}%)')

print('\n' + '='*70)
print('predictor.py TYRE_PERFORMANCE 更新值')
print('='*70)
print('TYRE_PERFORMANCE = {')
for c, r in results.items():
    print(f'    "{c}": {{"speed": {r["speed"]}, "deg_per_lap": {r["deg_per_lap"]}, "ideal_laps": {r["ideal_laps"]}, "cliff_lap": {r["cliff_lap"]}}},  # {r["samples"]} stints')
print('}')
