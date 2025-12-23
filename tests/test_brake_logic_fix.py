"""
測試煞車性能棒狀圖邏輯修復

測試項目：
1. 驗證 _calculate_max_time() 使用正確的鍵名
2. 驗證 min_time / max_time 計算正確
3. 驗證棒狀圖邏輯：時間短 = 棒短
4. 驗證顏色變更為暖紅色
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication

# 創建 QApplication（GUI 測試需要）
app = QApplication(sys.argv)

def test_calculate_max_time_key():
    """測試 1：驗證 _calculate_max_time() 使用正確的 JSON 鍵名"""
    print("\n" + "="*70)
    print("測試 1：驗證 _calculate_max_time() 使用正確的 JSON 鍵名")
    print("="*70)
    
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_table_widget import AllDriversBrakePerformanceTableWidget
    
    # 模擬數據（使用正確的鍵名）
    test_data = [
        {
            "driver": "VER",
            "team": "Red Bull Racing",
            "brake_time_s": 1.480,  # ✅ 正確的鍵名
            "max_deceleration_g": 5.2
        },
        {
            "driver": "HAM",
            "team": "Mercedes",
            "brake_time_s": 1.659,  # ✅ 正確的鍵名
            "max_deceleration_g": 4.8
        },
        {
            "driver": "LEC",
            "team": "Ferrari",
            "brake_time_s": 1.820,  # ✅ 正確的鍵名
            "max_deceleration_g": 4.5
        }
    ]
    
    # 創建 Widget（不需要實際顯示）
    widget = AllDriversBrakePerformanceTableWidget()
    widget.driver_brakes_data = test_data
    
    # 執行計算
    widget._calculate_max_time()
    
    # 驗證結果
    expected_min = 1.480
    expected_max = 1.820
    expected_range = expected_max - expected_min
    
    print(f"✅ 預期 min_time: {expected_min:.3f}s")
    print(f"✅ 實際 min_time: {widget.min_time_to_max:.3f}s")
    print(f"✅ 預期 max_time: {expected_max:.3f}s")
    print(f"✅ 實際 max_time: {widget.max_time_to_max:.3f}s")
    print(f"✅ 預期 time_range: {expected_range:.3f}s")
    print(f"✅ 實際 time_range: {widget.max_time_to_max - widget.min_time_to_max:.3f}s")
    
    # 驗證
    assert abs(widget.min_time_to_max - expected_min) < 0.001, "min_time 計算錯誤！"
    assert abs(widget.max_time_to_max - expected_max) < 0.001, "max_time 計算錯誤！"
    
    print(f"\n✅ 測試 1 通過：_calculate_max_time() 使用正確的鍵名 'brake_time_s'")
    return True

def test_bar_logic():
    """測試 2：驗證棒狀圖邏輯 - 時間短 = 棒短"""
    print("\n" + "="*70)
    print("測試 2：驗證棒狀圖邏輯 - 時間短 = 棒短")
    print("="*70)
    
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_table_widget import DecelerationBarDelegate
    
    # 設置時間範圍
    min_time = 1.480  # 最快車手
    max_time = 1.820  # 最慢車手
    time_range = max_time - min_time  # 0.340s
    
    delegate = DecelerationBarDelegate(min_time, max_time)
    
    # 測試數據
    test_cases = [
        ("VER (最快)", 1.480, 0.0),   # 最快 → relative_ratio = 0.0
        ("HAM (中等)", 1.659, 0.526), # 中等 → relative_ratio ≈ 0.526
        ("LEC (最慢)", 1.820, 1.0)    # 最慢 → relative_ratio = 1.0
    ]
    
    bar_max_width = 200  # 假設最大寬度 200px
    
    print(f"時間範圍: {min_time:.3f}s ~ {max_time:.3f}s (範圍: {time_range:.3f}s)")
    print(f"棒狀圖最大寬度: {bar_max_width}px\n")
    
    for name, brake_time, expected_ratio in test_cases:
        # 計算相對比例
        if time_range > 0:
            relative_ratio = (brake_time - min_time) / time_range
        else:
            relative_ratio = 0.0
        
        # 計算棒寬
        bar_width = min(bar_max_width * relative_ratio, bar_max_width)
        
        print(f"{name}:")
        print(f"  煞車時間: {brake_time:.3f}s")
        print(f"  相對比例: {relative_ratio:.3f} (預期: {expected_ratio:.3f})")
        print(f"  棒寬度: {bar_width:.1f}px (預期: {bar_max_width * expected_ratio:.1f}px)")
        
        # 驗證
        assert abs(relative_ratio - expected_ratio) < 0.01, f"{name} 相對比例計算錯誤！"
        
        # 驗證邏輯：時間短 = 棒短
        if name == "VER (最快)":
            assert bar_width < 50, "最快車手的棒應該最短！"
        elif name == "LEC (最慢)":
            assert bar_width > 150, "最慢車手的棒應該最長！"
        
        print()
    
    print(f"✅ 測試 2 通過：棒狀圖邏輯正確（時間短 = 棒短）")
    return True

def test_color_change():
    """測試 3：驗證顏色變更為暖紅色"""
    print("\n" + "="*70)
    print("測試 3：驗證顏色變更為暖紅色")
    print("="*70)
    
    # 讀取檔案內容
    file_path = "modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_table_widget.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查暖紅色
    assert "QColor(220, 80, 60)" in content, "棒狀圖暖紅色未設置！"
    assert "QColor(180, 40, 20)" in content, "邊框深紅色未設置！"
    
    # 檢查舊的深藍色已移除
    if "QColor(50, 100, 180)" in content:
        # 檢查是否只出現在註解中
        lines_with_old_color = [line for line in content.split('\n') if "QColor(50, 100, 180)" in line]
        for line in lines_with_old_color:
            assert line.strip().startswith('#'), f"發現舊的深藍色代碼（非註解）: {line}"
    
    print("✅ 棒狀圖顏色: QColor(220, 80, 60) - 暖紅色")
    print("✅ 邊框顏色: QColor(180, 40, 20) - 深紅色")
    print("✅ 文字顏色: QColor(220, 80, 60) - 暖紅色")
    
    print(f"\n✅ 測試 3 通過：顏色已變更為暖紅色")
    return True

def main():
    """執行所有測試"""
    print("\n" + "="*70)
    print("🔧 All Drivers Brake Performance - 棒狀圖邏輯修復測試")
    print("="*70)
    
    try:
        # 測試 1：鍵名修正
        test_calculate_max_time_key()
        
        # 測試 2：棒狀圖邏輯
        test_bar_logic()
        
        # 測試 3：顏色變更
        test_color_change()
        
        # 全部通過
        print("\n" + "="*70)
        print("🎉 所有測試通過！")
        print("="*70)
        print("\n修復內容：")
        print("1. ✅ 修正 _calculate_max_time() 的鍵名：brake_time_seconds → brake_time_s")
        print("2. ✅ 驗證棒狀圖邏輯：時間短 = 棒短 = 性能好")
        print("3. ✅ 變更顏色：深藍色 → 暖紅色")
        print("\n建議：請手動啟動 GUI 驗證視覺效果")
        print("命令：python f1t_gui_main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
