"""
診斷 v3.5 中三個改進率特徵重要性為 0 的原因
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent / 'CLI_modules'))

from cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3

def diagnose_features(track_name: str = "Japan"):
    """診斷特定賽道的特徵問題"""
    
    print(f"\n{'='*70}")
    print(f"診斷賽道：{track_name}")
    print('='*70)
    
    # 初始化訓練器
    trainer = TrackSpecificTrainerV3(verbose=True)
    
    # 載入訓練數據
    df = trainer.load_training_data_v3(track_name, 2022, 2024)
    
    if df is None or len(df) == 0:
        print(f"❌ 無法載入 {track_name} 的訓練數據")
        return
    
    print(f"\n✅ 載入 {len(df)} 筆訓練樣本")
    
    # 檢查三個問題特徵
    problem_features = [
        'track_avg_improvement_rate',
        'adjusted_ideal_lap', 
        'driver_historical_improvement'
    ]
    
    print(f"\n{'='*70}")
    print("特徵數值分析")
    print('='*70)
    
    for feature in problem_features:
        if feature not in df.columns:
            print(f"\n❌ 特徵不存在：{feature}")
            continue
        
        values = df[feature]
        unique_values = values.unique()
        
        print(f"\n特徵：{feature}")
        print(f"  唯一值數量：{len(unique_values)}")
        print(f"  最小值：{values.min():.10f}")
        print(f"  最大值：{values.max():.10f}")
        print(f"  平均值：{values.mean():.10f}")
        print(f"  標準差：{values.std():.10f}")
        
        if len(unique_values) <= 5:
            print(f"  所有唯一值：{unique_values}")
        
        # 檢查是否所有值都相同
        if len(unique_values) == 1:
            print(f"  ⚠️  **常數特徵**：所有樣本都是 {unique_values[0]}")
        elif values.std() < 1e-6:
            print(f"  ⚠️  **準常數特徵**：標準差接近 0")
    
    # 檢查相關特徵
    print(f"\n{'='*70}")
    print("相關特徵檢查")
    print('='*70)
    
    if 'ideal_lap' in df.columns and 'adjusted_ideal_lap' in df.columns:
        print("\n檢查 adjusted_ideal_lap 的計算邏輯：")
        print(f"  ideal_lap 範圍：{df['ideal_lap'].min():.3f} - {df['ideal_lap'].max():.3f}s")
        print(f"  adjusted_ideal_lap 範圍：{df['adjusted_ideal_lap'].min():.3f} - {df['adjusted_ideal_lap'].max():.3f}s")
        
        # 計算調整係數
        if 'track_avg_improvement_rate' in df.columns:
            track_rate = df['track_avg_improvement_rate'].iloc[0]
            print(f"  track_avg_improvement_rate：{track_rate:.6f} ({track_rate*100:.3f}%)")
            print(f"  調整係數 (1 - rate)：{1 - track_rate:.6f}")
            
            # 驗證計算公式
            expected_adjusted = df['ideal_lap'] * (1 - track_rate)
            actual_adjusted = df['adjusted_ideal_lap']
            diff = (expected_adjusted - actual_adjusted).abs().max()
            print(f"  公式驗證誤差：{diff:.10f}")
    
    # 檢查 is_top_driver 和 driver_historical_improvement 的關聯
    if 'is_top_driver' in df.columns and 'driver_historical_improvement' in df.columns:
        print("\n檢查 driver_historical_improvement 的計算邏輯：")
        top_driver_sample = df[df['is_top_driver'] == 1]['driver_historical_improvement'].unique()
        other_driver_sample = df[df['is_top_driver'] == 0]['driver_historical_improvement'].unique()
        
        print(f"  頂尖車手的 driver_historical_improvement：{top_driver_sample}")
        print(f"  其他車手的 driver_historical_improvement：{other_driver_sample}")
    
    # 分析為何 XGBoost 認為這些特徵不重要
    print(f"\n{'='*70}")
    print("XGBoost 特徵選擇分析")
    print('='*70)
    
    print("""
    XGBoost 特徵重要性為 0 的可能原因：
    
    1. **常數特徵**：
       - 如果特徵在所有樣本中都相同，無法進行分割
       - 例如：track_avg_improvement_rate 對整個賽道都是固定值
    
    2. **線性相關**：
       - adjusted_ideal_lap = ideal_lap * (1 - constant)
       - 與 ideal_lap 完全線性相關，XGBoost 只會選擇其中之一
    
    3. **資訊冗餘**：
       - driver_historical_improvement = is_top_driver * 0.002
       - 完全由 is_top_driver 決定，不提供額外資訊
    
    4. **數值範圍過小**：
       - 如果特徵變異性太小，對預測貢獻度低
    """)

def compare_all_tracks():
    """對比所有賽道的特徵重要性"""
    
    tracks = [
        "Japan", "Bahrain", "Saudi Arabia", "Italy", "Azerbaijan",
        "Monaco", "Canada", "Great Britain", "Hungary", "Singapore",
        "Mexico", "United States"
    ]
    
    print(f"\n{'='*70}")
    print("所有賽道的改進率特徵分析")
    print('='*70)
    
    trainer = TrackSpecificTrainerV3(verbose=False)
    
    results = []
    
    for track in tracks:
        df = trainer.load_training_data_v3(track, 2022, 2024)
        
        if df is None or len(df) == 0:
            continue
        
        track_rate = df['track_avg_improvement_rate'].iloc[0] if 'track_avg_improvement_rate' in df.columns else 0
        driver_hist_unique = len(df['driver_historical_improvement'].unique()) if 'driver_historical_improvement' in df.columns else 0
        
        results.append({
            'track': track,
            'samples': len(df),
            'track_rate': track_rate,
            'track_rate_pct': track_rate * 100,
            'driver_hist_unique': driver_hist_unique
        })
    
    df_results = pd.DataFrame(results)
    print("\n賽道改進率特徵統計：")
    print(df_results.to_string(index=False))
    
    print(f"\n結論：")
    print(f"  - track_avg_improvement_rate：每個賽道都是**常數**（單一值）")
    print(f"  - adjusted_ideal_lap：與 ideal_lap **線性相關**（乘以固定係數）")
    print(f"  - driver_historical_improvement：由 is_top_driver **完全決定**（兩個值）")

if __name__ == "__main__":
    # 詳細診斷日本站
    diagnose_features("Japan")
    
    # 對比所有賽道
    compare_all_tracks()
