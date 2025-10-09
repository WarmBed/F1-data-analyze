# 🔍 Lap Time Box Plot 重複實現深度分析報告

**日期**: 2025-10-04  
**分析對象**: Lap Time Box Plot 模組重複實現問題  
**調查結果**: 發現 3 個不同實現，但只有 1 個完整支援 System Settings

---

## 📊 發現的 3 個實現總覽

### 1️⃣ **新版本 - API 整合版**（lap_box_plot_analysis/）
```
modules/gui/lap_box_plot_analysis/
├── lap_box_plot_analysis_mdi.py (48,488 bytes, 2025-10-03)
├── lap_box_plot_chart_widget.py (24,409 bytes, 2025-10-02)
├── lap_box_plot_analysis_module.py (19,569 bytes, 2025-10-03)
└── __init__.py (1,136 bytes, 2025-10-03)
```

**特性**:
- ✅ 基於 UniversalAnalysisMDI 架構
- ✅ 完整 API 整合（LapTimeBoxPlotApiWorker）
- ✅ 75 秒 API 超時
- ✅ 完整 i18n 支援（core.gui_i18n）
- ❌ **不支援 System Settings 的 filter pit laps**

**System Settings 整合狀態**:
```python
# ❌ 沒有連接到 gui_settings_manager
# ❌ 沒有監聽 boxplot_settings_changed 信號
# ❌ 只有內部 filter_settings，無法從全域設定控制

# 內部過濾設定（寫死在初始化）
self.filter_settings = {
    'filter_pit_laps': True,        # 固定值
    'filter_outliers': True,         # 固定值
    'outlier_threshold': 1.5         # 固定值
}

# 只有控制面板內部的 checkbox，無法從 System Settings 控制
self.filter_pit_checkbox = QCheckBox(tr("filter_pit_laps", "過濾進站圈"))
```

**當前使用狀態**: ✅ **正在被 f1t_gui_main.py 使用**

---

### 2️⃣ **舊版本 - 完整 System Settings 整合**（driver_race/detailed_lap_analysis/）
```
modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py
(34,452 bytes, 2025-10-03)
```

**特性**:
- ✅ **完整支援 System Settings 的 filter pit laps**
- ✅ 連接到 gui_settings_manager
- ✅ 監聽 boxplot_settings_changed 信號
- ✅ 當 System Settings 改變時自動更新
- ❌ 沒有 API 整合（CLI 調用已禁用）
- ❌ 只能讀取本地 JSON 檔案

**System Settings 整合代碼**:
```python
# ✅ 完整的 System Settings 整合

# 1. 初始化時連接全域設定管理器
from core.gui_settings_manager import gui_settings_manager

self.settings_manager = gui_settings_manager
self.settings_manager.boxplot_settings_changed.connect(
    self._on_global_settings_changed
)

# 2. 套用全域設定
self._apply_boxplot_settings(self.settings_manager.get_boxplot_settings())

# 3. 當 System Settings 改變時自動更新
def _on_global_settings_changed(self, settings: Dict[str, Any]) -> None:
    """全域設定變更時更新顯示"""
    previous = (
        self.filter_pit_laps,
        self.filter_outliers,
        self.outlier_threshold,
    )
    self._apply_boxplot_settings(settings)
    
    current = (
        self.filter_pit_laps,
        self.filter_outliers,
        self.outlier_threshold,
    )
    
    # 設定改變時重新處理數據並更新顯示
    if previous != current and self.raw_data:
        self.processed_data = self._transform_data_for_display(self.raw_data)
        self._update_display(self.processed_data)

# 4. 套用設定方法
def _apply_boxplot_settings(self, settings: Dict[str, Any]) -> None:
    """套用全域箱型圖設定"""
    self.filter_pit_laps = settings.get('filter_pit_laps', True)
    self.filter_outliers = settings.get('filter_outliers', True)
    self.outlier_threshold = settings.get('outlier_threshold', 1.5)
    self._update_settings_summary()
```

**當前使用狀態**: ❌ **已被新版取代，但檔案仍存在**

---

### 3️⃣ **相容性包裝器**（driverLap_analysis/）
```
modules/gui/driverLap_analysis/laptime_boxplot_widget.py
(223 bytes, 2025-10-02)
```

**內容**:
```python
"""Compatibility wrapper for Lap Time Box Plot Widget"""

from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
    LapTimeBoxPlotWidget,
)
```

**功能**: 單純重定向到舊版本  
**當前使用狀態**: ❌ **沒有任何程式碼使用此包裝器**

---

## 🎯 關鍵發現：System Settings Filter Pit Laps 控制問題

### ❌ 新版本（當前使用）**不受** System Settings 控制

**問題**:
```python
# modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py

# ❌ 沒有導入 gui_settings_manager
# from core.gui_settings_manager import gui_settings_manager  # 缺少！

# ❌ 沒有連接到全域設定信號
# self.settings_manager.boxplot_settings_changed.connect(...)  # 缺少！

# ❌ filter_settings 只是內部變數，無法從外部控制
self.filter_settings = {
    'filter_pit_laps': True,        # 永遠是 True
    'filter_outliers': True,
    'outlier_threshold': 1.5
}
```

**影響**:
- 用戶在 System Settings 中更改 "Filter pit laps" 設定
- 新版 Lap Box Plot 模組**不會**收到通知
- 過濾行為永遠使用初始化時的固定值

### ✅ 舊版本**受** System Settings 控制

