import pandas as pd

print("=" * 70)
print("F81 數據收集結果驗證")
print("=" * 70)

# 載入訓練集
train_df = pd.read_csv('data/overtake_prediction/training_samples.csv')

print(f"\n總樣本數: {len(train_df)}")
print(f"欄位數: {len(train_df.columns)}")

# 檢查 close_combat_happened 標籤
print("\n" + "=" * 70)
print("close_combat_happened 標籤分布")
print("=" * 70)
print(train_df['close_combat_happened'].value_counts())

close_combat_count = (train_df['close_combat_happened'] == 1).sum()
print(f"\n近距離接觸樣本 (1): {close_combat_count} ({close_combat_count/len(train_df):.2%})")
print(f"非接觸樣本 (0): {len(train_df) - close_combat_count} ({(len(train_df) - close_combat_count)/len(train_df):.2%})")

# 超車 vs 近距離接觸交叉統計
print("\n" + "=" * 70)
print("超車 vs 近距離接觸 交叉統計")
print("=" * 70)
crosstab = pd.crosstab(
    train_df['overtake_happened'], 
    train_df['close_combat_happened'], 
    rownames=['overtake'], 
    colnames=['close_combat'],
    margins=True
)
print(crosstab)

# 計算超車樣本中有多少被標記為近距離接觸
overtake_samples = train_df[train_df['overtake_happened'] == 1]
overtake_with_combat = overtake_samples[overtake_samples['close_combat_happened'] == 1]
print(f"\n超車樣本中的近距離接觸比例: {len(overtake_with_combat)}/{len(overtake_samples)} ({len(overtake_with_combat)/len(overtake_samples):.2%})")

# 非超車樣本中的近距離接觸
non_overtake_samples = train_df[train_df['overtake_happened'] == 0]
non_overtake_with_combat = non_overtake_samples[non_overtake_samples['close_combat_happened'] == 1]
print(f"非超車樣本中的近距離接觸比例: {len(non_overtake_with_combat)}/{len(non_overtake_samples)} ({len(non_overtake_with_combat)/len(non_overtake_samples):.2%})")

# 顯示一些近距離接觸案例
print("\n" + "=" * 70)
print("前 10 個近距離接觸案例（非超車）")
print("=" * 70)
combat_cases = train_df[(train_df['close_combat_happened'] == 1) & (train_df['overtake_happened'] == 0)].head(10)
if len(combat_cases) > 0:
    print(combat_cases[['year', 'race', 'lap', 'attacker', 'defender', 'gap_seconds', 'gap_delta', 'is_catching']])
else:
    print("沒有找到非超車的近距離接觸案例")

print("\n" + "=" * 70)
print("年份分布")
print("=" * 70)
print(train_df['year'].value_counts().sort_index())

print("\n✅ 驗證完成！")
