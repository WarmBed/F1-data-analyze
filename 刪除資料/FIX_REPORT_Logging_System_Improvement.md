# 日誌系統改進和日語模式更新問題修復報告

## 📋 修復概要

**修復日期**: 2025-10-06  
**相關Issue**: 日語模式下圖表不更新 + 日誌系統改進  
**影響範圍**: 核心日誌系統 + GUI 主程式

---

## ✅ 已完成的改進

### 1️⃣ 日誌系統現代化

**修改檔案**: `core/logger.py`

#### 改進內容:

1. **日期式日誌檔案**
   - 舊格式: `f1_gui.log`
   - 新格式: `f1_gui_2025-10-06.log`
   - 實現方式: 使用 `TimedRotatingFileHandler` + `datetime.now().strftime("%Y-%m-%d")`

2. **自動日誌輪替**
   - `when="midnight"` - 每天午夜自動切換新檔案
   - `backupCount=30` - 保留 30 天的歷史日誌
   - `interval=1` - 每天一個檔案

3. **停用終端機輸出**
   - 移除所有 handler 中的 `"console"`
   - 日誌僅寫入檔案，不再輸出到終端
   - 保留 `patch_print` 功能以捕獲意外的 print() 語句

4. **降低日誌等級**
   - 預設等級: INFO（不再顯示 DEBUG 訊息）
   - WARNING 和 ERROR 會額外寫入錯誤日誌檔案
   - 保留 `F1_LOG_LEVEL` 環境變數支援動態調整

#### 程式碼變更:

```python
# 修改前
"file": {
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 5 * 1024 * 1024,
    "backupCount": 5,
}

# 修改後
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
base_filename = log_dir / f"f1_{component}_{today}.log"

"file": {
    "class": "logging.handlers.TimedRotatingFileHandler",
    "when": "midnight",
    "interval": 1,
    "backupCount": 30,
}
```

### 2️⃣ GUI 主程式日誌初始化

**修改檔案**: `f1t_gui_main.py`

#### 改進內容:

```python
# 修改前
setup_logging(component="gui", console_level="ERROR")

# 修改後
setup_logging(component="gui", level="INFO", console_level=None)
logger.info("F1T GUI 控制台初始化完成 - 日誌系統已啟用 (INFO level, 僅檔案輸出)")
```

### 3️⃣ 移除 print() 改用 logger

**修改檔案**: `f1t_gui_main.py` - `update_all_lap_analysis()` 方法

#### 全面替換日誌語句:

| 舊語句 (print) | 新語句 (logger) | 等級 |
|---|---|---|
| `print(f"[LAP_CONTROL] 🎯 更新參數...")` | `logger.info(f"圈速控制 - 更新參數...")` | INFO |
| `print(f"[LAP_CONTROL] ⏭️ 跳過非遙測...")` | `logger.debug(f"圈速控制 - 跳過非遙測...")` | DEBUG |
| `print(f"[LAP_CONTROL] ⚠️ 更新返回 False")` | `logger.warning(f"圈速控制 - 更新返回 False")` | WARNING |
| `print(f"[LAP_CONTROL] ❌ 更新失敗: {e}")` | `logger.error(f"圈速控制 - 更新失敗: {e}", exc_info=True)` | ERROR |

#### 改進效果:

1. **統一日誌格式** - 所有日誌都有時間戳和模組名稱
2. **異常追蹤** - 使用 `exc_info=True` 自動記錄完整的堆疊追蹤
3. **可控等級** - DEBUG 訊息不會干擾生產環境
4. **檔案持久化** - 所有日誌永久保存在 `logs/` 目錄

---

## 🔍 日語模式更新問題調查

### 問題描述

使用者在日語 UI 模式下，更新 driver2 為 LEC 時，圖表不會更新。

### 已修復的 driver2 檢測問題 ✅

**已在先前修復**: 使用 `currentData()` 代替 `currentText() != "無"`

```python
# ✅ 已修復（先前）
driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
```

### 新發現的潛在問題點 🔍

經過程式碼分析，發現圖表可能不更新的原因：

#### 1. 參數比較邏輯

`speed_analysis_mdi.py` 第 638-647 行:

```python
params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != driver2 or  # ⚠️ None 比較可能有問題
    self.lap1 != lap1 or
    self.lap2 != lap2
)
```

**問題**: 當 `self.driver2 = "なし"` 而 `driver2 = None` 時，`"なし" != None` 為 True，但實際上兩者都代表 "無車手2"。

#### 2. 日誌追蹤不足

`speed_analysis_mdi.py` 第 661 行:

```python
print(f"[SPEED_MDI] 參數是否變化: {params_changed}")
```

**問題**: 沒有詳細記錄每個參數的舊值和新值，難以診斷為何 `params_changed` 為 False。

---

## 📝 建議的下一步驟

### 立即執行

