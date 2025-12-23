#!/usr/bin/env python3
"""
對比 v3.3 vs v3.4 在 2025 驗證的結果
"""

import json
import pandas as pd

# 載入結果
with open('v3.3_2025_validation_results.json', 'r', encoding='utf-8') as f:
    v33 = json.load(f)

with open('v3.4_2025_validation_results.json', 'r', encoding='utf-8') as f:
    v34 = json.load(f)

print("="*80)
print("v3.3 vs v3.4 - 2025 驗證結果對比")
print("="*80)

# 整體對比
print("\n[整體表現對比]")
print(f"{'指標':<25} {'v3.3':<15} {'v3.4':<15} {'變化':<15}")
print("-"*70)

v33_summary = v33['summary']
v34_summary = v34['summary']

spearman_33 = v33_summary['avg_spearman']
spearman_34 = v34_summary['avg_spearman']
spearman_change = spearman_34 - spearman_33
spearman_pct = (spearman_change / spearman_33) * 100

mae_33 = v33_summary['avg_mae']
mae_34 = v34_summary['avg_mae']
mae_change = mae_34 - mae_33
mae_pct = (mae_change / mae_33) * 100

print(f"{'成功預測賽事數':<25} {v33['metadata']['successful_predictions']:<15} {v34['metadata']['successful_predictions']:<15} {v34['metadata']['successful_predictions'] - v33['metadata']['successful_predictions']:<15}")
print(f"{'平均 Spearman 相關性':<25} {spearman_33:<15.3f} {spearman_34:<15.3f} {spearman_change:+.3f} ({spearman_pct:+.1f}%)")
print(f"{'平均 MAE (秒)':<25} {mae_33:<15.3f} {mae_34:<15.3f} {mae_change:+.3f} ({mae_pct:+.1f}%)")

if 'avg_top3_accuracy' in v33_summary and 'avg_top3_accuracy' in v34_summary:
    top3_33 = v33_summary['avg_top3_accuracy']
    top3_34 = v34_summary['avg_top3_accuracy']
    top3_change = top3_34 - top3_33
    print(f"{'平均 Top3 準確率':<25} {top3_33:<15.1%} {top3_34:<15.1%} {top3_change:+.1%}")

# 共同賽道對比
v33_races = set(v33['race_results'].keys())
v34_races = set(v34['race_results'].keys())
common_races = sorted(v33_races & v34_races)

print(f"\n[共同驗證賽道: {len(common_races)} 場]")
print(f"{'賽道':<20} {'v3.3 Spearman':<15} {'v3.4 Spearman':<15} {'變化':<15} {'v3.3 MAE':<12} {'v3.4 MAE':<12} {'MAE變化':<12}")
print("-"*110)

improvements = []
degradations = []

for race in common_races:
    v33_race = v33['race_results'][race]
    v34_race = v34['race_results'][race]
    
    sp33 = v33_race['spearman']
    sp34 = v34_race['spearman']
    sp_change = sp34 - sp33
    
    mae33 = v33_race['mae']
    mae34 = v34_race['mae']
    mae_change = mae34 - mae33
    
    # 判斷改進或退步（Spearman 增加且 MAE 減少為改進）
    if sp_change > 0 and mae_change < 0:
        status = "✅ 改進"
        improvements.append((race, sp_change, mae_change))
    elif sp_change < 0 or mae_change > 0:
        status = "❌ 退步"
        degradations.append((race, sp_change, mae_change))
    else:
        status = "➖ 持平"
    
    print(f"{race:<20} {sp33:<15.3f} {sp34:<15.3f} {sp_change:+15.3f} {mae33:<12.3f}s {mae34:<12.3f}s {mae_change:+12.3f}s  {status}")

# 重點關注：Great Britain & Canada
print("\n" + "="*80)
print("⭐ 重點分析：Great Britain & Canada（max_speed 問題賽道）")
print("="*80)

for race in ['Great Britain', 'Canada']:
    if race in common_races:
        print(f"\n[{race}]")
        v33_race = v33['race_results'][race]
        v34_race = v34['race_results'][race]
        
        print(f"  v3.3 訓練 MAE: 0.489s (Great Britain) / Unknown (Canada)")
        print(f"  v3.4 訓練 MAE: 0.321s (Great Britain, -34.4%) / Unknown (Canada)")
        print(f"\n  2025 實際驗證:")
        print(f"    v3.3 - Spearman: {v33_race['spearman']:.3f}, MAE: {v33_race['mae']:.3f}s, R²: {v33_race.get('r2', 'N/A')}")
        print(f"    v3.4 - Spearman: {v34_race['spearman']:.3f}, MAE: {v34_race['mae']:.3f}s, R²: {v34_race.get('r2', 'N/A')}")
        print(f"\n  變化:")
        print(f"    Spearman: {v34_race['spearman'] - v33_race['spearman']:+.3f}")
        print(f"    MAE: {v34_race['mae'] - v33_race['mae']:+.3f}s")
        
        if race == 'Great Britain':
            print(f"\n  特徵重要性變化:")
            print(f"    v3.3: max_speed 55.50% (異常高)")
            print(f"    v3.4: max_speed_lap_ratio 67.56%, 總 max_speed 相關 68.83% (更糟!)")
        elif race == 'Canada':
            print(f"\n  特徵重要性:")
            print(f"    v3.4: max_speed 相關特徵總占比 77.26% (極度嚴重)")

