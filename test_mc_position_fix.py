#!/usr/bin/env python3
"""
測試 Monte Carlo 位置分析修正

驗證項目：
1. 策略列寬度是否合理（100px）
2. Tire Strategy 列寬度是否合理（100px）
3. 位置增益計算是否考慮起始位置限制
"""

from PyQt5.QtWidgets import QApplication, QHeaderView
import sys

def test_column_widths():
    """測試列寬度設置"""
    print("\n[測試 1] 檢查列寬度設置")
    print("="*60)
    
    from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    tab = StrategyComparisonTab()
    
    # 檢查 MC 表格列寬度
    mc_table = tab.mc_table
    
    col_0_width = mc_table.columnWidth(0)  # Strategy
    col_2_width = mc_table.columnWidth(2)  # Tire Strategy
    col_0_resize_mode = mc_table.horizontalHeader().sectionResizeMode(0)
    col_2_resize_mode = mc_table.horizontalHeader().sectionResizeMode(2)
    
    print(f"策略列 (0):")
    print(f"  - 寬度: {col_0_width}px")
    print(f"  - 模式: {col_0_resize_mode} (應為 Fixed={QHeaderView.Fixed})")
    
    print(f"\nTire Strategy 列 (2):")
    print(f"  - 寬度: {col_2_width}px")
    print(f"  - 模式: {col_2_resize_mode} (應為 Fixed={QHeaderView.Fixed})")
    
    # 驗證
    assert col_0_width == 100, f"❌ 策略列寬度錯誤: {col_0_width} (應為 100)"
    assert col_2_width == 100, f"❌ Tire Strategy 列寬度錯誤: {col_2_width} (應為 100)"
    assert col_0_resize_mode == QHeaderView.Fixed, "❌ 策略列應為 Fixed 模式"
    assert col_2_resize_mode == QHeaderView.Fixed, "❌ Tire Strategy 列應為 Fixed 模式"
    
    print("\n✅ 列寬度測試通過！")
    return True


def test_position_gain_logic():
    """測試位置增益計算邏輯"""
    print("\n[測試 2] 檢查位置增益計算邏輯")
    print("="*60)
    
    from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
    from strategy_simulator.core.monte_carlo import MonteCarloSummary
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    tab = StrategyComparisonTab()
    
    # 測試案例 1: P2 起跑，勝率 26%
    print("\n案例 1: P2 起跑，勝率 26%")
    mc = MonteCarloSummary(iterations=1000)
    mc.starting_position = 2
    mc.win_percentages = {"Plan A": 26.0}
    mc.mean_times = {"Plan A": 5128.504}
    mc.std_times = {"Plan A": 113.377}
    mc.sc_impact_analysis = {
        "Plan A": {'wins_without_sc': 200, 'wins_with_sc': 60}
    }
    
    tab._mc_results = mc
    
    gain = tab._estimate_position_gain("Plan A: M→H", 26.0, 113.377)
    
    print(f"  預期增益: {gain['expected']}")
    print(f"  最佳情況: +{gain['best']}")
    print(f"  最差情況: -{gain['worst']}")
    
    # 驗證：從 P2 起跑，最多只能 +1（到 P1）
    assert gain['expected'] <= 1, f"❌ 從 P2 起跑，預期增益不應超過 1: {gain['expected']}"
    assert gain['best'] <= 1, f"❌ 從 P2 起跑，最佳增益不應超過 1: {gain['best']}"
    
    print(f"  ✅ 正確！從 P2 最多只能 +{gain['best']}")
    
    # 測試案例 2: P10 起跑，勝率 11%
    print("\n案例 2: P10 起跑，勝率 11%")
    mc.starting_position = 10
    tab._mc_results = mc
    
    gain = tab._estimate_position_gain("Plan B: S→M→H", 11.0, 112.641)
    
    print(f"  預期增益: {gain['expected']}")
    print(f"  最佳情況: +{gain['best']}")
    print(f"  最差情況: -{gain['worst']}")
    
    # 驗證：從 P10 起跑，最多只能 +9（到 P1）
    assert gain['expected'] <= 9, f"❌ 從 P10 起跑，預期增益不應超過 9: {gain['expected']}"
    assert gain['best'] <= 9, f"❌ 從 P10 起跑，最佳增益不應超過 9: {gain['best']}"
    
    print(f"  ✅ 正確！從 P10 最多只能 +{gain['best']}")
    
    # 測試案例 3: P18 起跑，勝率 3%
    print("\n案例 3: P18 起跑，勝率 3%")
    mc.starting_position = 18
    tab._mc_results = mc
    
    gain = tab._estimate_position_gain("Plan E: M→M", 3.0, 114.751)
    
    print(f"  預期增益: {gain['expected']}")
    print(f"  最佳情況: +{gain['best']}")
    print(f"  最差情況: -{gain['worst']}")
    
    # 驗證：從 P18 起跑
    # 最多只能 +17（到 P1）
    # 最差只能 -2（到 P20）
    assert gain['expected'] <= 17, f"❌ 從 P18 起跑，預期增益不應超過 17: {gain['expected']}"
    assert gain['best'] <= 17, f"❌ 從 P18 起跑，最佳增益不應超過 17: {gain['best']}"
    assert gain['worst'] <= 2, f"❌ 從 P18 起跑，最差損失不應超過 2: {gain['worst']}"
    
    print(f"  ✅ 正確！從 P18 最多 +{gain['best']}, 最差 -{gain['worst']}")
    
    print("\n✅ 位置增益計算邏輯測試通過！")
    return True


