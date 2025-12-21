#!/usr/bin/env python3
"""
批次訓練所有賽道的 v3.0 模型 (2022-2024)
然後對 2025 賽季進行預測並生成完整分析報告
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score

# 導入 v3.0 trainer
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


def get_available_races():
    """掃描可用的賽事"""
    races_2022 = ['Abu Dhabi', 'Australia', 'Azerbaijan', 'Bahrain', 'Belgium', 'Canada', 'France', 
                  'Great Britain', 'Hungary', 'Italy', 'Japan', 'Mexico', 'Miami', 'Monaco', 
                  'Netherlands', 'Saudi Arabia', 'Singapore', 'Spain', 'United States']
    races_2023 = ['Abu Dhabi', 'Australia', 'Bahrain', 'Canada', 'Dutch', 'Great Britain', 'Hungary', 
                  'Italy', 'Japan', 'Las Vegas', 'Mexico', 'Miami', 'Monaco', 'Netherlands', 
                  'Saudi Arabia', 'Singapore', 'Spain']
    races_2024 = ['Abu Dhabi', 'Australia', 'Azerbaijan', 'Bahrain', 'Belgium', 'Canada', 
                  'Emilia Romagna', 'Hungary', 'Italy', 'Japan', 'Las Vegas', 'Mexico', 'Monaco', 
                  'Netherlands', 'Saudi Arabia', 'Singapore', 'Spain']
    
    return {
        2022: races_2022,
        2023: races_2023,
        2024: races_2024
    }


def find_2025_races():
    """找出 2025 年可用的賽事"""
    json_dir = Path('json/predictionJSON')
    fp_q_files = list(json_dir.glob('fp_q_data_2025_*.json'))
    
    races_2025 = set()
    for file in fp_q_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            race_name = data.get('race_name') or data.get('metadata', {}).get('race')
            if race_name:
                races_2025.add(race_name)
        except:
            pass
    
    return sorted(races_2025)


def train_track_model(race_name, years=[2022, 2023, 2024]):
    """訓練單個賽道的模型"""
    print(f"\n{'='*70}")
    print(f"Training: {race_name}")
    print(f"{'='*70}")
    
    try:
        trainer = TrackSpecificTrainerV3(verbose=False)
        
        # 訓練模型（內部會自動載入數據）
        result = trainer.train_track_model_v3(
            track_name=race_name,
            start_year=years[0],
            end_year=years[-1]
        )
        
        if not result.get('success', False):
            print(f"  [ERROR] Training failed for {race_name}: {result.get('message', 'Unknown error')}")
            return None
        
        performance = result
        
        # 儲存模型
        model_path = trainer.save_model(track_name=race_name)
        
        print(f"  [SUCCESS] Model saved: {model_path}")
        print(f"  Train MAE: {performance['train_mae']:.3f}s")
        print(f"  Test MAE: {performance['test_mae']:.3f}s")
        print(f"  Test R2: {performance['test_r2']:.4f}")
        
        return {
            'race': race_name,
            'model_path': str(model_path),
            'performance': performance,
            'samples': performance.get('train_samples', 0) + performance.get('test_samples', 0)
        }
    
    except Exception as e:
        print(f"  [ERROR] {race_name}: {e}")
        return None


def predict_2025_race(race_name, model_path):
    """對 2025 賽事進行預測"""
    print(f"\n  Predicting 2025 {race_name}...")
    
    try:
        # 載入模型
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        
        # 載入 2025 數據
        fp_q_file = None
        json_dir = Path('json/predictionJSON')
        for file in json_dir.glob(f'fp_q_data_2025_*.json'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                race = data.get('race_name') or data.get('metadata', {}).get('race')
                if race == race_name:
                    fp_q_file = file
                    break
            except:
                pass
        
        if not fp_q_file:
            print(f"    [SKIP] No 2025 data found for {race_name}")
            return None
        
        with open(fp_q_file, 'r', encoding='utf-8') as f:
            fp_q_data = json.load(f)
        
        # 載入彎角數據
        corner_file = Path(f'json/all_drivers_cornering_analysis_2025_{race_name}_FP3.json')
        if not corner_file.exists():
            print(f"    [SKIP] No corner data for 2025 {race_name}")
            return None
        
        with open(corner_file, 'r', encoding='utf-8') as f:
            corner_data = json.load(f)
        
        # 提取特徵
        features_list = extract_2025_features(fp_q_data, corner_data)
        if not features_list:
            print(f"    [SKIP] Failed to extract features for {race_name}")
            return None
        
        df = pd.DataFrame(features_list)
        
        # 預測
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
            'max_speed'
        ]
        
        X = df[feature_cols]
        predictions = model.predict(X)
        
        df['predicted_q_time'] = predictions
        df['predicted_position'] = df['predicted_q_time'].rank()
        
        # 評估
        mae = mean_absolute_error(df['actual_q_time'], df['predicted_q_time'])
        r2 = r2_score(df['actual_q_time'], df['predicted_q_time'])
        spearman_corr, _ = spearmanr(df['actual_position'], df['predicted_position'])
        
        print(f"    MAE: {mae:.4f}s | R2: {r2:.4f} | Spearman: {spearman_corr:.4f}")
        
        return {
            'race': race_name,
            'mae': mae,
            'r2': r2,
            'spearman': spearman_corr,
            'predictions': df.to_dict('records'),
            'drivers_count': len(df)
        }
    
    except Exception as e:
        print(f"    [ERROR] {race_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_2025_features(fp_q_data, corner_data):
    """提取 2025 特徵（與 test_v3_prediction.py 相同邏輯）"""
    features_list = []
    
    # 數據結構
    fp3_drivers = fp_q_data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
    q_results = fp_q_data.get('qualifying', {}).get('results', {})
    
    # 彎角數據
    corner_drivers = {d['driver']: d for d in corner_data.get('fastest_lap_analysis', {}).get('drivers', [])}
    selected_corners = corner_data.get('selected_corners', {})
    
    low_corner_num = selected_corners.get('low_speed', {}).get('corner_number')
    mid_corner_num = selected_corners.get('mid_speed', {}).get('corner_number')
    high_corner_num = selected_corners.get('high_speed', {}).get('corner_number')
    
    for driver in fp3_drivers.keys():
        if driver not in q_results or driver not in corner_drivers:
            continue
        
        fp3_data = fp3_drivers[driver]
        q_data = q_results[driver]
        corner_driver_data = corner_drivers[driver]
        
        # 提取 Q 時間
        q_time_str = str(q_data['best_time'])
        if 'days' in q_time_str:
            time_parts = q_time_str.split(' ')[-1]
            h, m, s = time_parts.split(':')
            actual_q_time = int(h) * 3600 + int(m) * 60 + float(s)
        else:
            continue
        
        # 特徵向量
        features = {
            'driver': driver,
            'ideal_s1': fp3_data.get('sector1_best', np.nan),
            'ideal_s2': fp3_data.get('sector2_best', np.nan),
            'ideal_s3': fp3_data.get('sector3_best', np.nan),
            'ideal_lap': fp3_data.get('best_lap_time', np.nan),
            'low_speed_apex': 0.0,
            'mid_speed_apex': 0.0,
            'high_speed_apex': 0.0,
            'max_speed': fp3_data.get('speed_trap_max', np.nan),
            'actual_q_time': actual_q_time,
            'actual_position': q_data['position']
        }
        
        # 彎角速度
        corners_dict = corner_driver_data.get('corners', {})
        if low_corner_num:
            corner_key = f"low_speed_corner_{low_corner_num}"
            if corner_key in corners_dict:
                features['low_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        if mid_corner_num:
            corner_key = f"mid_speed_corner_{mid_corner_num}"
            if corner_key in corners_dict:
                features['mid_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        if high_corner_num:
            corner_key = f"high_speed_corner_{high_corner_num}"
            if corner_key in corners_dict:
                features['high_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
        
        # 驗證數據完整性
        if all(not np.isnan(features[k]) for k in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'max_speed']):
            if all(features[k] > 0 for k in ['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']):
                features_list.append(features)
    
    return features_list


def generate_race_report(prediction_result):
    """生成單場賽事分析報告"""
    if not prediction_result:
        return ""
    
    df = pd.DataFrame(prediction_result['predictions'])
    df_sorted = df.sort_values('predicted_position')
    
    report = f"\n## {prediction_result['race']}\n\n"
    report += f"**Performance Metrics:**\n"
    report += f"- MAE: {prediction_result['mae']:.4f}s\n"
    report += f"- R²: {prediction_result['r2']:.4f}\n"
    report += f"- Spearman: {prediction_result['spearman']:.4f}\n"
    report += f"- Drivers: {prediction_result['drivers_count']}\n\n"
    
    # Top 10 預測 vs 實際
    report += "**Top 10 Predictions:**\n\n"
    report += "| Pred | Driver | Pred Time | Actual Time | Actual Pos | Error |\n"
    report += "|------|--------|-----------|-------------|------------|-------|\n"
    
    for idx, row in df_sorted.head(10).iterrows():
        pred_pos = int(row['predicted_position'])
        actual_pos = int(row['actual_position'])
        error = row['predicted_q_time'] - row['actual_q_time']
        
        report += f"| {pred_pos} | {row['driver']} | {row['predicted_q_time']:.3f}s | "
        report += f"{row['actual_q_time']:.3f}s | {actual_pos} | {error:+.3f}s |\n"
    
    # 最大誤差分析
    df['position_error'] = abs(df['predicted_position'] - df['actual_position'])
    max_error_row = df.loc[df['position_error'].idxmax()]
    
    report += f"\n**Biggest Position Error:**\n"
    report += f"- Driver: {max_error_row['driver']}\n"
    report += f"- Predicted: P{int(max_error_row['predicted_position'])}\n"
    report += f"- Actual: P{int(max_error_row['actual_position'])}\n"
    report += f"- Error: {int(max_error_row['position_error'])} positions\n"
    
    return report


def main():
    print("="*70)
    print("Batch Training & Prediction System v3.0")
    print("="*70)
    
    # 階段 1: 訓練所有賽道模型
    print("\n[STAGE 1] Training all track models (2022-2024)...")
    print("="*70)
    
    all_races = get_available_races()
    
    # 收集所有唯一賽道名稱
    unique_races = set()
    for year_races in all_races.values():
        unique_races.update(year_races)
    
    unique_races = sorted(unique_races)
    
    training_results = []
    for race in unique_races:
        result = train_track_model(race)
        if result:
            training_results.append(result)
    
    print(f"\n{'='*70}")
    print(f"[STAGE 1 COMPLETE] {len(training_results)}/{len(unique_races)} models trained successfully")
    print(f"{'='*70}")
    
    # 階段 2: 預測 2025 賽季
    print(f"\n[STAGE 2] Predicting 2025 season...")
    print("="*70)
    
    races_2025 = find_2025_races()
    print(f"Found {len(races_2025)} races in 2025 season")
    
    prediction_results = []
    for race in races_2025:
        # 找到對應的模型
        model_path = Path(f'models/track_specific_v3/{race}.pkl')
        if not model_path.exists():
            print(f"  [SKIP] No trained model for {race}")
            continue
        
        result = predict_2025_race(race, model_path)
        if result:
            prediction_results.append(result)
    
    print(f"\n{'='*70}")
    print(f"[STAGE 2 COMPLETE] {len(prediction_results)} races predicted")
    print(f"{'='*70}")
    
    # 階段 3: 生成報告
    print(f"\n[STAGE 3] Generating comprehensive report...")
    
    report_content = "# F1 Track-Specific Prediction System v3.0\n"
    report_content += "# Complete Analysis Report: 2022-2024 Training → 2025 Prediction\n\n"
    report_content += f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 訓練摘要
    report_content += "## Training Summary (2022-2024)\n\n"
    report_content += f"- Total tracks trained: {len(training_results)}\n"
    report_content += f"- Average test MAE: {np.mean([r['performance']['test_mae'] for r in training_results]):.3f}s\n"
    report_content += f"- Average test R²: {np.mean([r['performance']['test_r2'] for r in training_results]):.4f}\n\n"
    
    # 2025 預測摘要
    if prediction_results:
        report_content += "## 2025 Prediction Summary\n\n"
        report_content += f"- Total races predicted: {len(prediction_results)}\n"
        report_content += f"- Average MAE: {np.mean([r['mae'] for r in prediction_results]):.4f}s\n"
        report_content += f"- Average R²: {np.mean([r['r2'] for r in prediction_results]):.4f}\n"
        report_content += f"- Average Spearman: {np.mean([r['spearman'] for r in prediction_results]):.4f}\n\n"
        
        # 最佳/最差表現
        best_race = max(prediction_results, key=lambda x: x['spearman'])
        worst_race = min(prediction_results, key=lambda x: x['spearman'])
        
        report_content += f"**Best Performance:** {best_race['race']} (Spearman: {best_race['spearman']:.4f})\n"
        report_content += f"**Worst Performance:** {worst_race['race']} (Spearman: {worst_race['spearman']:.4f})\n\n"
        
        # 每場賽事詳細報告
        report_content += "## Detailed Race-by-Race Analysis\n"
        
        for result in sorted(prediction_results, key=lambda x: x['race']):
            report_content += generate_race_report(result)
    
    # 儲存報告
    report_file = Path(f'F77_V3_COMPLETE_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"  [SUCCESS] Report saved: {report_file}")
    
    # 顯示摘要
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Training: {len(training_results)} tracks")
    if prediction_results:
        print(f"2025 Predictions: {len(prediction_results)} races")
        print(f"Average Spearman: {np.mean([r['spearman'] for r in prediction_results]):.4f}")
    print(f"Full report: {report_file}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
