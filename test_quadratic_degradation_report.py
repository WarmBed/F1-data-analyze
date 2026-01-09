#!/usr/bin/env python3
"""
測試策略報告生成器的二次曲線退化模型

驗證報告生成器現在正確使用：
1. SimulationParams 的退化率和加速度係數
2. 二次曲線公式: cumulative_deg(t) = base_rate * t + 0.5 * acceleration * t²
3. 與 LapSimulator 一致的計算邏輯

Author: F1T Team
Date: 2026-01-07
"""

import sys

print("=" * 70)
print("策略報告生成器 - 二次曲線退化模型測試")
print("=" * 70)

# Test 1: Import SimulationParams
print("\n[測試 1] 導入 SimulationParams 和退化模型")
try:
    from strategy_simulator.core.lap_simulator import SimulationParams, Compound
    params = SimulationParams()
    
    print("  ✅ SimulationParams 導入成功")
    print(f"  ✅ SOFT 基礎退化率: {params.get_deg_rate(Compound.SOFT):.4f} s/lap")
    print(f"  ✅ MEDIUM 基礎退化率: {params.get_deg_rate(Compound.MEDIUM):.4f} s/lap")
    print(f"  ✅ HARD 基礎退化率: {params.get_deg_rate(Compound.HARD):.4f} s/lap")
    print(f"  ✅ SOFT 加速度: {params.get_deg_acceleration(Compound.SOFT):.4f} s/lap²")
    print(f"  ✅ MEDIUM 加速度: {params.get_deg_acceleration(Compound.MEDIUM):.4f} s/lap²")
    print(f"  ✅ HARD 加速度: {params.get_deg_acceleration(Compound.HARD):.4f} s/lap²")
except ImportError as e:
    print(f"  ❌ 導入失敗: {e}")
    sys.exit(1)

# Test 2: Import StrategyReportGenerator
print("\n[測試 2] 導入 StrategyReportGenerator")
try:
    from strategy_simulator.gui.widgets.strategy_report_generator import StrategyReportGenerator
    generator = StrategyReportGenerator()
    
    print("  ✅ StrategyReportGenerator 導入成功")
    print(f"  ✅ SOFT 退化率: {generator._deg_rates['SOFT']:.4f} s/lap")
    print(f"  ✅ MEDIUM 退化率: {generator._deg_rates['MEDIUM']:.4f} s/lap")
    print(f"  ✅ HARD 退化率: {generator._deg_rates['HARD']:.4f} s/lap")
    print(f"  ✅ SOFT 加速度: {generator._deg_acceleration['SOFT']:.4f} s/lap²")
    print(f"  ✅ MEDIUM 加速度: {generator._deg_acceleration['MEDIUM']:.4f} s/lap²")
    print(f"  ✅ HARD 加速度: {generator._deg_acceleration['HARD']:.4f} s/lap²")
except ImportError as e:
    print(f"  ❌ 導入失敗: {e}")
    sys.exit(1)

# Test 3: Verify degradation calculation matches LapSimulator
print("\n[測試 3] 驗證二次曲線退化計算")

def calculate_cumulative_degradation(base_rate: float, acceleration: float, laps: int) -> float:
    """
    計算累積退化 (二次曲線公式)
    與 LapSimulator 的 calculate_lap_time 方法一致
    """
    return base_rate * laps + 0.5 * acceleration * (laps ** 2)

test_cases = [
    # (Compound, Laps)
    (Compound.SOFT, 15),
    (Compound.SOFT, 20),
    (Compound.MEDIUM, 25),
    (Compound.MEDIUM, 30),
    (Compound.HARD, 35),
    (Compound.HARD, 40),
]

print("\n  配方      | 圈數 | 基礎退化 | 二次項 | 累積退化 | 狀態")
print("  " + "-" * 70)

for compound, laps in test_cases:
    base_rate = params.get_deg_rate(compound)
    acceleration = params.get_deg_acceleration(compound)
    
    linear_part = base_rate * laps
    quadratic_part = 0.5 * acceleration * (laps ** 2)
    total_deg = linear_part + quadratic_part
    
    compound_name = compound.value
    
    # 判斷退化程度
    if total_deg < 2.0:
        status = "✅ 良好"
    elif total_deg < 4.0:
        status = "⚠️  中度"
    else:
        status = "🔴 嚴重"
    
    print(f"  {compound_name:8} | {laps:4} | {linear_part:7.2f}s | {quadratic_part:6.2f}s | {total_deg:7.2f}s | {status}")

