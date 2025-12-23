# F1T Ollama 模型安裝腳本
# 針對 AMD RX 9070 XT 16GB 優化

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   F1T Ollama 模型自動安裝" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 檢查 Ollama 是否已安裝
Write-Host "[檢查] Ollama 安裝狀態..." -ForegroundColor Yellow
$ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollamaInstalled) {
    Write-Host "[錯誤] Ollama 未安裝，請先執行: winget install Ollama.Ollama" -ForegroundColor Red
    exit 1
}

Write-Host "[成功] Ollama 已安裝" -ForegroundColor Green

# 顯示模型選擇菜單
Write-Host "`n請選擇要安裝的模型:" -ForegroundColor Cyan
Write-Host "1. Qwen3 14B        - 最推薦（中文最強 + 最新）" -ForegroundColor White
Write-Host "2. DeepSeek-R1 14B  - 推理最強（Monaco/Netherlands 深度分析）" -ForegroundColor White
Write-Host "3. Qwen2.5 14B      - 穩定版（經過實戰驗證）" -ForegroundColor White
Write-Host "4. Qwen3-VL 8B      - 視覺分析（最新，4 天前更新）" -ForegroundColor White
Write-Host "5. 全部安裝         - 安裝所有推薦模型（需 ~50GB 空間）" -ForegroundColor Yellow

$choice = Read-Host "`n請輸入選項 (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n[安裝] Qwen3 14B..." -ForegroundColor Yellow
        ollama pull qwen3:14b
        Write-Host "`n[測試] 啟動 Qwen3 14B..." -ForegroundColor Yellow
        Write-Host "輸入測試 Prompt: '你好，請介紹你自己'" -ForegroundColor Cyan
        ollama run qwen3:14b "你好，請介紹你自己並告訴我你的能力"
    }
    "2" {
        Write-Host "`n[安裝] DeepSeek-R1 14B..." -ForegroundColor Yellow
        ollama pull deepseek-r1:14b
        Write-Host "`n[測試] 啟動 DeepSeek-R1 14B（會顯示思考過程）..." -ForegroundColor Yellow
        ollama run deepseek-r1:14b "分析以下問題：為什麼 Monaco 街道賽道的預測準確率只有 60%？"
    }
    "3" {
        Write-Host "`n[安裝] Qwen2.5 14B..." -ForegroundColor Yellow
        ollama pull qwen2.5:14b
        Write-Host "`n[測試] 啟動 Qwen2.5 14B..." -ForegroundColor Yellow
        ollama run qwen2.5:14b "你好，請介紹你自己"
    }
    "4" {
        Write-Host "`n[安裝] Qwen3-VL 8B（視覺模型）..." -ForegroundColor Yellow
        ollama pull qwen3-vl:8b
        Write-Host "`n[成功] Qwen3-VL 8B 已安裝" -ForegroundColor Green
        Write-Host "[提示] 視覺模型需要圖片輸入，請使用 Ollama API 調用" -ForegroundColor Cyan
    }
    "5" {
        Write-Host "`n[安裝] 全部推薦模型..." -ForegroundColor Yellow
        Write-Host "預計下載大小: ~50GB，需要時間: 30-60 分鐘" -ForegroundColor Yellow
        $confirm = Read-Host "確認繼續? (Y/N)"
        
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Write-Host "`n[1/4] 安裝 Qwen3 14B..." -ForegroundColor Yellow
            ollama pull qwen3:14b
            
            Write-Host "`n[2/4] 安裝 DeepSeek-R1 14B..." -ForegroundColor Yellow
            ollama pull deepseek-r1:14b
            
            Write-Host "`n[3/4] 安裝 Qwen2.5 14B..." -ForegroundColor Yellow
            ollama pull qwen2.5:14b
            
            Write-Host "`n[4/4] 安裝 Qwen3-VL 8B..." -ForegroundColor Yellow
            ollama pull qwen3-vl:8b
            
            Write-Host "`n[完成] 全部模型安裝完成！" -ForegroundColor Green
        } else {
            Write-Host "[取消] 安裝已取消" -ForegroundColor Yellow
        }
    }
    default {
        Write-Host "[錯誤] 無效選項" -ForegroundColor Red
        exit 1
    }
}

# 顯示已安裝模型
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   已安裝模型列表" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
ollama list

Write-Host "`n[完成] 安裝腳本執行完畢" -ForegroundColor Green
Write-Host "[下一步] 執行 'python f1_rl_optimizer.py --mode train' 開始訓練 PPO 優化器" -ForegroundColor Cyan
