#!/usr/bin/env python3
"""
測試腳本：重現 Brake Performance 彈窗問題

模擬 GUI 打開 Brake Performance 的完整流程
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.abspath('.'))

def test_brake_performance():
    print("="*80)
    print("[TEST] 測試 Brake Performance MDI 初始化")
    print("="*80)
    
    app = QApplication(sys.argv)
    
    # 記錄所有錯誤訊息
    error_messages = []
    
    # 攔截 QMessageBox.critical
    original_critical = QMessageBox.critical
    def mock_critical(parent, title, message, *args, **kwargs):
        print("\n[ALERT] 攔截到 QMessageBox.critical:")
        print(f"   標題: {title}")
        print(f"   訊息: {message}")
        error_messages.append((title, message))
        # 不實際顯示彈窗，直接返回
        return QMessageBox.Ok
    
    QMessageBox.critical = mock_critical
    
    try:
        print("\n📦 導入 Brake Performance MDI...")
        from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
        
        print("✅ 導入成功")
        
        print("\n🔧 創建 MDI 實例...")
        mdi = AllDriversBrakePerformanceMDI()
        
        print("✅ 實例創建成功")
        
        print("\n⚙️  設置參數...")
        mdi.current_year = 2025
        mdi.current_race = "Singapore"
        mdi.current_session = "R"
        
        print("✅ 參數設置完成")
        
        print("\n🚀 執行 initialize_module...")
        success = mdi.initialize_module()
        
        print(f"{'✅' if success else '❌'} initialize_module 返回: {success}")
        
        # 等待異步操作
        print("\n⏳ 等待 2 秒讓異步操作完成...")
        QTimer.singleShot(2000, app.quit)
        app.exec_()
        
        # 檢查是否有錯誤
        print(f"\n{'='*80}")
        print(f"📊 測試結果")
        print(f"{'='*80}")
        
        if error_messages:
            print(f"\n❌ 發現 {len(error_messages)} 個錯誤彈窗:")
            for i, (title, msg) in enumerate(error_messages, 1):
                print(f"\n  錯誤 {i}:")
                print(f"    標題: {title}")
                print(f"    訊息: {msg}")
        else:
            print("\n✅ 沒有錯誤彈窗")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 還原原始方法
        QMessageBox.critical = original_critical

def test_speed_analysis():
    print("\n" + "="*80)
    print("[TEST] 測試 Speed Analysis MDI 初始化（對照組）")
    print("="*80)
    
    app = QApplication(sys.argv)
    
    error_messages = []
    
    original_critical = QMessageBox.critical
    def mock_critical(parent, title, message, *args, **kwargs):
        print(f"\n🚨 攔截到 QMessageBox.critical:")
        print(f"   標題: {title}")
        print(f"   訊息: {message}")
        error_messages.append((title, message))
        return QMessageBox.Ok
    
    QMessageBox.critical = mock_critical
    
    try:
        print("\n📦 導入 Speed Analysis MDI...")
        from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
        
        print("✅ 導入成功")
        
        print("\n🔧 創建 MDI 實例...")
        mdi = AllDriversStraightLineSpeedMDI()
        
        print("✅ 實例創建成功")
        
        print("\n⚙️  設置參數...")
        mdi.current_year = 2025
        mdi.current_race = "Singapore"
        mdi.current_session = "R"
        
        print("✅ 參數設置完成")
        
        print("\n🚀 執行 initialize_module...")
        success = mdi.initialize_module()
        
        print(f"{'✅' if success else '❌'} initialize_module 返回: {success}")
        
        print("\n⏳ 等待 2 秒讓異步操作完成...")
        QTimer.singleShot(2000, app.quit)
        app.exec_()
        
        print(f"\n{'='*80}")
        print(f"📊 測試結果 (Speed)")
        print(f"{'='*80}")
        
        if error_messages:
            print(f"\n❌ 發現 {len(error_messages)} 個錯誤彈窗:")
            for i, (title, msg) in enumerate(error_messages, 1):
                print(f"\n  錯誤 {i}:")
                print(f"    標題: {title}")
                print(f"    訊息: {msg}")
        else:
            print("\n✅ 沒有錯誤彈窗")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        QMessageBox.critical = original_critical

if __name__ == "__main__":
    # 測試 Brake Performance
    test_brake_performance()
    
    print("\n" + "="*80)
    print("⏸️  分隔線 - 準備測試 Speed Analysis")
    print("="*80)
    
    # 測試 Speed Analysis（對照組）
    test_speed_analysis()
    
    print("\n" + "="*80)
    print("🎯 最終總結")
    print("="*80)
    print("\n如果 Brake 有彈窗而 Speed 沒有，就能定位問題所在")
