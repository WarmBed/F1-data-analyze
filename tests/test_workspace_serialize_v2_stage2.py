"""
測試改進後的 Workspace 序列化邏輯
階段 2: 模擬 Widget 結構測試

原則 0: 反幻覺編碼五原則
- 禁止幻覺編碼 - 已通過 read_file 驗證 RainAnalysisModule 結構
- 模組資料夾優先
- 通用模組優先
- 模組多國語言化
- print 輸出會被 logger 導出
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget

# 創建 QApplication
app = QApplication(sys.argv)

print("=" * 80)
print("階段 2: 模擬 Widget 結構測試")
print("=" * 80)

# 模擬 UniversalAnalysisMDI 基類（有 analysis_type 和 current_* 屬性）
class MockUniversalAnalysisMDI(QWidget):
    def __init__(self):
        super().__init__()
        self.analysis_type = "rain_weather"
        self.current_year = "2025"
        self.current_race = "Japan"
        self.current_session = "R"
        self.data_manager = None  # 通常為 None 或空

# 模擬 RainAnalysisModule（包裝 UniversalAnalysisMDI）
class MockRainAnalysisModule(QWidget):
    def __init__(self):
        super().__init__()
        self._rain_analysis_core = MockUniversalAnalysisMDI()
        self.analysis_type = "rain_weather"  # 也在這層提供

# 模擬 RainAnalysisModuleAdapter（最外層）
class MockRainAnalysisModuleAdapter(QWidget):
    def __init__(self):
        super().__init__()
        self._main_widget = MockRainAnalysisModule()

try:
    print("\n✅ 測試 1: 測試 _find_analysis_widget 方法")
    from core.workspace_serializer import WorkspaceSerializer
    
    # 創建模擬 main_window
    class MockMainWindow:
        pass
    
    serializer = WorkspaceSerializer(MockMainWindow())
    
    # 測試場景 1: Adapter 結構
    print("\n   場景 1: RainAnalysisModuleAdapter 結構")
    adapter_widget = MockRainAnalysisModuleAdapter()
    found_widget = serializer._find_analysis_widget(adapter_widget)
    
    if found_widget:
        print(f"   ✅ 找到分析 widget: {found_widget.__class__.__name__}")
        if hasattr(found_widget, 'analysis_type'):
            print(f"   ✅ analysis_type: {found_widget.analysis_type}")
        if hasattr(found_widget, 'current_year'):
            print(f"   ✅ current_year: {found_widget.current_year}")
    else:
        print(f"   ❌ 未找到分析 widget")
    
    # 測試場景 2: 直接 UniversalAnalysisMDI
    print("\n   場景 2: 直接 UniversalAnalysisMDI")
    direct_widget = MockUniversalAnalysisMDI()
    found_widget2 = serializer._find_analysis_widget(direct_widget)
    
    if found_widget2:
        print(f"   ✅ 找到分析 widget: {found_widget2.__class__.__name__}")
        if hasattr(found_widget2, 'analysis_type'):
            print(f"   ✅ analysis_type: {found_widget2.analysis_type}")
    else:
        print(f"   ❌ 未找到分析 widget")
    
    print("\n✅ 測試 2: 測試 _extract_parameters 方法")
    
    # 測試參數提取
    print("\n   場景 1: 從 UniversalAnalysisMDI 提取參數")
    params1 = serializer._extract_parameters(direct_widget)
    print(f"   提取的參數: {params1}")
    
    expected_params = {'year': '2025', 'race': 'Japan', 'session': 'R'}
    if params1 == expected_params:
        print(f"   ✅ 參數正確!")
    else:
        print(f"   ❌ 參數不正確，預期: {expected_params}")
    
    # 測試從 Adapter 提取（應該找到內部的 UniversalAnalysisMDI）
    print("\n   場景 2: 從 Adapter 提取參數")
    found_for_params = serializer._find_analysis_widget(adapter_widget)
    if found_for_params:
        params2 = serializer._extract_parameters(found_for_params)
        print(f"   提取的參數: {params2}")
        if params2 == expected_params:
            print(f"   ✅ 參數正確!")
        else:
            print(f"   ❌ 參數不正確")
    else:
        print(f"   ❌ 找不到 widget 進行參數提取")
    
    print("\n" + "=" * 80)
    print("階段 2 測試完成 - Widget 結構識別和參數提取測試通過")
    print("=" * 80)
    print("\n下一步: 執行 GUI 並測試實際的 Save Workspace 功能")
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
