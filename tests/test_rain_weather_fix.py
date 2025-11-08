"""
測試 rain_weather 類型的 Workspace 序列化/反序列化
"""
from PyQt5.QtWidgets import QApplication
import sys

def test_create_module_instance():
    """測試 _create_module_instance 是否支援 rain_weather"""
    from core.workspace_serializer import WorkspaceSerializer
    
    print("=" * 60)
    print("測試 rain_weather 模組創建")
    print("=" * 60)
    
    serializer = WorkspaceSerializer(main_window=None)
    
    # 測試參數
    test_params = {
        'year': '2025',
        'race': 'United States',
        'session': 'R'
    }
    
    # 測試 rain_weather 類型
    print("\n[測試 1] 創建 rain_weather 模組")
    module = serializer._create_module_instance('rain_weather', test_params)
    
    if module:
        print(f"✅ 模組創建成功: {module.__class__.__name__}")
        print(f"   模組類型: {getattr(module, 'analysis_type', 'N/A')}")
        print(f"   Year: {getattr(module, 'current_year', 'N/A')}")
        print(f"   Race: {getattr(module, 'current_race', 'N/A')}")
        print(f"   Session: {getattr(module, 'current_session', 'N/A')}")
    else:
        print(f"❌ 模組創建失敗")
    
    # 測試 rain_analysis 類型（向後兼容）
    print("\n[測試 2] 創建 rain_analysis 模組（向後兼容）")
    module2 = serializer._create_module_instance('rain_analysis', test_params)
    
    if module2:
        print(f"✅ 模組創建成功: {module2.__class__.__name__}")
        print(f"   模組類型: {getattr(module2, 'analysis_type', 'N/A')}")
    else:
        print(f"❌ 模組創建失敗")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_create_module_instance()
