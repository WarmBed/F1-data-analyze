import pandas as pd

df = pd.read_csv('data/overtake_prediction/training_samples.csv')

print("=" * 70)
print("close_combat_happened 檢查")
print("=" * 70)

print("\n值分布:")
print(df['close_combat_happened'].value_counts())

positive = (df['close_combat_happened'] == 1).sum()
total = len(df)
print(f"\n正樣本: {positive}")
print(f"總樣本: {total}")
print(f"比例: {positive / total:.2%}")

# 比較兩個標籤
print("\n兩個標籤的關係:")
print(pd.crosstab(df['overtake_happened'], df['close_combat_happened'], margins=True))
