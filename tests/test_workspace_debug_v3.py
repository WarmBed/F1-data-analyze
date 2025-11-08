"""
Workspace 序列化調試 - 詳細日誌版本
日期: 2025-10-21 20:52

已添加詳細調試訊息到序列化邏輯
"""

print("=" * 80)
print("🔍 調試版本已就緒")
print("=" * 80)

print("\n✅ 已添加的調試訊息:")
print("1. 開始序列化 MDI 視窗")
print("2. SubWindow 標題和 Widget 類名")
print("3. 檢查 analysis_type 屬性")
print("4. 搜索分析 widget 過程")
print("5. 遞歸深度和每層檢查結果")
print("6. _rain_analysis_core 和 _main_widget 檢測")
print("7. findChildren 搜索結果")

print("\n" + "=" * 80)
print("🚀 測試步驟")
print("=" * 80)

print("\n步驟 1: 重啟 GUI（必須！）")
print("  python f1t_gui_main.py")

print("\n步驟 2: 創建 Rain Analysis")
print("  參數: 2025, United States, R")

print("\n步驟 3: 保存 Workspace")
print("  名稱: Debug Test V3")

print("\n步驟 4: 查看詳細日誌")
print("  Get-Content -Path 'logs\\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String -Pattern 'WORKSPACE'")

print("\n" + "=" * 80)
print("預期看到的日誌模式:")
print("=" * 80)

print("\n如果 Widget 結構正確，應該看到:")
print("  [WORKSPACE] 🔍 開始序列化 MDI 視窗")
print("  [WORKSPACE]    SubWindow: 🌧️ Rain Analysis_2025_United States_R")
print("  [WORKSPACE]    Widget: RainAnalysisModuleAdapter")
print("  [WORKSPACE] 🔍 檢查 analysis_type 屬性...")
print("  [WORKSPACE] 🔍 搜索模組類型 (頂層: RainAnalysisModuleAdapter)")
print("  [WORKSPACE] 🔍 開始搜索分析 widget（根: RainAnalysisModuleAdapter）")
print("  [WORKSPACE]    檢查深度 0: RainAnalysisModuleAdapter")
print("  [WORKSPACE]    🔍 發現 _main_widget，深入檢查")
print("  [WORKSPACE]    檢查深度 1: RainAnalysisModule")
print("  [WORKSPACE]    🔍 發現 _rain_analysis_core，深入檢查")
print("  [WORKSPACE]    檢查深度 2: RainAnalysisUniversal")
print("  [WORKSPACE]    ✅ 找到 analysis_type: rain_weather")
print("  [WORKSPACE]    ✅ 有參數屬性，返回此 widget")
print("  [WORKSPACE] ✅ 搜索完成，找到: RainAnalysisUniversal")
print("  [WORKSPACE] ✅ 在子層找到模組類型: rain_weather")

print("\n如果出現問題，可能看到:")
print("  [WORKSPACE]    Widget: QWidget  ← 錯誤的 widget 類型")
print("  [WORKSPACE]    ❌ 深度 X 未找到符合條件的 widget")
print("  [WORKSPACE] ❌ 搜索完成，未找到符合條件的 widget")

print("\n" + "=" * 80)
print("開始測試！記得查看日誌找出問題！🔍")
print("=" * 80)
