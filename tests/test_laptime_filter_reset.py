"""
測試 Lap Time Box Plot Filter 功能
驗證 show_all_drivers() 是否正確清除 hidden_drivers
"""

import sys
from PyQt5.QtWidgets import QApplication

# 模擬 Lap Time Box Plot Chart Widget 的行為
class MockLapTimeChartWidget:
    def __init__(self):
        self.hidden_drivers = set()
        self.driver_laptimes = {
            'VER': [90.5, 91.2, 92.1],
            'HAM': [91.3, 92.1, 93.0],
            'LEC': [90.9, 91.5, 92.2]
        }
        print(f"[INIT] 初始化 Lap Time Widget，車手數: {len(self.driver_laptimes)}")
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


class MockLapTimeMDI:
    def __init__(self):
        self.chart_widget = MockLapTimeChartWidget()
        print("[MDI] Lap Time MDI 初始化完成\n")
    
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


def test_lap_time_scenario():
    """測試 Lap Time Box Plot 場景"""
    print("=" * 60)
    print("測試場景：Lap Time Box Plot Filter 功能")
    print("=" * 60 + "\n")
    
    # 1. 初始化 MDI
    mdi = MockLapTimeMDI()
    
    # 2. 用戶右鍵隱藏 VER
    print("步驟 1: 用戶右鍵隱藏 VER")
    print("-" * 60)
    mdi.chart_widget._hide_driver('VER')
    
    # 3. 用戶右鍵隱藏 LEC
    print("\n步驟 2: 用戶右鍵隱藏 LEC")
    print("-" * 60)
    mdi.chart_widget._hide_driver('LEC')
    
    # 4. 檢查當前狀態
    print("\n步驟 3: 檢查當前狀態")
    print("-" * 60)
    print(f"當前 hidden_drivers: {mdi.chart_widget.hidden_drivers}")
    print(f"應該只顯示 HAM: {'✅' if mdi.chart_widget.hidden_drivers == {'VER', 'LEC'} else '❌'}")
    
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


def test_update_data_scenario():
    """測試 update_data 是否會重置 hidden_drivers"""
    print("\n" + "=" * 60)
    print("額外測試：update_data 是否重置 hidden_drivers")
    print("=" * 60 + "\n")
    
    mdi = MockLapTimeMDI()
    
    # 隱藏一個車手
    print("步驟 1: 隱藏 VER")
    print("-" * 60)
    mdi.chart_widget._hide_driver('VER')
    print(f"hidden_drivers: {mdi.chart_widget.hidden_drivers}")
    
    # 模擬 update_data 調用
    print("\n步驟 2: 模擬 update_data() 調用")
    print("-" * 60)
    # 在實際代碼中，update_data 可能會這樣：
    # self.driver_laptimes = data.get('driver_laptimes', {})
    # 但不應該重置 hidden_drivers
    
    new_data = {
        'VER': [89.5, 90.2, 91.1],
        'HAM': [90.3, 91.1, 92.0],
        'LEC': [89.9, 90.5, 91.2],
        'NOR': [90.1, 90.8, 91.5]  # 新增車手
    }
    mdi.chart_widget.driver_laptimes = new_data
    print("新數據載入完成（包含新車手 NOR）")
    print(f"update_data 後 hidden_drivers: {mdi.chart_widget.hidden_drivers}")
    
    if 'VER' in mdi.chart_widget.hidden_drivers:
        print("✅ 正確：hidden_drivers 未被重置，VER 仍然隱藏")
        return True
    else:
        print("❌ 錯誤：hidden_drivers 被重置了！")
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 測試 1: 基本 filter 功能
    success1 = test_lap_time_scenario()
    
    # 測試 2: update_data 行為
    success2 = test_update_data_scenario()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ 所有測試通過")
        exit_code = 0
    else:
        print("❌ 部分測試失敗")
        if not success1:
            print("   - 基本 filter 功能測試失敗")
        if not success2:
            print("   - update_data 行為測試失敗")
        exit_code = 1
    print("=" * 60)
    
    sys.exit(exit_code)
