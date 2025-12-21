"""
Acceleration Analysis 按鈕清理修復驗證腳本

檢查 Acceleration Analysis 是否遵循 Speed Analysis 的清理模式
"""

import re

def check_acceleration_cleanup():
    """檢查 Acceleration Analysis 的 cleanup() 方法"""
    
    file_path = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\lap_analysis\acceleration_analysis\acceleration_analysis_mdi.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 80)
    print("🔍 Acceleration Analysis cleanup() 方法驗證")
    print("=" * 80)
    
    # 檢查項目
    checks = {
        "1. 有 cleanup() 方法": r"def cleanup\(self\):",
        "2. 有清理順序註解": r"清理順序：analysis_manager → data_manager → linkage_manager",
        "3. 斷開循環引用 (module_ref = None)": r"self\.data_manager\.module_ref = None",
        "4. 沒有調用 cleanup_module()": r"(?!.*[^#]\s*self\.cleanup_module\(\))",
        "5. 有詳細 DEBUG 日誌": r"\[ACCELERATION_MDI\] \[DEBUG\]",
        "6. 有 main_widget = None": r"self\.main_widget = None",
        "7. 使用統一日誌前綴": r"\[ACCELERATION_MDI\]",
    }
    
    results = {}
    for check_name, pattern in checks.items():
        if check_name == "4. 沒有調用 cleanup_module()":
            # 特殊檢查：確認 cleanup() 方法中沒有未註解的 self.cleanup_module()
            cleanup_match = re.search(r"def cleanup\(self\):.*?(?=\n    def |\Z)", content, re.DOTALL)
            if cleanup_match:
                cleanup_code = cleanup_match.group(0)
                # 檢查是否有未註解的 cleanup_module() 調用
                has_call = bool(re.search(r"^\s*self\.cleanup_module\(\)", cleanup_code, re.MULTILINE))
                results[check_name] = not has_call
            else:
                results[check_name] = False
        else:
            results[check_name] = bool(re.search(pattern, content))
    
    # 輸出結果
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    # 對比 Speed Analysis
    print("\n📊 與 Speed Analysis 對比")
    print("=" * 80)
    
    speed_file = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\lap_analysis\speed_analysis\speed_analysis_mdi.py"
    
    try:
        with open(speed_file, 'r', encoding='utf-8') as f:
            speed_content = f.read()
        
        # 提取兩者的 cleanup() 方法
        accel_cleanup = re.search(r"def cleanup\(self\):.*?(?=\n    def |\Z)", content, re.DOTALL)
        speed_cleanup = re.search(r"def cleanup\(self\):.*?(?=\n    def |\Z)", speed_content, re.DOTALL)
        
        if accel_cleanup and speed_cleanup:
            accel_lines = accel_cleanup.group(0).split('\n')
            speed_lines = speed_cleanup.group(0).split('\n')
            
            print(f"Acceleration cleanup() 行數: {len(accel_lines)}")
            print(f"Speed cleanup() 行數: {len(speed_lines)}")
            
            # 檢查關鍵步驟
            key_patterns = {
                "analysis_manager.unregister_module": r"_analysis_manager\.unregister_module",
                "module_ref = None": r"module_ref = None",
                "data_manager.cleanup()": r"data_manager\.cleanup\(\)",
                "linkage_manager.unregister_module": r"linkage_manager\.unregister_module",
                "chart_widget.cleanup()": r"chart_widget\.cleanup\(\)",
                "chart_widget.deleteLater()": r"chart_widget\.deleteLater\(\)",
                "main_widget.deleteLater()": r"main_widget\.deleteLater\(\)",
                "main_widget = None": r"main_widget = None",
            }
            
            print("\n關鍵步驟對比：")
            for step_name, pattern in key_patterns.items():
                accel_has = bool(re.search(pattern, accel_cleanup.group(0)))
                speed_has = bool(re.search(pattern, speed_cleanup.group(0)))
                
                if accel_has == speed_has:
                    status = "✅ 一致"
                else:
                    status = "⚠️ 不同"
                    all_passed = False
                
                print(f"  {status} - {step_name}: Accel={accel_has}, Speed={speed_has}")
        
    except FileNotFoundError:
        print("⚠️ 無法找到 Speed Analysis 檔案進行對比")
    
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 所有檢查通過！Acceleration Analysis 已遵循 Speed Analysis 模式")
        return True
    else:
        print("\n⚠️ 部分檢查失敗，請檢查上方詳情")
        return False

if __name__ == "__main__":
    check_acceleration_cleanup()
