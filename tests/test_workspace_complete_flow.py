"""
Workspace Manager 序列化修復 - 完整測試流程
日期: 2025-10-21 20:45
狀態: 代碼已修復，需要重啟 GUI 並重新測試

原則 0: 反幻覺編碼五原則
- 禁止幻覺編碼
- 模組資料夾優先
- 通用模組優先
- 模組多國語言化
- print 輸出會被 logger 導出
"""

print("=" * 80)
print("🔍 問題診斷結果")
print("=" * 80)

print("\n❌ 當前問題:")
print("1. GUI 仍在使用舊的序列化邏輯（20:43 的日誌）")
print("2. workspace_serializer.py 已更新（20:39）")
print("3. 數據庫中的 Workspace 是用舊邏輯保存的（所有 window_type='unknown'）")

print("\n✅ 新代碼已就緒:")
print("1. _serialize_mdi_window() - 基於 analysis_type 識別")
print("2. _find_analysis_widget() - 遞歸搜索有參數的 widget")
print("3. _extract_parameters() - 從 current_year 等屬性提取")

print("\n" + "=" * 80)
print("🚀 完整測試流程")
print("=" * 80)

print("\n步驟 1: 重啟 GUI（必須！）")
print("-" * 40)
print("操作:")
print("  1. 關閉當前運行的 F1T GUI")
print("  2. 重新啟動: python f1t_gui_main.py")
print("")
print("原因:")
print("  - Python 不會自動重新載入已導入的模組")
print("  - 必須重啟才能使用新的序列化邏輯")

print("\n步驟 2: 創建測試 Workspace")
print("-" * 40)
print("操作:")
print("  1. 打開「降雨分析」（Rain Analysis）")
print("     - 參數: 2025, United States, R")
print("     - 等待數據載入完成")
print("")
print("  2. 打開「輪胎分析」（Tire Strategy）")
print("     - 參數: 2025, United States, R")
print("     - 等待數據載入完成")
print("")
print("  3. 保存 Workspace")
print("     - 名稱: Test Serialize V2 Fix")
print("     - 標籤: test, v2, fixed")
print("     - 描述: 使用新的序列化邏輯測試")

print("\n步驟 3: 檢查保存結果")
print("-" * 40)
print("新終端執行:")
print("  python check_workspace_db.py")
print("")
print("預期看到:")
print("  ✅ window_type: 'rain_weather' (不是 'unknown')")
print("  ✅ parameters: '{\"year\": \"2025\", \"race\": \"United States\", \"session\": \"R\"}'")
print("  ✅ window_type: 'tire_strategy' (不是 'unknown')")
print("  ✅ parameters: '{\"year\": \"2025\", \"race\": \"United States\", \"session\": \"R\"}'")

print("\n步驟 4: 檢查日誌")
print("-" * 40)
print("命令:")
print("  Get-Content -Path 'logs\\f1_gui_2025-10-21.log' -Tail 50 | Select-String -Pattern '直接識別|搜索模組|找到分析|提取參數成功|序列化視窗'")
print("")
print("預期看到:")
print("  [WORKSPACE] ✅ 直接識別模組類型: rain_weather")
print("  [WORKSPACE] 📊 提取參數成功: {'year': '2025', 'race': 'United States', 'session': 'R'}")
print("  [WORKSPACE] 📦 序列化視窗: rain_weather | 參數: {...}")

print("\n步驟 5: 測試 Load Workspace")
print("-" * 40)
print("操作:")
print("  1. 關閉所有 MDI 視窗（或創建新分頁）")
print("  2. 點擊「Load Workspace」")
print("  3. 選擇剛才保存的「Test Serialize V2 Fix」")
print("  4. 點擊「載入」")
print("")
print("預期結果:")
print("  ✅ 分頁正確創建")
print("  ✅ Rain Analysis 視窗顯示")
print("  ✅ Tire Strategy 視窗顯示")
print("  ✅ 參數正確（2025, United States, R）")
print("  ✅ 圖表可以正常載入數據")

print("\n步驟 6: 檢查反序列化日誌")
print("-" * 40)
print("命令:")
print("  Get-Content -Path 'logs\\f1_gui_2025-10-21.log' -Tail 100 | Select-String -Pattern '重建視窗|創建模組|deserialize'")
print("")
print("預期看到:")
print("  [WORKSPACE] 🔨 重建視窗: rain_weather")
print("  [WORKSPACE] ✅ 創建模組實例成功")
print("  [WORKSPACE] 🔨 重建視窗: tire_strategy")

print("\n" + "=" * 80)
print("🎯 檢查清單")
print("=" * 80)

checklist = [
    ("重啟 GUI", "必須關閉舊進程，重新啟動"),
    ("創建 Rain Analysis", "參數: 2025, United States, R"),
    ("創建 Tire Strategy", "參數: 2025, United States, R"),
    ("保存 Workspace", "名稱: Test Serialize V2 Fix"),
    ("檢查數據庫", "window_type 不是 'unknown'"),
    ("檢查日誌", "看到 '直接識別模組類型'"),
    ("Load Workspace", "視窗正確顯示"),
    ("驗證參數", "參數正確傳遞"),
]

for i, (task, desc) in enumerate(checklist, 1):
    print(f"  [ ] {i}. {task}")
    print(f"      {desc}")

print("\n" + "=" * 80)
print("⚠️ 重要提醒")
print("=" * 80)
print("\n1. **必須重啟 GUI**")
print("   - 舊的 GUI 進程仍在使用舊代碼")
print("   - Python 不會自動重新載入模組")
print("")
print("2. **舊的 Workspace 無法使用**")
print("   - 數據庫中 ID=7 的 Workspace 是用舊邏輯保存的")
print("   - 必須創建新的 Workspace 才能測試新邏輯")
print("")
print("3. **保存時查看日誌**")
print("   - 如果沒看到 '直接識別模組類型'，代表 GUI 未重啟")
print("   - 必須完全關閉 GUI 再重啟")

print("\n" + "=" * 80)
print("開始測試！記得先重啟 GUI！🚀")
print("=" * 80)
