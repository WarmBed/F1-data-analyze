"""
測試 Driver Strategy 的多配方預測線功能

測試要點:
1. 三條配方線 (S/M/H) 是否正確計算
2. 圖例是否正確顯示
3. 線條顏色與樣式是否符合預期
4. 與實際圈速的對比是否合理

運行方式:
python test_multi_compound_strategy.py
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.live_timing.live_timing_modules.driver_strategy import DriverStrategyWidget

def test_multi_compound_prediction():
    """測試多配方預測功能"""
    print("=" * 80)
    print("測試 Driver Strategy 多配方預測線")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    window = QMainWindow()
    window.setWindowTitle("Driver Strategy - Multi-Compound Test")
    window.resize(1200, 800)
    
    # 創建 Driver Strategy Widget
    strategy_widget = DriverStrategyWidget()
    
    # 設置基本參數
    strategy_widget.set_total_laps(53)  # 日本站總圈數
    strategy_widget.set_driver_info("VER", "VERSTAPPEN", "3671C6")  # Red Bull 藍色
    strategy_widget.set_circuit("Japan")
    strategy_widget.set_compound("MEDIUM")
    
    # 模擬實際圈速數據（前 10 圈）
    actual_laps = {
        1: 92.5,
        2: 91.8,
        3: 91.5,
        4: 91.7,
        5: 91.9,
        6: 92.1,
        7: 92.3,
        8: 92.5,
        9: 92.7,
        10: 92.9,
    }
    
    lap_compounds = {i: "MEDIUM" for i in range(1, 11)}
    
    # 載入歷史數據
    strategy_widget.load_driver_history(
        actual_lap_times=actual_laps,
        lap_compounds=lap_compounds,
        pit_laps=[],
        pit_out_laps=set(),
        sc_laps=set(),
        sc_restart_laps=set(),
        current_compound="MEDIUM",
        current_lap=10
    )
    
    # 設置為中心 widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.addWidget(strategy_widget)
    window.setCentralWidget(central_widget)
    
    # 顯示視窗
    window.show()
    
    # 打印測試結果
    print("\n✅ 測試配置:")
    print(f"   - 總圈數: {strategy_widget._total_laps}")
    print(f"   - 當前圈數: {strategy_widget._current_lap}")
    print(f"   - 當前配方: {strategy_widget._current_compound}")
    print(f"   - 實際圈速記錄: {len(actual_laps)} 圈")
    
    print("\n✅ 多配方預測狀態:")
    print(f"   - 顯示多配方線: {strategy_widget._show_multi_compound}")
    print(f"   - 預估進站圈數: {strategy_widget._current_predicted_pit}")
    print(f"   - SOFT 預測數據點: {len(strategy_widget._multi_compound_predictions['SOFT'])}")
    print(f"   - MEDIUM 預測數據點: {len(strategy_widget._multi_compound_predictions['MEDIUM'])}")
    print(f"   - HARD 預測數據點: {len(strategy_widget._multi_compound_predictions['HARD'])}")
    
    # 檢查預測數據
    if strategy_widget._multi_compound_predictions['SOFT']:
        # 檢查 PIT Est 之前（應該沒有數據）
        pit_est = strategy_widget._current_predicted_pit
        before_pit = pit_est - 5
        
        soft_before = strategy_widget._multi_compound_predictions['SOFT'].get(before_pit, None)
        print(f"\n✅ 第 {before_pit} 圈 (PIT Est 前 5 圈):")
        if soft_before is None:
            print(f"   - 多配方線: 無數據 ✓ (正確！PIT Est 之前不應顯示)")
        else:
            print(f"   - SOFT: {soft_before:.3f}s ✗ (錯誤！不應在 PIT Est 之前顯示)")
        
        # 檢查 PIT Est 當圈（應該是起點）
        soft_at_pit = strategy_widget._multi_compound_predictions['SOFT'].get(pit_est, None)
        medium_at_pit = strategy_widget._multi_compound_predictions['MEDIUM'].get(pit_est, None)
        hard_at_pit = strategy_widget._multi_compound_predictions['HARD'].get(pit_est, None)
        
        print(f"\n✅ 第 {pit_est} 圈 (PIT Est):")
        if soft_at_pit:
            print(f"   - SOFT:   {soft_at_pit:.3f}s (換胎後第 1 圈)")
            print(f"   - MEDIUM: {medium_at_pit:.3f}s (換胎後第 1 圈)")
            print(f"   - HARD:   {hard_at_pit:.3f}s (換胎後第 1 圈)")
        # 檢查 PIT Est 之後（第 35 圈）
        after_pit_lap = 35
        soft_after = strategy_widget._multi_compound_predictions['SOFT'].get(after_pit_lap, 0)
        medium_after = strategy_widget._multi_compound_predictions['MEDIUM'].get(after_pit_lap, 0)
        hard_after = strategy_widget._multi_compound_predictions['HARD'].get(after_pit_lap, 0)
        
        tyre_age_at_35 = after_pit_lap - pit_est + 1
        print(f"\n✅ 第 {after_pit_lap} 圈 (PIT Est 後，輪胎圈數 {tyre_age_at_35}):")
        print(f"   - SOFT:   {soft_after:.3f}s")
        print(f"   - MEDIUM: {medium_after:.3f}s")
        print(f"   - HARD:   {hard_after:.3f}s")
        
        # 檢查後期圈（第 50 圈）
        late_lap = 50
        soft_late = strategy_widget._multi_compound_predictions['SOFT'].get(late_lap, 0)
        medium_late = strategy_widget._multi_compound_predictions['MEDIUM'].get(late_lap, 0)
        hard_late = strategy_widget._multi_compound_predictions['HARD'].get(late_lap, 0)
        
        tyre_age_at_50 = late_lap - pit_est + 1
        print(f"\n✅ 第 {late_lap} 圈 (輪胎圈數 {tyre_age_at_50}):")
        print(f"   - SOFT:   {soft_late:.3f}s")
        print(f"   - MEDIUM: {medium_late:.3f}s")
        print(f"   - HARD:   {hard_late:.3f}s")
        
        # 驗證合理性
        print("\n✅ 配方特性驗證:")
        if soft_at_pit and soft_at_pit < medium_at_pit < hard_at_pit:
            print("   - 換胎後初期: SOFT 最快 ✓")
        elif soft_at_pit:
            print("   - 換胎後初期: 配方速度關係異常 ✗")
            
        if soft_late and hard_late and soft_late > hard_late:
            print("   - 輪胎衰退後: SOFT 已慢於 HARD ✓")
        elif soft_late and hard_late:
            print("   - 輪胎衰退後: 衰退模型異常 ✗")
    
    print("\n" + "=" * 80)
    print("測試視窗已開啟，請檢查:")
    print(f"1. 三條配方線是否從第 {strategy_widget._current_predicted_pit} 圈（PIT Est）才開始顯示")
    print("2. PIT Est 之前只有紫色預測線（當前配方）")
    print("3. PIT Est 之後三條線分別為紅/黃/白（S/M/H）")
    print("4. 三條線的斜率不同，軟胎衰退最快")
    print("=" * 80)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_multi_compound_prediction()
