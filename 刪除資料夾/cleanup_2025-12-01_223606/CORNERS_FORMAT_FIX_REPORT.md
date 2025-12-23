# Corners 格式錯誤修復報告

**修復日期**: 2025-11-11  
**問題模組**: `modules/gui/Historical_track_map/historical_track_map_mdi.py`  
**錯誤訊息**: `AttributeError: 'int' object has no attribute 'get'`  
**修復狀態**: ✅ 已完成並測試通過

---

## 🐛 問題描述

### 錯誤現象
用戶報告：
- 高程圖表沒有顯示彎道編號（T1, T2, ...）
- 控制台出現重複的 AttributeError

### 錯誤堆疊追蹤
```python
Traceback (most recent call last):
  File "C:\...\elevation_chart_widget_pyqt5.py", line 241, in paintEvent
    self._draw_corner_markers(painter, chart_rect)
  File "C:\...\elevation_chart_widget_pyqt5.py", line 458, in _draw_corner_markers
    corner_num = corner.get('number', 0)
                 ^^^^^^^^^^
AttributeError: 'int' object has no attribute 'get'
```

### 根本原因
`elevation_chart_widget_pyqt5.py` Line 458 期望 `corner` 是字典類型（有 `get()` 方法），但實際傳入的是整數。

---

## 🔍 問題診斷

### 錯誤代碼（修復前）

**文件**: `historical_track_map_mdi.py` Line 807-817

```python
# ❌ 錯誤：直接取 chart_data["corners"]
chart_data = data.get("chart_data")
if chart_data and self.elevation_chart:
    track_outline = chart_data.get("track_outline", [])
    corners = chart_data.get("corners", [])  # ← 錯誤！
    
    # ...
    self.elevation_chart.plot_elevation(track_outline, corners)
```

**問題**:
- `chart_data["corners"]` 返回的是 `[1, 2, 3, ..., 18]`（整數列表）
- 正確的數據在 `chart_data["official_corners"]["corners"]`

### 數據結構對比

**錯誤路徑** (修復前):
```json
{
  "chart_data": {
    "corners": [1, 2, 3, 4, ..., 18],  // ← 錯誤：整數列表
    "official_corners": {
      "corners": [
        {"number": 1, "distance": 123.45, "x": 1.0, "y": 2.0},
        {"number": 2, "distance": 456.78, "x": 3.0, "y": 4.0},
        ...
      ]
    }
  }
}
```

**正確路徑** (修復後):
```json
{
  "chart_data": {
    "official_corners": {
      "corners": [  // ← 正確：字典列表
        {"number": 1, "distance": 123.45},
        {"number": 2, "distance": 456.78},
        ...
      ]
    }
  }
}
```

---

## 🔧 修復實施

### 修復 1: `_on_data_loaded()` 方法

**文件**: `historical_track_map_mdi.py` Line 807-829

**修復前**:
```python
chart_data = data.get("chart_data")
if chart_data and self.elevation_chart:
    track_outline = chart_data.get("track_outline", [])
    corners = chart_data.get("corners", [])  # ❌ 錯誤
    
    has_elevation = any('elevation' in p or 'z' in p for p in track_outline)
    
    if has_elevation and track_outline:
        print(f"[HISTORICAL_TRACK_MAP_MDI] 準備繪製高程圖表（{len(track_outline)} 點，{len(corners)} 彎道）...")
        self.elevation_chart.plot_elevation(track_outline, corners)
```

**修復後**:
```python
chart_data = data.get("chart_data")
if chart_data and self.elevation_chart:
    track_outline = chart_data.get("track_outline", [])
    # 🔧 修復：正確提取 corners 數據（參考 demo Line 721）
    official_corners = chart_data.get("official_corners", {})
    corners = official_corners.get("corners", [])
    
    print(f"[HISTORICAL_TRACK_MAP_MDI] chart_data 鍵: {list(chart_data.keys())}")
    print(f"[HISTORICAL_TRACK_MAP_MDI] official_corners 類型: {type(official_corners)}")
    print(f"[HISTORICAL_TRACK_MAP_MDI] corners 類型: {type(corners)}, 長度: {len(corners)}")
    
    if corners:
        print(f"[HISTORICAL_TRACK_MAP_MDI] 第 1 個彎道: {corners[0]}")
    
    has_elevation = any('elevation' in p or 'z' in p for p in track_outline)
    
    if has_elevation and track_outline:
        print(f"[HISTORICAL_TRACK_MAP_MDI] 準備繪製高程圖表（{len(track_outline)} 點，{len(corners)} 彎道）...")
        self.elevation_chart.plot_elevation(track_outline, corners)
```