# 統計摘要
print("\n" + "="*80)
print("結論總結")
print("="*80)

print(f"\n改進賽道: {len(improvements)} 場")
if improvements:
    for race, sp_change, mae_change in sorted(improvements, key=lambda x: x[1], reverse=True):
        print(f"  • {race}: Spearman {sp_change:+.3f}, MAE {mae_change:+.3f}s")

print(f"\n退步賽道: {len(degradations)} 場")
if degradations:
    for race, sp_change, mae_change in sorted(degradations, key=lambda x: x[1]):
        print(f"  • {race}: Spearman {sp_change:+.3f}, MAE {mae_change:+.3f}s")

# 最終判斷
print("\n" + "="*80)
print("⚠️  v3.4 實施效果評估")
print("="*80)

if spearman_34 > spearman_33:
    print(f"✅ 整體 Spearman 提升 {spearman_pct:+.1f}% ({spearman_33:.3f} → {spearman_34:.3f})")
else:
    print(f"❌ 整體 Spearman 下降 {spearman_pct:.1f}% ({spearman_33:.3f} → {spearman_34:.3f})")

if mae_34 < mae_33:
    print(f"✅ 整體 MAE 改善 {mae_pct:.1f}% ({mae_33:.3f}s → {mae_34:.3f}s)")
else:
    print(f"❌ 整體 MAE 惡化 {mae_pct:+.1f}% ({mae_33:.3f}s → {mae_34:.3f}s)")

print("\n📊 核心發現:")
print("  1. v3.4 添加 max_speed 交互特徵的策略在實際 2025 驗證中表現如何？")
print(f"     → 整體 Spearman: {spearman_pct:+.1f}% 變化")
print(f"     → 整體 MAE: {mae_pct:+.1f}% 變化")

if 'Great Britain' in common_races:
    gb_v33 = v33['race_results']['Great Britain']
    gb_v34 = v34['race_results']['Great Britain']
    gb_sp_change = gb_v34['spearman'] - gb_v33['spearman']
    gb_mae_change = gb_v34['mae'] - gb_v33['mae']
    
    print(f"\n  2. Great Britain 問題是否解決？")
    print(f"     訓練時: MAE 從 0.489s 降至 0.321s (-34.4%) ✅")
    print(f"     但特徵: max_speed 相關從 55.50% 增至 68.83% (+24%) ❌")
    print(f"     2025 驗證: Spearman {gb_sp_change:+.3f}, MAE {gb_mae_change:+.3f}s")
    if gb_sp_change > 0 and gb_mae_change < 0:
        print(f"     → ✅ Great Britain 在 2025 實際表現改善!")
    elif gb_mae_change > 0:
        print(f"     → ❌ Great Britain MAE 惡化 {gb_mae_change:+.3f}s，問題未解決")
    else:
        print(f"     → ⚠️  Great Britain 改善不明顯")

if 'Canada' in common_races:
    ca_v33 = v33['race_results']['Canada']
    ca_v34 = v34['race_results']['Canada']
    ca_sp_change = ca_v34['spearman'] - ca_v33['spearman']
    ca_mae_change = ca_v34['mae'] - ca_v33['mae']
    
    print(f"\n  3. Canada 表現（v3.4 中 77.26% max_speed 相關）:")
    print(f"     2025 驗證: Spearman {ca_sp_change:+.3f} ({ca_v33['spearman']:.3f} → {ca_v34['spearman']:.3f})")
    print(f"     2025 驗證: MAE {ca_mae_change:+.3f}s ({ca_v33['mae']:.3f}s → {ca_v34['mae']:.3f}s)")
    if ca_mae_change > 0:
        print(f"     → ❌ Canada 問題更嚴重，v3.4 策略失敗")

print("\n💡 建議:")
if len(degradations) > len(improvements):
    print("  ❌ v3.4 整體表現不如 v3.3，不建議採用")
    print("  → 應探索其他策略（如移除 max_speed 特徵或限制權重）")
else:
    print("  ✅ v3.4 可能有改善，但需進一步分析")
    print("  → 檢查改善是否來自 max_speed 交互特徵")