**正確實現**:
```python
# modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py

# ✅ 導入並連接全域設定管理器
from core.gui_settings_manager import gui_settings_manager

self.settings_manager = gui_settings_manager
self.settings_manager.boxplot_settings_changed.connect(
    self._on_global_settings_changed  # ✅ 監聽設定變更
)

# ✅ 當 System Settings 改變時，自動重新處理數據
def _on_global_settings_changed(self, settings: Dict[str, Any]) -> None:
    # ... 更新 filter_pit_laps
    # ... 重新處理數據
    # ... 更新顯示
```

---

## 🔄 f1t_gui_main.py 當前使用狀況

### 當前導入（2025-10-03 修改）
```python
# f1t_gui_main.py line 7967-7968

from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
    LapTimeBoxPlotAnalysis,  # ← 使用新版（無 System Settings 整合）
)
```

### 之前的導入（已移除）
```python
# 舊版導入（已被替換）
from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
    LapTimeBoxPlotWidget,  # ← 舊版（有 System Settings 整合）
)
```

---

## 📋 System Settings Dialog 配置

**System Settings 提供的控制項**:
```python
# modules/gui/settings/system_settings_dialog.py

self.filter_pit_checkbox = QCheckBox(tr("boxplot_filter_pit", "Filter pit laps"))
# ↓
# 通過 gui_settings_manager 發送信號
self.settings_manager.boxplot_settings_changed.emit({
    'filter_pit_laps': self.filter_pit_checkbox.isChecked(),
    'filter_outliers': self.filter_outliers_checkbox.isChecked(),
    'outlier_threshold': float(self.outlier_threshold_spinbox.value()),
})
```

**誰在監聽這個信號？**
- ✅ **舊版本**: `laptime_boxplot_widget.py` 正確監聽並響應
- ❌ **新版本**: `lap_box_plot_analysis_mdi.py` 完全沒有連接

---

## 🐛 問題總結

### 目前狀況
1. **新版本**（API 整合）正在被 `f1t_gui_main.py` 使用
2. **新版本不支援 System Settings 的 filter pit laps 控制**
3. **舊版本支援 System Settings，但已被棄用**
4. **相容性包裝器**指向舊版本，但無人使用

### 用戶體驗問題
```
用戶操作流程：
1. 用戶打開 System Settings
2. 取消勾選 "Filter pit laps"
3. 點擊 OK
4. ❌ Lap Box Plot 模組不會更新（因為新版本沒有監聽信號）
5. 圖表仍然過濾進站圈（filter_pit_laps 永遠是 True）
```

---

## 🛠️ 解決方案建議

### 方案 A：為新版本添加 System Settings 整合（推薦）

**優點**:
- 保持 API 整合的優勢
- 修復 System Settings 控制問題
- 符合系統統一架構

**需要修改**:
```python
# modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py

# 1. 添加導入
from core.gui_settings_manager import gui_settings_manager

# 2. 在 LapTimeBoxPlotDataManager.__init__() 中連接信號
self.settings_manager = gui_settings_manager
self.settings_manager.boxplot_settings_changed.connect(
    self._on_global_settings_changed
)

# 3. 初始化時套用全域設定
self._apply_boxplot_settings(self.settings_manager.get_boxplot_settings())

# 4. 實現信號處理方法
def _on_global_settings_changed(self, settings: Dict[str, Any]) -> None:
    """全域設定變更時更新"""
    self.update_filter_settings(settings)
    # 觸發數據重新處理和圖表更新
```

### 方案 B：暫時切回舊版本

**優點**:
- System Settings 立即可用
- 無需修改代碼

**缺點**:
- 失去 API 整合功能
- 只能使用本地 JSON
- 不符合現代化方向

### 方案 C：保留兩個版本，根據需求切換

**不推薦**：會造成維護混亂

---

## 🎯 建議行動方案

### 立即執行（修復新版本）
1. ✅ 在新版本中添加 `gui_settings_manager` 整合
2. ✅ 實現 `_on_global_settings_changed()` 方法
3. ✅ 測試 System Settings 控制是否正常
4. ✅ 驗證 API 功能仍然正常

### 後續清理
5. ✅ 移除舊版本到 `刪除資料/`
6. ✅ 刪除相容性包裝器
7. ✅ 更新文檔說明

---

## 📊 檔案使用狀況統計

### 程式碼引用分析
```powershell
# 搜尋結果：
grep "from.*driver_race\.detailed_lap_analysis\.laptime_boxplot"

結果：只有以下非程式碼檔案引用舊版本：
- LAPTIME_BOXPLOT_API_STATUS_REPORT.md（文檔）
- LAPTIME_BOXPLOT_API_FIX_COMPLETE.md（文檔）
- laptime_boxplot_widget.py（相容性包裝器，223 bytes）

✅ 沒有任何實際 Python 程式碼使用舊版本或包裝器
```

### f1t_gui_main.py 引用
```python
# ✅ 唯一的引用點（line 7967）
from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
    LapTimeBoxPlotAnalysis,
)
```

---

## 📝 結論

**回答問題：「是不是有兩個？」**

實際上有 **3 個實現**：
1. **新版本**（lap_box_plot_analysis/）- 正在使用，但**缺少 System Settings 整合**
2. **舊版本**（driver_race/detailed_lap_analysis/）- 已棄用，但**有完整 System Settings 整合**
3. **相容性包裝器**（driverLap_analysis/）- 無人使用

**關鍵問題**：
- ✅ 新版本有 API 整合
- ❌ 新版本**不受 System Settings 的 filter pit laps 控制**
- ✅ 舊版本受 System Settings 控制
- ❌ 舊版本沒有 API 整合

**建議**：修復新版本，添加 System Settings 整合，然後移除舊版本和包裝器。

---

**報告生成**: 2025-10-04  
**調查者**: GitHub Copilot  
**狀態**: ⚠️ 需要修復新版本的 System Settings 整合
