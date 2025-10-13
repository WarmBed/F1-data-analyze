#!/usr/bin/env python3
"""
測試 GUI 整合 - 檢查 f1t_gui_main.py 中的整合代碼
"""

import sys
import re

print("=" * 70)
print("檢查 GUI 整合代碼")
print("=" * 70)
print()

# 讀取 f1t_gui_main.py
with open('d:\\OneDrive\\Code\\F1-data-analyze\\f1t_gui_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查 1: 理想圈分析菜單項是否存在
print("檢查 1: 菜單項...")
if '理想圈分析' in content or 'Ideal Lap' in content:
    print("✅ 找到理想圈分析菜單項")
else:
    print("❌ 未找到理想圈分析菜單項")

print()

# 檢查 2: 對話框方法是否存在
print("檢查 2: 對話框方法...")
if '_prompt_ideal_lap_ranking_options' in content:
    print("✅ 找到對話框方法 _prompt_ideal_lap_ranking_options")
else:
    print("❌ 未找到對話框方法")

print()

# 檢查 3: 創建視窗方法是否存在
print("檢查 3: 創建視窗方法...")
if '_create_ideal_lap_ranking_window' in content:
    print("✅ 找到創建視窗方法 _create_ideal_lap_ranking_window")
    
    # 提取方法代碼
    pattern = r'def _create_ideal_lap_ranking_window\(.*?\):(.*?)(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        method_code = match.group(0)
        
        # 檢查關鍵代碼
        checks = {
            'IdealLapRankingTableModule': '導入模組類',
            'analysis_module.initialize_module': '初始化模組',
            'PopoutSubWindow': '創建子視窗',
            'mdi_area.addSubWindow': '添加到 MDI',
            'analysis_module.load_data': '載入資料'
        }
        
        print("  關鍵代碼檢查:")
        for key, desc in checks.items():
            if key in method_code:
                print(f"    ✅ {desc} ({key})")
            else:
                print(f"    ❌ {desc} ({key})")
else:
    print("❌ 未找到創建視窗方法")

print()

# 檢查 4: MDI 查找邏輯
print("檢查 4: MDI 查找邏輯...")
if 'current_tab = self.tab_widget.currentWidget()' in content:
    print("✅ 找到 current_tab 查找")
if 'findChildren(CustomMdiArea)' in content:
    print("✅ 找到 CustomMdiArea 查找邏輯")

print()

# 檢查 5: 錯誤處理
print("檢查 5: 錯誤處理...")
ideal_lap_section = content[content.find('def _prompt_ideal_lap_ranking_options'):content.find('def _prompt_ideal_lap_ranking_options') + 5000] if 'def _prompt_ideal_lap_ranking_options' in content else ""

if 'try:' in ideal_lap_section and 'except' in ideal_lap_section:
    print("✅ 找到錯誤處理 (try-except)")
else:
    print("⚠️  缺少錯誤處理")

if 'QMessageBox' in ideal_lap_section:
    print("✅ 找到錯誤訊息顯示 (QMessageBox)")

print()
print("=" * 70)
print("GUI 整合代碼檢查完成")
print("=" * 70)
