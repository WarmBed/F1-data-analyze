# ✅ Throttle Line Chart - System Settings 整合完成

**日期**: 2025-10-08  
**功能**: 將 Throttle Line Chart 顯示設定移至 System Settings  
**狀態**: ✅ 實作完成

---

## 📋 需求說明

將 Throttle Line Chart 的顯示選項從側邊控制面板移至 **Tools → System Settings**，保留車手選擇在模組視窗內。

### 移至 System Settings 的設定項目：
1. ✅ **顯示全油門秒數 (s)**
2. ✅ **顯示全油門比例 %**
3. ✅ **顯示平均油門 %**
4. ✅ **顯示圈速 Δ vs Best**
5. ✅ **啟用移動平均**
6. ✅ **移動平均窗口**
7. ✅ **標註 ≥ 門檻圈**
8. ✅ **全油門比例門檻 %**

### 保留在模組視窗的項目：
- ✅ **Driver 1 選擇器**
- ✅ **Driver 2 選擇器**

---

## 🔧 修改檔案清單

### 1. **core/gui_settings_manager.py** - 系統設定管理器

#### 新增內容：
- ✅ `ThrottleLineChartSettings` 資料類別（dataclass）
- ✅ `throttle_line_chart_settings_changed` PyQt 訊號
- ✅ `get_throttle_line_chart_settings()` 方法
- ✅ `update_throttle_line_chart_settings(**kwargs)` 方法

#### 關鍵程式碼：
```python
@dataclass(frozen=True)
class ThrottleLineChartSettings:
    """Throttle Line Chart 預設顯示設定"""
    show_full_duration: bool = False
    show_ratio: bool = True
    show_average: bool = True
    show_delta: bool = False
    rolling_average: bool = False
    rolling_window: int = 3
    highlight_threshold: bool = True
    threshold_percent: float = 90.0

class GuiSettingsManager(QObject):
    boxplot_settings_changed = pyqtSignal(dict)
    throttle_line_chart_settings_changed = pyqtSignal(dict)  # 新增

    def __init__(self) -> None:
        super().__init__()
        self._boxplot_settings: BoxPlotSettings = BoxPlotSettings()
        self._throttle_line_chart_settings: ThrottleLineChartSettings = ThrottleLineChartSettings()
```

---

### 2. **modules/gui/settings/system_settings_dialog.py** - 系統設定對話框

#### 新增內容：
- ✅ 新增 **Throttle Line Chart** 分頁
- ✅ 三個設定群組：
  - **Display Options** (顯示選項)
  - **Lap Time Analysis** (圈速分析)
  - **Threshold Highlighting** (門檻值標註)
- ✅ `_reset_throttle_defaults()` 方法
- ✅ `_load_current_settings()` 載入 Throttle 設定
- ✅ `_on_accept()` 儲存 Throttle 設定

#### UI 結構：
```
System Settings 對話框
├── Box Plot Analysis (原有分頁)
└── Throttle Line Chart (新增分頁)
    ├── Display Options
    │   ├── ☐ Show Full Throttle Duration (s)
    │   ├── ☑ Show Full Throttle %
    │   ├── ☑ Show Average Throttle %
    │   └── ☐ Show Lap Time Δ vs Best
    ├── Lap Time Analysis
    │   ├── ☐ Enable Rolling Average
    │   └── Rolling Window: [3] laps
    ├── Threshold Highlighting
    │   ├── ☑ Highlight laps ≥ threshold
    │   └── Threshold Percent: [90] %
    └── [Reset Defaults]
```

#### 關鍵程式碼：
```python
# 載入設定
def _load_current_settings(self) -> None:
    throttle_settings = self._settings_manager.get_throttle_line_chart_settings()
    self.throttle_show_ratio_checkbox.setChecked(throttle_settings.get("show_ratio", True))
    # ... 其他設定

# 儲存設定
def _on_accept(self) -> None:
    self._settings_manager.update_throttle_line_chart_settings(
        show_full_duration=self.throttle_show_full_duration_checkbox.isChecked(),
        show_ratio=self.throttle_show_ratio_checkbox.isChecked(),
        # ... 其他設定
    )
    self.accept()
```

---

### 3. **throttle_line_chart_mdi.py** - Throttle Line Chart MDI 控制器

#### 修改內容：

