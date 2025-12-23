# API-ONLY 模式修復腳本
# 目的：移除 Brake/RPM 模組中自動創建遙測分析視窗的邏輯

Write-Host "🔧 開始 API-ONLY 模式修復..." -ForegroundColor Cyan

# 修復文件列表
$files = @(
    "modules\gui\lap_analysis\brake_analysis\brake_analysis_mdi.py",
    "modules\gui\lap_analysis\rpm_analysis\rpm_analysis_mdi.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "📝 處理檔案: $file" -ForegroundColor Yellow
        
        # 讀取檔案
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # 修復 1：移除自動創建遙測分析視窗的邏輯
        $pattern1 = '# 如果沒有遙測分析視窗，嘗試創建一個\s+print\(f"\[.*?MDI\] 📡 嘗試創建遙測分析視窗..."\)\s+if hasattr\(main_window, ''create_telemetry_analysis''\):\s+main_window\.create_telemetry_analysis\(\)\s+return True'
        $replacement1 = '# ❌ [API-ONLY 修復] 不自動創建遙測分析視窗
                    print(f"[{0}_MDI] 💡 [API-ONLY] 未找到現有遙測分析視窗")' -f ($file -replace '.*\\(\w+)_analysis.*','$1').ToUpper()
        
        $content = $content -replace $pattern1, $replacement1
        
        # 修復 2：更新 _check_and_load_telemetry_if_needed 的提示訊息
        $pattern2 = 'print\("⚠️ \[.*?MDI\] 未能自動載入遙測分析，請使用主視窗遙測模組或 REST API 先取得資料"\)'
        $replacement2 = 'print("⚠️ [{0}_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存")
            print("💡 [{0}_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
            print("💡 [{0}_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")' -f ($file -replace '.*\\(\w+)_analysis.*','$1').ToUpper()
        
        $content = $content -replace $pattern2, $replacement2
        
        # 寫回檔案
        $content | Set-Content $file -Encoding UTF8 -NoNewline
        
        Write-Host "✅ 完成: $file" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 檔案不存在: $file" -ForegroundColor Red
    }
}

Write-Host "`n🎉 API-ONLY 模式修復完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 修復摘要：" -ForegroundColor Cyan
Write-Host "  ✅ 移除自動創建遙測分析視窗的邏輯"
Write-Host "  ✅ 更新為僅檢查本地 JSON 緩存"
Write-Host "  ✅ 添加用戶提示訊息"
Write-Host ""
Write-Host "🧪 建議測試：" -ForegroundColor Yellow
Write-Host "  1. 開啟 Brake 分析模組"
Write-Host "  2. 勾選最速圈選項"
Write-Host "  3. 更新 driver 參數"
Write-Host "  4. 驗證不會自動創建 Pitstop 視窗"
Write-Host ""
