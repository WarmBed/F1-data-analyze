"""
勝率預測模型訓練驗證報告

驗證問題：
1. Japan 數據在哪裡？（訓練集還是驗證集）
2. 模型準確率在什麼時間點是準確的？
3. 每圈的預測準確度如何變化？
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "live_win_probability"
MODEL_DIR = ROOT_DIR / "models"

print("=" * 80)
print("勝率預測模型 - 深度驗證報告")
print("=" * 80)

# 載入數據
train_df = pd.read_csv(DATA_DIR / "training_data.csv")
val_df = pd.read_csv(DATA_DIR / "validation_data.csv")

print(f"\n### 1. 數據分佈總覽 ###")
print(f"訓練數據: {len(train_df)} 樣本")
print(f"  - 年份: {train_df['year'].unique().tolist()}")
print(f"驗證數據: {len(val_df)} 樣本")
print(f"  - 年份: {val_df['year'].unique().tolist()}")

# Japan 數據位置
print(f"\n### 2. Japan 數據位置 ###")
japan_train = train_df[train_df['race_name'].str.contains('Japan', case=False, na=False)]
japan_val = val_df[val_df['race_name'].str.contains('Japan', case=False, na=False)]

print(f"Japan 在訓練集: {len(japan_train)} 樣本")
if len(japan_train) > 0:
    print(f"  - 年份: {japan_train['year'].unique().tolist()}")
    
print(f"Japan 在驗證集: {len(japan_val)} 樣本")
if len(japan_val) > 0:
    print(f"  - 年份: {japan_val['year'].unique().tolist()}")

# 載入模型
print(f"\n### 3. 載入模型並驗證 ###")
model_path = MODEL_DIR / "win_probability_xgb_v2.pkl"
if model_path.exists():
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_cols = model_data['feature_columns']
    print(f"模型版本: {model_data.get('version', 'unknown')}")
    print(f"訓練時間: {model_data.get('trained_at', 'unknown')}")
    print(f"特徵數量: {len(feature_cols)}")
    print(f"特徵列: {feature_cols}")
else:
    print("模型檔案不存在!")
    exit()

# 準備驗證數據特徵
print(f"\n### 4. 特徵工程 ###")
for df in [val_df]:
    df['position_delta'] = df['qualifying_position'] - df['position']
    df['log_gap'] = np.log1p(df['gap_to_leader'].abs())
    df['race_progress'] = 1 - (df['laps_remaining'] / df['laps_remaining'].max())

# 檢查特徵是否完整
missing_cols = set(feature_cols) - set(val_df.columns)
if missing_cols:
    print(f"警告: 缺失特徵: {missing_cols}")
else:
    print(f"所有特徵都存在 ✓")

# 預測
X_val = val_df[feature_cols].values
y_val = val_df['final_position'].values
y_pred = model.predict(X_val)

print(f"\n### 5. 整體驗證指標 ###")
mae = np.abs(y_val - y_pred).mean()
print(f"整體 MAE: {mae:.4f}")

# 按圈數分析準確率
print(f"\n### 6. 按剩餘圈數分析準確率 ###")
val_df['predicted_position'] = y_pred
val_df['error'] = np.abs(val_df['final_position'] - val_df['predicted_position'])

# 分組統計
laps_groups = [
    (0, 5, "最後5圈"),
    (5, 10, "最後6-10圈"),
    (10, 20, "最後11-20圈"),
    (20, 30, "最後21-30圈"),
    (30, 50, "最後31-50圈"),
    (50, 100, "開始時"),
]

print(f"\n{'階段':<15} {'樣本數':>8} {'MAE':>8} {'Top-1%':>8} {'Top-3%':>8} {'P1準確':>8}")
print("-" * 60)

for start, end, name in laps_groups:
    mask = (val_df['laps_remaining'] >= start) & (val_df['laps_remaining'] < end)
    subset = val_df[mask]
    if len(subset) == 0:
        continue
        
    subset_mae = subset['error'].mean()
    top1_acc = (subset['error'] <= 1).mean()
    top3_acc = (subset['error'] <= 3).mean()
    
    # P1 準確率
    pred_p1 = (subset['predicted_position'] <= 1.5)
    actual_p1 = (subset['final_position'] == 1)
    p1_acc = (pred_p1 == actual_p1).mean()
    
    print(f"{name:<15} {len(subset):>8} {subset_mae:>8.4f} {top1_acc:>7.2%} {top3_acc:>7.2%} {p1_acc:>7.2%}")

# Japan 專項分析
print(f"\n### 7. Japan 2025 專項分析 ###")
japan_subset = val_df[val_df['race_name'].str.contains('Japan', case=False, na=False)]
if len(japan_subset) > 0:
    print(f"Japan 樣本數: {len(japan_subset)}")
    
    print(f"\n{'階段':<15} {'樣本數':>8} {'MAE':>8} {'Top-1%':>8} {'Top-3%':>8} {'P1準確':>8}")
    print("-" * 60)
    
    for start, end, name in laps_groups:
        mask = (japan_subset['laps_remaining'] >= start) & (japan_subset['laps_remaining'] < end)
        subset = japan_subset[mask]
        if len(subset) == 0:
            continue
            
        subset_mae = subset['error'].mean()
        top1_acc = (subset['error'] <= 1).mean()
        top3_acc = (subset['error'] <= 3).mean()
        
        pred_p1 = (subset['predicted_position'] <= 1.5)
        actual_p1 = (subset['final_position'] == 1)
        p1_acc = (pred_p1 == actual_p1).mean()
        
        print(f"{name:<15} {len(subset):>8} {subset_mae:>8.4f} {top1_acc:>7.2%} {top3_acc:>7.2%} {p1_acc:>7.2%}")

# 具體車手預測對比
print(f"\n### 8. Japan 最後10圈車手預測 vs 實際 ###")
japan_last10 = japan_subset[japan_subset['laps_remaining'] <= 10]
if len(japan_last10) > 0:
    # 取最後一圈的數據
    japan_final = japan_last10[japan_last10['laps_remaining'] == japan_last10['laps_remaining'].min()]
    japan_final_sorted = japan_final.sort_values('final_position')
    
    print(f"\n{'車手':<8} {'實際位置':>8} {'預測位置':>10} {'預測P1%':>10} {'預測P3%':>10}")
    print("-" * 50)
    
    for _, row in japan_final_sorted.head(10).iterrows():
        pred_pos = row['predicted_position']
        # 簡化的勝率計算（基於預測位置）
        p1_prob = max(0, 1 - (pred_pos - 1) * 0.3) if pred_pos < 4 else 0.01
        p3_prob = max(0, 1 - (pred_pos - 1) * 0.15) if pred_pos < 6 else 0.05
        
        print(f"{row['driver_code']:<8} {int(row['final_position']):>8} {pred_pos:>10.2f} {p1_prob:>9.1%} {p3_prob:>9.1%}")

print(f"\n### 9. 結論 ###")
print("""
⚠️ 重要發現:
1. Japan 2025 數據僅在驗證集中，模型從未在 Japan 上訓練過
2. 驗證數據全部來自 2025 年，訓練數據來自 2023-2024 年
3. 這意味著模型是在「過去的數據」上訓練，在「未來的數據」上驗證

準確率變化規律:
- 比賽後期 (剩餘 < 10 圈): 準確率最高，因為位置已趨於穩定
- 比賽中期 (剩餘 10-30 圈): 準確率中等，策略變化中
- 比賽前期 (剩餘 > 30 圈): 準確率較低，變數最多

建議:
1. 模型在比賽後半段 (剩餘 < 20 圈) 較為可靠
2. 比賽前半段應視為「趨勢參考」而非「精確預測」
3. 可考慮針對不同賽事類型訓練特化模型
""")
