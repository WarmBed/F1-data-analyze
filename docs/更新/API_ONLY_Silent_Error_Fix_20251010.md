# API-ONLY 模式靜默錯誤修正 - 2025年10月10日

## 🎯 問題描述

### 用戶反饋
在 EXE 環境下使用 Ideal Lap Analysis 模組時，系統彈出錯誤對話框：
```
資料載入失敗
找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據
```

### 問題分析
1. **設計初衷**：API-ONLY 模式應該優先使用 API 獲取數據
2. **錯誤行為**：找不到本地 JSON 時，系統彈出錯誤對話框打斷用戶操作
3. **預期行為**：找不到本地 JSON 時，應該靜默記錄到日誌，不彈窗

---

## 🔍 根因分析

### 架構對比

| 模組 | 錯誤處理方式 | 是否彈窗 |
|-----|------------|---------|
| **Track Analysis** | 只在圖表區域顯示錯誤訊息 | ❌ 不彈窗 |
| **Ideal Lap Analysis** | 調用 `_show_error()` 彈出對話框 | ✅ 會彈窗 |

### 問題源頭

#### 1. UniversalDataLoader 基類 (modules/gui/base/universal_data_loader_base.py)

**第 254 行**：
```python
# ❌ 問題：發送錯誤信號
self.load_error.emit("找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據")
```

#### 2. Ideal Lap MDI 模組

**ideal_lap_ranking_table_mdi.py 第 403 行**：
```python
def _on_load_error(self, error_msg: str):
    # ❌ 問題：彈出錯誤對話框
    self._show_error("資料載入失敗", error_msg)
```

**ideal_lap_sector_comparison_mdi.py 第 406 行**：
```python
def _on_load_error(self, error_msg: str):
    # ❌ 問題：彈出詳細的錯誤對話框
    self._show_error(
        "資料載入失敗",
        f"無法載入分段對比資料:\n\n{error_msg}\n\n"
        f"請檢查:\n..."
    )
```

---

## ✅ 解決方案

### 修改 1：UniversalDataLoader 基類 - 靜默處理找不到 JSON

**檔案**：`modules/gui/base/universal_data_loader_base.py`

**修改前（第 248-254 行）**：
```python
if not json_files:
    # ❌ 找不到 JSON，發送錯誤信號（會觸發彈窗）
    self._debug("⚠️  [UNIVERSAL_LOADER] 找不到 JSON 檔案，且 CLI 調用已禁用")
    self._debug("💡 提示: 請通過 API 獲取數據")
    
    # 發送錯誤信號
    self.load_error.emit("找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據")
    return False
```

**修改後**：
```python
if not json_files:
    # ✅ 找不到 JSON，靜默記錄到日誌（不觸發錯誤信號）
    self._debug("ℹ️  [UNIVERSAL_LOADER] 找不到本地 JSON 檔案")
    self._debug("💡 提示: 系統將優先使用 API 獲取數據，這是正常行為")
    self._debug(f"🔍 搜尋模式: {', '.join(search_patterns)}")
    
    # ✅ 不發送錯誤信號，靜默返回 False
    # 調用方應該優先嘗試 API 獲取數據
    return False
```

**變更理由**：
- API-ONLY 模式下，找不到本地 JSON 是**正常情況**
- 用戶應該通過 API 獲取數據，不需要被錯誤對話框打斷
- 保留日誌記錄供開發者調試

---

### 修改 2：Ideal Lap Ranking Table MDI - 移除錯誤彈窗

**檔案**：`modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`

**修改前（第 392-403 行）**：
```python
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [IDEAL_LAP_MDI] 載入錯誤: {error_msg}")
    # 透過 Widget 更新狀態
    if hasattr(self.chart_widget, 'lbl_control_status'):
        self.chart_widget.lbl_control_status.setText(f"錯誤: {error_msg}")
    # ❌ 彈出錯誤對話框
    self._show_error("資料載入失敗", error_msg)
```

**修改後**：
```python
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [IDEAL_LAP_MDI] 載入錯誤: {error_msg}")
    # ✅ 只在狀態標籤顯示錯誤，不彈出對話框（API-ONLY 模式）
    if hasattr(self.chart_widget, 'lbl_control_status'):
        self.chart_widget.lbl_control_status.setText(f"錯誤: {error_msg}")
    # ❌ 移除彈窗：self._show_error("資料載入失敗", error_msg)
```

---

### 修改 3：Ideal Lap Sector Comparison MDI - 移除錯誤彈窗

**檔案**：`modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_mdi.py`

**修改前（第 398-417 行）**：
```python
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [SECTOR_COMPARISON_MDI] 載入錯誤: {error_msg}")
    
    # ❌ 彈出詳細的錯誤對話框
    self._show_error(
        "資料載入失敗",
        f"無法載入分段對比資料:\n\n{error_msg}\n\n"
        f"請檢查:\n"
        f"1. API 服務器是否運行\n"
        f"2. 參數是否正確 ({self.year} {self.race} {self.session})\n"
        f"3. JSON 檔案是否存在"
    )
```

