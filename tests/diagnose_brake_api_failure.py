#!/usr/bin/env python3
"""診斷 Brake Performance API 失敗問題"""

import re

# 讀取最新的 error log
log_file = "logs/f1_gui_error_2025-10-19.log"

print("=" * 80)
print("Brake Performance API 失敗診斷")
print("=" * 80)

try:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # 找出所有與 BRAKE_PERF 相關的行
    brake_errors = []
    for i, line in enumerate(lines):
        if "BRAKE_PERF" in line or "BRAKE_MDI" in line or "BRAKE_TABLE" in line:
            brake_errors.append((i, line.strip()))
    
    print(f"\n找到 {len(brake_errors)} 行與 Brake Performance 相關的錯誤訊息\n")
    
    # 分析錯誤模式
    step_failures = []
    api_failures = []
    cli_mentions = []
    
    for line_num, line in brake_errors:
        if "步驟" in line and "失敗" in line:
            step_failures.append((line_num, line))
        if "API" in line and ("失敗" in line or "錯誤" in line):
            api_failures.append((line_num, line))
        if "CLI" in line:
            cli_mentions.append((line_num, line))
    
    print("📊 錯誤分類：")
    print(f"   - 步驟失敗: {len(step_failures)} 次")
    print(f"   - API 失敗: {len(api_failures)} 次")
    print(f"   - CLI 提及: {len(cli_mentions)} 次")
    
    if step_failures:
        print("\n❌ 步驟失敗詳情：")
        for line_num, line in step_failures[:10]:  # 只顯示前 10 個
            print(f"   行 {line_num + 1}: {line}")
    
    if api_failures:
        print("\n🔴 API 失敗詳情：")
        for line_num, line in api_failures[:5]:
            print(f"   行 {line_num + 1}: {line}")
    
    if cli_mentions:
        print("\n⚠️  CLI 提及（應該已禁用）：")
        for line_num, line in cli_mentions[:5]:
            print(f"   行 {line_num + 1}: {line}")
    
    # 尋找完整的錯誤流程
    print("\n" + "=" * 80)
    print("完整錯誤流程（最近 50 行）：")
    print("=" * 80)
    for line_num, line in brake_errors[-50:]:
        # 嘗試解碼亂碼（如果有的話）
        try:
            # 移除時間戳記和日誌等級，只顯示訊息
            parts = line.split("|", 2)
            if len(parts) >= 3:
                message = parts[2].strip()
                print(f"[{line_num + 1:4d}] {message}")
            else:
                print(f"[{line_num + 1:4d}] {line}")
        except Exception:
            print(f"[{line_num + 1:4d}] {line}")

except FileNotFoundError:
    print(f"❌ 找不到日誌檔案: {log_file}")
except Exception as e:
    print(f"❌ 讀取日誌時發生錯誤: {e}")

print("\n" + "=" * 80)
print("建議檢查項目：")
print("=" * 80)
print("1. API 端點是否正確：http://localhost:8000/api/v2/analysis/execute")
print("2. API 服務是否運行中")
print("3. loader 中的 _fetch_via_api_and_cache 是否正確處理錯誤")
print("4. 是否有 CLI 回退邏輯（應該已禁用）")