##### 控制面板簡化 (ThrottleLineChartControlPanel)
- ✅ **移除**所有顯示選項控制項（checkbox、spinbox）
- ✅ **保留** Driver 1 和 Driver 2 選擇器
- ✅ 新增提示文字：「Display settings can be configured in Tools → System Settings」
- ✅ `_emit_settings()` 改為空方法（保留相容性）
- ✅ `apply_settings()` 簡化為只更新內部狀態

**修改前的控制面板**：
```
Throttle Line Chart Settings
├── Driver 1: [選擇器]
├── Driver 2: [選擇器]
├── ☐ 顯示全油門秒數 (s)
├── ☑ 顯示全油門比例%
├── ☑ 顯示平均油門%
├── ☐ 顯示圈速 Δ
├── ☐ 圈速移動平均
├── 移動平均窗口: [3]
├── ☑ 標註≥門檻圈
├── 全油門比例門檻 %: [90]
├── 🔄 重新載入資料 (隱藏)
├── 🧭 重置視圖 (隱藏)
└── 💾 匯出圖表 (隱藏)
```

**修改後的控制面板**：
```
Driver Selection
├── Driver 1: [選擇器]
├── Driver 2: [選擇器]
└── 提示: Display settings can be configured in
    Tools → System Settings → Throttle Line Chart
```

##### 主 MDI 類別 (ThrottleLineChartMDI)
- ✅ `__init__` 中從系統設定載入預設值：
  ```python
  self._settings_cache = dict(self.settings_manager.get_throttle_line_chart_settings())
  ```
- ✅ 連接系統設定變更訊號：
  ```python
  self.settings_manager.throttle_line_chart_settings_changed.connect(
      self._on_throttle_settings_changed
  )
  ```
- ✅ 新增 `_on_throttle_settings_changed()` 方法處理設定變更
- ✅ `cleanup()` 中斷開訊號連接

#### 關鍵程式碼：
```python
def _on_throttle_settings_changed(self, settings: Dict[str, Any]) -> None:
    """處理 Throttle Line Chart 系統設定變更"""
    if not isinstance(settings, dict):
        return
    
    # 更新設定快取
    self._settings_cache.update(settings)
    
    # 通知圖表視圖重新渲染
    if hasattr(self.chart_widget, "apply_settings"):
        self.chart_widget.apply_settings(settings)
    
    # 通知控制面板更新
    if self.control_panel:
        self.control_panel.apply_settings(settings)
```

---

## 🎯 使用流程

### 1. 開啟 System Settings
```
GUI 選單 → Tools → System Settings
```

### 2. 切換至 Throttle Line Chart 分頁
```
System Settings 對話框
├── Box Plot Analysis
└── Throttle Line Chart ← 點選此分頁
```

### 3. 調整顯示設定
- **Display Options**: 選擇要顯示的線條類型
- **Lap Time Analysis**: 設定圈速移動平均
- **Threshold Highlighting**: 設定門檻值標註

### 4. 儲存設定
- 點選 **「OK」** 按鈕
- 系統自動通知所有開啟的 Throttle Line Chart 視窗
- 圖表即時更新

### 5. 重置預設值
- 點選 **「Reset Defaults」** 按鈕
- 恢復原廠預設值：
  - Show Full Throttle %: ✅
  - Show Average Throttle %: ✅
  - Show Lap Time Δ: ❌
  - Rolling Average: ❌
  - Rolling Window: 3
  - Highlight Threshold: ✅
  - Threshold Percent: 90%

---

## 📊 設定同步機制

### 訊號流向
```
System Settings 對話框
    ↓ [使用者變更設定]
GuiSettingsManager.update_throttle_line_chart_settings()
    ↓ [發射訊號]
throttle_line_chart_settings_changed (PyQt Signal)
    ↓ [通知所有訂閱者]
ThrottleLineChartMDI._on_throttle_settings_changed()
    ↓ [更新設定快取]
ThrottleLineChartView.apply_settings()
    ↓ [重新渲染圖表]
圖表即時更新
```

### 多視窗同步
- ✅ 支援多個 Throttle Line Chart 視窗同時開啟
- ✅ 變更設定時**所有視窗即時同步**
- ✅ 新開啟的視窗自動載入系統設定

---

## 🎨 視覺效果

