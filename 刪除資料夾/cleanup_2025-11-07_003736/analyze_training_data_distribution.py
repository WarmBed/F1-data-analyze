"""
分析訓練數據的時間分佈
檢查 62.9s - 128.5s 的範圍是否合理
"""
import pickle
import numpy as np
import json
from collections import defaultdict

def analyze_model_training_data():
    """從 XGBoost 訓練器載入數據並分析"""
    from CLI_modules.cli.prediction.xgboost_trainer import XGBoostTrainer
    
    print("=" * 70)
    print("訓練數據時間分佈分析")
    print("=" * 70)
    
    # 載入訓練數據
    trainer = XGBoostTrainer(verbose=False)
    print("\n正在載入 2018-2024 訓練數據...")
    training_data = trainer.load_training_data(
        start_year=2018,
        end_year=2024,
        exclude_wet=True
    )
    
    if training_data is None or len(training_data) == 0:
        print("錯誤: 無法載入訓練數據")
        return
    
    # 提取所有排位賽時間（training_data 是 DataFrame）
    print(f"數據形狀: {training_data.shape}")
    print(f"欄位: {list(training_data.columns)[:10]}...")
    
    # 檢查是否有 q_time 欄位
    if 'q_time' not in training_data.columns:
        print("錯誤: 數據中沒有 q_time 欄位")
        print(f"可用欄位: {list(training_data.columns)}")
        return
    
    q_times = training_data['q_time'].values
    q_times = q_times[q_times > 0]  # 過濾無效值
    
    # 按賽道分組
    race_times = defaultdict(list)
    for _, row in training_data.iterrows():
        race = row.get('race', 'Unknown')
        q_time = row.get('q_time')
        if q_time and q_time > 0:
            race_times[race].append(q_time)
    
    print(f"\n總樣本數: {len(q_times)}")
    print(f"時間範圍: {q_times.min():.3f}s - {q_times.max():.3f}s")
    print(f"範圍差距: {q_times.max() - q_times.min():.3f}s")
    print(f"平均時間: {q_times.mean():.3f}s")
    print(f"中位數時間: {np.median(q_times):.3f}s")
    print(f"標準差: {q_times.std():.3f}s")
    
    # 分位數分析
    print("\n時間分位數:")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        print(f"  {p:2d}%: {np.percentile(q_times, p):6.3f}s")
    
    # 檢查極端值
    print("\n極端值分析:")
    
    # 最快的 5 個
    fastest_idx = np.argsort(q_times)[:5]
    print("\n最快的 5 個樣本:")
    valid_data = training_data[training_data['q_time'] > 0]
    for i, idx in enumerate(fastest_idx, 1):
        row = valid_data.iloc[idx]
        print(f"  {i}. {q_times[idx]:6.3f}s - {row.get('year', 'N/A')} {row.get('race', 'N/A')} - {row.get('driver', 'N/A')}")
    
    # 最慢的 5 個
    slowest_idx = np.argsort(q_times)[-5:]
    print("\n最慢的 5 個樣本:")
    for i, idx in enumerate(slowest_idx, 1):
        row = valid_data.iloc[idx]
        print(f"  {i}. {q_times[idx]:6.3f}s - {row.get('year', 'N/A')} {row.get('race', 'N/A')} - {row.get('driver', 'N/A')}")
    
    # 賽道時間範圍
    print("\n賽道時間範圍（顯示前 10 條賽道）:")
    race_ranges = []
    for race, times in race_times.items():
        times = np.array(times)
        race_ranges.append({
            'race': race,
            'min': times.min(),
            'max': times.max(),
            'mean': times.mean(),
            'range': times.max() - times.min(),
            'count': len(times)
        })
    
    race_ranges.sort(key=lambda x: x['max'], reverse=True)
    
    print(f"\n{'賽道':<20} {'最快':<8} {'最慢':<8} {'平均':<8} {'範圍':<8} {'樣本數'}")
    print("-" * 70)
    for r in race_ranges[:10]:
        print(f"{r['race']:<20} {r['min']:6.3f}s {r['max']:6.3f}s {r['mean']:6.3f}s {r['range']:6.3f}s {r['count']:>4}")
    
    # 檢查是否有異常值
    print("\n異常值檢測（使用 IQR 方法）:")
    Q1 = np.percentile(q_times, 25)
    Q3 = np.percentile(q_times, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = q_times[(q_times < lower_bound) | (q_times > upper_bound)]
    print(f"  Q1 (25%): {Q1:.3f}s")
    print(f"  Q3 (75%): {Q3:.3f}s")
    print(f"  IQR: {IQR:.3f}s")
    print(f"  下界: {lower_bound:.3f}s")
    print(f"  上界: {upper_bound:.3f}s")
    print(f"  異常值數量: {len(outliers)} ({len(outliers)/len(q_times)*100:.2f}%)")
    
    if len(outliers) > 0:
        print(f"  異常值範圍: {outliers.min():.3f}s - {outliers.max():.3f}s")
    
    # F1 實際排位賽時間參考
    print("\nF1 實際排位賽時間參考（2024 賽季）:")
    reference_times = {
        'Monza (最快)': '1:19.327 (79.327s)',
        'Monaco (最慢)': '1:10.270 (70.270s)',
        'Spa': '1:41.252 (101.252s)',
        'Silverstone': '1:25.819 (85.819s)',
        'Singapore': '1:29.525 (89.525s)',
        'Mexico': '1:15.946 (75.946s)'
    }
    
    for track, time in reference_times.items():
        print(f"  {track}: {time}")
    
    print("\n典型範圍: 約 70s (Monaco) 至 105s (Spa)")
    print("訓練數據範圍: {:.3f}s - {:.3f}s".format(q_times.min(), q_times.max()))
    
    # 結論
    print("\n" + "=" * 70)
    print("分析結論:")
    print("=" * 70)
    
    if q_times.min() < 60:
        print("⚠️  警告: 最小值 {:.3f}s 低於典型 F1 排位賽時間（通常 > 70s）".format(q_times.min()))
        print("   → 可能原因: 數據單位錯誤、只包含扇區時間、或數據損壞")
    
    if q_times.max() > 110:
        print("⚠️  警告: 最大值 {:.3f}s 高於大部分賽道（除 Spa 外通常 < 105s）".format(q_times.max()))
        print("   → 可能原因: 包含練習賽數據、交通影響、或數據異常")
    
    if q_times.max() - q_times.min() > 40:
        print("⚠️  警告: 範圍差距 {:.3f}s 過大".format(q_times.max() - q_times.min()))
        print("   → 典型範圍應在 30-35s 左右（70s Monaco 至 105s Spa）")
        print("   → 當前範圍可能包含異常數據")
    
    # 建議
    print("\n建議:")
    if len(outliers) > len(q_times) * 0.05:
        print(f"1. 移除 {len(outliers)} 個異常值（{len(outliers)/len(q_times)*100:.2f}%）")
        print(f"   → 保留範圍: {lower_bound:.3f}s - {upper_bound:.3f}s")
    
    if q_times.min() < 60 or q_times.max() > 110:
        print("2. 檢查極端值的數據來源和正確性")
        print("3. 驗證數據收集過程中的單位轉換")

if __name__ == '__main__':
    analyze_model_training_data()
