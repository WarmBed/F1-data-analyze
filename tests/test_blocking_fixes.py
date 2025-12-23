#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試腳本：驗證主線程阻塞問題修復
=========================================

此腳本驗證以下4個模組不再包含主線程阻塞的 subprocess 調用：
1. timediff_analysis_mdi.py
2. throttle_analysis_mdi.py
3. distancediff_analysis_mdi.py
4. throttle_analysis_mdi_new.py (已廢棄)

檢查項目：
- [OK] 禁止在主線程調用 subprocess.Popen().communicate()
- [OK] 禁止在主線程調用 time.sleep()
- [OK] 阻塞性方法已被禁用或改為提示訊息
"""

import sys
import os
import ast
import inspect

def check_module_for_blocking_calls(module_path: str) -> dict:
    """
    檢查模組中是否存在阻塞性調用
    
    Returns:
        dict: {
            'has_subprocess_communicate': bool,
            'has_time_sleep': bool,
            'suspicious_methods': List[str]
        }
    """
    result = {
        'has_subprocess_communicate': False,
        'has_time_sleep': False,
        'suspicious_methods': []
    }
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查 subprocess.communicate
        if 'subprocess' in content and '.communicate(' in content:
            # 檢查是否在注釋或文檔字串中
            for line_num, line in enumerate(content.split('\n'), 1):
                if '.communicate(' in line and not line.strip().startswith('#'):
                    # 檢查這一行是否在多行字串中
                    if '"""' not in line and "'''" not in line:
                        result['has_subprocess_communicate'] = True
                        result['suspicious_methods'].append(f"Line {line_num}: {line.strip()[:60]}")
                        
        # 檢查 time.sleep（排除測試代碼和範例）
        if 'time.sleep' in content:
            for line_num, line in enumerate(content.split('\n'), 1):
                if 'time.sleep' in line and not line.strip().startswith('#'):
                    # 排除在 if __name__ == "__main__" 區塊中的測試代碼
                    context_start = max(0, line_num - 5)
                    context_lines = content.split('\n')[context_start:line_num]
                    is_in_test = any('if __name__' in ctx_line for ctx_line in context_lines)
                    
                    if not is_in_test and '"""' not in line and "'''" not in line:
                        result['has_time_sleep'] = True
                        result['suspicious_methods'].append(f"Line {line_num}: {line.strip()[:60]}")
                        
    except Exception as e:
        print(f"[ERROR] Failed to check {module_path}: {e}")
        
    return result

def main():
    print("="*70)
    print("F1T GUI 主線程阻塞修復驗證")
    print("="*70)
    print()
    
    modules_to_check = [
        "modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py",
        "modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi.py",
        "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py",
    ]
    
    all_passed = True
    
    for module_path in modules_to_check:
        full_path = os.path.join(os.getcwd(), module_path)
        module_name = os.path.basename(module_path)
        
        print(f"[CHECK] {module_name}")
        print(f"   Path: {module_path}")
        
        if not os.path.exists(full_path):
            print(f"   [WARNING] File not found")
            all_passed = False
            continue
            
        result = check_module_for_blocking_calls(full_path)
        
        # 檢查是否存在阻塞性調用
        has_issues = result['has_subprocess_communicate'] or result['has_time_sleep']
        
        if not has_issues:
            print(f"   [PASS] No blocking calls found")
        else:
            print(f"   [FAIL] Issues detected:")
            if result['has_subprocess_communicate']:
                print(f"      - Found subprocess.communicate() call")
            if result['has_time_sleep']:
                print(f"      - Found time.sleep() call")
            
            if result['suspicious_methods']:
                print(f"      Suspicious locations:")
                for method in result['suspicious_methods'][:3]:  # 只顯示前3個
                    print(f"        - {method}")
            
            all_passed = False
            
        print()
    
    # 測試模組導入
    print("="*70)
    print("模組導入測試")
    print("="*70)
    print()
    
    test_imports = [
        ("timediff_analysis_mdi", "modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi", "timediffDataManager"),
        ("throttle_analysis_mdi", "modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi", "ThrottleAnalysisModule"),
        ("distancediff_analysis_mdi", "modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi", "distancediffDataManager"),
    ]
    
    for module_name, module_path, class_name in test_imports:
        try:
            exec(f"from {module_path} import {class_name}")
            print(f"   [PASS] {module_name}: Import successful")
        except Exception as e:
            print(f"   [FAIL] {module_name}: Import failed - {e}")
            all_passed = False
    
    print()
    print("="*70)
    if all_passed:
        print("[SUCCESS] All tests passed!")
        print("="*70)
        print()
        print("Fix Summary:")
        print("  - timediff_analysis_mdi.py: CLI blocking calls disabled")
        print("  - throttle_analysis_mdi.py: CLI blocking calls disabled")
        print("  - distancediff_analysis_mdi.py: CLI blocking calls disabled")
        print()
        print("Users now need to:")
        print("  1. Pre-fetch data via Telemetry Analysis module, or")
        print("  2. Use REST API to fetch data, or")
        print("  3. Manually run CLI commands to generate JSON files")
        print()
        return 0
    else:
        print("[FAIL] Some tests failed!")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
