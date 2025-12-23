#!/usr/bin/env python3
"""
驗證 Function 28 的數據載入問題
模擬 CLI 執行流程
"""

print("="*80)
print("Function 28 數據載入流程驗證")
print("="*80)

# 模擬場景：
# 1. 先載入 Japan GP (2025)
# 2. 然後執行 Function 28 for United States GP (2025)
# 3. 檢查 analyzer 使用的數據是哪個賽事

print("\n📋 問題場景重現:")
print("   1. 用戶先查看 Japan GP 的某個分析（如 ideal_lap_ranking）")
print("   2. data_loader 載入了 2025 Japan Race 的數據")
print("   3. 用戶切換到 United States GP")
print("   4. 執行 Function 28 (detailed_laptime_analysis)")
print("   5. Function 28 接收到 year=2025, race='United States', session='R'")
print("   6. 但 SingleDriverDetailedLaptimeAnalysis 直接使用 data_loader.get_loaded_data()")
print("   7. data_loader 仍然是 Japan 的數據！")

print("\n🔍 數據流分析:")
print("\n✅ Function 53 (ideal_lap) - 正確流程:")
print("   function_mapper.py:")
print("     → _execute_ideal_lap_analysis(**kwargs)")
print("     → IdealLapAnalyzer(self.data_loader)")
print("     → analyzer.load_data()")
print("     → data_loader.get_loaded_data()  # 使用已載入的數據")
print("   ")
print("   ✅ 因為 ideal_lap 不接受 year/race/session 參數")
print("   ✅ 它假設 data_loader 已經載入了正確的數據")

print("\n❌ Function 28 (detailed_laptime) - 錯誤流程:")
print("   function_mapper.py:")
print("     → execute_function_by_number(28, year='United States', race=...)")
print("     → _execute_driver_lap_time_analysis(year, race, session, driver)")
print("     → SingleDriverDetailedLaptimeAnalysis(data_loader, year, race, session)")
print("     → analyzer.analyze_every_lap()")
print("     → data = self.data_loader.get_loaded_data()  # ❌ 使用舊數據！")
print("   ")
print("   ❌ analyzer 接收了正確的 year/race/session 參數")
print("   ❌ 但沒有重新載入數據，直接使用 data_loader 的舊數據")
print("   ❌ 導致 JSON metadata 寫 'United States' 但內容是 'Japan' 的數據")

print("\n💡 根本原因:")
print("   • FunctionMapper 使用單一共享的 data_loader 實例")
print("   • data_loader 只在 CLI 啟動時載入一次（或用戶手動切換賽事時）")
print("   • Function 28 雖然接收 year/race/session 參數，但只用於:")
print("     - 存儲在 self.year, self.race, self.session")
print("     - 生成 JSON 檔案名稱和 metadata")
print("     - 但不會重新載入 session 數據！")
print("   • analyzer 直接使用 data_loader 中已載入的數據")

print("\n🔧 修復方案選項:")
print("\n方案 A: 在 SingleDriverDetailedLaptimeAnalysis 中添加數據驗證")
print("   • 在 analyze_every_lap() 開始時檢查 data_loader 的 year/race/session")
print("   • 如果不匹配，拋出錯誤或重新載入數據")
print("   • 優點：安全，不會使用錯誤數據")
print("   • 缺點：需要修改 analyzer 邏輯")

print("\n方案 B: 讓 analyzer 自行載入數據（不依賴 data_loader）")
print("   • SingleDriverDetailedLaptimeAnalysis 使用傳入的 year/race/session")
print("   • 直接調用 FastF1 載入對應的 session")
print("   • 不依賴外部 data_loader")
print("   • 優點：完全獨立，不受 data_loader 狀態影響")
print("   • 缺點：重複載入數據，性能較差")

print("\n方案 C: CLI 主程式確保 data_loader 同步（推薦）")
print("   • 在 execute_function_by_number() 中檢查參數")
print("   • 如果 year/race/session 與 data_loader 當前狀態不符")
print("   • 自動重新載入正確的數據")
print("   • 優點：統一處理，所有功能受益")
print("   • 缺點：需要修改 function_mapper 核心邏輯")

print("\n📝 建議實施步驟:")
print("   1. 立即採用方案 A 添加驗證（防止生成錯誤數據）")
print("   2. 長期採用方案 C 改進 CLI 架構（根本解決）")
print("   3. 刪除現有錯誤的 JSON 檔案")
print("   4. 重新生成正確的數據")

print("\n🚨 當前緊急修復:")
print("   1. 刪除錯誤 JSON:")
print("      Remove-Item json\\detailed_laptime_analysis_2025_United?States_R_all_drivers.json")
print("   2. 確保 CLI 載入 United States GP:")
print("      # 先確認沒有其他賽事數據在內存中")
print("   3. 重新生成:")
print("      python f1_analysis_modular_main.py -f 28 -y 2025 -r \"United States\" -s R")
