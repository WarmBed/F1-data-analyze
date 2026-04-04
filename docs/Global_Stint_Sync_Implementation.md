# Global Stint Sync 跨模組 Stint 選擇同步功能

> 版本: V0.15.1  
> 日期: 2026-01-19  
> 作者: F1T Team

## 概述

Global Stint Sync 是一個跨模組的 Stint 選擇同步機制，允許使用者在一個分析模組中選擇特定的 Stint（輪胎階段），並自動將該選擇同步到所有啟用同步功能的相關模組。

### 核心功能

- **跨模組同步**: 在一個模組選擇 ALB Stint 1，所有已連結的模組會同步更新
- **Session 過濾**: 只有顯示相同 Session（年份 + 賽事 + 場次）的模組會同步
- **雙向同步**: 任何已連結模組的變更都會廣播到其他模組
- **防迴圈機制**: 防止信號無限循環傳遞

---

## 架構設計

### 核心組件

```
┌─────────────────────────────────────────────────────────┐
│                  GlobalChartSyncSignal                   │
│                     (Singleton)                          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │     stint_selection_changed (pyqtSignal)         │    │
│  │     ↓                                            │    │
│  │  • selected_stints (List[Dict])                  │    │
│  │  • is_merge_mode (bool)                          │    │
│  │  • year, race, session (str)                     │    │
│  │  • source_module (str)                           │    │
│  └─────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Module A   │ │   Module B   │ │   Module C   │
    │ (Corner)     │ │ (Brake)      │ │ (Accel)      │
    │              │ │              │ │              │
    │ UniversalS.. │ │ UniversalS.. │ │ UniversalS.. │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 修改的檔案

### Phase 1: GlobalChartSyncSignal 擴展

**檔案**: `modules/gui/base/global_chart_sync_signal.py`

新增內容:
- `stint_selection_changed` 信號
- `emit_stint_selection_changed()` 方法
- `get_current_stint_selection()` 方法
- `is_same_session()` 驗證方法
- `_current_stint_selection` 狀態存儲

### Phase 2: UniversalStintSelector 擴展

**檔案**: `modules/gui/base/universal_stint_selector.py`

新增內容:
- `__init__` 新增 `module_id` 參數
- `_global_sync_enabled` 屬性
- `set_session_info()` 設置 Session 資訊
- `enable_global_sync()` 啟用/停用同步
- `_on_global_stint_selection_changed()` 處理外部同步
- `apply_external_selection()` 應用外部選擇
- `_emit_global_sync()` 發射同步信號
- `_emit_selection_changed()` 修改以觸發全局同步

### Phase 3: MDI 模組整合

已整合的模組:

| 模組 | 檔案 | module_id |
|------|------|-----------|
| Corner Performance | `all_drivers/corner_performance/all_drivers_corner_performance_mdi.py` | `corner_performance` |
| Brake Chart | `all_drivers/brake/brake_chart_mdi.py` | `brake_chart` |
| Acceleration Chart | `all_drivers/acceleration/acceleration_chart_mdi.py` | `acceleration_chart` |
| Lap Box Plot (lap_analysis) | `lap_analysis/lap_box_plot/lap_box_plot_analysis_mdi.py` | `lap_boxplot_lap_analysis` |
| Lap Box Plot (driver_race) | `driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py` | `lap_boxplot_driver_race` |
| Throttle Box Plot | `lap_analysis/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py` | `throttle_boxplot` |
| Pedal Behavior | `lap_analysis/pedal_behavior_analysis/pedal_behavior_analysis_mdi.py` | `pedal_behavior` |

**待整合模組**:
- Long Run MDI

---

## 使用方式

### 在 MDI 模組中啟用 Global Sync

```python
# 1. 創建 UniversalStintSelector 時傳入 module_id
self.stint_selector = UniversalStintSelector(module_id="my_module_name")

# 2. 啟用全局同步
self.stint_selector.enable_global_sync(True)

