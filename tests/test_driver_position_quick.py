#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試車手比賽排名模組是否正確註冊
Quick test for Driver Position Analysis module registration
"""

import sys
import os

# 設置 UTF-8 輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_module_registration():
    """測試模組是否正確註冊到 GUI 主文件"""
    print("\n" + "="*80)
    print("快速測試：車手比賽排名模組註冊狀態")
    print("="*80 + "\n")
    
    # 測試 1: 模組導入
    print("測試 1: 模組導入")
    try:
        from modules.gui.driver_position_analysis.driver_position_analysis_mdi import (
            DriverPositionAnalysisMDI
        )
        print("[OK] DriverPositionAnalysisMDI 導入成功")
    except Exception as e:
        print(f"[FAIL] 導入失敗: {e}")
        return False
    
    # 測試 2: 檢查 GUI 主文件的模組工廠導入
    print("\n測試 2: 模組工廠導入")
    try:
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'import modules.gui.driver_position_analysis.driver_position_analysis_mdi' in content:
            print("[OK] 模組已添加到 _create_analysis_module 頂部導入")
        else:
            print("[FAIL] 模組未添加到頂部導入")
            return False
    except Exception as e:
        print(f"[FAIL] 檢查失敗: {e}")
        return False
    
    # 測試 3: 檢查 module_alias_groups
    print("\n測試 3: 模組別名字典")
    if '"driver_position_analysis": [' in content:
        print("[OK] driver_position_analysis 已添加到 module_alias_groups")
    else:
        print("[FAIL] module_alias_groups 未找到")
        return False
    
    # 測試 4: 檢查 elif 處理邏輯
    print("\n測試 4: 模組處理邏輯")
    if 'elif module_type == "driver_position_analysis":' in content:
        print("[OK] elif 處理分支已添加")
    else:
        print("[FAIL] elif 處理分支未找到")
        return False
    
    # 測試 5: 檢查選單項目
    print("\n測試 5: 選單項目")
    if 'tr("driver_position_analysis", "Driver Race Position")' in content:
        print("[OK] 選單項目已添加")
    else:
        print("[FAIL] 選單項目未找到")
        return False
    
    # 測試 6: 檢查 Workspace 支援
    print("\n測試 6: Workspace 支援")
    workspace_count = content.count("'driver_position'")
    if workspace_count >= 3:
        print(f"[OK] Workspace 支援已註冊 ({workspace_count} 個註冊點)")
    else:
        print(f"[WARN] Workspace 支援不完整 ({workspace_count}/3)")
    
    # 測試 7: 檢查語言翻譯
    print("\n測試 7: 語言翻譯")
    try:
        from core.gui_i18n import tr
        translation = tr("driver_position_analysis", "Driver Race Position")
        print(f"[OK] 翻譯功能正常: '{translation}'")
    except Exception as e:
        print(f"[WARN] 翻譯檢查失敗: {e}")
    
    print("\n" + "="*80)
    print("[SUCCESS] 所有基礎註冊檢查通過！")
    print("="*80)
    print("\n後續步驟:")
    print("1. 啟動 GUI: python f1t_gui_main.py")
    print("2. 檢查左側功能樹 -> Race Overview Analysis")
    print("3. 點擊 'Driver Race Position' / '車手比賽排名'")
    print("4. 驗證視窗是否正常創建")
    
    return True

if __name__ == "__main__":
    try:
        success = test_module_registration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
