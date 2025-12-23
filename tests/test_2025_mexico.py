"""
測試 2025 墨西哥站的預測效果
比較每位車手的預測值與實際 Q 最速圈
"""
import json
import glob
import pandas as pd
import numpy as np
from pathlib import Path
import pickle

def find_mexico_file():
    """找到 2025 墨西哥站的數據檔案 (Race 20)"""
    # 2025 F1 賽曆: Race 20 是墨西哥大獎賽
    # 根據檔案命名規則，尋找最新的 race 20 檔案
    files = sorted(glob.glob('json/predictionJSON/fp_q_data_2025_20_*.json'), reverse=True)
    
    if not files:
        print("[ERROR] 找不到 2025 Race 20 (墨西哥站) 的數據")
        return None, None
    
    # 使用最新的檔案
    file = files[0]
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    print(f"[OK] 找到 2025 Race 20 (墨西哥站) 檔案: {Path(file).name}")
    print(f"    年份: {metadata.get('year', 'N/A')}")
    print(f"    Race: {metadata.get('race', 'N/A')}")
    print(f"    數據來源: {metadata.get('data_source', 'N/A')}")
    print(f"    收集時間: {metadata.get('collection_timestamp', 'N/A')}")
    
    return file, data

def load_mexico_model():
    """載入墨西哥賽道的模型"""
    model_path = 'models/track_specific/Mexico.pkl'
    
    if not Path(model_path).exists():
        print(f"[ERROR] 找不到墨西哥模型: {model_path}")
        return None, None
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    print(f"[OK] 載入墨西哥模型")
    print(f"    訓練樣本數: {model_data.get('n_samples', 'N/A')}")
    
    train_mae = model_data.get('train_mae', None)
    test_mae = model_data.get('test_mae', None)
    test_r2 = model_data.get('test_r2', None)
    
    if train_mae is not None:
        print(f"    訓練 MAE: {train_mae:.3f}s")
    if test_mae is not None:
        print(f"    測試 MAE: {test_mae:.3f}s")
    if test_r2 is not None:
        print(f"    R2 分數: {test_r2:.4f}")
    
    return model_data['model'], model_data

def timedelta_to_seconds(td_str):
    """將 timedelta 字串轉換為秒數"""
    if pd.isna(td_str) or td_str is None:
        return np.nan
    
    try:
        # 格式: '0 days 00:01:16.899000'
        if isinstance(td_str, str):
            td = pd.Timedelta(td_str)
            return td.total_seconds()
        elif isinstance(td_str, (int, float)):
            return float(td_str)
        else:
            return np.nan
    except:
        return np.nan

def extract_2025_features(driver_data, fp3_session):
    """從 2025 新格式中提取特徵"""
    features = {}
    
    # FP3 數據
    features['fp3_best'] = timedelta_to_seconds(driver_data.get('best_lap_time'))
    features['fp3_mean'] = timedelta_to_seconds(driver_data.get('avg_lap_time'))
    features['fp3_std'] = driver_data.get('lap_time_std', np.nan)
    features['fp3_laps'] = driver_data.get('valid_laps', 0)
    
    # FP3 sector times
    features['fp3_sector1'] = timedelta_to_seconds(driver_data.get('sector1_best'))
    features['fp3_sector2'] = timedelta_to_seconds(driver_data.get('sector2_best'))
    features['fp3_sector3'] = timedelta_to_seconds(driver_data.get('sector3_best'))
    
    # FP3 speed trap and intermediate speeds
    features['fp3_speed_st'] = driver_data.get('speed_trap_max', np.nan)
    # 2025 數據中可能沒有這些中間速度點，使用 NaN
    features['fp3_speed_i1'] = np.nan
    features['fp3_speed_i2'] = np.nan
    features['fp3_speed_fl'] = np.nan
    
    # 賽道特徵 (墨西哥 Autódromo Hermanos Rodríguez)
    features['track_length'] = 4.304  # 墨西哥賽道長度 (km)
    features['turns_count'] = 17  # 墨西哥彎道數
    features['track_cluster'] = 2  # 墨西哥的 cluster
    
    # 天氣數據 (從 FP3 session)
    weather = fp3_session.get('weather', {})
    features['air_temp'] = weather.get('air_temp', 20.0)
    features['track_temp'] = weather.get('track_temp', 30.0)
    features['humidity'] = weather.get('humidity', 50.0)
    features['pressure'] = weather.get('pressure', 1013.0)
    features['wind_speed'] = weather.get('wind_speed', 0.0)
    
    # 歷史特徵 (2025 年沒有歷史數據，使用預設值)
    features['driver_avg_q_time_this_track'] = np.nan
    features['driver_best_q_time_this_track'] = np.nan
    features['driver_appearances_this_track'] = 0
    
    return features

