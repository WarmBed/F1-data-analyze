#!/usr/bin/env python3
"""
測試腳本：Accident Analysis 和 Pitstop Analysis 賽段類型檢查
驗證兩個模組正確限制 Session 類型
"""

import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopDataManager

def test_accident_session_check():
    """測試 Accident Analysis 賽段類型檢查"""
    
    print("=" * 80)
    print("測試 1: Accident Analysis 賽段類型檢查")
    print("=" * 80)
    
    # 創建 AccidentDataManager
    data_manager = AccidentDataManager()
    
    # 追蹤錯誤訊息
    error_messages = []
    
    def on_error(msg):
        error_messages.append(msg)
        print(f"✅ 收到錯誤訊息: {msg}")
    
    data_manager.error_occurred.connect(on_error)
    
    # 測試案例
    test_cases = [
        ("2025", "Japan", "R", True, "正賽 (R) 應該允許載入"),
        ("2025", "Japan", "Q", True, "排位賽 (Q) 應該允許載入"),
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
        
        # 測試事故統計數據載入
        result = data_manager.loadAccidentStatistics(year, race, session)
        
        # 檢查結果
        if should_allow:
            # R 和 Q 應該允許（可能因為 API 不可用而失敗，但不應該因為 session 檢查失敗）
            if not result:
                has_session_error = any("僅適用於正賽" in msg and "排位賽" in msg for msg in error_messages)
                if has_session_error:
                    print(f"❌ 失敗: R 和 Q 不應該被 session 檢查拒絕")
                    failed_tests += 1
                else:
                    print(f"⚠️  允許嘗試載入（可能因為其他原因失敗）")
                    passed_tests += 1
            else:
                print(f"✅ 通過: 允許載入")
                passed_tests += 1
        else:
            # 非 R/Q 應該被拒絕
            if not result:
                has_session_error = any("僅適用於正賽" in msg and "排位賽" in msg for msg in error_messages)
                if has_session_error:
                    print(f"✅ 通過: 正確拒絕練習賽載入")
                    passed_tests += 1
                else:
                    print(f"❌ 失敗: 應該顯示 session 檢查錯誤訊息")
                    print(f"    實際錯誤: {error_messages}")
                    failed_tests += 1
            else:
                print(f"❌ 失敗: 練習賽不應該允許載入")
                failed_tests += 1
        
        # 重置 loading 狀態
        data_manager._is_loading = False
    
    print("\n" + "=" * 80)
    print(f"Accident Analysis 測試摘要: ✅ {passed_tests}/{len(test_cases)} 通過")
    print("=" * 80)
    
    return passed_tests, failed_tests


def test_pitstop_session_check():
    """測試 Pitstop Analysis 賽段類型檢查"""
    
    print("\n" + "=" * 80)
    print("測試 2: Pitstop Analysis 賽段類型檢查")
    print("=" * 80)
    
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
            if not result:
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
            if not result:
                has_session_error = any("僅適用於正賽" in msg for msg in error_messages)
                if has_session_error:
                    print(f"✅ 通過: 正確拒絕非正賽載入")
                    passed_tests += 1
                else:
                    print(f"❌ 失敗: 應該顯示 session 檢查錯誤訊息")
                    print(f"    實際錯誤: {error_messages}")
                    failed_tests += 1
            else:
                print(f"❌ 失敗: 非正賽不應該允許載入")
                failed_tests += 1
        
        # 重置 loading 狀態
        data_manager._is_loading = False
        data_manager._team_is_loading = False
        data_manager._detail_is_loading = False
    
    print("\n" + "=" * 80)
    print(f"Pitstop Analysis 測試摘要: ✅ {passed_tests}/{len(test_cases)} 通過")
    print("=" * 80)
    
    return passed_tests, failed_tests


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 執行測試
    accident_passed, accident_failed = test_accident_session_check()
    pitstop_passed, pitstop_failed = test_pitstop_session_check()
    
    # 總計
    total_passed = accident_passed + pitstop_passed
    total_failed = accident_failed + pitstop_failed
    total_tests = total_passed + total_failed
    
    print("\n" + "=" * 80)
    print("📊 總測試摘要")
    print("=" * 80)
    print(f"總測試數: {total_tests}")
    print(f"✅ 通過: {total_passed}")
    print(f"❌ 失敗: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 所有測試通過！")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {total_failed} 個測試失敗")
        sys.exit(1)
