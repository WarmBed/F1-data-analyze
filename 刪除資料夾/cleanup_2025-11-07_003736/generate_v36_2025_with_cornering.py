#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3.6 2025 賽季預測報告生成器（整合彎角分析）
用 2022-2024 訓練的模型預測 2025 年賽季
"""

import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import spearmanr
import sys
import json

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 2025 賽季賽道映射（賽事編號 → 賽道名稱）
RACE_MAPPING_2025 = {
    1: 'Bahrain',
    2: 'Saudi Arabia',
    3: 'Japan',
    6: 'Monaco',
    9: 'Canada',
    11: 'Great Britain',
    13: 'Hungary',
    14: 'Netherlands',
    15: 'Italy',
    16: 'Azerbaijan'
}


def load_models():
    """Load all v3.6 models"""
    models_dir = "models/v3.6"
    models = {}
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    
    for model_file in model_files:
        track_name = model_file.replace('.pkl', '')
        model_path = os.path.join(models_dir, model_file)
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        models[track_name] = model_data
    
    return models


def find_2025_data_file(race_number, track_name):
    """找到 2025 年特定賽事的最新數據檔案（支援賽事編號和賽道名稱兩種格式）"""
    json_dir = "json/predictionJSON"
    
    # 優先使用賽道名稱（新格式，包含衝刺賽 FP3）
    pattern_name = f"fp_q_data_2025_{track_name}_"
    matching_files = [f for f in os.listdir(json_dir) if f.startswith(pattern_name)]
    
    # 如果找不到，嘗試使用賽事編號（舊格式）
    if not matching_files:
        pattern_num = f"fp_q_data_2025_{race_number}_"
        matching_files = [f for f in os.listdir(json_dir) if f.startswith(pattern_num)]
    
    if not matching_files:
        return None
    
    # 返回最新的檔案（按時間戳排序）
    matching_files.sort(reverse=True)
    return os.path.join(json_dir, matching_files[0])


def find_cornering_file(track_name, session='FP3'):
    """找到 2025 年彎角分析檔案"""
    json_dir = "json"
    filename = f"all_drivers_cornering_analysis_2025_{track_name}_{session}.json"
    filepath = os.path.join(json_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    return None


def parse_timedelta(td_str):
    """將 '0 days 00:01:15.096000' 格式轉換為秒數"""
    if not td_str or td_str == 'nan':
        return None
    try:
        parts = td_str.split()
        time_part = parts[-1]  # 取 HH:MM:SS.ffffff
        h, m, s = time_part.split(':')
        return float(h) * 3600 + float(m) * 60 + float(s)
    except:
        return None


def load_cornering_data(track_name, session='FP3'):
    """載入彎角分析數據"""
    cornering_file = find_cornering_file(track_name, session)
    if not cornering_file:
        return {}
    
    with open(cornering_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取每位車手的彎角速度
    corner_speeds = {}
    
    if 'fastest_lap_analysis' in data:
        drivers_data = data['fastest_lap_analysis'].get('drivers', [])
        
        for driver_info in drivers_data:
            driver = driver_info['driver']
            corners = driver_info.get('corners', {})
            
            # 找出 low/mid/high speed 彎角的 apex_speed
            low_speed = None
            mid_speed = None
            high_speed = None
            
            for corner_name, corner_data in corners.items():
                if 'low_speed' in corner_name:
                    low_speed = corner_data.get('apex_speed')
                elif 'mid_speed' in corner_name:
                    mid_speed = corner_data.get('apex_speed')
                elif 'high_speed' in corner_name:
                    high_speed = corner_data.get('apex_speed')
            
            corner_speeds[driver] = {
                'low_speed_apex': low_speed,
                'mid_speed_apex': mid_speed,
                'high_speed_apex': high_speed
            }
    
    return corner_speeds


def load_2025_fp3_data(race_number, track_name):
    """載入 2025 年 FP3 數據並整合彎角分析"""
    # 載入 FP3/Q 數據（支援賽道名稱和賽事編號）
    data_file = find_2025_data_file(race_number, track_name)
    if not data_file:
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查必要數據是否存在
    if 'practice_sessions' not in data or 'FP3' not in data['practice_sessions']:
        return None
    if 'qualifying' not in data or 'results' not in data['qualifying']:
        return None
    
    fp3_data = data['practice_sessions']['FP3']['driver_data']
    q_results = data['qualifying']['results']
    
    # 載入彎角分析數據
    corner_speeds = load_cornering_data(track_name, 'FP3')
    
    drivers_data = []
    for driver_code in data.get('drivers', []):
        # 檢查車手是否有 FP3 和 Q 數據
        if driver_code not in fp3_data or driver_code not in q_results:
            continue
        
        fp3 = fp3_data[driver_code]
        q = q_results[driver_code]
        
        # 提取基本特徵
        row = {
            'driver': driver_code,
            'ideal_s1': fp3.get('sector1_best'),
            'ideal_s2': fp3.get('sector2_best'),
            'ideal_s3': fp3.get('sector3_best'),
            'ideal_lap': fp3.get('best_lap_time'),
            'max_speed': fp3.get('speed_trap_max'),
            'actual_q_time': parse_timedelta(q.get('best_time'))
        }
        
        # 計算 ideal_lap 如果不存在
        if row['ideal_lap'] is None:
            s1, s2, s3 = row['ideal_s1'], row['ideal_s2'], row['ideal_s3']
            if all(x is not None for x in [s1, s2, s3]):
                row['ideal_lap'] = s1 + s2 + s3
        
        # 整合彎角速度（如果找不到，使用 0 作為預設值，如同 v3.5 和 v3.6 訓練邏輯）
        if driver_code in corner_speeds:
            row['low_speed_apex'] = corner_speeds[driver_code]['low_speed_apex'] or 0.0
            row['mid_speed_apex'] = corner_speeds[driver_code]['mid_speed_apex'] or 0.0
            row['high_speed_apex'] = corner_speeds[driver_code]['high_speed_apex'] or 0.0
        else:
            # 沒有彎角數據時，使用 0（如 v3.5 策略）
            row['low_speed_apex'] = 0.0
            row['mid_speed_apex'] = 0.0
            row['high_speed_apex'] = 0.0
        
        # 檢查基本特徵是否存在（彎角速度允許為 0）
        basic_features = ['ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap', 'max_speed', 'actual_q_time']
        if all(row[k] is not None for k in basic_features):
            drivers_data.append(row)
    
    if not drivers_data:
        return None
    
    return pd.DataFrame(drivers_data)


def predict_2025(models):
    """Predict 2025 races"""
    results = {}
    
    for race_num, track_name in sorted(RACE_MAPPING_2025.items()):
        print(f"\n[{track_name}] (Race {race_num})")
        
        if track_name not in models:
            print(f"  ❌ 沒有訓練模型")
            continue
        
        # 載入 2025 數據
        fp3_data = load_2025_fp3_data(race_num, track_name)
        
        if fp3_data is None or fp3_data.empty:
            print(f"  ❌ 沒有 2025 年數據或彎角分析數據")
            continue
        
        # 預測
        model_data = models[track_name]
        model = model_data['model']
        feature_names = model_data['feature_names']
        
        X = fp3_data[feature_names]
        predictions = model.predict(X)
        
        fp3_data['predicted_q_time'] = predictions
        
        # 排序並計算排名
        fp3_data = fp3_data.sort_values('predicted_q_time')
        fp3_data['predicted_position'] = range(1, len(fp3_data) + 1)
        
        # 計算實際排名
        fp3_data = fp3_data.sort_values('actual_q_time')
        fp3_data['actual_position'] = range(1, len(fp3_data) + 1)
        
        # 計算誤差
        fp3_data['position_error'] = abs(fp3_data['predicted_position'] - fp3_data['actual_position'])
        fp3_data['time_error'] = abs(fp3_data['predicted_q_time'] - fp3_data['actual_q_time'])
        
        # Top5 分析
        top5_actual = set(fp3_data.nsmallest(5, 'actual_position')['driver'].values)
        top5_predicted = set(fp3_data.nsmallest(5, 'predicted_position')['driver'].values)
        top5_correct = len(top5_actual & top5_predicted)
        
        mae = fp3_data['time_error'].mean()
        corr, _ = spearmanr(fp3_data['actual_position'], fp3_data['predicted_position'])
        
        print(f"  ✓ {len(fp3_data)} 位車手")
        print(f"  MAE: {mae:.3f}s")
        print(f"  Top5 準確率: {top5_correct}/5 ({top5_correct*20:.0f}%)")
        print(f"  Spearman 相關: {corr:.3f}")
        
        results[track_name] = {
            'data': fp3_data,
            'mae': mae,
            'top5_correct': top5_correct,
            'correlation': corr
        }
    
    return results


def generate_report(results):
    """生成報告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"V3_6_2025_PREDICTION_REPORT_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# v3.6 2025 賽季預測報告\n\n")
        f.write(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**模型版本**: v3.6 (Optuna 500 trials)\n")
        f.write(f"**訓練期間**: 2022-2024\n")
        f.write(f"**預測賽季**: 2025\n\n")
        
        f.write("## 整體統計\n\n")
        
        total_mae = np.mean([r['mae'] for r in results.values()])
        total_top5 = sum(r['top5_correct'] for r in results.values())
        total_races = len(results)
        avg_corr = np.mean([r['correlation'] for r in results.values()])
        
        f.write(f"- **預測賽事數**: {total_races}\n")
        f.write(f"- **平均 MAE**: {total_mae:.3f}s\n")
        f.write(f"- **Top5 總準確率**: {total_top5}/{total_races*5} ({total_top5/(total_races*5)*100:.1f}%)\n")
        f.write(f"- **平均 Spearman 相關**: {avg_corr:.3f}\n\n")
        
        f.write("## 各賽道詳細結果\n\n")
        
        for track_name in sorted(results.keys()):
            result = results[track_name]
            df = result['data']
            
            f.write(f"### {track_name}\n\n")
            f.write(f"- **MAE**: {result['mae']:.3f}s\n")
            f.write(f"- **Top5 準確率**: {result['top5_correct']}/5 ({result['top5_correct']*20:.0f}%)\n")
            f.write(f"- **Spearman 相關**: {result['correlation']:.3f}\n\n")
            
            # 預測 Top5
            top5_pred = df.nsmallest(5, 'predicted_position')[['driver', 'predicted_position', 'actual_position', 'position_error']]
            f.write("**預測 Top5**:\n\n")
            f.write("| 排名 | 車手 | 實際排名 | 誤差 |\n")
            f.write("|------|------|----------|------|\n")
            for idx, row in top5_pred.iterrows():
                f.write(f"| {int(row['predicted_position'])} | {row['driver']} | {int(row['actual_position'])} | {int(row['position_error'])} |\n")
            f.write("\n")
            
            # 實際 Top5
            top5_actual = df.nsmallest(5, 'actual_position')[['driver', 'actual_position', 'predicted_position']]
            f.write("**實際 Top5**:\n\n")
            f.write("| 排名 | 車手 | 預測排名 |\n")
            f.write("|------|------|----------|\n")
            for idx, row in top5_actual.iterrows():
                f.write(f"| {int(row['actual_position'])} | {row['driver']} | {int(row['predicted_position'])} |\n")
            f.write("\n")
    
    print(f"\n✅ 報告已生成: {report_file}")
    return report_file


def main():
    print("=" * 70)
    print("v3.6 2025 賽季預測")
    print("=" * 70)
    
    # 載入模型
    print("\n載入 v3.6 模型...")
    models = load_models()
    print(f"✓ 載入 {len(models)} 個賽道模型")
    
    # 預測 2025
    print("\n開始預測 2025 賽季...")
    results = predict_2025(models)
    
    if not results:
        print("\n❌ 沒有任何預測結果")
        return
    
    # 生成報告
    print("\n生成報告...")
    report_file = generate_report(results)
    
    # 保存 JSON 格式（用於比較分析）
    print("\n保存 JSON 格式...")
    json_results = {}
    for track, result in results.items():
        df = result['data']
        json_results[track] = {
            'mae': float(result['mae']),
            'correlation': float(result['correlation']),
            'spearman': float(result['correlation']),  # 別名，用於兼容
            'top5_correct': int(result['top5_correct']),
            'predictions': df[['driver', 'actual_q_time', 'predicted_q_time',
                              'actual_position', 'predicted_position']].rename(columns={
                'actual_q_time': 'actual_q_time',
                'predicted_q_time': 'predicted_time',
                'actual_position': 'actual_rank',
                'predicted_position': 'predicted_rank'
            }).to_dict('records')
        }
    
    json_file = 'v3.6_2025_predictions.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON 結果已保存: {json_file}")
    
    print("\n" + "=" * 70)
    print("完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
