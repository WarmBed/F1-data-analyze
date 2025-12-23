"""
測試 F81 近距離接觸標籤生成
"""
from CLI_modules.cli.prediction.overtake_prediction.data_collector import OvertakeDataCollector
import pandas as pd

print("=" * 70)
print("測試 F81 近距離接觸標籤生成（Abu Dhabi 2024）")
print("=" * 70)

# 初始化收集器
collector = OvertakeDataCollector(verbose=True)

# 收集單場比賽測試
print("\n[測試] 收集 Abu Dhabi 2024...")
count = collector.collect_race(2024, "Abu_Dhabi_Race")

print(f"\n[結果] 收集到 {count} 次超車事件")
print(f"[結果] 訓練樣本: {len(collector.training_samples)} 筆")

# 檢查 close_combat_happened 標籤
if collector.training_samples:
    df = pd.DataFrame([{
        'gap_seconds': s.gap_seconds,
        'overtake_happened': s.overtake_happened,
        'close_combat_happened': s.close_combat_happened,
        'lap': s.lap,
        'attacker': s.attacker,
        'defender': s.defender
    } for s in collector.training_samples])
    
    print("\n" + "=" * 70)
    print("close_combat_happened 標籤統計")
    print("=" * 70)
    print(f"總樣本: {len(df)}")
    print(f"\nclose_combat_happened 分布:")
    print(df['close_combat_happened'].value_counts())
    
    close_combat_count = (df['close_combat_happened'] == 1).sum()
    print(f"\n近距離接觸樣本: {close_combat_count} ({close_combat_count/len(df):.2%})")
    
    # 顯示一些近距離接觸案例
    if close_combat_count > 0:
        print("\n前 5 個近距離接觸案例:")
        combat_samples = df[df['close_combat_happened'] == 1].head(5)
        print(combat_samples[['lap', 'attacker', 'defender', 'gap_seconds', 'overtake_happened']])
    
    # 交叉統計
    print("\n超車 vs 近距離接觸:")
    print(pd.crosstab(df['overtake_happened'], df['close_combat_happened'], margins=True))
else:
    print("[錯誤] 沒有收集到訓練樣本")