1. **加強參數比較日誌**

   在 `speed_analysis_mdi.py` 的 `update_lap_parameters` 中添加:

   ```python
   logger.debug(f"參數比較詳情:")
   logger.debug(f"  year: {self.current_year} -> {year} (變化: {self.current_year != str(year)})")
   logger.debug(f"  race: {self.current_race} -> {race} (變化: {self.current_race != race})")
   logger.debug(f"  driver1: {self.driver1} -> {driver1} (變化: {self.driver1 != driver1})")
   logger.debug(f"  driver2: {self.driver2!r} -> {driver2!r} (變化: {self.driver2 != driver2})")
   ```

2. **正規化 driver2 比較**

   在參數比較前，將 driver2 統一為 None 或車手代碼:

   ```python
   # 正規化 driver2（無論語言都統一為 None）
   old_driver2 = None if not self.driver2 else self.driver2
   new_driver2 = None if not driver2 else driver2
   
   params_changed = (
       # ... 其他參數 ...
       old_driver2 != new_driver2 or
       # ... 其他參數 ...
   )
   ```

### 測試計畫

1. **日語模式測試**
   - 啟動 GUI 並設置語言為日語
   - 開啟速度分析視窗（driver2 = なし）
   - 更改 driver2 為 LEC
   - 檢查日誌檔案 `logs/f1_gui_2025-10-06.log` 中的參數比較詳情

2. **日誌系統驗證**
   - 執行 `python test_logging_and_japanese_update.py`
   - 確認終端機無 logger 輸出
   - 檢查 `logs/f1_test_2025-10-06.log` 存在且格式正確
   - 確認無 DEBUG 訊息（僅 INFO/WARNING/ERROR）

---

## 📊 測試結果

### 日誌系統測試 ✅

執行 `test_logging_and_japanese_update.py` 後:

1. ✅ 日誌檔案已創建: `logs/f1_test_2025-10-06.log`
2. ✅ 錯誤日誌已創建: `logs/f1_test_error_2025-10-06.log`
3. ✅ 終端機無 logger 輸出（僅測試的 print）
4. ⚠️ 日誌檔案編碼問題（中文顯示亂碼）

### 編碼問題修復

**原因**: Windows PowerShell 預設編碼為 Big5，但日誌檔案使用 UTF-8

**解決方案**:

1. 讀取日誌時指定編碼:
   ```powershell
   Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 -Tail 20
   ```

2. 或設置 PowerShell 預設編碼:
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   ```

---

## 🎯 完成狀態

| 項目 | 狀態 | 備註 |
|---|---|---|
| 日期式日誌檔案 | ✅ 完成 | `f1_gui_2025-10-06.log` |
| 自動日誌輪替 | ✅ 完成 | 每天午夜，保留 30 天 |
| 停用終端輸出 | ✅ 完成 | 僅寫入檔案 |
| 降低日誌等級 | ✅ 完成 | INFO 預設，無 DEBUG |
| 移除 print() | ✅ 完成 | `update_all_lap_analysis` 已改用 logger |
| driver2 檢測修復 | ✅ 完成 | 已在先前修復 |
| 日語模式更新問題 | 🔍 調查中 | 需要更多日誌追蹤 |

---

## 🛠️ 使用指南

### 查看日誌

```powershell
# 查看今天的 GUI 日誌（最後 50 行）
Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 -Tail 50

# 查看錯誤日誌
Get-Content logs/f1_gui_error_2025-10-06.log -Encoding UTF8

# 即時監控日誌
Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 -Wait
```

### 臨時啟用 DEBUG

```powershell
# 設置環境變數
$env:F1_LOG_LEVEL = "DEBUG"
python f1t_gui_main.py

# 或在程式碼中強制:
setup_logging(component="gui", level="DEBUG", force=True)
```

### 日誌檔案管理

```powershell
# 清理 30 天前的舊日誌
Get-ChildItem logs/f1_*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item

# 檢視日誌檔案大小
Get-ChildItem logs/f1_*.log | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 2)}}
```

---

## 📌 總結

### 已完成 ✅

1. **日誌系統現代化** - 日期式檔案、自動輪替、停用 console
2. **GUI 主程式改進** - 統一使用 logger 而非 print
3. **測試腳本** - 驗證日誌系統和 driver2 參數處理

### 待處理 🔍

1. **日語模式更新問題** - 需要在實際環境中測試並查看日誌
2. **參數比較邏輯優化** - 正規化 driver2 比較（None vs 文字）
3. **全面移除 print** - 替換所有分析模組中的 print() 為 logger

### 下一步建議

1. 在日語模式下重現問題，檢查新的日誌檔案
2. 根據日誌內容確定問題根源（參數比較 vs 數據載入 vs UI 更新）
3. 逐步替換所有模組中的 print() 為 logger
4. 建立日誌監控 dashboard（可選）

---

**修復者**: GitHub Copilot  
**審核者**: 待確認  
**相關文檔**: `copilot-instructions.md` - API-ONLY 模式政策
