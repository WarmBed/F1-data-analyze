# Logger 性能測試快速指令

## 🎯 快速測試 Logger 對性能的影響

### 1️⃣ 查看當前狀態
```powershell
python tools/toggle_logger.py
```

### 2️⃣ 禁用 Logger（測試性能提升）
```powershell
python tools/toggle_logger.py --disable
# 然後重啟 F1T GUI 測試
```

### 3️⃣ 重新啟用 Logger
```powershell
python tools/toggle_logger.py --enable
# 重啟 F1T GUI
```

## 📊 建議的測試步驟

### A. 基準測試（Logger 啟用）
1. 確認 logger 啟用：`python tools/toggle_logger.py --status`
2. 啟動 GUI 並運行 Live Timing
3. 記錄：
   - CPU 使用率（任務管理器）
   - 記憶體使用量
   - UI 響應速度（主觀感受）
   - 運行時間：15-30 分鐘

### B. 禁用測試（Logger 關閉）
1. 禁用 logger：`python tools/toggle_logger.py --disable`
2. 重新啟動 GUI 並運行相同場景
3. 記錄相同指標
4. 比較差異

### C. 中間方案測試（只記錄錯誤）
1. 啟用但降低等級：`python tools/toggle_logger.py --enable; python tools/toggle_logger.py --set-level ERROR`
2. 重啟並測試
3. 這樣可以保留錯誤日誌但減少大量 INFO/DEBUG 輸出

## 🔍 檢查日誌檔案大小

```powershell
# 查看 logs 目錄大小
Get-ChildItem logs -Recurse | Measure-Object -Property Length -Sum

# 查看最近的日誌檔案
Get-ChildItem logs -Filter *.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## ⚡ 性能提示

如果發現 logger 確實占用資源：

1. **保持禁用**（不需除錯時）
   ```powershell
   python tools/toggle_logger.py --disable
   ```

2. **只在需要時啟用**（出現問題時）
   ```powershell
   python tools/toggle_logger.py --enable
   python tools/toggle_logger.py --set-level DEBUG
   ```

3. **正常使用設為 WARNING**（平衡性能與除錯）
   ```powershell
   python tools/toggle_logger.py --set-level WARNING
   ```

## 📁 相關檔案

- **設定檔**：`config/logging_config.json`
- **工具**：`tools/toggle_logger.py`
- **詳細文檔**：`tools/README_LOGGER_TOOL.md`
- **日誌目錄**：`logs/`
