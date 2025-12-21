"""
測試連動更新崩潰問題
===================

重現場景：
1. 創建多個理想圈分析模組
2. 變更 Year/Race/Session
3. 檢查是否崩潰
"""

print("=" * 60)
print("🔍 檢查日誌中的崩潰信息")
print("=" * 60)

import os
from pathlib import Path

log_file = Path("logs/f1_gui_2025-10-11.log")

if log_file.exists():
    print(f"\n📄 日誌檔案: {log_file}")
    print(f"📊 檔案大小: {log_file.stat().st_size / 1024:.2f} KB")
    
    # 讀取最後 200 行
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        last_lines = lines[-200:]
    
    # 查找錯誤相關的行
    error_patterns = [
        "ERROR",
        "Exception",
        "Traceback",
        "Failed",
        "崩潰",
        "crash",
        "CRITICAL",
        "AttributeError",
        "KeyError",
        "TypeError"
    ]
    
    error_lines = []
    for i, line in enumerate(last_lines):
        for pattern in error_patterns:
            if pattern.lower() in line.lower():
                # 取前後各 3 行的上下文
                start = max(0, i - 3)
                end = min(len(last_lines), i + 4)
                context = last_lines[start:end]
                error_lines.extend(context)
                error_lines.append("-" * 60 + "\n")
                break
    
    if error_lines:
        print("\n🚨 找到錯誤相關內容：")
        print("=" * 60)
        for line in error_lines:
            print(line.rstrip())
    else:
        print("\n✅ 最後 200 行沒有發現明顯錯誤")
        print("\n💡 可能的情況：")
        print("1. 程式在UI層崩潰（沒有記錄到日誌）")
        print("2. 崩潰發生在日誌之外的部分")
        print("3. 程式正常結束但視窗卡住")
        
        # 顯示最後 10 行
        print("\n📋 日誌最後 10 行：")
        print("=" * 60)
        for line in last_lines[-10:]:
            print(line.rstrip())
else:
    print(f"\n❌ 找不到日誌檔案: {log_file}")

print("\n" + "=" * 60)
print("💡 請提供以下資訊以協助診斷：")
print("=" * 60)
print("1. 崩潰時是否有彈出錯誤對話框？")
print("2. 程式是完全無響應還是可以點擊但無反應？")
print("3. 是否在終端看到 Python Exception？")
print("4. 能否重現崩潰？（重新啟動 GUI → 變更參數）")
print("=" * 60)
