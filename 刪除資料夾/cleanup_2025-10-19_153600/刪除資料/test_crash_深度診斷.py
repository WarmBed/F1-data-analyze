"""
深度診斷 Lap Analysis 崩潰問題
================================

根據日誌分析：
1. 所有數據載入成功
2. 所有通知發送完成
3. 然後程式無聲崩潰（沒有 Exception 日誌）

可能的原因：
1. UI 線程死鎖
2. Qt 對象在非 UI 線程被刪除
3. 信號/槽循環引用
4. Painter 相關問題（CumulativeBarDelegate）
5. Table Widget 更新時的資源競爭

測試策略：
1. 檢查是否有在非 UI 線程更新 UI
2. 檢查 API Worker 的線程安全性
3. 檢查 Delegate 的 paint 方法是否有問題
"""

import sys
from pathlib import Path

print("=" * 80)
print("🔍 深度診斷 Lap Analysis 崩潰問題")
print("=" * 80)

# 分析日誌中的關鍵模式
log_file = Path("logs/f1_gui_2025-10-11.log")

if not log_file.exists():
    print(f"❌ 找不到日誌檔案: {log_file}")
    sys.exit(1)

print(f"\n📄 分析日誌檔案: {log_file}")

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# 找到崩潰前的最後幾行
crash_time = None
for i, line in enumerate(lines):
    if "02:11:13" in line and "[STATS] [SYNC] MDI區域 MdiArea_1 通知完成" in line:
        crash_time = i
        print(f"\n🎯 找到崩潰時間點: Line {i}")
        print(f"   內容: {line.strip()}")
        break

if crash_time:
    # 顯示崩潰前後的 context
    print("\n📋 崩潰前 10 行:")
    print("=" * 80)
    for line in lines[max(0, crash_time - 10):crash_time]:
        print(line.rstrip())
    
    print("\n🚨 崩潰點:")
    print("=" * 80)
    print(lines[crash_time].rstrip())
    
    print("\n📋 崩潰後 20 行:")
    print("=" * 80)
    for line in lines[crash_time + 1:crash_time + 21]:
        print(line.rstrip())

# 檢查是否有 Worker 線程相關的日誌
print("\n" + "=" * 80)
print("🔍 檢查 API Worker 相關日誌")
print("=" * 80)

worker_lines = []
for i, line in enumerate(lines):
    if "02:11:13" in line and any(keyword in line for keyword in [
        "API Worker",
        "API 請求",
        "Worker",
        "Thread",
        "Signal",
        "Slot"
    ]):
        worker_lines.append((i, line.strip()))

if worker_lines:
    print(f"\n找到 {len(worker_lines)} 條 Worker 相關日誌:")
    for line_num, content in worker_lines[-10:]:  # 最後 10 條
        print(f"Line {line_num}: {content}")
else:
    print("❌ 沒有找到 Worker 相關日誌")

# 檢查是否有 Delegate/Painter 相關的日誌
print("\n" + "=" * 80)
print("🔍 檢查 Delegate/Painter 相關日誌")
print("=" * 80)

painter_lines = []
for i, line in enumerate(lines):
    if "02:11:13" in line and any(keyword in line for keyword in [
        "Delegate",
        "Painter",
        "paint",
        "draw",
        "render"
    ]):
        painter_lines.append((i, line.strip()))

if painter_lines:
    print(f"\n找到 {len(painter_lines)} 條 Painter 相關日誌:")
    for line_num, content in painter_lines:
        print(f"Line {line_num}: {content}")
else:
    print("✅ 沒有找到 Painter 相關日誌（可能沒有記錄）")

# 分析可能的問題
print("\n" + "=" * 80)
print("💡 可能的崩潰原因分析")
print("=" * 80)

print("""
根據日誌分析，崩潰發生在發送完 20 個通知後。

可能原因：
1. ✅ 信號槽遞歸觸發
   - 20 個視窗同時更新
   - 每個視窗都觸發數據載入
   - 可能導致信號槽遞歸

2. ✅ UI 線程阻塞
   - 大量 API Worker 同時運行
   - Table Widget 同時更新
   - Delegate paint 方法被大量調用

3. ✅ Qt 對象在錯誤線程被刪除
   - API Worker 完成後可能在非 UI 線程刪除 Qt 對象
   - 需要確保使用 deleteLater()

4. ✅ Painter 資源競爭
   - CumulativeBarDelegate 的 paint 方法
   - 可能在多個表格同時渲染時衝突

建議修復：
1. 在 API Worker 完成時使用 QMetaObject.invokeMethod 確保在 UI 線程處理
2. 限制同時更新的視窗數量（批量處理）
3. 檢查 Delegate 的 paint 方法是否線程安全
4. 添加 try-except 捕獲異常並記錄日誌
""")

print("\n" + "=" * 80)
print("🎯 下一步行動")
print("=" * 80)
print("""
1. 在 Sector Comparison MDI 的 _on_api_success 中添加異常捕獲
2. 在 Table Widget 的 update_data 中添加異常捕獲  
3. 在 Delegate 的 paint 方法中添加異常捕獲
4. 使用 QTimer.singleShot 延遲 UI 更新，避免同時更新
5. 添加更多調試日誌以追蹤崩潰點
""")