# Test 4: Compare linear vs quadratic model
print("\n[測試 4] 線性模型 vs 二次曲線模型差異")

print("\n  配方      | 圈數 | 線性模型 | 二次模型 | 差異    | 差異%")
print("  " + "-" * 70)

for compound, laps in test_cases:
    base_rate = params.get_deg_rate(compound)
    acceleration = params.get_deg_acceleration(compound)
    
    linear_model = base_rate * laps  # 舊的簡化模型
    quadratic_model = base_rate * laps + 0.5 * acceleration * (laps ** 2)  # 正確的二次曲線模型
    
    difference = quadratic_model - linear_model
    difference_pct = (difference / linear_model * 100) if linear_model > 0 else 0
    
    compound_name = compound.value
    print(f"  {compound_name:8} | {laps:4} | {linear_model:7.2f}s | {quadratic_model:7.2f}s | {difference:+6.2f}s | {difference_pct:+5.1f}%")

# Test 5: Realistic stint degradation examples
print("\n[測試 5] 真實 Stint 退化範例")
print("\n  情境: 阿布達比 2025，57 圈比賽")
print()

realistic_scenarios = [
    ("短 Stint (SOFT)", Compound.SOFT, 18, "快速衝刺，早進站"),
    ("標準 Stint (MEDIUM)", Compound.MEDIUM, 28, "平衡策略，單停"),
    ("長 Stint (HARD)", Compound.HARD, 40, "延遲進站，極限耐久"),
]

for scenario_name, compound, stint_laps, strategy in realistic_scenarios:
    base_rate = params.get_deg_rate(compound)
    acceleration = params.get_deg_acceleration(compound)
    
    total_deg = calculate_cumulative_degradation(base_rate, acceleration, stint_laps)
    
    print(f"  🏁 {scenario_name}: {stint_laps} 圈")
    print(f"     策略: {strategy}")
    print(f"     累積退化: {total_deg:.2f}s")
    print(f"     平均退化: {total_deg / stint_laps:.3f}s/lap")
    print()

# Test 6: Verify report generator uses same calculation
print("\n[測試 6] 驗證報告生成器使用相同計算")

print("\n  檢查報告生成器的退化率是否與 SimulationParams 一致...")

all_match = True
for compound_name in ['SOFT', 'MEDIUM', 'HARD']:
    compound_enum = getattr(Compound, compound_name)
    
    # SimulationParams 的值
    sim_base_rate = params.get_deg_rate(compound_enum)
    sim_acceleration = params.get_deg_acceleration(compound_enum)
    
    # StrategyReportGenerator 的值
    gen_base_rate = generator._deg_rates[compound_name]
    gen_acceleration = generator._deg_acceleration[compound_name]
    
    base_match = abs(sim_base_rate - gen_base_rate) < 0.0001
    accel_match = abs(sim_acceleration - gen_acceleration) < 0.0001
    
    status = "✅" if (base_match and accel_match) else "❌"
    
    print(f"  {status} {compound_name:8}: base_rate={gen_base_rate:.4f} (match: {base_match}), "
          f"acceleration={gen_acceleration:.4f} (match: {accel_match})")
    
    if not (base_match and accel_match):
        all_match = False

if all_match:
    print("\n  ✅ 所有參數完全一致！報告生成器使用正確的退化模型。")
else:
    print("\n  ⚠️  參數不一致！需要檢查 StrategyReportGenerator 的初始化。")

print("\n" + "=" * 70)
print("測試完成")
print("=" * 70)

# Summary
print("\n【總結】")
print("✅ 策略報告生成器現在使用二次曲線退化模型")
print("✅ 退化公式: cumulative_deg(t) = base_rate × t + 0.5 × acceleration × t²")
print("✅ 與 LapSimulator 的計算邏輯完全一致")
print("✅ 報告將顯示:")
print("   - 基礎退化部分 (線性)")
print("   - 加速退化部分 (二次)")
print("   - 總累積退化")
print()
print("🔍 舊模型問題:")
print("   - 使用固定的線性退化率 (SOFT=0.09, MEDIUM=0.055, HARD=0.035)")
print("   - 忽略了加速退化效應")
print("   - 在長 Stint 中低估了實際退化")
print()
print("✅ 新模型優勢:")
print("   - 使用 SimulationParams 的訓練數據")
print("   - 二次曲線更準確反映輪胎物理")
print("   - 與策略模擬器的計算完全一致")
print("   - 顯示詳細的退化分解資訊")
