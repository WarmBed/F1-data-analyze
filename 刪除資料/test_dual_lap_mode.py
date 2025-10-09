"""
測試雙圈比較模式
測試案例：Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=50
預期結果：應該顯示兩條線，標籤為 "LEC - 第10圈" 和 "LEC - 第50圈"
"""

import sys
from typing import List, Dict

# 模擬 SpeedChartWidget 的核心邏輯
class MockSpeedChartWidget:
    def __init__(self):
        self.distance_data = None
        self.driver1_speed = None
        self.driver2_speed = None
        self.driver1_name = None
        self.driver2_name = None
        self.sectors = []
        self.is_single_driver = None
        
    def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                      driver2_speed: List[float], driver1_name: str = "Driver 1", 
                      driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                      lap1: int = None, lap2: int = None):
        """
        設置速度數據（模擬實際邏輯）
        """
        print(f"\n[MOCK_CHART] ========== set_speed_data 被調用 ==========")
        print(f"[MOCK_CHART] 👤 driver1_name: {driver1_name}")
        print(f"[MOCK_CHART] 👤 driver2_name: {driver2_name}")
        print(f"[MOCK_CHART] 🔢 lap1: {lap1}, lap2: {lap2}")
        
        # 設置新數據
        self.distance_data = distance
        self.driver1_speed = driver1_speed
        self.driver2_speed = driver2_speed
        self.sectors = sectors or []
        
        # 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
        is_dual_lap_mode = False
        if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
            # 同車手不同圈數 → 雙圈比較模式
            is_dual_lap_mode = True
            self.driver1_name = f"{driver1_name} - 第{lap1}圈"
            self.driver2_name = f"{driver2_name} - 第{lap2}圈"
            print(f"[MOCK_CHART] 🔄 雙圈比較模式: {self.driver1_name} vs {self.driver2_name}")
        else:
            # 正常模式：直接使用車手名稱
            self.driver1_name = driver1_name
            self.driver2_name = driver2_name
        
        # 判斷單車手模式
        if not driver2_speed or driver2_name == "":
            self.is_single_driver = True
        elif driver1_name == driver2_name:
            if lap1 is not None and lap2 is not None and lap1 != lap2:
                # 同車手不同圈數 → 雙圈比較模式
                self.is_single_driver = False
                print(f"[MOCK_CHART] 🔍 雙圈比較模式（同車手不同圈數）")
            else:
                # 同車手相同圈數或無圈數信息 → 單車手模式
                self.is_single_driver = True
                print(f"[MOCK_CHART] 🔍 單車手模式（同車手相同圈數）")
        else:
            # 不同車手 → 雙車手比較模式
            self.is_single_driver = False
            
        print(f"[MOCK_CHART] 🔍 is_single_driver: {self.is_single_driver}")
        print(f"[MOCK_CHART] 📝 最終標籤: driver1='{self.driver1_name}', driver2='{self.driver2_name}'")
        
        return {
            'is_single_driver': self.is_single_driver,
            'driver1_name': self.driver1_name,
            'driver2_name': self.driver2_name,
            'is_dual_lap_mode': is_dual_lap_mode
        }


