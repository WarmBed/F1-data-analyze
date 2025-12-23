"""
GUI Log 收集指南

請在 GUI 運行的終端中執行以下操作，然後將輸出貼給我：

步驟 1: 載入 Workspace
===================
1. 在 GUI 中點擊 File > Load Workspace
2. 選擇包含 Rain Analysis 的 Workspace (例如: "2025_United States_R (2)")
3. 點擊 Load

步驟 2: 收集 Log
===================
在終端中查找以下關鍵訊息：

【必須檢查的 Log 片段】

1. Workspace 載入開始:
   [WORKSPACE] 🔄 開始反序列化 Workspace...

2. MDI 視窗重建:
   [WORKSPACE] ========== 開始重建 MDI 視窗（與手動開啟一致） ==========
   [WORKSPACE] 📋 視窗類型: rain_weather  ← 確認這個值

3. 模組創建:
   [WORKSPACE] 🔧 調用主視窗的 _create_analysis_module() 方法...
   [DEBUG]    [MODULE_FACTORY] 使用提供的模組類型提示: rain_weather
   [DEBUG]    [MODULE_FACTORY] 開始創建降雨分析模組...

4. 成功或失敗訊息:
   [WORKSPACE] ✅ 模組創建成功: RainAnalysisModuleAdapter
   或
   [WORKSPACE] ❌ 無法創建模組: type=rain_weather

步驟 3: 如果看到錯誤
===================
如果看到任何 [ERROR] 或 ❌ 訊息，請完整複製該段落。

步驟 4: 檢查關鍵點
===================
請確認以下訊息是否出現：

□ [WORKSPACE] 📦 PopoutSubWindow 已創建
□ [WORKSPACE] 🎨 Widget 已設置
□ [WORKSPACE] ✅ 已添加到 MDI 區域
□ [WORKSPACE] 👁️ 視窗已顯示

如果缺少任何一項，視窗就不會顯示！

步驟 5: 貼上完整 Log
===================
請將從 "開始反序列化 Workspace" 到 "視窗重建完成" 的所有訊息複製貼上。

【快速調試命令】
如果終端輸出太多，可以使用以下 PowerShell 命令過濾：

# 方法 1: 即時查看 WORKSPACE 相關訊息
Get-Content -Path "latest_log.txt" -Tail 100 | Select-String "WORKSPACE"

# 方法 2: 查看最近的錯誤
Get-Content -Path "latest_log.txt" -Tail 100 | Select-String "ERROR|❌|Exception"

# 方法 3: 完整查看最近 50 行
Get-Content -Path "latest_log.txt" -Tail 50

【預期成功的完整流程】
如果一切正常，你應該看到類似這樣的輸出：

[WORKSPACE] 🔄 開始反序列化 Workspace...
[WORKSPACE] 📊 需要重建 1 個分頁
[WORKSPACE] 🔨 重建分頁: 'Tab 1' (1 個視窗)
[WORKSPACE] ========== 開始重建 MDI 視窗（與手動開啟一致） ==========
[WORKSPACE] 📋 視窗類型: rain_weather
[WORKSPACE] 🔧 調用主視窗的 _create_analysis_module() 方法...
[DEBUG]    [MODULE_FACTORY] 使用提供的模組類型提示: rain_weather
[DEBUG]    [MODULE_FACTORY] 開始尋找匹配的模組類型，功能名稱: 'rain_weather'
[DEBUG]    [MODULE_FACTORY] ✅ 找到匹配! 關鍵字: 'rain_weather' -> 模組類型: 'rain_analysis'
[DEBUG]    [MODULE_FACTORY] 最終確定的模組類型: rain_analysis
[DEBUG]    [MODULE_FACTORY] 開始創建降雨分析模組...
[OK] [MODULE_FACTORY] 降雨分析適配器導入成功
[INIT] [MODULE_FACTORY] 降雨分析模組參數: 2025 United States R
[OK] 降雨分析模組初始化成功
[WORKSPACE] ✅ 模組創建成功: RainAnalysisModuleAdapter
[WORKSPACE] 📊 當前參數: 2025 United States R
[WORKSPACE] 🏷️ 動態生成標題: 'Rain Analysis - 2025 United States R'
[WORKSPACE] 📦 PopoutSubWindow 已創建
[WORKSPACE] 🎨 Widget 已設置
[WORKSPACE] 📏 尺寸已設置: 1200x800
[WORKSPACE] ✅ 已添加到 MDI 區域
[WORKSPACE] 🔗 已連接 window_closed 信號
[WORKSPACE] 📋 已添加到 active_subwindows 追蹤列表
[WORKSPACE] 👁️ 視窗已顯示
[WORKSPACE] 📍 位置已自動計算
[WORKSPACE] ========== MDI 視窗重建完成 ==========

如果你的 log 與上面不同，請告訴我：
1. 在哪一步停止了？
2. 看到什麼錯誤訊息？
3. 是否有 [DEBUG] [MODULE_FACTORY] 相關訊息？
"""

print(__doc__)
