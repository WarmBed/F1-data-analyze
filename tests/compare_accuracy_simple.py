import json
import numpy as np

print("\n" + "="*70)
print("F57 vs F91 準確度對比分析 - VER (2025 Abu Dhabi GP)")
print("="*70)

# 載入 F57 預測
with open('json/combined_laptime_2025_Abu_Dhabi_R_20251213_025407.json', encoding='utf-8') as f:
    f57_data = json.load(f)

# 載入最新 F91 預測
with open('json/fp2_race_ml_prediction_v2_2025_Abu_Dhabi_20251213_041436.json', encoding='utf-8') as f:
    f91_data = json.load(f)

# VER 的實際圈速（從您的截圖數據手動輸入關鍵圈數）
# Real 數據：綠色實線顯示大部分圈速在 88-90 秒，pit lap (24圈) 約 109 秒
real_reference = 89.0  # 正常圈速平均值（從圖表估計）

# 解析 F57 預測
f57_predictions = f57_data['drivers']['1']['predictions']
f57_predicted_times = [lap['predicted_time'] for lap in f57_predictions]
f57_normal_laps = [t for t in f57_predicted_times if t < 100]  # 排除異常值
f57_avg = np.mean(f57_normal_laps)
f57_std = np.std(f57_normal_laps)

# 解析 F91 預測
f91_predictions = f91_data['predictions']['1']['predicted_laps']
f91_values = [float(v) for v in f91_predictions.values()]
f91_normal_laps = [t for t in f91_values if t < 100]  # 排除異常值
f91_avg = np.mean(f91_normal_laps)
f91_std = np.std(f91_normal_laps)

print(f"\n基於圖表的對比分析:")
print(f"{'='*70}")
print(f"\n{'方法':<10} {'預測圈數':<12} {'平均圈速':<12} {'標準差':<12} {'與Real差距':<12}")
print("-" * 70)

print(f"{'Real':<10} {'-':<12} {real_reference:<12.3f} {'-':<12} {'-':<12}")
print(f"{'F57':<10} {len(f57_normal_laps):<12} {f57_avg:<12.3f} {f57_std:<12.3f} {abs(f57_avg - real_reference):<12.3f}")
print(f"{'F91':<10} {len(f91_normal_laps):<12} {f91_avg:<12.3f} {f91_std:<12.3f} {abs(f91_avg - real_reference):<12.3f}")

# 計算改進
f57_error = abs(f57_avg - real_reference)
f91_error = abs(f91_avg - real_reference)
improvement = ((f57_error - f91_error) / f57_error) * 100 if f57_error > 0 else 0

print(f"\n{'='*70}")
if f91_error < f57_error:
    print(f"✅ F91 平均誤差比 F57 小 {improvement:.1f}%")
    print(f"   F91 更接近實際圈速 ({f91_avg:.3f}s vs F57 {f57_avg:.3f}s)")
else:
    print(f"❌ F57 平均誤差比 F91 小 {abs(improvement):.1f}%")

# 分析預測穩定性
print(f"\n預測穩定性分析:")
print(f"  F57 標準差: {f57_std:.3f}s {'(更穩定 ✓)' if f57_std < f91_std else ''}")
print(f"  F91 標準差: {f91_std:.3f}s {'(更穩定 ✓)' if f91_std < f57_std else ''}")

# 檢查異常值清理效果
f91_high_laps = [v for v in f91_values if v >= 100]
print(f"\nF91 異常值清理效果:")
print(f"  剩餘異常值（≥100s）: {len(f91_high_laps)} 個")
if f91_high_laps:
    print(f"  異常圈速: {[f'{v:.1f}s' for v in f91_high_laps]}")
else:
    print(f"  ✅ 所有異常值已成功移除！")

# 總結
print(f"\n{'='*70}")
print("總結:")
print("="*70)

print(f"\n1. **準確度**: ", end='')
if f91_error < f57_error:
    print(f"F91 勝出 ✓")
    print(f"   - F91 平均圈速 {f91_avg:.3f}s 更接近實際 {real_reference}s")
    print(f"   - 誤差減少 {improvement:.1f}%")
else:
    print(f"F57 勝出")

print(f"\n2. **穩定性**: ", end='')
if f91_std < f57_std:
    print(f"F91 勝出 ✓")
    print(f"   - F91 圈速變化更小（{f91_std:.3f}s vs {f57_std:.3f}s）")
else:
    print(f"F57 勝出")
    print(f"   - F57 圈速變化更小（{f57_std:.3f}s vs {f91_std:.3f}s）")

print(f"\n3. **數據品質**: ", end='')
if len(f91_high_laps) == 0:
    print("F91 勝出 ✓")
    print("   - F91 已成功移除所有異常值")
    print("   - 預測更平滑、更符合實際比賽圈速分佈")
else:
    print(f"仍有 {len(f91_high_laps)} 個異常值需要處理")

print(f"\n{'='*70}")
print("結論:")
print("="*70)
if f91_error < f57_error and len(f91_high_laps) == 0:
    print("✅ F91 (機器學習) 在此次比賽中比 F57 (物理模型) 更準確")
    print("   - 使用 FP2 數據訓練的 XGBoost 模型能更好地捕捉實際比賽特性")
    print("   - 動態異常值過濾 + 插值補償策略有效")
elif f57_error < f91_error:
    print("✅ F57 (物理模型) 在此次比賽中更穩定可靠")
    print("   - 燃油消耗 + 輪胎退化的物理建模對此賽道更適用")
else:
    print("⚖️  F57 和 F91 性能相當，各有優勢")

print("\n💡 建議: 結合兩者優勢，可以開發混合預測模型 (F92)")
print("="*70 + "\n")
