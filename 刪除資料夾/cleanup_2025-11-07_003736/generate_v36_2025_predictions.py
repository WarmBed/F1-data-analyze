# -*- coding: utf-8 -*-
"""
v3.6 2025 賽季預測報告生成器
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


def find_2025_data_file(race_number):
    """找到 2025 年特定賽事的最新數據檔案"""
    json_dir = "json/predictionJSON"
    pattern = f"fp_q_data_2025_{race_number}_"
    
    matching_files = [f for f in os.listdir(json_dir) if f.startswith(pattern)]
    if not matching_files:
        return None
    
    # 返回最新的檔案（按時間戳排序）
    matching_files.sort(reverse=True)
    return os.path.join(json_dir, matching_files[0])


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


def load_2025_fp3_data(race_number):
    """載入 2025 年 FP3 數據"""
    data_file = find_2025_data_file(race_number)
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
    
    drivers_data = []
    for driver_code in data.get('drivers', []):
        # 檢查車手是否有 FP3 和 Q 數據
        if driver_code not in fp3_data or driver_code not in q_results:
            continue
        
        fp3 = fp3_data[driver_code]
        q = q_results[driver_code]
        
        # 提取特徵
        row = {
            'driver': driver_code,
            'ideal_s1': fp3.get('sector1_best'),
            'ideal_s2': fp3.get('sector2_best'),
            'ideal_s3': fp3.get('sector3_best'),
            'ideal_lap': fp3.get('best_lap_time'),
            'low_speed_apex': fp3.get('low_speed_apex'),
            'mid_speed_apex': fp3.get('mid_speed_apex'),
            'high_speed_apex': fp3.get('high_speed_apex'),
            'max_speed': fp3.get('speed_trap_max'),
            'actual_q_time': parse_timedelta(q.get('best_time'))
        }
        
        # 計算 ideal_lap 如果不存在
        if row['ideal_lap'] is None:
            s1, s2, s3 = row['ideal_s1'], row['ideal_s2'], row['ideal_s3']
            if all(x is not None for x in [s1, s2, s3]):
                row['ideal_lap'] = s1 + s2 + s3
        
        # 檢查是否所有特徵都存在
        if all(v is not None for k, v in row.items() if k != 'driver'):
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
        fp3_data = load_2025_fp3_data(race_num)
        
        if fp3_data is None or fp3_data.empty:
            print(f"  ❌ 沒有 2025 年數據")
            continue
        
        print(f"  ✅ 載入 {len(fp3_data)} 位車手數據")
        
        model_data = models[track_name]
        model = model_data['model']
        feature_names = model_data['feature_names']
        cv_mae = model_data.get('best_cv_mae', 0)
        
        # 預測
        X_pred = fp3_data[feature_names].values
        drivers = fp3_data['driver'].values
        y_pred = model.predict(X_pred)
        y_actual = fp3_data['actual_q_time'].values
        
        # 創建結果 DataFrame
        predictions_df = pd.DataFrame({
            'driver': drivers,
            'predicted_time': y_pred,
            'actual_time': y_actual
        })
        
        # 排名
        predictions_df = predictions_df.sort_values('predicted_time')
        predictions_df['predicted_rank'] = range(1, len(predictions_df) + 1)
        
        # 實際排名
        actual_sorted = predictions_df.sort_values('actual_time')
        actual_sorted['actual_rank'] = range(1, len(actual_sorted) + 1)
        predictions_df = predictions_df.merge(
            actual_sorted[['driver', 'actual_rank']], 
            on='driver'
        )
        
        # 計算誤差
        predictions_df['time_error'] = predictions_df['predicted_time'] - predictions_df['actual_time']
        predictions_df['time_error_pct'] = (predictions_df['time_error'].abs() / predictions_df['actual_time'] * 100)
        predictions_df['rank_error'] = (predictions_df['predicted_rank'] - predictions_df['actual_rank']).abs()
        
        # 計算指標
        mae = predictions_df['time_error'].abs().mean()
        spearman, _ = spearmanr(predictions_df['actual_rank'], predictions_df['predicted_rank'])
        
        # Top5 準確率
        pred_top5 = set(predictions_df.nsmallest(5, 'predicted_time')['driver'])
        actual_top5 = set(predictions_df.nsmallest(5, 'actual_time')['driver'])
        top5_correct = len(pred_top5 & actual_top5)
        top5_accuracy = top5_correct / 5 * 100
        
        print(f"  📊 MAE: {mae:.3f}s, Spearman: {spearman:.3f}, Top5: {top5_accuracy:.0f}% ({top5_correct}/5)")
        
        results[track_name] = {
            'race_number': race_num,
            'predictions': predictions_df,
            'mae': mae,
            'spearman': spearman,
            'top5_correct': top5_correct,
            'top5_accuracy': top5_accuracy,
            'cv_mae': cv_mae
        }
    
    return results


def generate_markdown_report(results, output_path):
    """Generate detailed markdown report"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# v3.6 2025 賽季 Top5 預測分析報告\n\n")
        f.write(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**模型版本**: v3.6 (Optuna 超參數優化賽道專家模型)\n")
        f.write(f"**訓練數據**: 2022-2024 年（3 年歷史數據）\n")
        f.write(f"**預測年份**: 2025 年賽季（真正的未來預測）\n")
        f.write(f"**分析賽事**: {len(results)} 場\n\n")
        f.write("---\n\n")
        
        # Overall statistics
        f.write("## 📊 整體統計\n\n")
        
        total_correct = sum(r['top5_correct'] for r in results.values())
        total_possible = len(results) * 5
        overall_accuracy = total_correct / total_possible * 100
        
        avg_mae = np.mean([r['mae'] for r in results.values()])
        avg_spearman = np.mean([r['spearman'] for r in results.values()])
        avg_cv_mae = np.mean([r['cv_mae'] for r in results.values()])
        
        f.write("| 指標 | 數值 |\n")
        f.write("|------|------|\n")
        f.write(f"| **Top5 準確率** | **{overall_accuracy:.1f}%** ({total_correct}/{total_possible}) |\n")
        f.write(f"| **平均 MAE** | {avg_mae:.3f}s |\n")
        f.write(f"| **平均訓練 CV MAE** | {avg_cv_mae:.3f}s |\n")
        f.write(f"| **平均 Spearman** | {avg_spearman:.3f} |\n")
        f.write(f"| **分析賽事** | {len(results)} |\n\n")
        
        # Per-track analysis
        f.write("## 🏁 賽道詳細分析\n\n")
        
        for track, data in sorted(results.items(), key=lambda x: x[1]['top5_accuracy'], reverse=True):
            predictions = data['predictions']
            
            f.write(f"### {track} (Race {data['race_number']})\n\n")
            
            # Metrics
            f.write(f"**性能指標:**\n")
            f.write(f"- 訓練 CV MAE: {data['cv_mae']:.3f}s\n")
            f.write(f"- 2025 預測 MAE: {data['mae']:.3f}s\n")
            f.write(f"- Spearman 相關性: {data['spearman']:.3f}\n")
            f.write(f"- Top5 準確率: {data['top5_accuracy']:.1f}% ({data['top5_correct']}/5)\n\n")
            
            # Top5 prediction vs actual
            f.write("**預測 Top5 vs 實際 Top5:**\n\n")
            f.write("| 預測排名 | 車手 | 預測時間 | 實際時間 | 實際排名 | 時間誤差 | 誤差% |\n")
            f.write("|---------|------|---------|---------|---------|---------|-------|\n")
            
            top5_pred = predictions.head(5)
            for _, row in top5_pred.iterrows():
                f.write(f"| {int(row['predicted_rank'])} | {row['driver']} | ")
                f.write(f"{row['predicted_time']:.3f}s | {row['actual_time']:.3f}s | ")
                f.write(f"{int(row['actual_rank'])} | ")
                f.write(f"{row['time_error']:+.3f}s | {row['time_error_pct']:.2f}% |\n")
            
            f.write("\n")
            
            # Top5 comparison
            pred_top5 = set(predictions.nsmallest(5, 'predicted_time')['driver'])
            actual_top5 = set(predictions.nsmallest(5, 'actual_time')['driver'])
            correct = pred_top5 & actual_top5
            missed = actual_top5 - pred_top5
            false_pos = pred_top5 - actual_top5
            
            f.write(f"**Top5 車手匹配:**\n")
            f.write(f"- 實際 Top5: {', '.join(sorted(actual_top5))}\n")
            f.write(f"- 預測 Top5: {', '.join(sorted(pred_top5))}\n")
            f.write(f"- 預測正確: {', '.join(sorted(correct))}\n")
            if missed:
                f.write(f"- 漏掉: {', '.join(sorted(missed))}\n")
            if false_pos:
                f.write(f"- 誤判: {', '.join(sorted(false_pos))}\n")
            
            f.write("\n---\n\n")
    
    print(f"\n✅ 報告已生成: {output_path}")


def main():
    print("="*70)
    print("v3.6 2025 賽季預測報告生成器")
    print("="*70)
    print("訓練數據: 2022-2024 年")
    print("預測目標: 2025 年賽季")
    print("="*70)
    
    # Load models
    print("\n📦 載入 v3.6 模型...")
    models = load_models()
    print(f"✅ 已載入 {len(models)} 個模型: {', '.join(sorted(models.keys()))}\n")
    
    # Predict 2025 races
    print("🔮 開始預測 2025 年賽季...")
    print("="*70)
    results = predict_2025(models)
    print("="*70)
    
    if not results:
        print("\n❌ 沒有可用的預測結果！")
        return
    
    # Generate report
    print(f"\n✅ 成功預測 {len(results)} 場賽事")
    print("\n📝 生成 Markdown 報告...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"V3.6_2025_PREDICTIONS_{timestamp}.md"
    generate_markdown_report(results, report_path)
    
    print("\n" + "="*70)
    print("✅ 完成！")
    print("="*70)
    print(f"📄 報告檔案: {report_path}")


if __name__ == "__main__":
    main()
