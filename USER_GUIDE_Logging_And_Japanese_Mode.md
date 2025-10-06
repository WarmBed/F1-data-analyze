# 🎯 日誌系統改進 & 日語模式更新問題調查報告

## 📝 修復摘要

**完成日期**: 2025-10-06  
**修改內容**:
1. ✅ 日誌系統改為日期式儲存 (`f1_gui_2025-10-06.log`)
2. ✅ 終端機不再輸出日誌訊息（僅寫入檔案）
3. ✅ 日誌等級降為 INFO（減少 DEBUG 干擾）
4. ✅ 移除 `update_all_lap_analysis()` 中的 print() 改用 logger
5. 🔍 日語模式更新問題需進一步測試

---

## ✅ 已完成的改進

### 1. 日誌系統現代化

#### 修改檔案: `core/logger.py`

**主要變更**:

1. **日期式日誌檔案名稱**
   ```python
   # 舊: f1_gui.log
   # 新: f1_gui_2025-10-06.log
   
   from datetime import datetime
   today = datetime.now().strftime("%Y-%m-%d")
   base_filename = log_dir / f"f1_{component}_{today}.log"
   ```

2. **自動日誌輪替** (TimedRotatingFileHandler)
   - 每天午夜自動切換新檔案
   - 保留 30 天的歷史日誌
   - 錯誤日誌單獨儲存在 `f1_gui_error_2025-10-06.log`

3. **停用終端機輸出**
   ```python
   # handlers 中移除 "console"
   "loggers": {
       "f1": {
           "handlers": ["file", "error_file"],  # ❌ 移除 "console"
       }
   }
   ```

4. **日誌等級設定**
   - 預設: INFO（不顯示 DEBUG 訊息）
   - 保留環境變數支援: `$env:F1_LOG_LEVEL = "DEBUG"`

#### 修改檔案: `f1t_gui_main.py`

**主要變更**:

1. **初始化配置**
   ```python
   # 舊
   setup_logging(component="gui", console_level="ERROR")
   
   # 新
   setup_logging(component="gui", level="INFO", console_level=None)
   ```

2. **替換所有 print() 為 logger**

   `update_all_lap_analysis()` 方法中:
   
   | 舊語句 | 新語句 | 等級 |
   |--------|--------|------|
   | `print(f"[LAP_CONTROL] 🎯 更新參數...")` | `logger.info(f"圈速控制 - 更新參數...")` | INFO |
   | `print(f"[LAP_CONTROL] ⏭️ 跳過...")` | `logger.debug(f"圈速控制 - 跳過...")` | DEBUG |
   | `print(f"[LAP_CONTROL] ⚠️ 更新失敗")` | `logger.warning(f"圈速控制 - 更新失敗")` | WARNING |
   | `print(f"[LAP_CONTROL] ❌ 錯誤: {e}")` | `logger.error(f"圈速控制 - 錯誤: {e}", exc_info=True)` | ERROR |

**改進效果**:
- ✅ 統一日誌格式（時間戳 + 等級 + 模組名稱）
- ✅ 異常堆疊追蹤自動記錄 (`exc_info=True`)
- ✅ 終端機乾淨無干擾
- ✅ 可按日期查看歷史日誌

---

## 🔍 日語模式更新問題調查

### 問題描述

> **使用者回報**: 在日語 UI 模式下，將 driver2 從 "なし" (無) 更新為 "LEC" 時，圖表不會更新。

### 已確認修復的問題 ✅

**driver2 參數檢測** (已在先前修復):

```python
# ✅ 正確邏輯（已修復）
driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
```

此修復確保所有語言（中文"無"、英文"None"、日語"なし"）都能正確識別為 `None`。

### 可能的新問題點 🔍

#### 1. 參數比較邏輯

**位置**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py` 第 638-647 行

```python
params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != driver2 or  # ⚠️ 可能的問題
    self.lap1 != lap1 or
    self.lap2 != lap2
)
```

**潛在問題**: 如果 `self.driver2 = "なし"` 而 `driver2 = None`，比較結果為 True（視為參數變化），但可能導致意外行為。

**建議修復**:

```python
# 正規化 driver2 以避免語言差異
old_driver2 = None if not self.driver2 or self.driver2 in ["無", "None", "なし"] else self.driver2
new_driver2 = None if not driver2 or driver2 in ["無", "None", "なし"] else driver2

params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    old_driver2 != new_driver2 or  # ✅ 安全的比較
    self.lap1 != lap1 or
    self.lap2 != lap2
)
```

#### 2. 日誌追蹤不足

**位置**: `speed_analysis_mdi.py` 第 619-661 行

**問題**: 目前使用 `print()`，且沒有詳細記錄每個參數的變化。

**建議改進**:

```python
from core.logger import get_logger
logger = get_logger("speed_analysis")

