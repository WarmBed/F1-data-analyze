#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整測試批次生成器的錯誤處理邏輯"""

import subprocess

def test_execute_task(function_id, year, race, session):
    """模擬 _execute_task 方法"""
    print(f"\n{'='*60}")
    print(f"測試: F{function_id} {year} {race} {session}")
    print('='*60)
    
    cmd = [
        "python",
        "f1_analysis_modular_main.py",
        "-f", str(function_id),
        "-y", str(year),
        "-r", race,
        "-s", session
    ]
    
    print(f"執行命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'  # 處理編碼錯誤
        )
        
        print(f"\n返回碼: {process.returncode}")
        
        if process.returncode == 0:
            print("✅ 結果: 成功（退出碼 0）")
            return {"status": "success", "message": "Generated successfully"}
        else:
            # 改進錯誤訊息處理：過濾掉 FastF1 警告，只顯示真正的錯誤
            stderr = process.stderr or ""
            stdout = process.stdout or ""
            
            # 優先收集真正的 [ERROR] 訊息（最高優先級）
            real_errors = []
            for line in stdout.split('\n'):
                if '[ERROR]' in line:
                    # 跳過警告相關的錯誤
                    if 'fastf1.api' in line or 'WARNING' in line.upper():
                        continue
                    real_errors.append(line.strip())
            
            print(f"\n找到的 [ERROR] 訊息數量: {len(real_errors)}")
            if real_errors:
                print(f"第一條錯誤: {real_errors[0][:100]}...")
                return {"status": "failed", "message": real_errors[0][:200]}
            
            # 過濾 stderr 中的無害警告
            filtered_stderr = []
            for line in stderr.split('\n'):
                if 'UserWarning' in line and 'fastf1.api' in line:
                    continue
                if line.strip():
                    filtered_stderr.append(line.strip())
            
            # 過濾 stdout 中的 [FAIL] 訊息（只保留真正的錯誤）
            filtered_stdout_errors = []
            for line in stdout.split('\n'):
                if '[FAIL]' in line:
                    if 'fastf1.api' in line and 'warnings.warn' in line:
                        continue
                    if 'WARNING Correcting user input' in line:
                        continue
                    if 'events WARNING' in line:
                        continue
                    if 'will be considered private in future releases' in line:
                        continue
                    filtered_stdout_errors.append(line.strip())
            
            print(f"過濾後的 stderr: {len(filtered_stderr)} 行")
            print(f"過濾後的 [FAIL]: {len(filtered_stdout_errors)} 行")
            
            # 判斷是否真的失敗
            if not filtered_stderr and not filtered_stdout_errors:
                if '[SUCCESS]' in stdout or 'JSON 檔案已儲存' in stdout:
                    print("✅ 結果: 成功（有警告但實際成功）")
                    return {"status": "success", "message": "Generated successfully (with warnings)"}
                print("❓ 結果: 未知錯誤")
                error_msg = "Unknown error (check logs)"
            elif filtered_stdout_errors:
                print(f"❌ 結果: 失敗 - {filtered_stdout_errors[0][:50]}...")
                error_msg = filtered_stdout_errors[0][:200]
            else:
                print(f"❌ 結果: 失敗 - {' | '.join(filtered_stderr[:3])[:50]}...")
                error_msg = ' | '.join(filtered_stderr[:3])[:200]
            
            return {"status": "failed", "message": error_msg}
            
    except subprocess.TimeoutExpired:
        print("⏱️ 結果: 超時")
        return {"status": "failed", "message": "Timeout (>10 min)"}
    except Exception as e:
        print(f"💥 結果: 異常 - {str(e)}")
        return {"status": "failed", "message": str(e)[:200]}

if __name__ == "__main__":
    # 測試 1: Qatar FP2 (應該失敗 - Session 不存在)
    result1 = test_execute_task(121, 2025, "Qatar", "FP2")
    print(f"\n最終返回: {result1}")
    
    # 測試 2: Qatar R (應該成功或顯示正確錯誤)
    result2 = test_execute_task(121, 2025, "Qatar", "R")
    print(f"\n最終返回: {result2}")
