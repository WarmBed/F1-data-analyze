"""
測試 Throttle Box Plot Filter 功能
驗證 show_all_drivers() 是否正確清除 hidden_drivers
"""

import sys
from PyQt5.QtWidgets import QApplication

# 模擬 Throttle Box Plot Chart Widget 的行為
class MockThrottleChartWidget:
    def __init__(self):
        self.hidden_drivers = set()
        self.driver_throttle_durations = {
            'VER': [85.5, 86.2, 87.1],
            'HAM': [84.3, 85.1, 86.0],
            'LEC': [83.9, 84.5, 85.2]
        }
        print(f"[INIT] 初始化 Widget，車手數: {len(self.driver_throttle_durations)}")
        print(f"[INIT] hidden_drivers: {self.hidden_drivers}")
    
    def _hide_driver(self, driver: str):
        """隱藏車手"""
        if driver in self.hidden_drivers:
            print(f"[HIDE] 車手 {driver} 已經被隱藏")
            return
        
        self.hidden_drivers.add(driver)
        print(f"[HIDE] 隱藏車手: {driver}")
        print(f"[HIDE] 當前 hidden_drivers: {self.hidden_drivers}")
    
    def show_all_drivers(self):
        """恢復所有車手"""
        print(f"\n[SHOW_ALL] ========== show_all_drivers() 被調用 ==========")
        print(f"[SHOW_ALL] 調用前 hidden_drivers: {self.hidden_drivers}")
        
        if not self.hidden_drivers:
            print("[SHOW_ALL] 沒有隱藏的車手需要恢復")
            return
        
        hidden_count = len(self.hidden_drivers)
        self.hidden_drivers.clear()
        print(f"[SHOW_ALL] 已清空 hidden_drivers，恢復了 {hidden_count} 個車手")
        print(f"[SHOW_ALL] 調用後 hidden_drivers: {self.hidden_drivers}")
        print(f"[SHOW_ALL] ========================================\n")


class MockThrottleMDI:
    def __init__(self):
        self.chart_widget = MockThrottleChartWidget()
        print("[MDI] MDI 初始化完成\n")
    
    def reset_chart_view(self):
        """主 GUI "Show All Data" 按鈕調用此方法"""
        print("[MDI] ========== reset_chart_view() 被調用 ==========")
        
        # 檢查 chart_widget 是否存在
        if not hasattr(self, 'chart_widget') or not self.chart_widget:
            print("[MDI] ⚠️  chart_widget 不存在")
            return
        
        # 檢查 chart_widget 是否有 show_all_drivers 方法
        if not hasattr(self.chart_widget, 'show_all_drivers'):
            print("[MDI] ⚠️  chart_widget 沒有 show_all_drivers 方法")
            return
        
        # 調用 Widget 的 show_all_drivers() 方法
        print("[MDI] ✅ 調用 chart_widget.show_all_drivers()")
        self.chart_widget.show_all_drivers()
        print("[MDI] ==========================================\n")


def test_scenario():
    """測試完整場景"""
    print("=" * 60)
    print("測試場景：Throttle Box Plot Filter 功能")
    print("=" * 60 + "\n")
    
    # 1. 初始化 MDI
    mdi = MockThrottleMDI()
    
    # 2. 用戶右鍵隱藏 VER
    print("步驟 1: 用戶右鍵隱藏 VER")
    print("-" * 60)
    mdi.chart_widget._hide_driver('VER')
    
    # 3. 用戶右鍵隱藏 HAM
    print("\n步驟 2: 用戶右鍵隱藏 HAM")
    print("-" * 60)
    mdi.chart_widget._hide_driver('HAM')
    
    # 4. 檢查當前狀態
    print("\n步驟 3: 檢查當前狀態")
    print("-" * 60)
    print(f"當前 hidden_drivers: {mdi.chart_widget.hidden_drivers}")
    print(f"應該只顯示 LEC: {'✅' if mdi.chart_widget.hidden_drivers == {'VER', 'HAM'} else '❌'}")
    
    # 5. 用戶點擊 "Show All Data" 按鈕
    print("\n步驟 4: 用戶點擊 'Show All Data' 按鈕")
    print("-" * 60)
    mdi.reset_chart_view()
    
    # 6. 驗證結果
    print("步驟 5: 驗證結果")
    print("-" * 60)
    print(f"最終 hidden_drivers: {mdi.chart_widget.hidden_drivers}")
    
    if len(mdi.chart_widget.hidden_drivers) == 0:
        print("✅ 測試通過：所有車手都已恢復顯示")
        return True
    else:
        print(f"❌ 測試失敗：仍有 {len(mdi.chart_widget.hidden_drivers)} 個車手被隱藏")
        print(f"   隱藏的車手: {mdi.chart_widget.hidden_drivers}")
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    success = test_scenario()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有測試通過")
    else:
        print("❌ 測試失敗")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
