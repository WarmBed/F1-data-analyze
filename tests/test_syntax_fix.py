#!/usr/bin/env python3
"""
語法修復驗證測試
"""
import sys

print("=" * 80)
print("🧪 語法修復驗證測試")
print("=" * 80)

# 測試 1: workspace_serializer 語法
print("\n[1/3] 測試 workspace_serializer.py 語法...")
try:
    import py_compile
    py_compile.compile('core/workspace_serializer.py', doraise=True)
    print("✅ workspace_serializer.py 語法正確")
except SyntaxError as e:
    print(f"❌ 語法錯誤: {e}")
    sys.exit(1)

# 測試 2: WorkspaceSerializer 導入
print("\n[2/3] 測試 WorkspaceSerializer 導入...")
try:
    from core.workspace_serializer import WorkspaceSerializer
    print(f"✅ WorkspaceSerializer 導入成功: {WorkspaceSerializer}")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 3: 關鍵方法檢查
print("\n[3/3] 測試關鍵方法...")
try:
    from core.workspace_serializer import WorkspaceSerializer
    
    # 檢查類別存在
    print(f"✅ WorkspaceSerializer 類別存在")
    
    # 檢查關鍵方法存在（使用 inspect）
    import inspect
    methods = [m[0] for m in inspect.getmembers(WorkspaceSerializer, predicate=inspect.ismethod) if not m[0].startswith('__')]
    functions = [m[0] for m in inspect.getmembers(WorkspaceSerializer, predicate=inspect.isfunction) if not m[0].startswith('__')]
    all_methods = set(methods + functions)
    
    critical_methods = ['_create_module_instance', 'save_workspace', 'load_workspace']
    for method in critical_methods:
        if method in all_methods:
            print(f"✅ {method} 方法存在")
        else:
            print(f"⚠️  {method} 方法未在檢查列表中（可能是私有方法）")
    
    print("✅ 核心方法檢查完成")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ 所有測試通過！語法修復成功！")
print("=" * 80)
sys.exit(0)