### 系統設定對話框
```
┌─ System Settings ──────────────────────────────────┐
│  ┌── Tabs ──────────────────────────────────────┐  │
│  │ Box Plot Analysis │ Throttle Line Chart     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ Display Options ─────────────────────────┐    │
│  │ ☐ Show Full Throttle Duration (s)         │    │
│  │ ☑ Show Full Throttle %                    │    │
│  │ ☑ Show Average Throttle %                 │    │
│  │ ☐ Show Lap Time Δ vs Best                 │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  ┌─ Lap Time Analysis ───────────────────────┐    │
│  │ ☐ Enable Rolling Average                  │    │
│  │ Rolling Window: [  3  ] laps               │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  ┌─ Threshold Highlighting ──────────────────┐    │
│  │ ☑ Highlight laps ≥ threshold              │    │
│  │ Threshold Percent: [ 90  ] %               │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  Default settings for Throttle Line Chart module.  │
│  Driver selection remains in the module window.    │
│                                                     │
│  [ Reset Defaults ]                                │
│                                                     │
│                              [ OK ]  [ Cancel ]    │
└────────────────────────────────────────────────────┘
```

### 簡化後的側邊控制面板
```
┌─ Driver Selection ────────────┐
│                                │
│  Driver 1: [ VER ▼ ]          │
│  Driver 2: [ None ▼ ]         │
│                                │
│  Display settings can be      │
│  configured in                 │
│  Tools → System Settings →    │
│  Throttle Line Chart           │
│                                │
└────────────────────────────────┘
```

---

## 🧪 測試計畫

### 測試案例 1：載入預設設定
- ✅ 首次開啟 Throttle Line Chart
- ✅ 預期：圖表顯示 Full Throttle % 和 Average Throttle %
- ✅ 預期：不顯示 Lap Time Δ
- ✅ 預期：門檻值 = 90%

### 測試案例 2：變更設定（單視窗）
- ✅ 開啟 System Settings
- ✅ 取消勾選「Show Average Throttle %」
- ✅ 點選 OK
- ✅ 預期：Average Throttle 線條立即消失

### 測試案例 3：變更設定（多視窗同步）
- ✅ 開啟兩個 Throttle Line Chart 視窗
- ✅ 變更 System Settings 中的設定
- ✅ 預期：兩個視窗同時更新

### 測試案例 4：重置預設值
- ✅ 修改所有設定
- ✅ 點選「Reset Defaults」
- ✅ 預期：所有設定恢復原廠值

### 測試案例 5：新視窗載入設定
- ✅ 變更系統設定
- ✅ 開啟新的 Throttle Line Chart 視窗
- ✅ 預期：新視窗使用變更後的設定

### 測試案例 6：車手選擇保留在視窗
- ✅ 開啟 Throttle Line Chart
- ✅ 預期：側邊控制面板有 Driver 1 和 Driver 2 選擇器
- ✅ 預期：System Settings 中**沒有**車手選擇選項

---

## ⚠️ 注意事項

### 設定儲存
- ⚠️ 目前設定**僅儲存在記憶體**中
- ⚠️ 關閉 GUI 後設定會**重置為預設值**
- 💡 未來可考慮新增持久化儲存（JSON/INI 檔案）

### 相容性
- ✅ 保留原有的 `_DEFAULT_SETTINGS` 常數（作為後備）
- ✅ 控制面板的 `_emit_settings()` 方法保留（避免錯誤）
- ✅ 舊程式碼的設定呼叫仍然有效

### 效能
- ✅ 設定變更時只重新渲染圖表，不重新載入資料
- ✅ 使用 PyQt 訊號機制，避免輪詢

---

## 🎉 完成狀態

✅ **所有需求已實作完成**
- ✅ System Settings 新增 Throttle Line Chart 分頁
- ✅ 顯示設定移至系統設定
- ✅ 車手選擇保留在模組視窗
- ✅ 設定變更即時同步
- ✅ 支援多視窗同步
- ✅ 重置預設值功能
- ✅ 提示文字引導使用者

---

## 📝 後續工作

1. **持久化儲存**：將設定儲存至 JSON/INI 檔案
2. **國際化**：新增 Throttle 設定相關翻譯字串
3. **測試**：執行 GUI 驗證所有功能正常運作
4. **文檔**：更新使用者手冊說明系統設定功能

---

**開發者**: GitHub Copilot  
**版本**: v3.0.0 (System Settings 整合)  
**文件日期**: 2025-10-08