logger.info(f"收到參數更新: year={year}, race={race}, session={session}")
logger.info(f"車手參數: driver1={driver1}, driver2={driver2!r}")
logger.debug(f"參數比較詳情:")
logger.debug(f"  year: {self.current_year} -> {year} (變化: {self.current_year != str(year)})")
logger.debug(f"  race: {self.current_race} -> {race} (變化: {self.current_race != race})")
logger.debug(f"  driver1: {self.driver1} -> {driver1} (變化: {self.driver1 != driver1})")
logger.debug(f"  driver2: {self.driver2!r} -> {driver2!r} (變化: {self.driver2 != driver2})")
logger.debug(f"  lap1: {self.lap1} -> {lap1} (變化: {self.lap1 != lap1})")
logger.debug(f"  lap2: {self.lap2} -> {lap2} (變化: {self.lap2 != lap2})")
logger.info(f"參數是否變化: {params_changed}")
```

---

## 🧪 測試驗證

### 測試腳本: `test_logging_and_japanese_update.py`

已建立測試腳本驗證:

1. ✅ 日誌系統配置
2. ✅ driver2 參數處理邏輯
3. ✅ 日語模式下的參數傳遞

**執行測試**:

```powershell
python test_logging_and_japanese_update.py
```

**測試結果**:

```
✅ 日誌檔案已創建: logs/f1_test_2025-10-06.log
✅ 錯誤日誌已創建: logs/f1_test_error_2025-10-06.log
✅ 終端機無 logger 輸出（僅測試的 print）
✅ 日誌檔案僅包含 INFO/WARNING/ERROR（無 DEBUG）
```

---

## 📋 使用指南

### 查看日誌檔案

```powershell
# 查看今天的 GUI 日誌（最後 50 行，UTF-8 編碼）
Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 -Tail 50

# 查看錯誤日誌
Get-Content logs/f1_gui_error_2025-10-06.log -Encoding UTF8

# 即時監控日誌（類似 tail -f）
Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 -Wait -Tail 20
```

### 臨時啟用 DEBUG 等級

**方法 1: 環境變數**

```powershell
$env:F1_LOG_LEVEL = "DEBUG"
python f1t_gui_main.py
```

**方法 2: 程式碼修改**

在 `f1t_gui_main.py` 中:

```python
setup_logging(component="gui", level="DEBUG", force=True)
```

### 清理舊日誌

```powershell
# 刪除 30 天前的日誌
Get-ChildItem logs/f1_*.log | Where-Object { 
    $_.LastWriteTime -lt (Get-Date).AddDays(-30) 
} | Remove-Item

# 查看日誌檔案大小
Get-ChildItem logs/f1_*.log | Select-Object Name, @{
    Name="Size(KB)"; Expression={[math]::Round($_.Length/1KB, 2)}
}
```

---

## 🎯 下一步行動計畫

### 立即執行（開發者）

1. **在日語模式下重現問題**
   - 啟動 GUI 並設置語言為日語
   - 開啟速度分析視窗（driver2 = なし）
   - 更改 driver2 為 LEC
   - 檢查日誌檔案: `logs/f1_gui_2025-10-06.log`

2. **檢查日誌內容**
   ```powershell
   # 過濾圈速控制相關日誌
   Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 | Select-String "圈速控制"
   
   # 過濾錯誤訊息
   Get-Content logs/f1_gui_2025-10-06.log -Encoding UTF8 | Select-String "ERROR|WARNING"
   ```

3. **根據日誌診斷問題**
   - 確認 `update_lap_parameters` 是否被調用
   - 確認參數傳遞是否正確（driver2 = "LEC" 而非 "なし"）
   - 確認 `params_changed` 的值
   - 確認數據重載是否成功

### 計畫中（待確認需求）

1. **全面移除 print() 語句**
   - `speed_analysis_mdi.py` 及其他分析模組
   - 統一使用 `get_logger()` 和 logger 方法

2. **改進參數比較邏輯**
   - 正規化 driver2 比較（避免語言差異）
   - 添加詳細的參數變化日誌（DEBUG 等級）

3. **單元測試**
   - 測試日語/中文/英文模式下的參數傳遞
   - 測試 driver2 從 None 更新為車手代碼
   - 測試參數比較邏輯的正確性

---

## ⚠️ 已知限制

1. **PowerShell 編碼問題**
   - 直接使用 `Get-Content` 可能顯示亂碼
   - 必須加上 `-Encoding UTF8` 參數

2. **日誌檔案累積**
   - 系統僅保留 30 天的日誌
   - 需定期檢查 `logs/` 目錄大小
   - 建議設定自動清理任務

3. **部分模組仍使用 print()**
   - 分析模組（`CLI_modules/` 和 `modules/gui/`）中仍有大量 print()
   - 需要逐步遷移至 logger 系統

---

## 📌 總結

### ✅ 已完成

1. **日誌系統現代化**
   - 日期式檔案名稱 (`f1_gui_2025-10-06.log`)
   - 自動輪替（每天午夜，保留 30 天）
   - 停用終端輸出（僅寫入檔案）
   - 降低日誌等級（INFO 預設）

2. **GUI 主程式改進**
   - 移除 `update_all_lap_analysis()` 中的 print()
   - 統一使用 logger（INFO/WARNING/ERROR）
   - 異常追蹤自動記錄

3. **測試驗證**
   - 建立測試腳本 `test_logging_and_japanese_update.py`
   - 驗證日誌系統配置
   - 驗證 driver2 參數處理邏輯

### 🔍 待確認

1. **日語模式更新問題**
   - 需在實際環境中測試
   - 需檢查日誌檔案診斷問題根源
   - 可能需要修改參數比較邏輯

2. **後續改進**
   - 全面移除 print() 語句
   - 改進參數比較邏輯
   - 建立單元測試

---

**修復者**: GitHub Copilot  
**審核者**: 待使用者確認  
**相關文檔**: 
- `copilot-instructions.md` - 專案開發政策
- `FIX_REPORT_Logging_System_Improvement.md` - 詳細技術報告
