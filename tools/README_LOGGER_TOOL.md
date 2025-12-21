# Logger 開關工具使用指南

## 📋 簡介

如果你懷疑 logging 系統占用大量資源影響性能，可以使用此工具快速禁用或啟用 logger 系統。

## 🚀 快速使用

### 查看當前狀態
```powershell
python tools/toggle_logger.py --status
```

### 禁用 Logger（提升性能）
```powershell
python tools/toggle_logger.py --disable
```
**⚠️ 重要：禁用後需要重新啟動 F1T GUI 才會生效**

### 重新啟用 Logger
```powershell
python tools/toggle_logger.py --enable
```

### 調整日誌等級
```powershell
# 設定為 ERROR（只記錄錯誤）
python tools/toggle_logger.py --set-level ERROR

# 設定為 WARNING（記錄警告和錯誤）
python tools/toggle_logger.py --set-level WARNING

# 設定為 DEBUG（記錄所有訊息，最詳細）
python tools/toggle_logger.py --set-level DEBUG
```

### 調整控制台輸出等級
```powershell
# 控制台只顯示錯誤
python tools/toggle_logger.py --console-level ERROR

# 控制台不顯示任何內容
python tools/toggle_logger.py --console-level NONE
```

### 切換 Print Patch
```powershell
python tools/toggle_logger.py --toggle-print
```

## 📊 性能測試建議

### 測試 Logger 對性能的影響

1. **啟用 Logger 運行測試**
   ```powershell
   python tools/toggle_logger.py --enable
   # 重新啟動 GUI 並記錄性能數據（CPU、記憶體使用率）
   ```

2. **禁用 Logger 運行測試**
   ```powershell
   python tools/toggle_logger.py --disable
   # 重新啟動 GUI 並記錄性能數據
   ```

3. **比較結果**
   - CPU 使用率差異
   - 記憶體使用量差異
   - UI 響應速度

### 漸進式測試

如果不確定是否要完全禁用，可以先調整日誌等級：

```powershell
# 步驟 1: 從 INFO 改為 WARNING（減少 70% 日誌量）
python tools/toggle_logger.py --set-level WARNING

# 步驟 2: 如果還不夠，改為 ERROR（只記錄錯誤）
python tools/toggle_logger.py --set-level ERROR

# 步驟 3: 如果性能仍有問題，完全禁用
python tools/toggle_logger.py --disable
```

## 📁 設定檔位置

設定儲存在：`config/logging_config.json`

手動編輯此檔案也可以：
```json
{
  "enabled": false,
  "level": "INFO",
  "console_level": null,
  "patch_print": true
}
```

## ⚠️ 注意事項

1. **修改後需重啟**：任何變更都需要重新啟動 F1T GUI 才會生效
2. **除錯困難**：禁用 logger 後將無法查看除錯訊息
3. **建議先測試**：建議先調整等級而非直接禁用

## 🔍 日誌等級說明

| 等級 | 描述 | 適用場景 |
|------|------|---------|
| **DEBUG** | 最詳細，記錄所有訊息 | 開發除錯時 |
| **INFO** | 一般資訊（預設） | 正常使用 |
| **WARNING** | 警告訊息 | 關注潛在問題 |
| **ERROR** | 錯誤訊息 | 只關心錯誤 |
| **CRITICAL** | 嚴重錯誤 | 只記錄致命問題 |

## 💡 最佳實踐

### 開發環境
```powershell
python tools/toggle_logger.py --enable
python tools/toggle_logger.py --set-level DEBUG
```

### 正常使用
```powershell
python tools/toggle_logger.py --enable
python tools/toggle_logger.py --set-level INFO
```

### 性能優先
```powershell
python tools/toggle_logger.py --disable
# 或
python tools/toggle_logger.py --set-level ERROR
```

### Live Timing 高負載場景
```powershell
python tools/toggle_logger.py --set-level WARNING
python tools/toggle_logger.py --console-level ERROR
```

## 🛠️ 進階選項

### 只禁用控制台輸出，保留檔案日誌
```powershell
python tools/toggle_logger.py --console-level NONE
# Logger 仍會寫入 logs/ 目錄，但不會在控制台顯示
```

### 禁用 Print Patch
```powershell
python tools/toggle_logger.py --toggle-print
# 這會讓 print() 使用原生行為而非透過 logger
```

## 📈 性能影響預估

根據經驗，logging 系統可能占用：
- **CPU**: 5-15%（取決於日誌量）
- **記憶體**: 10-50 MB（取決於緩衝區大小）
- **I/O**: 檔案寫入可能造成延遲

禁用 logger 或調整為 ERROR 等級可顯著降低這些開銷。

## 🆘 疑難排解

### 變更未生效
**原因**：未重新啟動 GUI  
**解決**：關閉並重新啟動 F1T GUI

### 找不到設定檔
**原因**：config 目錄不存在  
**解決**：工具會自動創建

### Logger 仍然輸出
**原因**：某些模組可能直接使用 logging 而非 core.logger  
**解決**：這是正常的，這些模組的日誌無法通過此工具控制
