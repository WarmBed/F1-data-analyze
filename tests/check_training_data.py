"""檢查訓練數據的詳細統計"""
import pandas as pd
import numpy as np

print("=" * 60)
print("訓練數據分析報告")
print("=" * 60)

# 載入訓練數據
train_df = pd.read_csv('data/live_win_probability/training_data.csv')
val_df = pd.read_csv('data/live_win_probability/validation_data.csv')

print(f"\n=== 訓練數據 ===")
print(f"總樣本數: {len(train_df)}")
print(f"\n欄位: {list(train_df.columns)}")

if 'year' in train_df.columns:
    print(f"\n年份分佈:")
    print(train_df.groupby('year').size())

if 'race' in train_df.columns:
    print(f"\n賽事分佈:")
    print(train_df.groupby('race').size())

print(f"\n圈數範圍:")
print(f"  laps_remaining: {train_df['laps_remaining'].min()} ~ {train_df['laps_remaining'].max()}")

if 'lap_number' in train_df.columns:
    print(f"\n每圈樣本數 (前10圈):")
    print(train_df.groupby('lap_number').size().head(10))
    print(f"\n最後10圈:")
    print(train_df.groupby('lap_number').size().tail(10))

print(f"\n\n=== 驗證數據 ===")
print(f"總樣本數: {len(val_df)}")

if 'year' in val_df.columns:
    print(f"\n年份分佈:")
    print(val_df.groupby('year').size())

if 'race' in val_df.columns:
    print(f"\n賽事分佈:")
    print(val_df.groupby('race').size())

print(f"\n圈數範圍:")
print(f"  laps_remaining: {val_df['laps_remaining'].min()} ~ {val_df['laps_remaining'].max()}")

# 檢查標籤分佈
print(f"\n\n=== 標籤分佈 ===")
if 'final_position' in train_df.columns:
    print(f"訓練數據 final_position 分佈:")
    print(train_df['final_position'].value_counts().sort_index().head(10))
    
    print(f"\n驗證數據 final_position 分佈:")
    print(val_df['final_position'].value_counts().sort_index().head(10))

# 檢查是否包含 Japan 2025
print(f"\n\n=== 關鍵問題: Japan 數據 ===")
if 'race' in val_df.columns:
    japan_mask = val_df['race'].str.contains('Japan|Japanese', case=False, na=False)
    japan_data = val_df[japan_mask]
    print(f"Japan 在驗證集: {len(japan_data)} 筆")
    if len(japan_data) > 0 and 'year' in japan_data.columns:
        print(f"Japan 年份: {japan_data['year'].unique()}")

if 'race' in train_df.columns:
    japan_mask = train_df['race'].str.contains('Japan|Japanese', case=False, na=False)
    japan_data = train_df[japan_mask]
    print(f"Japan 在訓練集: {len(japan_data)} 筆")
    if len(japan_data) > 0 and 'year' in japan_data.columns:
        print(f"Japan 年份: {japan_data['year'].unique()}")

# 特徵統計
print(f"\n\n=== 特徵統計 (訓練數據) ===")
feature_cols = ['position', 'gap_to_leader', 'gap_to_ahead', 'laps_remaining', 'tyre_age']
for col in feature_cols:
    if col in train_df.columns:
        print(f"{col}: mean={train_df[col].mean():.2f}, std={train_df[col].std():.2f}, min={train_df[col].min()}, max={train_df[col].max()}")
