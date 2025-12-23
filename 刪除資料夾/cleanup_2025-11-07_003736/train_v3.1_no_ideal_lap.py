#!/usr/bin/env python3
"""
批次訓練 v3.1 模型（移除 ideal_lap 特徵）
只使用 7 個特徵：ideal_s1, ideal_s2, ideal_s3, low/mid/high_speed_apex, max_speed
優先訓練：墨西哥、阿布達比
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_training_data_v31(track_name, start_year=2022, end_year=2024):
    """
    載入訓練數據（v3.1：移除 ideal_lap）
    特徵：ideal_s1, ideal_s2, ideal_s3, low_speed_apex, mid_speed_apex, high_speed_apex, max_speed
    """
    print(f"\n[載入訓練數據] {track_name} ({start_year}-{end_year})")
    
    all_data = []
    json_dir = Path('json')
    
    for year in range(start_year, end_year + 1):
        # FP3→Q 數據（使用更寬鬆的匹配模式）
        fp_q_pattern = f'predictionJSON/fp_q_data_{year}_*{track_name}*.json'
        fp_q_files = list(json_dir.glob(fp_q_pattern))
        
        if not fp_q_files:
            print(f"  ⚠️  {year}: 找不到 FP3→Q 數據")
            continue
        
        fp_q_file = fp_q_files[0]
        
        # 彎角數據
        corner_file = json_dir / f'all_drivers_cornering_analysis_{year}_{track_name}_FP3.json'
        
        if not corner_file.exists():
            print(f"  ⚠️  {year}: 找不到彎角數據")
            continue
        
        try:
            # 載入 FP3→Q 數據
            with open(fp_q_file, 'r', encoding='utf-8') as f:
                fp_q_data = json.load(f)
            
            # 提取 drivers 和 qualifying results
            if 'qualifying' in fp_q_data and 'results' in fp_q_data['qualifying']:
                quali_results = fp_q_data['qualifying']['results']
            else:
                print(f"  ⚠️  {year}: 排位賽數據格式錯誤")
                continue
            
            # 載入彎角數據
            with open(corner_file, 'r', encoding='utf-8') as f:
                corner_data = json.load(f)
            
            # 合併數據
            year_data = []
            for driver, quali_info in quali_results.items():
                if driver not in corner_data:
                    continue
                
                corner_features = corner_data[driver]
                
                # 提取排位賽時間（轉換為秒）
                best_time = quali_info.get('best_time')
                if not best_time or pd.isna(best_time):
                    continue
                
                # 處理 Timedelta 格式
                if isinstance(best_time, str) and 'days' in best_time:
                    from datetime import timedelta
                    td = pd.Timedelta(best_time)
                    q_time = td.total_seconds()
                else:
                    try:
                        q_time = float(best_time)
                    except:
                        continue
                
                # ✅ v3.1 特徵：移除 ideal_lap，只保留 7 個特徵
                row = {
                    'driver': driver,
                    'year': year,
                    'ideal_s1': corner_features.get('ideal_s1', np.nan),
                    'ideal_s2': corner_features.get('ideal_s2', np.nan),
                    'ideal_s3': corner_features.get('ideal_s3', np.nan),
                    'low_speed_apex': corner_features.get('low_speed_apex', np.nan),
                    'mid_speed_apex': corner_features.get('mid_speed_apex', np.nan),
                    'high_speed_apex': corner_features.get('high_speed_apex', np.nan),
                    'max_speed': corner_features.get('max_speed', np.nan),
                    'q_time': q_time,
                    'position': quali_info.get('position', 999)
                }
                
                year_data.append(row)
            
            if year_data:
                all_data.extend(year_data)
                print(f"  ✓ {year}: {len(year_data)} 筆資料")
        
        except Exception as e:
            print(f"  ✗ {year}: 載入失敗 - {e}")
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    print(f"\n總計：{len(df)} 筆訓練樣本")
    return df


def train_track_model_v31(track_name, start_year=2022, end_year=2024):
    """訓練 v3.1 模型（無 ideal_lap）"""
    print(f"\n{'='*80}")
    print(f"訓練 v3.1 模型: {track_name}")
    print(f"{'='*80}")
    
    # 載入數據
    df = load_training_data_v31(track_name, start_year, end_year)
    
    if df is None or len(df) < 20:
        return {
            'success': False,
            'message': f'數據不足（< 20 筆）'
        }
    
    # ✅ v3.1 特徵列表（7 個特徵）
    feature_cols = [
        'ideal_s1', 'ideal_s2', 'ideal_s3',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
        'max_speed'
    ]
    
    # 移除缺失值
    df_clean = df.dropna(subset=feature_cols + ['q_time'])
    
    if len(df_clean) < 20:
        return {
            'success': False,
            'message': f'清理後數據不足（{len(df_clean)} < 20）'
        }
    
    print(f"清理後：{len(df_clean)} 筆資料")
    
    # 準備特徵和目標
    X = df_clean[feature_cols].values
    y = df_clean['q_time'].values
    
    # 分割訓練/測試集（80/20）
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # 訓練 XGBoost 模型
    model = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    
    model.fit(X_train, y_train)
    
    # 評估
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    # 特徵重要性
    feature_importances = dict(zip(feature_cols, model.feature_importances_))
    
    print(f"\n訓練結果：")
    print(f"  訓練 MAE: {train_mae:.3f}s")
    print(f"  測試 MAE: {test_mae:.3f}s")
    print(f"  測試 R²: {test_r2:.4f}")
    print(f"\nv3.1 特徵重要性（7 個特徵）：")
    for feature, importance in sorted(feature_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature:<20} {importance:>10.2%}")
    
    # 儲存模型
    model_dir = Path('models/track_specific_v3.1')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_data = {
        'model': model,
        'performance': {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'test_r2': test_r2,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'samples': len(df_clean),
            'feature_importances': feature_importances
        },
        'track': track_name,
        'version': 'v3.1',
        'features': feature_cols,
        'train_date': datetime.now().isoformat()
    }
    
    model_path = model_dir / f'{track_name}.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n✓ 模型已儲存: {model_path}")
    
    return {
        'success': True,
        'track': track_name,
        'model_path': str(model_path),
        'train_mae': train_mae,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'feature_importances': feature_importances
    }


def predict_2025_v31(track_name):
    """使用 v3.1 模型預測 2025 賽季"""
    print(f"\n{'='*80}")
    print(f"預測 2025 {track_name}")
    print(f"{'='*80}")
    
    # 載入 v3.1 模型
    model_path = Path(f'models/track_specific_v3.1/{track_name}.pkl')
    if not model_path.exists():
        print(f"  ✗ 找不到 v3.1 模型")
        return None
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_cols = model_data['features']
    
    # 載入 2025 數據
    json_dir = Path('json')
    
    # FP3→Q 數據（使用更寬鬆的匹配模式）
    fp_q_files = list(json_dir.glob(f'predictionJSON/fp_q_data_2025_*{track_name}*.json'))
    if not fp_q_files:
        print(f"  ✗ 找不到 2025 FP3→Q 數據")
        return None
    
    # 彎角數據
    corner_file = json_dir / f'all_drivers_cornering_analysis_2025_{track_name}_FP3.json'
    if not corner_file.exists():
        print(f"  ✗ 找不到 2025 彎角數據")
        return None
    
    try:
        # 載入數據
        with open(fp_q_files[0], 'r', encoding='utf-8') as f:
            fp_q_data = json.load(f)
        
        with open(corner_file, 'r', encoding='utf-8') as f:
            corner_data = json.load(f)
        
        # 提取排位賽結果
        if 'qualifying' in fp_q_data and 'results' in fp_q_data['qualifying']:
            quali_results = fp_q_data['qualifying']['results']
        else:
            print(f"  ✗ 排位賽數據格式錯誤")
            return None
        
        # 準備預測數據
        predict_data = []
        for driver, quali_info in quali_results.items():
            if driver not in corner_data:
                continue
            
            corner_features = corner_data[driver]
            
            # 提取實際排位賽時間
            best_time = quali_info.get('best_time')
            if not best_time or pd.isna(best_time):
                continue
            
            if isinstance(best_time, str) and 'days' in best_time:
                td = pd.Timedelta(best_time)
                q_time = td.total_seconds()
            else:
                try:
                    q_time = float(best_time)
                except:
                    continue
            
            row = {
                'driver': driver,
                'ideal_s1': corner_features.get('ideal_s1', np.nan),
                'ideal_s2': corner_features.get('ideal_s2', np.nan),
                'ideal_s3': corner_features.get('ideal_s3', np.nan),
                'low_speed_apex': corner_features.get('low_speed_apex', np.nan),
                'mid_speed_apex': corner_features.get('mid_speed_apex', np.nan),
                'high_speed_apex': corner_features.get('high_speed_apex', np.nan),
                'max_speed': corner_features.get('max_speed', np.nan),
                'actual_q_time': q_time,
                'actual_position': quali_info.get('position', 999)
            }
            
            predict_data.append(row)
        
        df_predict = pd.DataFrame(predict_data)
        df_predict = df_predict.dropna(subset=feature_cols + ['actual_q_time'])
        
        if len(df_predict) < 5:
            print(f"  ✗ 2025 數據不足（{len(df_predict)} < 5）")
            return None
        
        # 預測
        X_predict = df_predict[feature_cols].values
        y_actual = df_predict['actual_q_time'].values
        
        y_pred = model.predict(X_predict)
        
        # 評估
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        
        # 排名相關性
        actual_ranks = df_predict['actual_position'].values
        pred_ranks = pd.Series(y_pred).rank().values
        
        spearman_corr, _ = spearmanr(actual_ranks, pred_ranks)
        
        print(f"\n2025 預測結果：")
        print(f"  Spearman 相關性: {spearman_corr:.4f}")
        print(f"  MAE: {mae:.4f}s")
        print(f"  R²: {r2:.4f}")
        print(f"  預測車手數: {len(df_predict)}")
        
        return {
            'track': track_name,
            'year': 2025,
            'spearman': spearman_corr,
            'mae': mae,
            'r2': r2,
            'drivers_count': len(df_predict),
            'predictions': df_predict.to_dict('records')
        }
    
    except Exception as e:
        print(f"  ✗ 預測失敗: {e}")
        return None


def main():
    """主程式：訓練墨西哥和阿布達比，然後預測 2025"""
    print("="*80)
    print("F1 Track-Specific Prediction v3.1")
    print("方案 A：移除 ideal_lap 特徵（7 個特徵）")
    print("="*80)
    
    # 優先訓練的賽道
    priority_tracks = ['Mexico', 'Abu Dhabi']
    
    results = {
        'training': {},
        'prediction_2025': {}
    }
    
    # 訓練
    for track in priority_tracks:
        result = train_track_model_v31(track, 2022, 2024)
        results['training'][track] = result
    
    # 預測 2025
    print(f"\n{'='*80}")
    print("預測 2025 賽季")
    print(f"{'='*80}")
    
    for track in priority_tracks:
        if results['training'][track]['success']:
            pred_result = predict_2025_v31(track)
            results['prediction_2025'][track] = pred_result
    
    # 儲存結果
    output_file = Path('v3.1_training_prediction_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n{'='*80}")
    print(f"結果已儲存: {output_file}")
    print(f"{'='*80}")
    
    return results


if __name__ == '__main__':
    main()