def test_realistic_scenario():
    """測試真實場景：用戶選擇 P2 車手"""
    print("\n[測試 3] 真實場景：P2 起跑車手的位置分析")
    print("="*60)
    
    from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
    from strategy_simulator.core.monte_carlo import MonteCarloSummary
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    tab = StrategyComparisonTab()
    
    # 模擬用戶提供的數據
    mc = MonteCarloSummary(iterations=1000)
    mc.starting_position = 2  # P2 起跑
    mc.win_percentages = {
        "Plan A": 26.0,
        "Plan B": 11.0,
        "Plan C": 10.0,
        "Plan D": 9.0,
        "Plan E": 3.0
    }
    mc.mean_times = {
        "Plan A": 5128.504,
        "Plan B": 5124.938,
        "Plan C": 5119.236,
        "Plan D": 5119.502,
        "Plan E": 5123.138
    }
    mc.std_times = {
        "Plan A": 113.377,
        "Plan B": 112.641,
        "Plan C": 114.748,
        "Plan D": 114.572,
        "Plan E": 114.751
    }
    mc.sc_impact_analysis = {
        name: {'wins_without_sc': 0, 'wins_with_sc': 0}
        for name in mc.win_percentages.keys()
    }
    mc.sc_occurrence_rate = 85.0
    mc.mean_sc_count = 1.56
    
    tab._mc_results = mc
    
    print("\n模擬用戶數據（從圖片）：")
    print("起始位置: P2")
    print("\n策略 | 勝率  | 標準差   | 位置增益 | 風險")
    print("-" * 60)
    
    for i, (name, win_pct) in enumerate(sorted(mc.win_percentages.items(), key=lambda x: x[1], reverse=True)):
        std = mc.std_times[name]
        gain = tab._estimate_position_gain(name, win_pct, std)
        
        print(f"{name:8} | {win_pct:5.1f}% | {std:7.3f}s | +{gain['expected']:8} | +{gain['best']}/-{gain['worst']}")
        
        # 驗證：所有策略的增益都不應超過 1
        assert gain['expected'] <= 1, f"❌ {name}: 預期增益 {gain['expected']} 超過限制"
        assert gain['best'] <= 1, f"❌ {name}: 最佳增益 {gain['best']} 超過限制"
    
    print("\n✅ 所有策略的位置增益都合理！")
    print("   從 P2 起跑，最多只能進步到 P1 (+1)")
    return True


def main():
    """執行所有測試"""
    print("="*60)
    print("Monte Carlo 位置分析修正驗證")
    print("="*60)
    
    try:
        test_column_widths()
        test_position_gain_logic()
        test_realistic_scenario()
        
        print("\n" + "="*60)
        print("✅ 所有測試通過！")
        print("="*60)
        print("\n修正內容總結：")
        print("1. ✅ 策略列寬度：Stretch → Fixed (100px)")
        print("2. ✅ Tire Strategy 列寬度：Stretch → Fixed (100px)")
        print("3. ✅ 位置增益計算：考慮起始位置限制")
        print("   - P2 起跑 → 最多 +1（到 P1）")
        print("   - P10 起跑 → 最多 +9（到 P1）")
        print("   - P18 起跑 → 最多 +17（到 P1），最差 -2（到 P20）")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
