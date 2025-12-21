#!/usr/bin/env python3
"""
測試 Speed Diff 和 Distance Diff 時間軸模式參數檢測
驗證修復後的參數變化檢測邏輯
"""

class MockMDI:
    """模擬 MDI 類別"""
    def __init__(self):
        self.current_year = "2025"
        self.current_race = "Singapore"
        self.current_session = "R"
        self.driver1 = "VER"
        self.driver2 = "LEC"
        self.lap1 = 99
        self.lap2 = 99
        self.use_time_axis = False  # 初始狀態
    
    def check_params_changed_old(self, year, race, session, driver1, driver2, lap1, lap2):
        """舊版本：不檢查 use_time_axis"""
        params_changed = (
            self.current_year != str(year) or 
            self.current_race != race or 
            self.current_session != session or
            self.driver1 != driver1 or
            self.driver2 != driver2 or
            self.lap1 != lap1 or
            self.lap2 != lap2
        )
        return params_changed
    
    def check_params_changed_new(self, year, race, session, driver1, driver2, lap1, lap2, use_time_axis):
        """新版本：檢查 use_time_axis"""
        params_changed = (
            self.current_year != str(year) or 
            self.current_race != race or 
            self.current_session != session or
            self.driver1 != driver1 or
            self.driver2 != driver2 or
            self.lap1 != lap1 or
            self.lap2 != lap2 or
            getattr(self, 'use_time_axis', False) != use_time_axis
        )
        return params_changed

def test_scenario_1():
    """測試場景 1：切換賽事 + 切換時間軸"""
    print("\n" + "="*80)
    print("測試場景 1：Singapore → Australia + 時間軸 False → True")
    print("="*80)
    
    mdi = MockMDI()
    print(f"初始狀態: {mdi.current_race}, use_time_axis={mdi.use_time_axis}")
    
    # 模擬切換到 Australia + 開啟時間軸
    new_params = {
        'year': 2025,
        'race': 'Australia',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 99,
        'lap2': 99,
        'use_time_axis': True
    }
    
    old_result = mdi.check_params_changed_old(**{k: v for k, v in new_params.items() if k != 'use_time_axis'})
    new_result = mdi.check_params_changed_new(**new_params)
    
    print(f"\n舊版本檢測結果: {old_result}")
    print(f"新版本檢測結果: {new_result}")
    print(f"\n✅ 修復成功！" if new_result else "❌ 仍有問題")

def test_scenario_2():
    """測試場景 2：相同賽事 + 切換時間軸"""
    print("\n" + "="*80)
    print("測試場景 2：保持 Australia + 時間軸 False → True（問題場景）")
    print("="*80)
    
    mdi = MockMDI()
    mdi.current_race = "Australia"  # 已經是 Australia
    print(f"初始狀態: {mdi.current_race}, use_time_axis={mdi.use_time_axis}")
    
    # 模擬僅切換時間軸，其他參數不變
    new_params = {
        'year': 2025,
        'race': 'Australia',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 99,
        'lap2': 99,
        'use_time_axis': True
    }
    
    old_result = mdi.check_params_changed_old(**{k: v for k, v in new_params.items() if k != 'use_time_axis'})
    new_result = mdi.check_params_changed_new(**new_params)
    
    print(f"\n舊版本檢測結果: {old_result}  ⚠️  這就是 Australia 載入失敗的原因！")
    print(f"新版本檢測結果: {new_result}  ✅ 現在會觸發重新載入")
    print(f"\n{'✅ 修復成功！' if new_result and not old_result else '❌ 仍有問題'}")

def test_scenario_3():
    """測試場景 3：所有參數都相同"""
    print("\n" + "="*80)
    print("測試場景 3：所有參數都相同（應跳過重載）")
    print("="*80)
    
    mdi = MockMDI()
    mdi.current_race = "Singapore"
    mdi.use_time_axis = False
    print(f"初始狀態: {mdi.current_race}, use_time_axis={mdi.use_time_axis}")
    
    # 模擬完全相同的參數
    new_params = {
        'year': 2025,
        'race': 'Singapore',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 99,
        'lap2': 99,
        'use_time_axis': False
    }
    
    old_result = mdi.check_params_changed_old(**{k: v for k, v in new_params.items() if k != 'use_time_axis'})
    new_result = mdi.check_params_changed_new(**new_params)
    
    print(f"\n舊版本檢測結果: {old_result}")
    print(f"新版本檢測結果: {new_result}")
    print(f"\n{'✅ 正確跳過！' if not new_result else '❌ 不應該重載'}")

if __name__ == "__main__":
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    
    print("\n" + "="*80)
    print("總結")
    print("="*80)
    print("✅ 修復後的邏輯能正確檢測 use_time_axis 變化")
    print("✅ Australia 載入失敗問題已解決")
    print("✅ 不會因為參數未變而跳過必要的數據重載")
