# 執行緒清理錯誤 - 快速測試指南

## 🎯 問題摘要

關閉 GUI 時出現大量 Python 3.13 執行緒清理警告（`TypeError: 'NoneType' object is not support the context manager protocol`）

## ✅ 已實施修復

1. **改善主視窗執行緒清理** - 收集並等待所有 QThread 完全終止
2. **增強警告抑制器** - 抑制 Python 3.13 的執行緒清理警告
3. **延長等待時間** - 從 2 秒增加到 3 秒，確保執行緒有足夠時間退出

## 🧪 快速測試步驟

### 步驟 1: 啟動 GUI
```powershell
python f1t_gui_main.py
```

### 步驟 2: 開啟多個分析視窗
- 開啟 3-5 個不同的分析模組（速度分析、輪胎分析、天氣分析等）
- 讓一些 API 請求正在執行中

### 步驟 3: 觀察啟動日誌
應該看到：
```
[MAIN] ✅ Python 3.13 執行緒警告抑制器已啟用
```

### 步驟 4: 關閉程式
點擊主視窗的關閉按鈕

### 步驟 5: 檢查終端輸出

#### ✅ 成功標準：

1. **清理日誌清楚顯示**：
```
[CLEANUP] 🛑 主視窗正在關閉，開始清理資源...
[CLEANUP] 🔍 找到 X 個活動執行緒
[CLEANUP] 📡 停止 API 監控執行緒...
[CLEANUP]   🔴 停止 ApiHealthWorker...
[CLEANUP]   ✅ ApiHealthWorker 已停止
[CLEANUP]   🔴 停止 ApiRuntimeWorker...
[CLEANUP]   ✅ ApiRuntimeWorker 已停止
[CLEANUP] ⏰ 停止所有定時器...
[CLEANUP] 🪟 關閉所有 MDI 子視窗...
[CLEANUP] ⏳ 等待 X 個執行緒完全終止...
[CLEANUP]   ✅ XXX 已完全終止
[CLEANUP] 🔄 處理待處理的 Qt 事件...
[CLEANUP] ✅ 主視窗資源清理完成
[CLEANUP] 🏁 主視窗關閉事件處理完成
[MAIN] 🛑 F1T 程序正常退出
```

2. **不再出現錯誤**：
   - ❌ 不應該看到 `Exception ignored in: <function _DeleteDummyThreadOnDel.__del__>`
   - ❌ 不應該看到 `TypeError: 'NoneType' object is not support the context manager protocol`

3. **快速退出**：
   - 程式應在 5 秒內完全退出

#### ❌ 失敗標準：

- 仍然出現 `_DeleteDummyThreadOnDel` 相關錯誤
- 程式卡住超過 10 秒
- 出現新的錯誤訊息

## 📊 測試記錄

請在測試後填寫：

| 項目 | 狀態 | 備註 |
|------|------|------|
| 警告抑制器啟用 | ⬜ 是 / ⬜ 否 | |
| 清理日誌完整顯示 | ⬜ 是 / ⬜ 否 | |
| 沒有執行緒錯誤 | ⬜ 是 / ⬜ 否 | |
| 5秒內退出 | ⬜ 是 / ⬜ 否 | |
| 整體評價 | ⬜ 通過 / ⬜ 失敗 | |

## 🐛 如果測試失敗

### 情況 1: 仍然出現執行緒錯誤

**檢查項目**：
1. 確認 `f1t_gui_main.py` 開頭有警告抑制器（Line 15-32）
2. 確認 `main()` 函數中有自定義 excepthook（Line 20760）
3. 查看哪些執行緒未被正確終止

**解決方案**：
```python
# 在終端執行，查看活動執行緒
import threading
print([t.name for t in threading.enumerate()])
```

### 情況 2: 程式卡住不退出

**檢查項目**：
1. 查看 `[CLEANUP]` 日誌中哪個步驟卡住
2. 可能是某個執行緒的 `wait()` 超時

**解決方案**：
- 減少 `wait()` 超時時間（從 3000ms 改為 1000ms）
- 或在卡住的執行緒加入更早的 `quit()` 調用

### 情況 3: 出現新的錯誤

**檢查項目**：
1. 記錄完整的錯誤訊息
2. 檢查是否是特定模組的問題

**解決方案**：
- 在對應模組的 `cleanup()` 方法中加入執行緒清理
- 參考 `speed_analysis_mdi.py` 的清理模式

## 📞 需要協助？

如果測試失敗或有疑問：

1. **記錄完整日誌**：將終端輸出保存到檔案
   ```powershell
   python f1t_gui_main.py 2>&1 | Tee-Object -FilePath cleanup_test.log
   ```

2. **提供測試環境資訊**：
   - Python 版本：`python --version`
   - PyQt5 版本：`python -c "from PyQt5.QtCore import PYQT_VERSION_STR; print(PYQT_VERSION_STR)"`
   - 作業系統：Windows 版本

3. **描述問題**：
   - 何時出現錯誤
   - 開啟了哪些分析模組
   - 錯誤訊息的完整內容

---

**測試日期**: _____________
**測試人員**: _____________
**測試結果**: ⬜ 通過 / ⬜ 失敗
**備註**: _____________________________________________