# 3. 在數據載入後設置 Session 資訊
self.stint_selector.set_session_info(
    year=str(self.year),
    race=self.race,
    session=self.session
)
```

### 同步流程

1. 使用者在 Module A 選擇 Stint
2. `UniversalStintSelector._emit_selection_changed()` 被調用
3. 如果 `_global_sync_enabled = True`，調用 `_emit_global_sync()`
4. `GlobalChartSyncSignal.emit_stint_selection_changed()` 廣播信號
5. 所有訂閱的 `UniversalStintSelector` 收到信號
6. 各模組檢查:
   - 來源是否為自己（忽略）
   - 是否啟用同步
   - Session 是否匹配
7. 符合條件的模組調用 `apply_external_selection()` 更新

---

## Session 匹配邏輯

同步只在以下條件都滿足時發生:

```python
# GlobalChartSyncSignal.is_same_session()
return (
    self._current_stint_selection.get('year') == year and
    self._current_stint_selection.get('race') == race and
    self._current_stint_selection.get('session') == session
)
```

**範例**:
- Module A: 2025 Monaco FP2 ✓ 同步
- Module B: 2025 Monaco FP2 ✓ 同步
- Module C: 2025 Monaco Q  ✗ 不同步（不同 Session）

---

## 防迴圈機制

### 1. Source Module 檢查

```python
def _on_global_stint_selection_changed(self, ..., source: str):
    # 忽略自己發出的信號
    if source == self._module_id:
        return
```

### 2. External Apply Flag

```python
def apply_external_selection(self, ...):
    if self._is_applying_external:
        return  # 防止遞迴
    
    self._is_applying_external = True
    try:
        # 更新選擇...
    finally:
        self._is_applying_external = False
```

### 3. Block Signals

```python
def _emit_selection_changed(self):
    if self._block_signals:
        return
    # ...
```

---

## 信號格式

### stint_selection_changed 信號參數

```python
stint_selection_changed = pyqtSignal(list, bool, str, str, str, str)
# 參數:
#   selected_stints: List[Dict]  - 選中的 Stint 列表
#   is_merge_mode: bool          - 是否為合併模式
#   year: str                    - 年份
#   race: str                    - 賽事名稱
#   session: str                 - 場次
#   source: str                  - 發出信號的模組 ID
```

### selected_stints 結構

```python
[
    {
        'driver': 'VER',           # 車手代碼
        'stint_number': 1,         # Stint 編號
        'start_lap': 1,            # 起始圈
        'end_lap': 15,             # 結束圈
        'compound': 'MEDIUM'       # 輪胎類型
    },
    # ...
]
```

---

## 測試驗證

### 測試場景

1. **單向同步**: Module A 選擇 → Module B 更新
2. **雙向同步**: Module B 選擇 → Module A 更新
3. **Session 隔離**: 不同 Session 的模組不應同步
4. **Merge Mode 同步**: 合併模式狀態應同步
5. **全選/取消全選**: 批量操作應正確同步

### 驗證方法

```bash
# 啟動 GUI
python main.py

# 開啟多個支援 Stint 的模組（同一 Session）
# 1. Corner Performance
# 2. Brake Chart
# 3. Acceleration Chart

# 在任一模組選擇 Stint，觀察其他模組是否同步
```

---

## 日誌標籤

相關日誌可通過以下標籤過濾:

- `[GLOBAL_SYNC]` - GlobalChartSyncSignal 相關
- `[STINT_SELECTOR]` - UniversalStintSelector 相關

---

## 未來擴展

1. **Linkage 按鈕 UI**: 在標題列添加 🔗 按鈕控制 opt-in/opt-out
2. **更多模組整合**: Long Run, Lap Box Plot, Throttle Box Plot, Pedal Behavior
3. **選擇記憶**: 保存使用者的同步偏好設定
4. **視覺指示**: 顯示同步狀態的 UI 指示器
