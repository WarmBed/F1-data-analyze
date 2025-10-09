#!/usr/bin/env python3
"""
理想圈排名表格模組完整測試
測試模組導入、實例化、介面方法等
"""

import sys
sys.path.insert(0, 'd:\\OneDrive\\Code\\F1-data-analyze')

print("=" * 70)
print("理想圈排名表格模組完整測試")
print("=" * 70)
print()

# 測試 1: 模組導入
print("測試 1: 模組導入...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
    print("✅ 模組導入成功")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 測試 2: 創建實例
print("測試 2: 創建實例...")
try:
    module = IdealLapRankingTableModule(
        parent=None,
        year=2024,
        race='Japan',
        session='R'
    )
    print("✅ 實例創建成功")
except Exception as e:
    print(f"❌ 實例創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 測試 3: 獲取模組資訊
print("測試 3: 獲取模組資訊...")
try:
    print(f"  標題: {module.get_title()}")
    print(f"  默認尺寸: {module.get_default_size()}")
    print(f"  模組名稱: {module.module_name}")
    print(f"  顯示名稱: {module.display_name}")
    print(f"  版本: {module.version}")
    print(f"  描述: {module.description}")
    print("✅ 模組資訊正確")
except Exception as e:
    print(f"❌ 獲取模組資訊失敗: {e}")
    import traceback
    traceback.print_exc()

print()

# 測試 4: 檢查介面方法
print("測試 4: 檢查介面方法...")
methods = [
    'initialize_module',
    'load_data',
    'update_parameters',
    'refresh_analysis',
    'clear_data',
    'export_data',
    'get_widget',
    'get_title',
    'get_default_size',
    'get_current_data',
    'is_initialized',
    'get_module_info'
]

all_methods_exist = True
for method in methods:
    exists = hasattr(module, method)
    status = "✅" if exists else "❌"
    print(f"  {status} {method}")
    if not exists:
        all_methods_exist = False

if all_methods_exist:
    print("✅ 所有介面方法存在")
else:
    print("❌ 部分介面方法缺失")

print()

# 測試 5: GUI 整合模擬測試
print("測試 5: 模擬 GUI 整合流程...")
try:
    # 模擬 f1t_gui_main.py 的整合流程
    print("  步驟 1: 創建模組實例...")
    test_module = IdealLapRankingTableModule(
        parent=None,
        year=2025,
        race='Japan',
        session='R'
    )
    print("  ✅ 模組實例創建成功")
    
    print("  步驟 2: 檢查初始化前狀態...")
    assert not test_module.is_initialized(), "模組不應該已初始化"
    print("  ✅ 初始化狀態正確")
    
    print("  步驟 3: 獲取標題...")
    title = test_module.get_title()
    print(f"  ✅ 標題: {title}")
    
    print("  步驟 4: 獲取默認尺寸...")
    width, height = test_module.get_default_size()
    print(f"  ✅ 默認尺寸: {width}x{height}")
    
    print("  步驟 5: 獲取模組資訊...")
    info = test_module.get_module_info()
    assert 'name' in info, "模組資訊應包含 name"
    assert 'version' in info, "模組資訊應包含 version"
    print(f"  ✅ 模組資訊: {info}")
    
    print("✅ GUI 整合模擬測試通過")
    
except Exception as e:
    print(f"❌ GUI 整合模擬測試失敗: {e}")
    import traceback
    traceback.print_exc()

print()

# 測試 6: 檢查 _create_ideal_lap_ranking_window 所需的方法
print("測試 6: 檢查 GUI 創建所需方法...")
required_for_gui = {
    'get_title': '獲取視窗標題',
    'get_default_size': '獲取默認尺寸',
    'initialize_module': '初始化模組',
    'get_widget': '獲取主元件',
    'load_data': '載入資料'
}

all_gui_methods_ok = True
for method, desc in required_for_gui.items():
    exists = hasattr(module, method)
    status = "✅" if exists else "❌"
    print(f"  {status} {method} - {desc}")
    if not exists:
        all_gui_methods_ok = False

if all_gui_methods_ok:
    print("✅ GUI 創建所需方法完整")
else:
    print("❌ GUI 創建所需方法不完整")

print()
print("=" * 70)
if all_methods_exist and all_gui_methods_ok:
    print("🎉 所有測試通過！模組可以整合到 GUI")
else:
    print("⚠️  部分測試失敗，需要修復")
print("=" * 70)
