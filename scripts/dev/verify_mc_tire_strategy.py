#!/usr/bin/env python3
"""
驗證 Monte Carlo 輪胎策略顯示功能

這個腳本驗證更新是否正確實現：
1. 表格有 10 列
2. 列標題包含 "Stops" 和 "Tire Strategy"
3. 數據填充邏輯正確
"""

import sys
import os

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.abspath('.'))

def verify_table_structure():
    """驗證表格結構"""
    print("=" * 60)
    print("驗證表格結構")
    print("=" * 60)
    
    from PyQt5.QtWidgets import QApplication
    from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
    
    # 創建 QApplication（如果不存在）
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 創建實例（不顯示 GUI）
    tab = StrategyComparisonTab()
    
    # 檢查列數
    col_count = tab.mc_table.columnCount()
    print(f"✅ 列數: {col_count}")
    assert col_count == 10, f"Expected 10 columns, got {col_count}"
    
    # 檢查列標題
    headers = []
    for i in range(col_count):
        item = tab.mc_table.horizontalHeaderItem(i)
        if item:
            headers.append(item.text())
    
    print(f"✅ 列標題: {headers}")
    
    # 驗證新列存在
    assert "Stops" in headers, "Missing 'Stops' column"
    assert "Tire Strategy" in headers, "Missing 'Tire Strategy' column"
    
    # 驗證列順序
    expected_order = ["Strategy", "Stops", "Tire Strategy", "Win%"]
    actual_order = headers[:4]
    print(f"✅ 前 4 列順序: {actual_order}")
    assert actual_order == expected_order, f"Column order mismatch: {actual_order} vs {expected_order}"
    
    print("\n✅ 表格結構驗證通過！\n")

def verify_data_logic():
    """驗證數據邏輯"""
    print("=" * 60)
    print("驗證數據填充邏輯")
    print("=" * 60)
    
    from strategy_simulator.core.lap_simulator import StrategySimulationResult, Stint, Compound
    from strategy_simulator.core.monte_carlo import MonteCarloSummary
    
    # 創建測試結果
    result = StrategySimulationResult(
        strategy_name="Test Plan",
        stints=[
            Stint(Compound.SOFT, 15, 1),
            Stint(Compound.MEDIUM, 20, 16),
            Stint(Compound.HARD, 23, 36)
        ]
    )
    
    # 驗證輪胎標記
    notation = result.get_stint_notation()
    print(f"✅ 輪胎標記: {notation}")
    assert notation == "S→M→H", f"Expected 'S→M→H', got '{notation}'"
    
    # 驗證進站次數
    stops = result.num_stops
    print(f"✅ 進站次數: {stops}")
    assert stops == 2, f"Expected 2 stops, got {stops}"
    
    # 驗證 MC 數據結構
    mc = MonteCarloSummary(iterations=1000)
    mc.win_percentages = {"Test Plan": 45.0}
    mc.mean_times = {"Test Plan": 5420.5}
    
    ranking = mc.get_ranking()
    print(f"✅ MC 排名: {ranking}")
    assert len(ranking) == 1, "Should have 1 strategy"
    assert ranking[0][0] == "Test Plan", "Strategy name mismatch"
    
    print("\n✅ 數據邏輯驗證通過！\n")

def verify_integration():
    """驗證整合邏輯"""
    print("=" * 60)
    print("驗證結果與 MC 整合")
    print("=" * 60)
    
    from PyQt5.QtWidgets import QApplication
    from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
    from strategy_simulator.core.lap_simulator import StrategySimulationResult, Stint, Compound
    from strategy_simulator.core.monte_carlo import MonteCarloSummary
    
    # 確保 QApplication 存在
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 創建標籤
    tab = StrategyComparisonTab()
    
    # 創建結果
    results = [
        StrategySimulationResult(
            strategy_name="Plan A",
            stints=[
                Stint(Compound.SOFT, 15, 1),
                Stint(Compound.MEDIUM, 20, 16),
                Stint(Compound.HARD, 23, 36)
            ]
        )
    ]
    
    # 更新結果
    tab.update_results(results)
    print(f"✅ 已設置 {len(tab._results)} 個結果")
    
    # 創建 MC 結果
    mc = MonteCarloSummary(iterations=1000)
    mc.win_percentages = {"Plan A": 45.0}
    mc.mean_times = {"Plan A": 5420.5}
    mc.std_times = {"Plan A": 3.5}
    mc.sc_impact_analysis = {
        "Plan A": {"wins_without_sc": 200, "wins_with_sc": 250}
    }
    mc.sc_occurrence_rate = 40.0
    
    # 更新 MC 結果
    tab.update_monte_carlo(mc)
    
    # 驗證表格有數據
    row_count = tab.mc_table.rowCount()
    print(f"✅ MC 表格行數: {row_count}")
    assert row_count == 1, f"Expected 1 row, got {row_count}"
    
    # 驗證數據正確填充
    name_item = tab.mc_table.item(0, 0)
    stops_item = tab.mc_table.item(0, 1)
    tire_item = tab.mc_table.item(0, 2)
    win_item = tab.mc_table.item(0, 3)
    
    assert name_item and name_item.text() == "Plan A", "Strategy name incorrect"
    assert stops_item and stops_item.text() == "2", "Stops count incorrect"
    assert tire_item and tire_item.text() == "S→M→H", "Tire strategy incorrect"
    assert win_item and "45.0" in win_item.text(), "Win% incorrect"
    
    print(f"✅ 策略名稱: {name_item.text()}")
    print(f"✅ 進站次數: {stops_item.text()}")
    print(f"✅ 輪胎策略: {tire_item.text()}")
    print(f"✅ 勝率: {win_item.text()}")
    
    print("\n✅ 整合邏輯驗證通過！\n")

def main():
    print("\n" + "=" * 60)
    print("Monte Carlo 輪胎策略顯示功能驗證")
    print("=" * 60 + "\n")
    
    try:
        verify_table_structure()
        verify_data_logic()
        verify_integration()
        
        print("=" * 60)
        print("✅✅✅ 所有驗證通過！功能已正確實現 ✅✅✅")
        print("=" * 60)
        print("\n更新內容:")
        print("  ✅ Monte Carlo 表格擴展至 10 列")
        print("  ✅ 新增 'Stops' 列顯示進站次數")
        print("  ✅ 新增 'Tire Strategy' 列顯示輪胎配置")
        print("  ✅ 數據正確整合並顯示")
        print("\n可以在實際 GUI 中測試了！")
        print("執行: python strategy_simulator_main.py")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 驗證失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
