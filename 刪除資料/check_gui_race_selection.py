#!/usr/bin/env python3
"""
檢查 GUI 實際的 Race 選擇狀態
在 GUI 啟動後通過命令行檢查
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 確保可以導入 GUI 主程式
sys.path.insert(0, '.')

def check_race_selection():
    """檢查當前 Race 選擇"""
    # 獲取當前運行的 QApplication 實例
    app = QApplication.instance()
    if not app:
        print("❌ 沒有運行中的 QApplication")
        return
    
    # 查找主視窗
    for widget in app.topLevelWidgets():
        if widget.objectName() == "" and hasattr(widget, 'race_combo'):
            print(f"✅ 找到主視窗: {widget.windowTitle()}")
            print(f"\n📊 Race ComboBox 狀態:")
            print(f"   總項目數: {widget.race_combo.count()}")
            print(f"   當前索引: {widget.race_combo.currentIndex()}")
            print(f"   當前顯示文字: {widget.race_combo.currentText()}")
            
            # 顯示前3項和後3項
            print(f"\n📝 前 3 項:")
            for i in range(min(3, widget.race_combo.count())):
                text = widget.race_combo.itemText(i)
                marker = " 👉 [當前]" if i == widget.race_combo.currentIndex() else ""
                print(f"   {i}: {text}{marker}")
            
            print(f"\n📝 後 3 項:")
            count = widget.race_combo.count()
            for i in range(max(0, count - 3), count):
                text = widget.race_combo.itemText(i)
                marker = " 👉 [當前]" if i == widget.race_combo.currentIndex() else ""
                print(f"   {i}: {text}{marker}")
            
            # 檢查 currentData
            current_data = widget.race_combo.currentData()
            if current_data:
                print(f"\n🎯 當前選擇的賽事數據:")
                print(f"   Race Key: {current_data.race_key if hasattr(current_data, 'race_key') else 'N/A'}")
                print(f"   Display Label: {current_data.display_label if hasattr(current_data, 'display_label') else 'N/A'}")
                print(f"   Round: {current_data.round if hasattr(current_data, 'round') else 'N/A'}")
            
            return

    print("❌ 未找到主視窗")

if __name__ == "__main__":
    print("=" * 60)
    print("F1T GUI Race 選擇檢查器")
    print("=" * 60)
    print("\n請確保 GUI 已經在運行...")
    print("此腳本需要手動在 GUI 的 Python 控制台中執行\n")
    print("使用方法：")
    print("1. 啟動 GUI")
    print("2. 在 GUI 中按 F12 打開 Python 控制台（如果有）")
    print("3. 或者從終端執行此腳本並連接到 GUI 進程")
    print("=" * 60)
    
    check_race_selection()
