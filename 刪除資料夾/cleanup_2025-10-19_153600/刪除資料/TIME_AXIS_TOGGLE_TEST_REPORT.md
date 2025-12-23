# 時間軸切換功能測試報告

## 測試日期
2025-10-11

## 測試目標
驗證速度分析模組的時間軸切換功能：當使用者勾選 "Use Time Axis" checkbox 時，X 軸標題從 "距離 (m)" / "Distance (m)" 更換為 "時間 (秒)" / "Time (s)"。

## 測試環境
- Python 版本: 3.13.5
- PyQt5: 已安裝
- 測試模組: `modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget`

## 測試結果

### ✅ 測試 1: 初始狀態
```
use_time_axis: False
x_axis_title: 'Distance (m)'
```
**結果**: PASS - 預設使用距離軸

### ✅ 測試 2: 設定包含時間數據的資料
```
time_axis_available: True
x_axis_title: 'Distance (m)'
```
**結果**: PASS - 時間軸可用，但仍顯示距離軸

### ✅ 測試 3: 切換到時間軸
```
success: True
use_time_axis: True
x_axis_title: 'Time (s)'
```
**結果**: PASS - 成功切換，X 軸標題正確更新為時間軸

### ✅ 測試 4: 切換回距離軸
```
success: True
use_time_axis: False
x_axis_title: 'Distance (m)'
```
**結果**: PASS - 成功切換回距離軸，X 軸標題正確恢復

## 關鍵代碼修改

### 1. 修正 `SpeedTelemetryChartWidget.__init__` (speed_analysis_chart_widget.py)
**問題**: 初始化時呼叫了兩次軸標題設定，導致衝突
```python
# 原本 (錯誤):
self.set_axis_titles(tr("distance_m", "距離 (m)"), tr("telemetry_speed", "速度 (km/h)"))
self._update_x_axis_title()  # 這會被上一行覆蓋

# 修正後:
self.y_axis_title = tr("telemetry_speed", "速度 (km/h)")
self._update_x_axis_title()  # 讓這個方法根據 use_time_axis 動態設定 X 軸
```

### 2. 增強日誌輸出 (speed_analysis_chart_widget.py)
```python
# SpeedTelemetryChartWidget.toggle_time_axis
if enabled and not self.time_axis_available:
    logger.warning("[SPEED_TIME_AXIS] Chart toggle skipped -> no time axis data available")
    return False

logger.info(
    "[SPEED_TIME_AXIS] Chart toggle result -> success=%s, new_mode=%s, x_title=%s",
    result,
    self.use_time_axis,
    getattr(self, "x_axis_title", None),
)
```

### 3. 新增即時提示反饋 (speed_analysis_chart_widget.py)
```python
def _show_axis_toggle_feedback(self, success: bool, enabled: bool, triggered_by_global: bool):
    """在軸模式切換後提供即時提示"""
    if success:
        message = tr("time_axis_switch_success_time" if enabled else "time_axis_switch_success_distance",
                    "已切換到時間軸" if enabled else "已切換回距離軸")
    else:
        message = tr("time_axis_switch_failed", "無法切換到時間軸，請檢查時間數據")
    
    QToolTip.showText(checkbox.mapToGlobal(checkbox.rect().center()), message, checkbox)
```

## 數據流程

```
使用者勾選 checkbox
    ↓
_on_time_axis_toggled(state)
    ↓
_perform_time_axis_toggle(enabled=True)
    ↓
chart_widget.toggle_time_axis(True)
    ↓
TelemetryChartWidgetBase.toggle_time_axis(True)
    ↓
_update_x_axis_title()  # 設定 x_axis_title = "Time (s)"
    ↓
_refresh_data_with_current_axis()  # 更新數據點 X 座標
    ↓
update()  # 觸發重繪
    ↓
paintEvent() → _draw_axis_titles()  # 繪製新的 X 軸標題
```

## 國際化支援
X 軸標題支援多語言：
- 中文: "時間 (秒)" / "距離 (公尺)"
- 英文: "Time (s)" / "Distance (m)"
- 日文: "時間 (秒)" / "距離 (m)"

來源: `core/gui_i18n.py` 的 `time_seconds` 和 `distance_meters` key

## 結論
✅ **所有測試通過** - 時間軸切換功能正常運作，X 軸標題正確更新。

## 測試腳本
- 完整測試: `test_time_axis_toggle.py`
- 簡化測試: `direct_test.py`
- 測試結果: `test_output_direct.txt`
