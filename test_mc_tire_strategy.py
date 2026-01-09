#!/usr/bin/env python3
"""
Test script to verify Monte Carlo tire strategy display
"""
from PyQt5.QtWidgets import QApplication
import sys

from strategy_simulator.gui.results_tabs.strategy_comparison import StrategyComparisonTab
from strategy_simulator.core.lap_simulator import StrategySimulationResult, Stint, Compound
from strategy_simulator.core.monte_carlo import MonteCarloSummary

def create_mock_results():
    """Create mock simulation results for testing"""
    results = []
    
    # Strategy A: S→M→H (2 stops)
    result_a = StrategySimulationResult(
        strategy_name="Plan A",
        stints=[
            Stint(Compound.SOFT, 15, 1),
            Stint(Compound.MEDIUM, 20, 16),
            Stint(Compound.HARD, 23, 36)
        ]
    )
    result_a.total_pit_loss = 44.0
    results.append(result_a)
    
    # Strategy B: M→M→H (2 stops)
    result_b = StrategySimulationResult(
        strategy_name="Plan B",
        stints=[
            Stint(Compound.MEDIUM, 18, 1),
            Stint(Compound.MEDIUM, 18, 19),
            Stint(Compound.HARD, 22, 37)
        ]
    )
    result_b.total_pit_loss = 44.0
    results.append(result_b)
    
    # Strategy C: M→H (1 stop)
    result_c = StrategySimulationResult(
        strategy_name="Plan C",
        stints=[
            Stint(Compound.MEDIUM, 28, 1),
            Stint(Compound.HARD, 30, 29)
        ]
    )
    result_c.total_pit_loss = 22.0
    results.append(result_c)
    
    return results

def create_mock_mc_results():
    """Create mock Monte Carlo results"""
    mc = MonteCarloSummary(iterations=1000)
    
    # Add results for each strategy
    mc.win_counts = {
        "Plan A": 450,
        "Plan B": 350,
        "Plan C": 200
    }
    mc.win_percentages = {
        "Plan A": 45.0,
        "Plan B": 35.0,
        "Plan C": 20.0
    }
    mc.mean_times = {
        "Plan A": 5420.5,
        "Plan B": 5422.8,
        "Plan C": 5425.2
    }
    mc.std_times = {
        "Plan A": 3.5,
        "Plan B": 4.2,
        "Plan C": 2.8
    }
    mc.sc_impact_analysis = {
        "Plan A": {"wins_without_sc": 200, "wins_with_sc": 250},
        "Plan B": {"wins_without_sc": 180, "wins_with_sc": 170},
        "Plan C": {"wins_without_sc": 120, "wins_with_sc": 80}
    }
    mc.sc_occurrence_rate = 40.0
    
    return mc

def main():
    app = QApplication(sys.argv)
    
    # Create tab
    tab = StrategyComparisonTab()
    
    # Set mock data
    results = create_mock_results()
    tab.update_results(results)
    
    # Set Monte Carlo results
    mc_results = create_mock_mc_results()
    tab.update_monte_carlo(mc_results)
    
    # Show window
    tab.setWindowTitle("Monte Carlo 輪胎策略測試")
    tab.resize(1200, 800)
    tab.show()
    
    print("✅ 測試視窗已開啟")
    print("檢查項目:")
    print("  - Monte Carlo 位置分析表應顯示 10 列（包含 Stops 和 Tire Strategy）")
    print("  - Tire Strategy 列應顯示輪胎配置（例如：S→M→H）")
    print("  - 所有列寬度應適當調整")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