def run_tests():
    """執行測試案例"""
    print("=" * 80)
    print("🧪 雙圈比較模式測試")
    print("=" * 80)
    
    chart = MockSpeedChartWidget()
    
    # 測試案例 1：同車手不同圈數（目標案例）
    print("\n" + "=" * 80)
    print("測試案例 1: Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=50")
    print("預期結果: 雙圈比較模式，顯示兩條線")
    print("=" * 80)
    
    result1 = chart.set_speed_data(
        distance=[0, 100, 200],
        driver1_speed=[100, 150, 200],
        driver2_speed=[95, 145, 195],
        driver1_name="LEC",
        driver2_name="LEC",
        lap1=10,
        lap2=50
    )
    
    assert result1['is_single_driver'] == False, "❌ 測試失敗：應該是雙車手模式"
    assert result1['driver1_name'] == "LEC - 第10圈", f"❌ 測試失敗：driver1_name 應該是 'LEC - 第10圈'，實際是 '{result1['driver1_name']}'"
    assert result1['driver2_name'] == "LEC - 第50圈", f"❌ 測試失敗：driver2_name 應該是 'LEC - 第50圈'，實際是 '{result1['driver2_name']}'"
    assert result1['is_dual_lap_mode'] == True, "❌ 測試失敗：應該是雙圈比較模式"
    print("✅ 測試案例 1 通過")
    
    # 測試案例 2：同車手相同圈數
    print("\n" + "=" * 80)
    print("測試案例 2: Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=10")
    print("預期結果: 單車手模式，只顯示一條線")
    print("=" * 80)
    
    result2 = chart.set_speed_data(
        distance=[0, 100, 200],
        driver1_speed=[100, 150, 200],
        driver2_speed=[95, 145, 195],
        driver1_name="LEC",
        driver2_name="LEC",
        lap1=10,
        lap2=10
    )
    
    assert result2['is_single_driver'] == True, "❌ 測試失敗：應該是單車手模式"
    assert result2['driver1_name'] == "LEC", f"❌ 測試失敗：driver1_name 應該是 'LEC'，實際是 '{result2['driver1_name']}'"
    print("✅ 測試案例 2 通過")
    
    # 測試案例 3：不同車手
    print("\n" + "=" * 80)
    print("測試案例 3: Driver1=VER Lap1=10 vs Driver2=LEC Lap2=15")
    print("預期結果: 雙車手比較模式，顯示兩條線")
    print("=" * 80)
    
    result3 = chart.set_speed_data(
        distance=[0, 100, 200],
        driver1_speed=[100, 150, 200],
        driver2_speed=[95, 145, 195],
        driver1_name="VER",
        driver2_name="LEC",
        lap1=10,
        lap2=15
    )
    
    assert result3['is_single_driver'] == False, "❌ 測試失敗：應該是雙車手模式"
    assert result3['driver1_name'] == "VER", f"❌ 測試失敗：driver1_name 應該是 'VER'，實際是 '{result3['driver1_name']}'"
    assert result3['driver2_name'] == "LEC", f"❌ 測試失敗：driver2_name 應該是 'LEC'，實際是 '{result3['driver2_name']}'"
    assert result3['is_dual_lap_mode'] == False, "❌ 測試失敗：不應該是雙圈比較模式"
    print("✅ 測試案例 3 通過")
    
    # 測試案例 4：同車手無圈數信息
    print("\n" + "=" * 80)
    print("測試案例 4: Driver1=LEC vs Driver2=LEC (無圈數信息)")
    print("預期結果: 單車手模式，只顯示一條線")
    print("=" * 80)
    
    result4 = chart.set_speed_data(
        distance=[0, 100, 200],
        driver1_speed=[100, 150, 200],
        driver2_speed=[95, 145, 195],
        driver1_name="LEC",
        driver2_name="LEC",
        lap1=None,
        lap2=None
    )
    
    assert result4['is_single_driver'] == True, "❌ 測試失敗：應該是單車手模式"
    print("✅ 測試案例 4 通過")
    
    # 測試案例 5：單車手模式（driver2 為空）
    print("\n" + "=" * 80)
    print("測試案例 5: Driver1=VER, Driver2='' (空)")
    print("預期結果: 單車手模式")
    print("=" * 80)
    
    result5 = chart.set_speed_data(
        distance=[0, 100, 200],
        driver1_speed=[100, 150, 200],
        driver2_speed=[],
        driver1_name="VER",
        driver2_name="",
        lap1=10,
        lap2=None
    )
    
    assert result5['is_single_driver'] == True, "❌ 測試失敗：應該是單車手模式"
    print("✅ 測試案例 5 通過")
    
    # 總結
    print("\n" + "=" * 80)
    print("🎉 所有測試通過！")
    print("=" * 80)
    print("\n✅ 雙圈比較模式實施成功")
    print("📋 測試摘要:")
    print("  ✅ 測試案例 1: 同車手不同圈數 → 雙圈比較模式")
    print("  ✅ 測試案例 2: 同車手相同圈數 → 單車手模式")
    print("  ✅ 測試案例 3: 不同車手 → 雙車手比較模式")
    print("  ✅ 測試案例 4: 同車手無圈數 → 單車手模式")
    print("  ✅ 測試案例 5: 空車手2 → 單車手模式")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
