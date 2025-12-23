"""診斷腳本：檢查當前開啟的 MDI 視窗"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔍 診斷：檢查當前 GUI 中開啟的 MDI 視窗")
print("=" * 80)

# 讀取最新的日誌，提取視窗列表
log_file = "latest_log.txt"

if not os.path.exists(log_file):
    print(f"❌ 找不到日誌檔案: {log_file}")
    sys.exit(1)

print(f"\n📄 讀取日誌檔案: {log_file}")

# 搜索 "圈速控制 - [X/Y] 更新視窗" 模式
import re

window_pattern = re.compile(r'圈速控制 - \[(\d+)/(\d+)\] 更新視窗: (.+?) \(類型: (.+?)\)')
module_pattern = re.compile(r'\[BATCH_DEBUG\] 模組 \d+/\d+: analysis_type=(.+)')

windows_found = []
total_windows = 0

with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        match = window_pattern.search(line)
        if match:
            index = int(match.group(1))
            total = int(match.group(2))
            title = match.group(3)
            window_type = match.group(4)
            
            windows_found.append({
                'index': index,
                'total': total,
                'title': title,
                'type': window_type
            })
            
            if total > total_windows:
                total_windows = total

print(f"\n📊 發現 {len(windows_found)} 個視窗更新記錄")
print(f"📊 總視窗數: {total_windows}")

if windows_found:
    print("\n🪟 視窗列表:")
    print("-" * 80)
    
    for win in windows_found:
        print(f"  [{win['index']}/{win['total']}] {win['title']}")
        print(f"       類型: {win['type']}")
    
    print("-" * 80)
    
    # 檢查 Speed 模組是否在列表中
    speed_modules = [w for w in windows_found if 'speed' in w['type'].lower() or 'Speed' in w['title']]
    
    if speed_modules:
        print(f"\n✅ 找到 {len(speed_modules)} 個 Speed 相關模組:")
        for win in speed_modules:
            print(f"  - {win['title']} (類型: {win['type']})")
    else:
        print("\n❌ 沒有找到 Speed 模組！")
        print("   可能原因：")
        print("   1. Speed 模組視窗沒有被創建")
        print("   2. Speed 模組創建失敗")
        print("   3. Workspace 載入時跳過了 Speed 模組")

print("\n" + "=" * 80)
print("🔍 檢查 Workspace 載入記錄")
print("=" * 80)

workspace_load_pattern = re.compile(r'載入 Workspace|Workspace.*load|deserialize|WORKSPACE.*載入')
workspace_logs = []

with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        if workspace_load_pattern.search(line):
            workspace_logs.append(line.strip())

if workspace_logs:
    print(f"\n✅ 找到 {len(workspace_logs)} 條 Workspace 載入相關日誌:")
    for log in workspace_logs[-10:]:  # 只顯示最後 10 條
        print(f"  {log}")
else:
    print("\n❌ 沒有找到 Workspace 載入日誌！")
    print("   這意味著：")
    print("   1. 用戶沒有載入 Workspace")
    print("   2. 或者 Workspace 載入過程沒有記錄日誌")
    print("   3. 當前視窗可能是手動開啟的")

print("\n" + "=" * 80)
