#!/usr/bin/env python3
"""
測試腳本：Pitstop Analysis 賽段類型檢查
驗證 Pitstop Analysis 模組在非 R 賽段時正確顯示「無資料」
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopDataManager

def test_session_check():
    """測試賽段類型檢查"""
    
    print("=" * 80)
    print("測試：Pitstop Analysis 賽段類型檢查")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    # 創建 PitstopDataManager
    data_manager = PitstopDataManager()
    
    # 追蹤錯誤訊息
    error_messages = []
    
    def on_error(msg):
        error_messages.append(msg)
        print(f"✅ 收到錯誤訊息: {msg}")
    
    data_manager.error_occurred.connect(on_error)
    
    # 測試案例
    test_cases = [
        ("2025", "Japan", "R", True, "正賽 (R) 應該允許載入"),
        ("2025", "Japan", "Q", False, "排位賽 (Q) 應該拒絕載入"),
        ("2025", "Japan", "FP1", False, "練習賽 (FP1) 應該拒絕載入"),
        ("2025", "Japan", "FP2", False, "練習賽 (FP2) 應該拒絕載入"),
        ("2025", "Japan", "FP3", False, "練習賽 (FP3) 應該拒絕載入"),
        ("2025", "Japan", "Sprint", False, "衝刺賽 (Sprint) 應該拒絕載入"),
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for year, race, session, should_allow, description in test_cases:
        print(f"\n--- 測試案例: {description} ---")
        print(f"參數: year={year}, race={race}, session={session}")
        
        error_messages.clear()
        
        # 測試車手進站數據載入
        result = data_manager.load_data(year, race, session)
        
        # 檢查結果
        if should_allow:
            # 正賽應該允許（可能因為 API 不可用而失敗，但不應該因為 session 檢查失敗）
            if not result:
                # 檢查是否因為 session 類型被拒絕
                has_session_error = any("僅適用於正賽" in msg for msg in error_messages)
                if has_session_error:
                    print(f"❌ 失敗: 正賽不應該被 session 檢查拒絕")
                    failed_tests += 1
                else:
                    print(f"⚠️  允許嘗試載入（可能因為其他原因失敗）")
                    passed_tests += 1
            else:
                print(f"✅ 通過: 允許載入")
                passed_tests += 1
        else:
            # 非正賽應該被拒絕
            if not result:
                has_session_error = any("僅適用於正賽" in msg for msg in error_messages)
                if has_session_error:
                    print(f"✅ 通過: 正確拒絕非正賽載入")
                    passed_tests += 1
                else:
                    print(f"❌ 失敗: 應該顯示 session 檢查錯誤訊息")
                    failed_tests += 1
            else:
                print(f"❌ 失敗: 非正賽不應該允許載入")
                failed_tests += 1
        
        # 重置 loading 狀態
        data_manager._is_loading = False
        data_manager._team_is_loading = False
        data_manager._detail_is_loading = False
    
    # 測試摘要
    print("\n" + "=" * 80)
    print("測試摘要")
    print("=" * 80)
    print(f"總測試數: {len(test_cases)}")
    print(f"✅ 通過: {passed_tests}")
    print(f"❌ 失敗: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 所有測試通過！")
        return True
    else:
        print(f"\n⚠️  有 {failed_tests} 個測試失敗")
        return False

if __name__ == "__main__":
    success = test_session_check()
    sys.exit(0 if success else 1)