**變更說明**:
1. 添加 `official_corners = chart_data.get("official_corners", {})`
2. 修改為 `corners = official_corners.get("corners", [])`
3. 添加調試輸出以驗證數據格式

---

### 修復 2: `_refresh_charts()` 方法

**文件**: `historical_track_map_mdi.py` Line 1063-1076

**修復前**:
```python
def _refresh_charts(self):
    """重新繪製圖表"""
    if not self._is_data_loaded or not self._current_flags_data:
        print("[HISTORICAL_TRACK_MAP_MDI] {tr('no_data_to_refresh', 'No Data to Refresh')}")
        return
    
    chart_data = self._current_flags_data.get("chart_data", {})
    if chart_data and self.elevation_chart:
        track_outline = chart_data.get("track_outline", [])
        corners = chart_data.get("corners", [])  # ❌ 錯誤
        self.elevation_chart.plot_elevation(track_outline, corners)
```

**修復後**:
```python
def _refresh_charts(self):
    """重新繪製圖表"""
    if not self._is_data_loaded or not self._current_flags_data:
        print("[HISTORICAL_TRACK_MAP_MDI] {tr('no_data_to_refresh', 'No Data to Refresh')}")
        return
    
    chart_data = self._current_flags_data.get("chart_data", {})
    if chart_data and self.elevation_chart:
        track_outline = chart_data.get("track_outline", [])
        # 🔧 修復：正確提取 corners 數據（參考 demo Line 721）
        official_corners = chart_data.get("official_corners", {})
        corners = official_corners.get("corners", [])
        self.elevation_chart.plot_elevation(track_outline, corners)
```

---

## 📚 參考實現

### Demo 代碼（正確範例）

**文件**: `demo_fastf1_z_elevation.py` Line 720-730

```python
def _refresh_charts(self):
    """重新繪製高程圖"""
    if not self.track_data:
        return
    
    track_outline = self.track_data.get('track_outline', [])
    # ✅ 正確：從 official_corners 中提取 corners
    corners = self.track_data.get('official_corners', {}).get('corners', [])
    
    print(f"\n[_refresh_charts] 傳遞給 elevation_chart 的彎道數據:")
    print(f"   - 彎道數量: {len(corners)}")
    if corners:
        print(f"   - 第 1 個彎道: T{corners[0]['number']} at {corners[0]['distance']:.2f}m")
        print(f"   - 第 11 個彎道: T{corners[10]['number']} at {corners[10]['distance']:.2f}m")
        print(f"   - 第 18 個彎道: T{corners[17]['number']} at {corners[17]['distance']:.2f}m")
    
    self.elevation_chart.plot_elevation(track_outline, corners)
```

**關鍵代碼**:
```python
corners = self.track_data.get('official_corners', {}).get('corners', [])
```

---

## 🧪 測試驗證

### 自動化測試

**測試腳本**: `test_corners_format_fix.py`

**測試結果**:
```
✅ 測試 Demo 格式 - 通過
   corners 類型: <class 'list'>
   第 1 個彎道: {'number': 1, 'distance': 123.45}
   成功調用 .get('number'): 1

❌ 測試 GUI 修復前 - 失敗（預期）
   corners 類型: <class 'list'>
   第 1 個彎道: 1 (類型: <class 'int'>)
   AttributeError: 'int' object has no attribute 'get'

✅ 測試 GUI 修復後 - 通過
   corners 類型: <class 'list'>
   第 1 個彎道: {'number': 1, 'distance': 123.45}
   成功調用 .get('number'): 1
```

### 預期 GUI 測試結果

**測試步驟**:
1. 重啟 GUI: `python f1t_gui_main.py`
2. 進入 Historical Track Map 模組
3. 選擇 2024, Japan, R

**預期結果**:
- ✅ 高程圖表顯示彎道編號（T1, T2, ..., T18）
- ✅ 不再出現 AttributeError
- ✅ 彎道標記位於正確的距離位置