def predict_and_compare(model, file_path, data):
    """對所有車手進行預測並比較"""
    metadata = data.get('metadata', {})
    qualifying_data = data.get('qualifying', {})
    fp3_session = data.get('practice_sessions', {}).get('FP3', {})
    
    results = []
    
    for driver_code, driver_data in fp3_session.get('driver_data', {}).items():
        # 提取特徵
        features = extract_2025_features(driver_data, fp3_session)
        
        # 獲取實際 Q 時間
        q_result = qualifying_data.get('results', {}).get(driver_code, {})
        actual_q_time_str = q_result.get('best_time', None)
        
        if actual_q_time_str is None or pd.isna(features['fp3_best']):
            continue
        
        # 轉換 Q 時間為秒數
        actual_q_time = timedelta_to_seconds(actual_q_time_str)
        if pd.isna(actual_q_time):
            continue
        
        # 轉換為 DataFrame
        feature_df = pd.DataFrame([features])
        
        # 預測
        try:
            predicted_q_time = model.predict(feature_df)[0]
            error = predicted_q_time - actual_q_time
            abs_error = abs(error)
            pct_error = (error / actual_q_time) * 100
            
            results.append({
                'driver': driver_code,
                'actual_q': actual_q_time,
                'predicted_q': predicted_q_time,
                'error': error,
                'abs_error': abs_error,
                'pct_error': pct_error,
                'fp3_best': features['fp3_best'],
                'position': q_result.get('position', None)
            })
        except Exception as e:
            print(f"[WARNING] {driver_code} 預測失敗: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return results

def generate_report(results, metadata):
    """生成詳細的比較報告"""
    if not results:
        print("[ERROR] 沒有有效的預測結果")
        return
    
    df = pd.DataFrame(results)
    df = df.sort_values('abs_error', ascending=False)
    
    print("\n" + "="*80)
    print("2025 墨西哥站預測結果分析")
    print("="*80)
    
    print(f"\n賽事資訊:")
    print(f"  賽事: 2025 墨西哥大獎賽 (Mexico City GP)")
    print(f"  賽道: Autódromo Hermanos Rodríguez")
    print(f"  年份: {metadata.get('year', 2025)}")
    print(f"  Race: {metadata.get('race', 20)}")
    print(f"  數據來源: {metadata.get('data_source', 'N/A')}")
    
    print(f"\n統計摘要:")
    print(f"  測試車手數: {len(results)}")
    print(f"  平均絕對誤差 (MAE): {df['abs_error'].mean():.3f}s")
    print(f"  中位數誤差: {df['abs_error'].median():.3f}s")
    print(f"  標準差: {df['abs_error'].std():.3f}s")
    print(f"  最大誤差: {df['abs_error'].max():.3f}s")
    print(f"  最小誤差: {df['abs_error'].min():.3f}s")
    print(f"  平均偏差 (Bias): {df['error'].mean():.3f}s")
    print(f"  RMSE: {np.sqrt((df['error']**2).mean()):.3f}s")
    
    # 誤差分布
    within_0_5 = (df['abs_error'] <= 0.5).sum()
    within_1_0 = (df['abs_error'] <= 1.0).sum()
    within_2_0 = (df['abs_error'] <= 2.0).sum()
    
    print(f"\n誤差分布:")
    print(f"  ≤ 0.5s: {within_0_5}/{len(results)} ({within_0_5/len(results)*100:.1f}%)")
    print(f"  ≤ 1.0s: {within_1_0}/{len(results)} ({within_1_0/len(results)*100:.1f}%)")
    print(f"  ≤ 2.0s: {within_2_0}/{len(results)} ({within_2_0/len(results)*100:.1f}%)")
    
    print(f"\n車手預測結果詳細表 (依誤差由大到小排序):")
    print("-"*80)
    print(f"{'排名':<4} {'車手':<6} {'實際Q':<8} {'預測Q':<8} {'誤差':<8} {'絕對誤差':<10} {'百分比':<8} {'名次':<4}")
    print("-"*80)
    
    for idx, row in enumerate(df.itertuples(), 1):
        print(f"{idx:<4} {row.driver:<6} {row.actual_q:<8.3f} {row.predicted_q:<8.3f} "
              f"{row.error:>+7.3f} {row.abs_error:<10.3f} {row.pct_error:>+6.2f}% "
              f"{row.position if row.position else 'N/A':<4}")
    
    # 前五名 vs 後五名
    print(f"\n誤差最大的 5 位車手:")
    print("-"*80)
    for idx, row in enumerate(df.head(5).itertuples(), 1):
        print(f"{idx}. {row.driver}: 實際 {row.actual_q:.3f}s → 預測 {row.predicted_q:.3f}s "
              f"(誤差 {row.error:+.3f}s, {row.pct_error:+.2f}%)")
    
    print(f"\n誤差最小的 5 位車手:")
    print("-"*80)
    for idx, row in enumerate(df.tail(5).sort_values('abs_error').itertuples(), 1):
        print(f"{idx}. {row.driver}: 實際 {row.actual_q:.3f}s → 預測 {row.predicted_q:.3f}s "
              f"(誤差 {row.error:+.3f}s, {row.pct_error:+.2f}%)")
    
    # 預測偏向分析
    overpredict = (df['error'] > 0).sum()
    underpredict = (df['error'] < 0).sum()
    
    print(f"\n預測偏向:")
    print(f"  預測過高 (高估): {overpredict}/{len(results)} ({overpredict/len(results)*100:.1f}%)")
    print(f"  預測過低 (低估): {underpredict}/{len(results)} ({underpredict/len(results)*100:.1f}%)")
    
    # 保存結果到 CSV
    output_file = 'reports/mexico_2025_prediction_results.csv'
    Path('reports').mkdir(exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n[OK] 詳細結果已保存至: {output_file}")

def main():
    print("="*80)
    print("2025 墨西哥站預測測試")
    print("="*80)
    
    # 1. 找到墨西哥站檔案
    file_path, data = find_mexico_file()
    if not file_path:
        return
    
    print()
    
    # 2. 載入墨西哥模型
    model, model_data = load_mexico_model()
    if not model:
        return
    
    print()
    
    # 3. 進行預測並比較
    print("[開始] 對所有車手進行預測...")
    results = predict_and_compare(model, file_path, data)
    
    # 4. 生成報告
    generate_report(results, data.get('metadata', {}))
    
    print("\n" + "="*80)
    print("測試完成")
    print("="*80)

if __name__ == '__main__':
    main()
