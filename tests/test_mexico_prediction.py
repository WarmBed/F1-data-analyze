"""
測試 2025 墨西哥 Q 的預測結果
"""
import json
import os
import pickle
import numpy as np
from datetime import datetime

def find_2025_races():
    """查找所有 2025 年的比賽數據"""
    json_dir = 'json/predictionJSON'
    races_2025 = []
    
    for filename in os.listdir(json_dir):
        if not filename.startswith('fp_q_data_'):
            continue
        
        filepath = os.path.join(json_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 新格式：metadata 中包含 year 和 race
                if 'metadata' in data:
                    year = data['metadata'].get('year')
                    race = data['metadata'].get('race')
                else:
                    # 舊格式：直接在根級別
                    year = data.get('year')
                    race = data.get('race')
                
                if year == 2025:
                    races_2025.append({
                        'filename': filename,
                        'race': race,
                        'year': year
                    })
        except Exception as e:
            continue
    
    return races_2025

def load_model():
    """載入最佳模型 (XGBoost)"""
    model_path = 'models/xgboost_pure_fp3.pkl'
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def extract_features(data, driver):
    """從 JSON 數據中提取指定車手的特徵"""
    try:
        # 從 FP3 數據中提取
        fp3_data = data['practice_sessions']['FP3']['driver_data'].get(driver)
        if not fp3_data:
            return None
        
        # 從排位賽結果中提取實際時間
        q_result = data['qualifying']['results'].get(driver)
        if not q_result:
            return None
        
        # 新格式使用 best_time
        actual_time = q_result.get('best_time') or q_result.get('q_time')
        if actual_time is None:
            return None
        
        # 如果是 timedelta 對象，轉換為秒
        if hasattr(actual_time, 'total_seconds'):
            actual_time = actual_time.total_seconds()
        elif isinstance(actual_time, str):
            # 處理字串格式的時間（如 "0 days 00:01:16.070000"）
            import pandas as pd
            actual_time = pd.Timedelta(actual_time).total_seconds()
        
        # 提取 15 個特徵
        features = []
        
        # FP3 基礎特徵
        features.append(fp3_data.get('best_lap', 0))
        features.append(fp3_data.get('avg_lap', 0))
        features.append(fp3_data.get('lap_std', 0))
        features.append(fp3_data.get('sector1', 0))
        features.append(fp3_data.get('sector2', 0))
        features.append(fp3_data.get('sector3', 0))
        features.append(fp3_data.get('speed_trap', 0))
        features.append(fp3_data.get('valid_laps', 0))
        
        # FP1/FP2 最佳圈速
        fp1_data = data['practice_sessions']['FP1']['driver_data'].get(driver, {})
        fp2_data = data['practice_sessions']['FP2']['driver_data'].get(driver, {})
        features.append(fp1_data.get('best_lap', 0))
        features.append(fp2_data.get('best_lap', 0))
        
        # 進步幅度
        fp1_best = fp1_data.get('best_lap', 0)
        fp2_best = fp2_data.get('best_lap', 0)
        fp3_best = fp3_data.get('best_lap', 0)
        
        improvement_fp3_fp1 = fp1_best - fp3_best if fp1_best > 0 else 0
        improvement_fp3_fp2 = fp2_best - fp3_best if fp2_best > 0 else 0
        features.append(improvement_fp3_fp1)
        features.append(improvement_fp3_fp2)
        
        # 一致性 (標準差 / 平均)
        consistency = fp3_data.get('lap_std', 0) / fp3_data.get('avg_lap', 1) if fp3_data.get('avg_lap', 0) > 0 else 0
        features.append(consistency)
        
        # 扇區平衡 (標準差)
        sectors = [fp3_data.get('sector1', 0), fp3_data.get('sector2', 0), fp3_data.get('sector3', 0)]
        sector_balance = np.std(sectors) if any(sectors) else 0
        features.append(sector_balance)
        
        # 賽道分類 (使用 Cluster 1 作為預設)
        features.append(1)  # track_cluster
        
        return {
            'features': np.array(features).reshape(1, -1),
            'actual_time': actual_time,
            'driver': driver,
            'team': fp3_data.get('team', 'Unknown'),
            'q_position': q_result.get('position', 0)
        }
    except Exception as e:
        print(f"錯誤提取 {driver} 的特徵: {e}")
        return None

def predict_race(race_file):
    """對指定比賽進行預測"""
    filepath = os.path.join('json/predictionJSON', race_file)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 新格式：metadata 中包含 year 和 race
    if 'metadata' in data:
        race_name = data['metadata'].get('race')
        year = data['metadata'].get('year')
    else:
        # 舊格式：直接在根級別
        race_name = data.get('race')
        year = data.get('year')
    
    print(f"\n{'='*70}")
    print(f"2025 {race_name} 排位賽預測結果")
    print(f"{'='*70}\n")
    
    # 載入模型
    model = load_model()
    
    # 獲取所有車手
    drivers = data.get('drivers', [])
    
    results = []
    skipped_count = 0
    for driver in drivers:
        driver_data = extract_features(data, driver)
        if driver_data is None:
            skipped_count += 1
            continue
        
        # 預測
        pred_time = model.predict(driver_data['features'])[0]
        actual_time = driver_data['actual_time']
        error = pred_time - actual_time
        error_pct = (error / actual_time) * 100
        
        results.append({
            'driver': driver,
            'team': driver_data['team'],
            'q_position': driver_data['q_position'],
            'actual_time': actual_time,
            'predicted_time': pred_time,
            'error': error,
            'error_pct': error_pct
        })
    
    # 按排位賽位置排序
    results.sort(key=lambda x: x['q_position'])
    
    # 顯示結果
    print(f"{'排位':<6} {'車手':<8} {'車隊':<25} {'實際時間':<12} {'預測時間':<12} {'誤差':<10} {'誤差%':<8}")
    print("-" * 100)
    
    total_mae = 0
    for r in results:
        print(f"{r['q_position']:<6} {r['driver']:<8} {r['team']:<25} {r['actual_time']:>10.3f}s {r['predicted_time']:>10.3f}s {r['error']:>+8.3f}s {r['error_pct']:>+6.2f}%")
        total_mae += abs(r['error'])
    
    mae = total_mae / len(results) if results else 0
    print("-" * 100)
    print(f"\n平均絕對誤差 (MAE): {mae:.4f}s")
    print(f"成功預測: {len(results)} 位車手")
    print(f"跳過車手: {skipped_count} 位 (特徵提取失敗)")
    
    return results, mae

def main():
    print("="*70)
    print("Function 76 - 2025 墨西哥排位賽預測驗證")
    print("="*70)
    
    # 查找 2025 年的比賽
    races_2025 = find_2025_races()
    
    if not races_2025:
        print("\n未找到 2025 年的比賽數據")
        print("可用的比賽數據需要先通過 CLI 功能收集")
        return
    
    print(f"\n找到 {len(races_2025)} 場 2025 年比賽:")
    for i, race in enumerate(races_2025, 1):
        print(f"  {i}. {race['race']}")
    
    # 查找最新的比賽（第 20 場）
    latest_race = None
    for race in races_2025:
        if race['race'] == 20:
            latest_race = race
            break
    
    if not latest_race:
        print("\n使用第一場比賽作為示範:")
        latest_race = races_2025[0]
    else:
        print(f"\n使用 2025 年第 {latest_race['race']} 場比賽進行示範預測")
    
    # 進行預測
    results, mae = predict_race(latest_race['filename'])
    
    print(f"\n{'='*70}")
    print("預測完成")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
