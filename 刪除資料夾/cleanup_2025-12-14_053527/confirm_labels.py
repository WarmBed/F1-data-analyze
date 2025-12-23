import pandas as pd

df = pd.read_csv('data/overtake_prediction/training_samples.csv')

print("=" * 70)
print("確認數據集同時包含 OT% 和 CC% 標籤")
print("=" * 70)

print(f"\n總樣本數: {len(df)}")

print(f"\n1. Overtake (OT%) 標籤:")
print(f"   overtake_happened = 1: {df['overtake_happened'].sum()} ({df['overtake_happened'].sum()/len(df):.2%})")
print(f"   overtake_happened = 0: {(df['overtake_happened']==0).sum()} ({(df['overtake_happened']==0).sum()/len(df):.2%})")

print(f"\n2. Close Combat (CC%) 標籤:")
print(f"   close_combat_happened = 1: {df['close_combat_happened'].sum()} ({df['close_combat_happened'].sum()/len(df):.2%})")
print(f"   close_combat_happened = 0: {(df['close_combat_happened']==0).sum()} ({(df['close_combat_happened']==0).sum()/len(df):.2%})")

print("\n✅ 數據集可以同時訓練兩個模型:")
print("   - F83: 預測 overtake_happened (OT%)")
print("   - F85: 預測 close_combat_happened (CC%)")