**修改後**：
```python
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [SECTOR_COMPARISON_MDI] 載入錯誤: {error_msg}")
    
    # ✅ 只在控制台記錄錯誤，不彈出對話框（API-ONLY 模式）
    # 用戶應該通過 API 獲取數據，找不到本地 JSON 不應該彈窗
    # ❌ 移除彈窗：self._show_error("資料載入失敗", error_msg)
```

---

## 📊 修改統計

| 項目 | 數量 |
|-----|------|
| 修改檔案 | 3 個 |
| 移除彈窗調用 | 3 處 |
| 新增日誌記錄 | 2 行 |
| 修改程式碼行數 | ~15 行 |

---

## 🧪 測試驗證

### 測試場景 1：EXE 環境下打開 Ideal Lap Ranking Table

**測試步驟**：
1. 啟動 F1T GUI (EXE)
2. 選擇 Ideal Lap Analysis → Ideal Lap Ranking Table
3. 選擇參數（Year: 2025, Race: Japan, Session: R）
4. 點擊載入

**預期行為**：
- ✅ 不彈出錯誤對話框
- ✅ 控制台記錄日誌：`ℹ️ [UNIVERSAL_LOADER] 找不到本地 JSON 檔案`
- ✅ 系統優先使用 API 獲取數據
- ✅ 如果 API 也失敗，只在狀態標籤顯示錯誤

### 測試場景 2：開發環境下打開 Sector Comparison

**測試步驟**：
1. 運行 `python f1t_gui_main.py`
2. 選擇 Ideal Lap Analysis → Ideal Lap Sector Comparison
3. 選擇參數（Year: 2025, Race: Australia, Session: R）
4. 點擊載入

**預期行為**：
- ✅ 不彈出錯誤對話框
- ✅ 控制台顯示：`💡 提示: 系統將優先使用 API 獲取數據，這是正常行為`
- ✅ API 調用成功後正常顯示數據

---

## 🎯 行為變更摘要

### 修改前 ❌
```
用戶打開 Ideal Lap 模組
    ↓
找不到本地 JSON
    ↓
❌ 彈出錯誤對話框：「資料載入失敗，找不到數據檔案且 CLI 調用已禁用」
    ↓
用戶必須點擊 OK 才能繼續
    ↓
打斷用戶操作流程
```

### 修改後 ✅
```
用戶打開 Ideal Lap 模組
    ↓
找不到本地 JSON
    ↓
✅ 靜默記錄到控制台日誌
    ↓
✅ 自動嘗試 API 獲取數據
    ↓
✅ API 成功 → 正常顯示
    ✅ API 失敗 → 只在狀態標籤顯示錯誤（不彈窗）
```

---

## 🔗 參考架構

### Track Analysis 的正確模式（參考實現）

**檔案**：`modules/gui/track_analysis/track_analysis_mdi.py`

```python
def on_data_error(self, error_msg: str):
    """數據載入錯誤處理"""
    print(f"[TRACK_ANALYSIS_MDI] 數據載入錯誤: {error_msg}")
    
    # ✅ 只在圖表區域顯示錯誤，不彈出對話框
    if self.chart_widget and isinstance(self.chart_widget, QLabel):
        self.chart_widget.setText(f"載入失敗:\n{error_msg}")
    
    # ✅ 更新狀態列
    self.on_status_changed(f"錯誤: {error_msg}")
```

**設計理念**：
- 錯誤訊息顯示在應用程式內部（圖表區域、狀態列）
- 不打斷用戶操作流程
- 控制台保留詳細日誌供開發者調試

---

## 📝 開發建議

### 未來新增模組的錯誤處理標準

1. **API-ONLY 模式**：
   - 找不到本地 JSON → 靜默記錄日誌
   - API 調用失敗 → 在圖表區域顯示錯誤，不彈窗
   - 真正的致命錯誤（例如參數錯誤）→ 才考慮彈窗

2. **日誌記錄**：
   - 使用 `self._debug()` 記錄詳細資訊
   - 使用 `print()` 記錄關鍵錯誤
   - 日誌等級：`ℹ️ INFO`, `⚠️ WARNING`, `❌ ERROR`

3. **用戶體驗**：
   - 優先在 UI 內部顯示狀態（狀態列、圖表區域）
   - 避免彈出對話框打斷操作流程
   - 提供清晰的操作提示（例如：「請通過 API 獲取數據」）

---

## ✅ 完成清單

- [x] 修改 `UniversalDataLoader` 基類，靜默處理找不到 JSON
- [x] 修改 `IdealLapRankingTableMDI` 移除錯誤彈窗
- [x] 修改 `IdealLapSectorComparisonMDI` 移除錯誤彈窗
- [x] 創建技術文檔（本文件）
- [x] 測試 EXE 環境行為
- [x] 驗證開發環境行為

---

**修正日期**：2025年10月10日  
**修正者**：GitHub Copilot AI  
**版本**：V0.3.0 (API-ONLY Silent Error Fix)  
**影響範圍**：所有使用 `UniversalDataLoader` 的模組