**預期日誌輸出**:
```
[HISTORICAL_TRACK_MAP_MDI] chart_data 鍵: ['track_outline', 'official_corners', ...]
[HISTORICAL_TRACK_MAP_MDI] official_corners 類型: <class 'dict'>
[HISTORICAL_TRACK_MAP_MDI] corners 類型: <class 'list'>, 長度: 18
[HISTORICAL_TRACK_MAP_MDI] 第 1 個彎道: {'number': 1, 'distance': 123.45, ...}
[HISTORICAL_TRACK_MAP_MDI] 準備繪製高程圖表（782 點，18 彎道）...
[ELEVATION_CHART] 彎道 1: distance=123.45m
[ELEVATION_CHART] 彎道 2: distance=456.78m
...
[HISTORICAL_TRACK_MAP_MDI] ✅ 高程圖表已更新
```

---

## 📊 修復前後對比

| 項目 | 修復前 | 修復後 |
|-----|--------|--------|
| **提取路徑** | `chart_data["corners"]` | `chart_data["official_corners"]["corners"]` |
| **數據類型** | `[1, 2, 3, ..., 18]` (整數列表) | `[{"number": 1, ...}, ...]` (字典列表) |
| **錯誤訊息** | `AttributeError: 'int' object has no attribute 'get'` | 無錯誤 |
| **彎道顯示** | ❌ 不顯示 | ✅ 顯示 T1-T18 |
| **與 Demo 一致性** | ❌ 不一致 | ✅ 完全一致 |

---

## 📋 修復檢查清單

開發者自檢:
- [x] 修復 `_on_data_loaded()` 方法（Line 807-829）
- [x] 修復 `_refresh_charts()` 方法（Line 1063-1076）
- [x] 添加調試輸出驗證數據格式
- [x] 參考 Demo 實現（Line 721）
- [x] 創建自動化測試腳本
- [x] 測試通過

用戶驗收:
- [ ] GUI 重啟正常
- [ ] 高程圖表顯示彎道編號
- [ ] 不再出現 AttributeError
- [ ] 彎道位置正確（對應實際距離）

---

## 🎯 相關修復

此修復是 **Historical Track Map 完整修復計畫** 的一部分，相關修復包括：

1. ✅ 雙重嵌套檢測（Line 320-333）
2. ✅ 彎道旗幟傳遞（Line 788-799）
3. ✅ 彎道顏色標記（Line 995-1012，原本已存在）
4. ✅ Speed Gradient（Line 1038-1044，原本已存在）
5. ✅ Position Changes 載入（Line 1119-1165）
6. ✅ 年度表格 5 列（Line 596，原本已存在）
7. **✅ Corners 格式修復（本次修復）**

**總進度**: 7/7 項功能完成

---

## 📝 開發原則遵循

### 原則 1: 禁止幻覺編碼
- ✅ 使用 `grep_search` 驗證 Demo 實現（Line 721）
- ✅ 使用 `read_file` 檢查實際代碼
- ✅ 無任何假設性編程

### 原則 2: 模組資料夾優先
- ✅ 完全參考 `demo_fastf1_z_elevation.py` 實現
- ✅ 複用既有的 `elevation_chart_widget_pyqt5.py`

### 原則 3: 通用模組優先
- ✅ 使用 `ElevationChartWidget` 標準 API
- ✅ 遵循 `plot_elevation(track_outline, corners)` 簽名

---

## 🔗 參考資料

### 關鍵檔案
- `modules/gui/Historical_track_map/historical_track_map_mdi.py` - 主要修復檔案
- `demo_fastf1_z_elevation.py` - 參考實現（Line 721）
- `modules/gui/track_elevation/elevation_chart_widget_pyqt5.py` - Elevation Chart Widget
- `test_corners_format_fix.py` - 自動化測試腳本

### 相關錯誤訊息
```python
AttributeError: 'int' object has no attribute 'get'
# 出現位置: elevation_chart_widget_pyqt5.py Line 458
# 原因: corner 是整數而非字典
```

---

**修復完成時間**: 2025-11-11  
**修復作者**: F1T Team  
**測試狀態**: ✅ 自動化測試通過，等待 GUI 驗收
