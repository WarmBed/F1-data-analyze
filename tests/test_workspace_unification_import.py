"""
測試 Workspace 統一載入修改後的 Import 和基本邏輯

執行命令:
    python test_workspace_unification_import.py
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """測試 Import"""
    print("=" * 80)
    print("測試 1: Import Workspace Serializer")
    print("=" * 80)
    
    try:
        from core.workspace_serializer import WorkspaceSerializer
        print("✅ WorkspaceSerializer import 成功")
        return True
    except Exception as e:
        print(f"❌ WorkspaceSerializer import 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_signature():
    """測試方法簽名"""
    print("\n" + "=" * 80)
    print("測試 2: 檢查 _rebuild_mdi_window 方法")
    print("=" * 80)
    
    try:
        from core.workspace_serializer import WorkspaceSerializer
        import inspect
        
        # 獲取方法簽名
        method = getattr(WorkspaceSerializer, '_rebuild_mdi_window')
        signature = inspect.signature(method)
        
        print(f"✅ 方法存在")
        print(f"   簽名: _rebuild_mdi_window{signature}")
        
        # 檢查參數
        params = list(signature.parameters.keys())
        print(f"   參數列表: {params}")
        
        expected_params = ['self', 'mdi_area', 'window_config']
        if params == expected_params:
            print(f"✅ 參數列表正確")
            return True
        else:
            print(f"❌ 參數列表不正確，預期: {expected_params}")
            return False
            
    except Exception as e:
        print(f"❌ 方法檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_window_methods():
    """測試主視窗方法存在性"""
    print("\n" + "=" * 80)
    print("測試 3: 檢查主視窗必要方法")
    print("=" * 80)
    
    try:
        # 這個測試只檢查 import，不實際運行 GUI
        print("⚠️  注意: 此測試只驗證 import，不啟動 GUI")
        
        # 檢查方法是否在源代碼中定義
        import ast
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 使用簡單的字串搜索（不解析 AST，避免複雜度）
        required_methods = [
            '_create_analysis_module',
            '_get_race_key_from_display',
            '_position_subwindow',
            'on_subwindow_closed'
        ]
        
        all_found = True
        for method in required_methods:
            if f"def {method}(" in source:
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法不存在: {method}")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ 主視窗方法檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_popout_subwindow():
    """測試 PopoutSubWindow Import"""
    print("\n" + "=" * 80)
    print("測試 4: PopoutSubWindow Import")
    print("=" * 80)
    
    try:
        # 檢查 PopoutSubWindow 是否在源代碼中定義
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        if "class PopoutSubWindow" in source:
            print("✅ PopoutSubWindow 類別定義存在")
            return True
        else:
            print("❌ PopoutSubWindow 類別定義不存在")
            return False
            
    except Exception as e:
        print(f"❌ PopoutSubWindow 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試流程"""
    print("\n" + "=" * 80)
    print("🧪 Workspace 統一載入修改 - Import 測試")
    print("=" * 80)
    
    results = []
    
    # 測試 1: Import
    results.append(("Import WorkspaceSerializer", test_import()))
    
    # 測試 2: 方法簽名
    results.append(("方法簽名檢查", test_method_signature()))
    
    # 測試 3: 主視窗方法
    results.append(("主視窗方法存在性", test_main_window_methods()))
    
    # 測試 4: PopoutSubWindow
    results.append(("PopoutSubWindow 存在性", test_popout_subwindow()))
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 測試總結")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    print(f"測試結果: {passed}/{total} 通過")
    print("=" * 80)
    
    if passed == total:
        print("\n✅ 所有 Import 測試通過！")
        print("✅ 可以進行下一步：啟動 GUI 並測試實際功能")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 個測試失敗")
        print("❌ 請修復失敗項目後再進行 GUI 測試")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
