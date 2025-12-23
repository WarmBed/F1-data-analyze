# 排位賽預測 GUI Demo 啟動器
# Qualifying Prediction Demo Launcher
# 
# 啟動所有 5 個版本的 Demo 進行對比

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  排位賽預測 GUI Demo 啟動器" -ForegroundColor Yellow
Write-Host "  Qualifying Prediction Demo Launcher" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 可用的 Demo 版本：" -ForegroundColor Green
Write-Host ""
Write-Host "  [1] V1 基礎版 (6 欄)" -ForegroundColor White
Write-Host "      - 排名、車手、車隊、預測時間、信賴度、△FP3" -ForegroundColor Gray
Write-Host "      - 完整功能，包含車隊顏色、梯度改善、進度條" -ForegroundColor Gray
Write-Host ""
Write-Host "  [2] V2 極簡版 (4 欄)" -ForegroundColor White
Write-Host "      - 排名、車手、預測時間、信賴度" -ForegroundColor Gray
Write-Host "      - 快速查看，僅顯示前 10 名" -ForegroundColor Gray
Write-Host ""
Write-Host "  [3] V3 詳細版 (10 欄)" -ForegroundColor White
Write-Host "      - 包含 FP3、預測、△、信賴度、R²、MAE、樣本數" -ForegroundColor Gray
Write-Host "      - 深入分析，顯示模型詳細指標" -ForegroundColor Gray
Write-Host ""
Write-Host "  [4] V4 對比版 (8 欄)" -ForegroundColor White
Write-Host "      - v3.7 vs v3.8 模型對比" -ForegroundColor Gray
Write-Host "      - 顯示實際結果和準確度" -ForegroundColor Gray
Write-Host ""
Write-Host "  [5] V5 棒狀圖版 (7 欄)" -ForegroundColor White
Write-Host "      - 使用自定義 Delegate 繪製棒狀圖" -ForegroundColor Gray
Write-Host "      - 預測時間棒、FP3 對比雙棒" -ForegroundColor Gray
Write-Host ""
Write-Host "  [6] 啟動所有 Demo" -ForegroundColor Yellow
Write-Host "  [0] 退出" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "請選擇要啟動的 Demo (0-6)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 啟動 V1 基礎版..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "demo_qualifying_prediction.py" -NoNewWindow
    }
    "2" {
        Write-Host "`n🚀 啟動 V2 極簡版..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "demo_qualifying_prediction_v2_minimal.py" -NoNewWindow
    }
    "3" {
        Write-Host "`n🚀 啟動 V3 詳細版..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "demo_qualifying_prediction_v3_detailed.py" -NoNewWindow
    }
    "4" {
        Write-Host "`n🚀 啟動 V4 對比版..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "demo_qualifying_prediction_v4_comparison.py" -NoNewWindow
    }
    "5" {
        Write-Host "`n🚀 啟動 V5 棒狀圖版..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "demo_qualifying_prediction_v5_barchart.py" -NoNewWindow
    }
    "6" {
        Write-Host "`n🎉 啟動所有 Demo..." -ForegroundColor Yellow
        Write-Host "   V1 基礎版..." -ForegroundColor Gray
        Start-Process python -ArgumentList "demo_qualifying_prediction.py" -NoNewWindow
        Start-Sleep -Milliseconds 500
        
        Write-Host "   V2 極簡版..." -ForegroundColor Gray
        Start-Process python -ArgumentList "demo_qualifying_prediction_v2_minimal.py" -NoNewWindow
        Start-Sleep -Milliseconds 500
        
        Write-Host "   V3 詳細版..." -ForegroundColor Gray
        Start-Process python -ArgumentList "demo_qualifying_prediction_v3_detailed.py" -NoNewWindow
        Start-Sleep -Milliseconds 500
        
        Write-Host "   V4 對比版..." -ForegroundColor Gray
        Start-Process python -ArgumentList "demo_qualifying_prediction_v4_comparison.py" -NoNewWindow
        Start-Sleep -Milliseconds 500
        
        Write-Host "   V5 棒狀圖版..." -ForegroundColor Gray
        Start-Process python -ArgumentList "demo_qualifying_prediction_v5_barchart.py" -NoNewWindow
        
        Write-Host "`n✅ 所有 Demo 已啟動！" -ForegroundColor Green
    }
    "0" {
        Write-Host "`n👋 再見！" -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "`n❌ 無效選擇，請輸入 0-6" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
