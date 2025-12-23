#!/usr/bin/env python3
"""
測試 Ideal Lap Ranking Table UI 清理
驗證以下變更：
1. ✅ 移除 Export CSV 按鈕
2. ✅ 移除底部工具列（包含 "Loaded X drivers" 狀態）
3. ✅ 移除 Action 欄位和 Details 按鈕
4. ✅ 移除 detail_requested 信號
5. ✅ 更新欄位數量從 8 欄變為 7 欄

作者: F1T Team
日期: 2025-10-09
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_widget_structure():
    """測試 Widget 檔案結構"""
    print("=" * 60)
    print("測試 1: Widget 檔案結構")
    print("=" * 60)
    
    widget_file = project_root / "modules" / "gui" / "ideal_lap_analysis" / "ideal_lap_ranking_table" / "ideal_lap_ranking_table_widget.py"
    
    with open(widget_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查不應該存在的元素
    issues = []
    
    if 'QPushButton' in content.split('\n')[15]:  # 檢查導入行
        issues.append("❌ 仍然導入 QPushButton（已不需要）")
    else:
        print("✅ 已移除 QPushButton 導入")
    
    if 'detail_requested = pyqtSignal' in content:
        issues.append("❌ 仍然定義 detail_requested 信號")
    else:
        print("✅ 已移除 detail_requested 信號定義")
    
    if '_create_toolbar' in content:
        issues.append("❌ 仍然有 _create_toolbar 方法")
    else:
        print("✅ 已移除 _create_toolbar 方法")
    
    if 'detail_btn' in content:
        issues.append("❌ 仍然有 Details 按鈕建立程式碼")
    else:
        print("✅ 已移除 Details 按鈕建立程式碼")
    
    if "tr('table_header_action'" in content:
        issues.append("❌ 仍然有 Action 欄位標題")
    else:
        print("✅ 已移除 Action 欄位標題")
    
    if 'setColumnWidth(7' in content:
        issues.append("❌ 仍然有第 7 欄寬度設定")
    else:
        print("✅ 已移除第 7 欄寬度設定")
    
    # 檢查欄位數量
    if 'setColumnCount(len(columns))' in content:
        print("✅ 欄位數量動態設定（使用 len(columns)）")
    elif 'setColumnCount(7)' in content:
        print("✅ 欄位數量正確設為 7 欄")
    else:
        issues.append("❌ 欄位數量設定不正確")
    
    if issues:
        print("\n發現問題:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Widget 檔案結構檢查通過")
        return True

def test_mdi_structure():
    """測試 MDI 檔案結構"""
    print("\n" + "=" * 60)
    print("測試 2: MDI 檔案結構")
    print("=" * 60)
    
    mdi_file = project_root / "modules" / "gui" / "ideal_lap_analysis" / "ideal_lap_ranking_table" / "ideal_lap_ranking_table_mdi.py"
    
    with open(mdi_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    if 'detail_requested.connect' in content:
        issues.append("❌ 仍然連接 detail_requested 信號")
    else:
        print("✅ 已移除 detail_requested 信號連接")
    
    if 'def _on_detail_requested' in content:
        issues.append("❌ 仍然有 _on_detail_requested 方法")
    else:
        print("✅ 已移除 _on_detail_requested 方法")
    
    if issues:
        print("\n發現問題:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ MDI 檔案結構檢查通過")
        return True

def test_column_structure():
    """測試欄位結構一致性"""
    print("\n" + "=" * 60)
    print("測試 3: 欄位結構一致性")
    print("=" * 60)
    
    widget_file = project_root / "modules" / "gui" / "ideal_lap_analysis" / "ideal_lap_ranking_table" / "ideal_lap_ranking_table_widget.py"
    
    with open(widget_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到 _create_table 方法
    column_headers = []
    column_widths = []
    
    for i, line in enumerate(lines):
        if "tr('table_header_" in line:
            column_headers.append(line.strip())
        if "setColumnWidth(" in line:
            column_widths.append(line.strip())
    
    print(f"找到 {len(column_headers)} 個欄位標題")
    print(f"找到 {len(column_widths)} 個欄位寬度設定")
    
    if len(column_headers) == 7 and len(column_widths) == 7:
        print("✅ 欄位數量一致（7 欄）")
        print("\n欄位標題:")
        for i, header in enumerate(column_headers):
            print(f"  {i}: {header}")
        print("\n欄位寬度:")
        for width in column_widths:
            print(f"  {width}")
        return True
    else:
        print(f"❌ 欄位數量不一致（標題: {len(column_headers)}, 寬度: {len(column_widths)}）")
        return False

def main():
    """主測試函數"""
    print("🧪 開始測試 Ideal Lap Ranking Table UI 清理")
    print()
    
    results = []
    
    # 執行測試
    results.append(("Widget 結構", test_widget_structure()))
    results.append(("MDI 結構", test_mdi_structure()))
    results.append(("欄位一致性", test_column_structure()))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有測試通過！UI 清理完成。")
        print("\n變更摘要:")
        print("  • 移除 Export CSV 按鈕（底部工具列）")
        print("  • 移除 'Loaded X drivers' 狀態顯示")
        print("  • 移除 Action 欄位和 Details 按鈕")
        print("  • 移除 detail_requested 信號")
        print("  • 更新欄位數量：8 欄 → 7 欄")
        print("\n下一步:")
        print("  1. 執行 GUI 確認視覺效果")
        print("  2. 測試表格載入和顯示功能")
        print("  3. 更新相關文檔（如有需要）")
        return 0
    else:
        print("\n❌ 部分測試失敗，請檢查上述問題")
        return 1

if __name__ == "__main__":
    sys.exit(main())
