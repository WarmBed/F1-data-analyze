#!/usr/bin/env python3
"""
Non-GUI test to verify Monte Carlo tire strategy logic
"""
from strategy_simulator.core.lap_simulator import StrategySimulationResult, Stint, Compound
from strategy_simulator.core.monte_carlo import MonteCarloSummary

def test_tire_notation():
    """Test tire notation generation"""
    print("=" * 60)
    print("測試輪胎策略標記生成")
    print("=" * 60)
    
    # Strategy A: S→M→H (2 stops)
    result_a = StrategySimulationResult(
        strategy_name="Plan A",
        stints=[
            Stint(Compound.SOFT, 15, 1),
            Stint(Compound.MEDIUM, 20, 16),
            Stint(Compound.HARD, 23, 36)
        ]
    )
    notation_a = result_a.get_stint_notation()
    print(f"✅ Plan A: {notation_a} ({result_a.num_stops} 停)")
    assert notation_a == "S→M→H", f"Expected 'S→M→H', got '{notation_a}'"
    assert result_a.num_stops == 2, f"Expected 2 stops, got {result_a.num_stops}"
    
    # Strategy B: M→M→H (2 stops)
    result_b = StrategySimulationResult(
        strategy_name="Plan B",
        stints=[
            Stint(Compound.MEDIUM, 18, 1),
            Stint(Compound.MEDIUM, 18, 19),
            Stint(Compound.HARD, 22, 37)
        ]
    )
    notation_b = result_b.get_stint_notation()
    print(f"✅ Plan B: {notation_b} ({result_b.num_stops} 停)")
    assert notation_b == "M→M→H", f"Expected 'M→M→H', got '{notation_b}'"
    
    # Strategy C: M→H (1 stop)
    result_c = StrategySimulationResult(
        strategy_name="Plan C",
        stints=[
            Stint(Compound.MEDIUM, 28, 1),
            Stint(Compound.HARD, 30, 29)
        ]
    )
    notation_c = result_c.get_stint_notation()
    print(f"✅ Plan C: {notation_c} ({result_c.num_stops} 停)")
    assert notation_c == "M→H", f"Expected 'M→H', got '{notation_c}'"
    assert result_c.num_stops == 1, f"Expected 1 stop, got {result_c.num_stops}"
    
    print("\n✅ 所有輪胎標記測試通過！\n")

def test_mc_summary_structure():
    """Test Monte Carlo summary data structure"""
    print("=" * 60)
    print("測試 Monte Carlo 數據結構")
    print("=" * 60)
    
    mc = MonteCarloSummary(iterations=1000)
    
    # Add results
    strategies = ["Plan A", "Plan B", "Plan C"]
    mc.win_percentages = {"Plan A": 45.0, "Plan B": 35.0, "Plan C": 20.0}
    mc.mean_times = {"Plan A": 5420.5, "Plan B": 5422.8, "Plan C": 5425.2}
    mc.std_times = {"Plan A": 3.5, "Plan B": 4.2, "Plan C": 2.8}
    mc.sc_occurrence_rate = 40.0
    
    # Test ranking
    ranking = mc.get_ranking()
    print(f"✅ 策略排名: {ranking}")
    assert ranking[0][0] == "Plan A", "Best strategy should be Plan A"
    assert ranking[0][1] == 45.0, "Plan A win% should be 45.0"
    
    print(f"✅ 總迭代次數: {mc.iterations}")
    print(f"✅ SC 發生率: {mc.sc_occurrence_rate}%")
    
    for name, win_pct in ranking:
        mean_time = mc.mean_times[name]
        std = mc.std_times[name]
        mins = int(mean_time // 60)
        secs = mean_time % 60
        print(f"   {name}: {win_pct:.1f}% 勝率, {mins}:{secs:06.3f}, σ={std:.3f}s")
    
    print("\n✅ Monte Carlo 數據結構測試通過！\n")

def test_data_integration():
    """Test integration between results and MC data"""
    print("=" * 60)
    print("測試結果與 MC 數據整合")
    print("=" * 60)
    
    # Create mock results
    results = []
    for i, (compound_seq, stops) in enumerate([
        (["S", "M", "H"], 2),
        (["M", "M", "H"], 2),
        (["M", "H"], 1)
    ]):
        name = f"Plan {chr(65+i)}"
        stints = []
        lap = 1
        for comp in compound_seq:
            compound = {"S": Compound.SOFT, "M": Compound.MEDIUM, "H": Compound.HARD}[comp]
            laps = 20
            stints.append(Stint(compound, laps, lap))
            lap += laps
        
        result = StrategySimulationResult(strategy_name=name, stints=stints)
        results.append(result)
    
    # Match with MC data
    mc_data = {
        "Plan A": {"win_pct": 45.0, "notation": None},
        "Plan B": {"win_pct": 35.0, "notation": None},
        "Plan C": {"win_pct": 20.0, "notation": None}
    }
    
    print("\n整合結果:")
    for result in results:
        name = result.strategy_name
        notation = result.get_stint_notation()
        stops = result.num_stops
        win_pct = mc_data[name]["win_pct"]
        
        print(f"✅ {name}: {stops} 停, {notation}, 勝率 {win_pct:.1f}%")
        
        # Verify data can be retrieved
        assert name in mc_data, f"Strategy {name} not in MC data"
        assert notation, f"Empty notation for {name}"
        assert stops >= 1, f"Invalid stops count for {name}"
    
    print("\n✅ 數據整合測試通過！\n")

def main():
    print("\n" + "=" * 60)
    print("Monte Carlo 輪胎策略顯示邏輯測試")
    print("=" * 60 + "\n")
    
    try:
        test_tire_notation()
        test_mc_summary_structure()
        test_data_integration()
        
        print("=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)
        print("\n功能驗證:")
        print("  ✅ 輪胎標記生成正確（例如：S→M→H）")
        print("  ✅ 進站次數計算正確")
        print("  ✅ Monte Carlo 數據結構完整")
        print("  ✅ 結果與 MC 數據可正確整合")
        print("\n準備在 GUI 中顯示!")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
