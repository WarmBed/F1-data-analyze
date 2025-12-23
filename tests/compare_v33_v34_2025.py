"""
直接驗證 v3.4 模型在 2025 賽季的表現
對比 v3.3 vs v3.4，特別關注 Great Britain
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error

# 2025 賽事映射（從 validate_2025_direct.py）
RACE_2025_MAPPING = {
    1: "Australia", 2: "China", 3: "Japan", 4: "Bahrain",
    5: "Saudi Arabia", 6: "Miami", 7: "Emilia Romagna", 8: "Monaco",
    9: "Spain", 10: "Canada", 11: "Austria", 12: "Great Britain",
    13: "Belgium", 14: "Hungary", 15: "Dutch", 16: "Italy",
    17: "Azerbaijan", 18: "Singapore", 19: "United States", 20: "Mexico",
    21: "Brazil", 22: "Las Vegas", 23: "Qatar", 24: "Abu Dhabi"
}

def parse_time_to_seconds(time_str):
    """解析時間字串（可能是 timedelta 或浮點數）"""
    if isinstance(time_str, (int, float)):
        return float(time_str)
    
    if isinstance(time_str, str):
        if 'days' in time_str:
            import re
            match = re.search(r'(\d+) days? ([\d:\.]+)', time_str)
            if match:
                days = int(match.group(1))
                time_part = match.group(2)
                hours, minutes, seconds = map(float, time_part.split(':'))
                return days * 86400 + hours * 3600 + minutes * 60 + seconds
        
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
        except:
            pass
    
    return None

def add_interaction_features_v33(df):
    """添加 v3.3 交互特徵"""
    df = df.copy()
    df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
    sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
    sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
    df['sector_cv'] = sector_std / (sector_mean + 1e-6)
    df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
    return df

def add_interaction_features_v34(df):
    """添加 v3.4 所有交互特徵"""
    df = add_interaction_features_v33(df)
    df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
    df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
    apex_std = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']].std(axis=1)
    df['speed_consistency'] = apex_std / (df['max_speed'] + 1e-6)
    return df

def load_2025_data(race_number):
    """載入 2025 賽事數據"""
    race_name = RACE_2025_MAPPING.get(race_number)
    if not race_name:
        return None, None
    
    # 搜索 JSON 檔案
    json_dir = Path("json/predictionJSON")
    pattern = f"race_{race_number}_*_*.json"
    files = list(json_dir.glob(pattern))
    
    if not files:
        return None, race_name
    
    # 載入最新檔案
    latest_file = max(files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取排位賽數據
    if 'qualifying' not in data or 'drivers' not in data['qualifying']:
        return None, race_name
    
    rows = []
    for driver_data in data['qualifying']['drivers']:
        if not isinstance(driver_data, dict):
            continue
        
        if 'track_features' not in driver_data or 'position' not in driver_data:
            continue
        
        tf = driver_data['track_features']
        
        # 解析實際排位時間
        actual_time = driver_data.get('actual_q_time') or driver_data.get('q_time')
        if actual_time:
            actual_time = parse_time_to_seconds(actual_time)
        
        if not actual_time:
            continue
        
        row = {
            'driver': driver_data.get('driver_name', 'unknown'),
            'position': driver_data['position'],
            'actual_q_time': actual_time,
            'ideal_s1': tf.get('ideal_s1'),
            'ideal_s2': tf.get('ideal_s2'),
            'ideal_s3': tf.get('ideal_s3'),
            'ideal_lap': tf.get('ideal_lap'),
            'low_speed_apex': tf.get('low_speed_apex'),
            'mid_speed_apex': tf.get('mid_speed_apex'),
            'high_speed_apex': tf.get('high_speed_apex'),
            'max_speed': tf.get('max_speed')
        }
        
        if all(row[k] is not None for k in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap']):
            rows.append(row)
    
    if not rows:
        return None, race_name
    
    df = pd.DataFrame(rows)
    return df, race_name

def validate_single_race(race_number, model_version='v3.4'):
    """驗證單一賽事"""
    df, race_name = load_2025_data(race_number)
    
    if df is None or df.empty:
        return None
    
    # 添加交互特徵
    if model_version == 'v3.3':
        df = add_interaction_features_v33(df)
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
            's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
        ]
        model_path = Path(f"models/track_specific_v3.3/{race_name}.pkl")
    else:  # v3.4
        df = add_interaction_features_v34(df)
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
            's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
            'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency'
        ]
        model_path = Path(f"models/track_specific_v3.4/{race_name}.pkl")
    
    # 清理數據
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    if df.empty:
        return None
    
    # 載入模型
    if not model_path.exists():
        return None
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # 預測
    X = df[feature_cols]
    y_actual = df['actual_q_time']
    y_pred = model.predict(X)
    
    # 評估
    mae = mean_absolute_error(y_actual, y_pred)
    spearman, _ = spearmanr(y_actual, y_pred)
    
    return {
        'race': race_name,
        'race_number': race_number,
        'mae': float(mae),
        'spearman': float(spearman),
        'n_samples': len(df)
    }

print("="*80)
print("v3.3 vs v3.4 - 2025 賽季驗證對比")
print("="*80)

results_v33 = {}
results_v34 = {}

# 驗證所有 2025 賽事
for race_num in range(1, 25):
    # v3.3
    result_v33 = validate_single_race(race_num, 'v3.3')
    if result_v33:
        results_v33[result_v33['race']] = result_v33
        print(f"\n[v3.3] Race {race_num:2d} - {result_v33['race']}")
        print(f"  MAE: {result_v33['mae']:.3f}s, Spearman: {result_v33['spearman']:.3f}")
    
    # v3.4
    result_v34 = validate_single_race(race_num, 'v3.4')
    if result_v34:
        results_v34[result_v34['race']] = result_v34
        print(f"[v3.4] Race {race_num:2d} - {result_v34['race']}")
        print(f"  MAE: {result_v34['mae']:.3f}s, Spearman: {result_v34['spearman']:.3f}")
        
        # 對比
        if result_v33:
            mae_change = result_v34['mae'] - result_v33['mae']
            spearman_change = result_v34['spearman'] - result_v33['spearman']
            
            mae_symbol = "✅" if mae_change < 0 else "❌"
            spearman_symbol = "✅" if spearman_change > 0 else "❌"
            
            print(f"  變化: MAE {mae_change:+.3f}s {mae_symbol}, Spearman {spearman_change:+.3f} {spearman_symbol}")

# 總結
print(f"\n{'='*80}")
print("總結對比")
print(f"{'='*80}")

common_races = set(results_v33.keys()) & set(results_v34.keys())

if common_races:
    print(f"\n共同驗證賽道數: {len(common_races)}")
    
    # Great Britain 專項對比
    if "Great Britain" in common_races:
        print(f"\n{'='*80}")
        print("Great Britain 專項對比")
        print(f"{'='*80}")
        
        gb_v33 = results_v33["Great Britain"]
        gb_v34 = results_v34["Great Britain"]
        
        print(f"\nv3.3: MAE {gb_v33['mae']:.3f}s, Spearman {gb_v33['spearman']:.3f}")
        print(f"v3.4: MAE {gb_v34['mae']:.3f}s, Spearman {gb_v34['spearman']:.3f}")
        
        mae_improvement = (gb_v33['mae'] - gb_v34['mae']) / gb_v33['mae'] * 100
        spearman_improvement = gb_v34['spearman'] - gb_v33['spearman']
        
        print(f"\n改進幅度:")
        print(f"  MAE:      {mae_improvement:+.1f}% ({gb_v34['mae'] - gb_v33['mae']:+.3f}s)")
        print(f"  Spearman: {spearman_improvement:+.3f}")
        
        if gb_v34['mae'] < gb_v33['mae'] and gb_v34['spearman'] > gb_v33['spearman']:
            print("\n✅✅✅ v3.4 全面改進 Great Britain 預測！")
        elif gb_v34['mae'] < gb_v33['mae']:
            print("\n✅ v3.4 改進 MAE，但 Spearman 未改善")
        elif gb_v34['spearman'] > gb_v33['spearman']:
            print("\n✅ v3.4 改進 Spearman，但 MAE 未改善")
        else:
            print("\n❌ v3.4 未能改進 Great Britain 預測")
    
    # 整體統計
    print(f"\n{'='*80}")
    print("整體統計對比")
    print(f"{'='*80}")
    
    mae_v33_list = [results_v33[r]['mae'] for r in common_races]
    mae_v34_list = [results_v34[r]['mae'] for r in common_races]
    spearman_v33_list = [results_v33[r]['spearman'] for r in common_races]
    spearman_v34_list = [results_v34[r]['spearman'] for r in common_races]
    
    print(f"\nv3.3: 平均 MAE {np.mean(mae_v33_list):.3f}s, 平均 Spearman {np.mean(spearman_v33_list):.3f}")
    print(f"v3.4: 平均 MAE {np.mean(mae_v34_list):.3f}s, 平均 Spearman {np.mean(spearman_v34_list):.3f}")
    
    # 改進/退步統計
    improvements = sum(1 for r in common_races if results_v34[r]['mae'] < results_v33[r]['mae'])
    print(f"\nMAE 改進賽道數: {improvements}/{len(common_races)}")
    
    improvements_spearman = sum(1 for r in common_races if results_v34[r]['spearman'] > results_v33[r]['spearman'])
    print(f"Spearman 改進賽道數: {improvements_spearman}/{len(common_races)}")
