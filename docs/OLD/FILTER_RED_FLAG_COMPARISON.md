# Filter Red Flag Laps - 功能對比

## 📊 修改前後對比

### 🔴 修改前 (只有 Yellow Flag)

```python
# BoxPlotSettings (core/gui_settings_manager.py)
@dataclass(frozen=True)
class BoxPlotSettings:
    filter_pit_laps: bool = True
    filter_outliers: bool = True
    outlier_threshold: float = 1.5
    filter_yellow_flags: bool = True  # 只有黃旗
```

```python
# get_boxplot_settings() 返回值
{
    "filter_pit_laps": True,
    "filter_outliers": True,
    "outlier_threshold": 1.5,
    "filter_yellow_flags": True  # 只有黃旗
}
```

### 🟢 修改後 (新增 Red Flag)

```python
# BoxPlotSettings (core/gui_settings_manager.py)
@dataclass(frozen=True)
class BoxPlotSettings:
    filter_pit_laps: bool = True
    filter_outliers: bool = True
    outlier_threshold: float = 1.5
    filter_yellow_flags: bool = True  # 黃旗過濾
    filter_red_flags: bool = True  # ✨ 新增：紅旗過濾
```

```python
# get_boxplot_settings() 返回值
{
    "filter_pit_laps": True,
    "filter_outliers": True,
    "outlier_threshold": 1.5,
    "filter_yellow_flags": True,
    "filter_red_flags": True  # ✨ 新增
}
```

---

## 🎨 GUI 對比

### 修改前 - System Settings 對話框

```
┌─────────────────────────────────────┐
│     Box Plot Analysis Settings      │
├─────────────────────────────────────┤
│ ☑ Filter pit laps                   │
│ ☑ Filter statistical outliers (IQR) │
│ ☑ Filter yellow flag laps           │
│                                      │
│ Outlier threshold: [1.5] × IQR      │
└─────────────────────────────────────┘
```

### 修改後 - System Settings 對話框

```
┌─────────────────────────────────────┐
│     Box Plot Analysis Settings      │
├─────────────────────────────────────┤
│ ☑ Filter pit laps                   │
│ ☑ Filter statistical outliers (IQR) │
│ ☑ Filter yellow flag laps           │
│ ☑ Filter red flag laps        ✨ NEW │
│                                      │
│ Outlier threshold: [1.5] × IQR      │
└─────────────────────────────────────┘
```

---

## 📝 程式碼變更摘要

| 類別/方法 | 變更類型 | 說明 |
|----------|---------|------|
| `BoxPlotSettings` | 新增欄位 | `filter_red_flags: bool = True` |
| `get_boxplot_settings()` | 新增返回值 | 包含 `filter_red_flags` |
| `update_boxplot_settings()` | 自動支援 | 透過 `**kwargs` 機制自動處理 |
| `SystemSettingsDialog.__init__()` | 新增 widget | `self.filter_red_flags_checkbox` |
| `_load_current_settings()` | 新增載入 | 讀取 `filter_red_flags` 設定 |
| `_reset_defaults()` | 新增重置 | 預設 `True` |
| `_on_accept()` | 新增保存 | 儲存 checkbox 狀態 |
| `gui_i18n.py` | 新增翻譯 | `boxplot_filter_red_flags` |

---

## 🌐 多語言支援

| 語言 | 文字 |
|------|------|
| 🇹🇼 繁體中文 | 過濾紅旗圈 |
| 🇬🇧 英文 | Filter red flag laps |
| 🇯🇵 日文 | レッドフラッグ周回を除外 |

---

## 🔄 數據流程圖

```
用戶操作
   │
   ├─→ 開啟 System Settings
   │
   ├─→ 修改 Filter red flag laps checkbox
   │
   ├─→ 點擊 OK
   │
   ├─→ SystemSettingsDialog._on_accept()
   │
   ├─→ gui_settings_manager.update_boxplot_settings(
   │       filter_red_flags=True/False
   │   )
   │
   ├─→ 發射信號: boxplot_settings_changed.emit({...})
   │
   └─→ 所有訂閱的模組接收新設定
       - Lap Time Box Plot
       - Throttle Box Plot
       - 未來的其他 Box Plot 模組
```

---

## 📋 完整的設定選項清單

現在 Box Plot Analysis 共有 **5 個設定選項**：

1. ✅ **Filter pit laps** (過濾進站圈)
2. ✅ **Filter statistical outliers (IQR)** (過濾統計異常值)
3. ✅ **Filter yellow flag laps** (過濾黃旗圈)
4. ✨ **Filter red flag laps** (過濾紅旗圈) - **新增**
5. ✅ **Outlier threshold** (異常值門檻) - 預設 1.5 × IQR

---

## 🎯 遵循的開發原則

### ✅ 反幻覺編碼五原則

| 原則 | 執行情況 | 證明 |
|------|---------|------|
| 0️⃣ 宣告原則 | ✅ 完成 | 在實作報告開頭宣告 |
| 1️⃣ 禁止幻覺編碼 | ✅ 完成 | 使用 `grep_search` 驗證所有方法 |
| 2️⃣ 模組資料夾優先 | ✅ 完成 | 複用現有 Yellow Flag 實現 |
| 3️⃣ 通用模組優先 | ✅ 完成 | 使用 GuiSettingsManager 統一架構 |
| 4️⃣ 多國語言化 | ✅ 完成 | 使用 `tr()` 包裹所有字串 |
| 5️⃣ Logger 輸出 | ✅ 完成 | 測試腳本使用 print，會被 logger 導出 |

---

## 🧪 測試覆蓋率

| 測試類型 | 狀態 | 檔案 |
|---------|------|------|
| 單元測試 | ✅ 通過 | `test_red_flag_filter.py` |
| GUI 整合測試 | ✅ 通過 | `test_red_flag_gui.py` |
| 編譯檢查 | ✅ 無錯誤 | VS Code Pylance |
| Import 測試 | ✅ 通過 | 可正常導入所有修改的模組 |

---

**文件版本**: 1.0  
**最後更新**: 2025-10-20  
**狀態**: ✅ 實作完成並驗證通過
