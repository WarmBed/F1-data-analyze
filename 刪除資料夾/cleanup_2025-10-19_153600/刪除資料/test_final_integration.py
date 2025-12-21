#!/usr/bin/env python3
"""
最終整合驗證測試
檢查所有組件是否就緒
"""

import sys
import os

print("=" * 70)
print("理想圈排名表格 - 最終整合驗證")
print("=" * 70)
print()

test_results = []

# 測試 1: 檢查所有模組檔案是否存在
print("測試 1: 檢查模組檔案...")
required_files = [
    'd:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_module.py',
    'd:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_mdi.py',
    'd:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_widget.py',
    'd:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_data_loader.py',
    'd:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_options_dialog.py',
]

all_files_exist = True
for file in required_files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    filename = os.path.basename(file)
    print(f"  {status} {filename}")
    if not exists:
        all_files_exist = False

test_results.append(("模組檔案", all_files_exist))
print()

# 測試 2: 檢查 GUI 整合方法
print("測試 2: 檢查 GUI 整合方法...")
with open('d:\\OneDrive\\Code\\F1-data-analyze\\f1t_gui_main.py', 'r', encoding='utf-8') as f:
    gui_content = f.read()

methods_to_check = {
    '_prompt_ideal_lap_options': '對話框方法',
    '_create_ideal_lap_ranking_window': '視窗創建方法',
}

gui_methods_ok = True
for method, desc in methods_to_check.items():
    exists = method in gui_content
    status = "✅" if exists else "❌"
    print(f"  {status} {desc} ({method})")
    if not exists:
        gui_methods_ok = False

test_results.append(("GUI 整合方法", gui_methods_ok))
print()

# 測試 3: 檢查關鍵邏輯
print("測試 3: 檢查 GUI 關鍵邏輯...")
key_logic = {
    'IdealLapRankingTableModule': '模組導入',
    'analysis_module.initialize_module': '模組初始化',
    'analysis_module.get_default_size': '獲取尺寸',
    'analysis_module.get_widget': '獲取元件',
    'analysis_module.load_data': '載入資料',
    'PopoutSubWindow': '子視窗包裝',
    'findChildren(CustomMdiArea)': 'MDI 查找',
}

logic_ok = True
for key, desc in key_logic.items():
    exists = key in gui_content
    status = "✅" if exists else "❌"
    print(f"  {status} {desc}")
    if not exists:
        logic_ok = False

test_results.append(("關鍵邏輯", logic_ok))
print()

# 測試 4: 檢查錯誤處理
print("測試 4: 檢查錯誤處理...")
error_handling = {
    'try:': 'Try 區塊',
    'except Exception as': '異常捕獲',
    'QMessageBox.critical': '錯誤訊息顯示',
    'import traceback': 'Traceback 導入',
    'traceback.print_exc()': '異常追蹤',
}

# 提取理想圈相關代碼段
ideal_lap_start = gui_content.find('if is_ideal_lap_analysis:')
ideal_lap_section = gui_content[ideal_lap_start:ideal_lap_start + 5000] if ideal_lap_start != -1 else ""

error_ok = True
for key, desc in error_handling.items():
    exists = key in ideal_lap_section
    status = "✅" if exists else "⚠️ "
    print(f"  {status} {desc}")
    if not exists:
        error_ok = False

test_results.append(("錯誤處理", error_ok))
print()

# 測試 5: 檢查模組介面完整性
print("測試 5: 檢查模組介面完整性...")
with open('d:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_module.py', 'r', encoding='utf-8') as f:
    module_content = f.read()

required_methods = [
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
    'get_module_info',
]

interface_ok = True
for method in required_methods:
    exists = f'def {method}(' in module_content
    status = "✅" if exists else "❌"
    print(f"  {status} {method}")
    if not exists:
        interface_ok = False

test_results.append(("模組介面", interface_ok))
print()

# 測試 6: 檢查 API-ONLY 模式合規性
print("測試 6: 檢查 API-ONLY 模式合規性...")
with open('d:\\OneDrive\\Code\\F1-data-analyze\\modules\\gui\\ideal_lap_analysis\\ideal_lap_ranking_table\\ideal_lap_ranking_table_data_loader.py', 'r', encoding='utf-8') as f:
    loader_content = f.read()

api_only_checks = {
    '_generate_data_via_cli': 'CLI 生成方法已禁用',
    '# ❌ 禁止': '禁用標記存在',
    'API-ONLY': 'API-ONLY 註解',
}

# 檢查 _generate_data_via_cli 是否返回 False
generate_method_start = loader_content.find('def _generate_data_via_cli(')
if generate_method_start != -1:
    generate_method = loader_content[generate_method_start:generate_method_start + 500]
    api_only_ok = 'return False' in generate_method
else:
    api_only_ok = False

status = "✅" if api_only_ok else "❌"
print(f"  {status} CLI 調用已禁用（固定返回 False）")

test_results.append(("API-ONLY 模式", api_only_ok))
print()

# 最終總結
print("=" * 70)
print("測試總結:")
print("=" * 70)

all_passed = True
for test_name, result in test_results:
    status = "✅ 通過" if result else "❌ 失敗"
    print(f"  {status} - {test_name}")
    if not result:
        all_passed = False

print()
print("=" * 70)
if all_passed:
    print("🎉 所有測試通過！模組已就緒，可以整合到 GUI")
    print("=" * 70)
    print()
    print("下一步:")
    print("  1. 啟動 GUI: python f1t_gui_main.py")
    print("  2. 選擇賽事參數（例如: 2025, Japan, R）")
    print("  3. 點擊「理想圈分析」菜單項")
    print("  4. 在對話框中選擇「排名表格」")
    print("  5. 確認視窗正確顯示")
else:
    print("⚠️  部分測試失敗，需要修復")
    print("=" * 70)

print()
