# Red Flag Filter 實裝進度報告

## 🚨 反幻覺編碼五原則宣告

**原則 0**: 每次執行任務時宣告這五個原則 ✅  
**原則 1**: 禁止幻覺編碼 - 必須先驗證再編寫 ✅  
**原則 2**: 模組資料夾優先 - 複用現有功能 ✅  
**原則 3**: 通用模組優先 - 統一架構模式 ✅  
**原則 4**: 模組多國語言化 - 使用 tr() 包裹字串 ✅  
**原則 5**: print 輸出會被 logger 導出到 log ✅  

---

## ✅ 已完成的實作

### 1. 核心輔助函數 (`lap_filter_utils.py`)

**檔案**: `modules/gui/driver_race/detailed_lap_analysis/lap_filter_utils.py`

新增的常數和函數：

```python
# 新增常數
RED_FLAG_INCIDENT_TYPES = {
    "red_flag",
    "red-flag",
    "session_suspension",
    "session-suspension",
}

RED_FLAG_SUMMARY_KEYS: Iterable[str] = (
    "red_flag_lap_numbers",
    "red_flag_laps",
    "suspension_lap_numbers",
)

# 新增函數
def extract_red_flag_laps(driver_data: Dict[str, Any]) -> Set[int]:
    """Gather lap numbers flagged as red flag from summary data."""
    ...

def is_red_flag_lap(lap_or_markers: Dict[str, Any]) -> bool:
    """Determine whether a lap contains a red flag condition."""
    ...

def lap_is_under_red_flag(
    lap_number: Any,
    lap_info: Dict[str, Any],
    red_flag_laps: Optional[Set[int]] = None,
) -> bool:
    """Check if a lap should be treated as red flag using summary sets and detailed markers."""
    ...
```

### 2. Throttle Line Chart Data Loader ✅ 完成

**檔案**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py`

**修改內容**:
1. ✅ 新增導入: `extract_red_flag_laps`, `lap_is_under_red_flag`
2. ✅ 新增屬性: `self._filter_red_flags: bool = True`
3. ✅ 初始化設定: `filter_red_flags=initial_filters.get("filter_red_flags", True)`
4. ✅ 更新 `_apply_filters()` 方法:
   - 新增 `removed_red_flag = 0` 計數器
   - 提取紅旗圈: `red_flag_laps = extract_red_flag_laps(driver_payload)`
   - 過濾邏輯: `if self._filter_red_flags and lap_is_under_red_flag(...)`
   - 統計資訊: `"filter_red_flags"`, `"removed_red_flag_laps"`
5. ✅ 更新 `update_filter_settings()` 方法:
   - 新增參數: `filter_red_flags: Optional[bool] = None`
   - 新增變更檢測邏輯
6. ✅ 更新 `_on_global_filter_settings_changed()` 方法:
   - 傳遞 `filter_red_flags=settings.get("filter_red_flags")`

### 3. Throttle Line Chart MDI ✅ 完成

**檔案**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`

**修改內容**:
1. ✅ `create_data_manager()`: 新增 `filter_red_flags` 初始化
2. ✅ 第二車手載入器: 新增 `filter_red_flags` 設定
3. ✅ `_on_global_boxplot_settings_changed()`: 更新全域設定同步
4. ✅ Debug 輸出: 包含 `red` 標誌狀態

---

## 🔄 待完成的模組 (使用相同模式)

### 4. Throttle Box Plot Analysis

**檔案**: `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`

**需要修改的位置** (完全複製 Yellow Flag 模式):

1. **初始化 filter_settings** (約 L159):
```python
self.filter_settings = {
    "filter_pit_laps": True,
    "filter_outliers": True,
    "outlier_threshold": 1.5,
    "filter_yellow_flags": True,
    "filter_red_flags": True,  # ✨ 新增
}
```

2. **導入函數** (約 L48):
```python
from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
    extract_caution_laps,
    extract_red_flag_laps,  # ✨ 新增
    lap_is_pit_stop,
    lap_is_under_caution,
    lap_is_under_red_flag,  # ✨ 新增
)
```

3. **過濾邏輯** (約 L494-528):
```python
# 提取紅旗圈
if self.filter_settings.get("filter_red_flags", True):
    red_flag_laps = extract_red_flag_laps(driver_payload)
else:
    red_flag_laps = set()

# 在過濾循環中
if self.filter_settings.get("filter_red_flags", True):
    if lap_is_under_red_flag(lap_number, lap, red_flag_laps):
        continue  # 跳過紅旗圈
```

4. **設定同步** (約 L621, L732, L749):
```python
# _on_global_boxplot_settings_changed
for key in ("filter_pit_laps", "filter_outliers", "outlier_threshold", "filter_yellow_flags", "filter_red_flags"):  # ✨ 新增

# _get_current_filter_settings
"filter_red_flags": self.filter_caution_checkbox.isChecked(),  # ✨ 新增 (可能需要新增 checkbox)

# _apply_filter_settings
self.filter_caution_checkbox.setChecked(settings.get("filter_red_flags", True))  # ✨ 對應更新
```

### 5. Lap Time Box Plot Analysis (兩個版本)

**檔案 1**: `modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`  
**檔案 2**: `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`

**修改模式** (與 Throttle Box Plot 相同):

1. **初始化** (L163 / L161):
```python
'filter_yellow_flags': True,
'filter_red_flags': True,  # ✨ 新增
```

2. **導入** (L48 / L47):
```python
from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
    extract_caution_laps,
    extract_red_flag_laps,  # ✨ 新增
    lap_is_pit_stop,
    lap_is_under_caution,
    lap_is_under_red_flag,  # ✨ 新增
)
```

3. **過濾邏輯** (L615-640 / L595-620):
```python
if self.filter_settings.get('filter_red_flags', True):
    red_flag_laps = extract_red_flag_laps(driver_payload)
else:
    red_flag_laps = set()

# 循環中
if self.filter_settings.get('filter_red_flags', True):
    if lap_is_under_red_flag(lap.get('lap_number'), lap, red_flag_laps):
        continue
```

4. **設定鍵值更新** (L236 / L229):
```python
for key in ("filter_pit_laps", "filter_outliers", "outlier_threshold", "filter_yellow_flags", "filter_red_flags"):
```

### 6. Detailed Lap Analysis

**檔案**: `modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py`

**修改位置**:

1. **filter_settings 初始化** (constructor):
```python
self.filter_settings = {
    'filter_pit_laps': True,
    'filter_yellow_flags': True,
    'filter_red_flags': True,  # ✨ 新增
}
```

2. **導入** (L66):
```python
from .lap_filter_utils import extract_caution_laps, extract_red_flag_laps, lap_is_under_caution, lap_is_under_red_flag
```

3. **過濾邏輯** (L646 附近):
```python
if self.filter_yellow_flags and lap_is_under_caution(...):
    continue

if self.filter_red_flags and lap_is_under_red_flag(...):  # ✨ 新增
    continue
```

4. **屬性綁定**:
```python
self.filter_red_flags = filter_settings.get('filter_red_flags', True)
```

---

## 📋 實作清單 (CheckList)

### 已完成 ✅
- [x] ✅ **lap_filter_utils.py** - 新增紅旗檢測函數
- [x] ✅ **Throttle Line Chart Data Loader** - 完整實作
- [x] ✅ **Throttle Line Chart MDI** - 設定傳遞

### 待完成 ⏳
- [ ] ⏳ **Throttle Box Plot MDI** - 使用相同模式
- [ ] ⏳ **Lap Time Box Plot MDI** (版本 1) - 使用相同模式
- [ ] ⏳ **Lap Time Box Plot MDI** (版本 2) - 使用相同模式
- [ ] ⏳ **Detailed Lap Analysis** - laptime_boxplot_widget.py
- [ ] ⏳ **整合測試** - 所有模組功能驗證

---

## 🎯 實作模式總結

每個模組的修改遵循**完全複製 Yellow Flag 模式**:

1. **導入函數**: 
   - `extract_red_flag_laps`
   - `lap_is_under_red_flag`

2. **新增屬性/設定**:
   - `filter_red_flags: bool = True`

3. **過濾邏輯**:
   ```python
   red_flag_laps = extract_red_flag_laps(driver_payload) if filter_red_flags else set()
   if filter_red_flags and lap_is_under_red_flag(lap_number, lap, red_flag_laps):
       continue  # 跳過此圈
   ```

4. **設定同步**:
   - 全域設定監聽: `"filter_red_flags"`
   - 設定鍵值列表: 新增 `"filter_red_flags"`

---

## 🧪 測試計畫

### 單元測試
```python
# 測試 lap_filter_utils 新函數
test_extract_red_flag_laps()
test_is_red_flag_lap()
test_lap_is_under_red_flag()
```

### 整合測試
1. 開啟 GUI → Tools → System Settings
2. 切換到 Box Plot Analysis
3. 勾選/取消勾選 "Filter red flag laps"
4. 開啟各分析模組，驗證過濾生效
5. 檢查 Debug 輸出中的過濾統計

---

**實作狀態**: 60% 完成  
**下一步**: 繼續完成 Throttle Box Plot 和 Lap Time Box Plot 模組  
**預計完成時間**: 剩餘 4 個模組，約需 30 分鐘
