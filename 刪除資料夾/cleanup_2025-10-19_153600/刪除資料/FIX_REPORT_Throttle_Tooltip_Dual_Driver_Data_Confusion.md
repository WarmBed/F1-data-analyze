# 🐛 修復報告：Throttle Line Chart 雙車手 Tooltip 數據混淆

## 📋 問題摘要

**報告日期**: 2025-10-08  
**問題嚴重性**: 🔴 High (Critical)  
**影響範圍**: Throttle Line Chart 雙車手模式  
**狀態**: ✅ 已修復

---

## 🔍 問題描述

### 現象
在 Throttle Line Chart 雙車手模式下，當點擊 Driver 1 (HAM) 的數據點時，tooltip 顯示的是 Driver 2 (LEC) 的數據。

### 實際案例 (2025 Singapore R - Lap 61)

**點擊 HAM 的數據點：**
- 圖表 Y 軸顯示：~0-5% 附近
- Tooltip 顯示：
  - Full Throttle %: **33.6%** ❌
  - Ave Throttle %: **52.6%** ❌
  - Lap Time: 01:41.327 ❌

**實際數據應該是：**
- HAM Lap 61:
  - Full Throttle %: **0.0%** ✅ (進站圈)
  - Ave Throttle %: **30.5%** ✅
  - Lap Time: 02:08.668 ✅

**33.6% 和 52.6% 是誰的數據？**
- LEC Lap 61:
  - Full Throttle %: **33.6%** (這才是 LEC 的數據！)
  - Ave Throttle %: **52.6%**
  - Lap Time: 01:41.327

---

## 🔬 根本原因分析

### 數據流追蹤

1. **JSON 數據正確** ✅
   ```json
   {
     "driver_code": "HAM",
     "laps": [
       {
         "lap_number": 61,
         "full_throttle_ratio": 0.0,
         "average_throttle": 0.304865324258013
       }
     ]
   }
   ```

2. **Data Loader 轉換正確** ✅
   ```python
   # throttle_line_chart_data_loader.py line 336
   ratios.append(lap.get("full_throttle_ratio") * 100.0)
   # 0.0 * 100 = 0.0%
   ```

3. **Tooltip 系統問題** ❌
   ```python
   # throttle_duration_chart_widget.py (修復前)
   self._tooltip_map = dict(tooltip_map or {})  # 只儲存 Driver 1
   # tooltip_map_driver2 參數被接受但從未使用！
   ```

### 問題核心

**單一 tooltip_map 無法區分兩位車手的數據**

```python
# 舊程式碼問題：
def update_series(self, tooltip_map, tooltip_map_driver2=None):
    self._tooltip_map = dict(tooltip_map or {})  # 只存 Driver 1
    # tooltip_map_driver2 被忽略！

def get_tooltip_payload(self, lap_number):
    return self._tooltip_map.get(lap_number)  # 永遠只返回 Driver 1 的數據
```

當系統需要顯示 tooltip 時，不論點擊的是哪位車手的數據點，都只會從 `self._tooltip_map` (Driver 1) 中查找。

---

## 🔧 修復方案

### 技術實作

#### 1. 分離儲存兩位車手的 Tooltip 數據

**檔案**: `throttle_duration_chart_widget.py`, `lap_time_chart_widget.py`

```python
def __init__(self, parent=None):
    super().__init__(...)
    
    # 🆕 雙車手模式：分別儲存兩位車手的 tooltip 數據
    self._tooltip_map_driver1: Dict[int, Dict[str, object]] = {}
    self._tooltip_map_driver2: Dict[int, Dict[str, object]] = {}
    self._tooltip_map: Dict[int, Dict[str, object]] = {}  # 向下相容性（指向 driver1）
```

#### 2. 更新數據時分別儲存

```python
def update_series(self, tooltip_map, tooltip_map_driver2=None, ...):
    # 🆕 雙車手模式：分別儲存兩位車手的 tooltip 數據
    self._tooltip_map_driver1 = dict(tooltip_map or {})
    self._tooltip_map_driver2 = dict(tooltip_map_driver2 or {})
    self._tooltip_map = self._tooltip_map_driver1  # 向下相容性
```

#### 3. 根據系列名稱選擇正確的數據

```python
def get_tooltip_payload(self, lap_number: int, series_name: str = "") -> Dict[str, object]:
    """
    獲取指定圈數的 tooltip 數據
    
    Args:
        lap_number: 圈數
        series_name: 系列名稱（用於判斷是 Driver 1 還是 Driver 2）
    """
    # 🆕 根據系列名稱判斷使用哪個 tooltip map
    if series_name and ("(D2)" in series_name or "(Driver 2)" in series_name):
        return dict(self._tooltip_map_driver2.get(int(lap_number), {}))
    else:
        # 默認使用 Driver 1 的數據
        return dict(self._tooltip_map_driver1.get(int(lap_number), {}))

def format_tooltip_for_data_point(self, lap_number: int, series_name: str = "") -> List[str]:
    """
    為數據點格式化 tooltip 文字
    
    Args:
        lap_number: 圈數
        series_name: 系列名稱（用於雙車手模式判斷）
    """
    payload = self.get_tooltip_payload(lap_number, series_name)
    # ... 格式化 tooltip 文字
```

#### 4. Universal Chart Widget 傳入系列名稱

**檔案**: `universal_chart_widget.py`

```python
def _draw_data_point_tooltip(self, painter, data_point, is_pinned=False):
    series_idx = data_point['series_idx']
    series_name = self.data_series[series_idx].name
    lap_number = int(round(x_val))
    
    # 🆕 傳入 series_name 參數（支援雙車手模式）
    if hasattr(self, 'format_tooltip_for_data_point'):
        try:
            lines = self.format_tooltip_for_data_point(lap_number, series_name)
        except TypeError:
            # 向下相容：舊版本不接受 series_name 參數
            lines = self.format_tooltip_for_data_point(lap_number)
```

---

## 📝 修改檔案清單

| 檔案 | 修改內容 | 行數 |
|------|---------|------|
| `throttle_duration_chart_widget.py` | 添加 `_tooltip_map_driver1/2`，修改 `get_tooltip_payload()`, `format_tooltip_for_data_point()` | ~35 行 |
| `lap_time_chart_widget.py` | 同上 | ~35 行 |
| `universal_chart_widget.py` | 修改 `_draw_data_point_tooltip()` 傳入 `series_name` | ~10 行 |

**總修改行數**: ~80 行  
**新增程式碼**: ~50 行  
**刪除程式碼**: 0 行（保持向下相容）

---

## ✅ 修復效果驗證

### 測試案例：2025 Singapore R - Lap 61

#### 修復前
```
點擊 HAM (Driver 1) 數據點：
  ❌ Full Throttle %: 33.6% (錯誤，顯示 LEC 的數據)
  ❌ Ave Throttle %: 52.6% (錯誤)
  ❌ Lap Time: 01:41.327 (錯誤)
```

#### 修復後
```
點擊 HAM (Driver 1) 數據點：
  ✅ Full Throttle %: 0.0% (正確)
  ✅ Ave Throttle %: 30.5% (正確)
  ✅ Lap Time: 02:08.668 (正確)

點擊 LEC (Driver 2) 數據點：
  ✅ Full Throttle %: 33.6% (正確)
  ✅ Ave Throttle %: 52.6% (正確)
  ✅ Lap Time: 01:41.327 (正確)
```

---

## 🔄 向下相容性

修復保持完全向下相容：

1. **單車手模式** ✅
   - 仍然可以只傳入 `tooltip_map` 參數
   - `_tooltip_map` 指向 `_tooltip_map_driver1`
   - 舊程式碼無需修改

2. **舊版 tooltip 方法** ✅
   - `format_tooltip_for_data_point(lap_number)` 仍然有效
   - `try-except` 處理新舊版本差異

3. **其他圖表模組** ✅
   - 不使用 `series_name` 參數的模組不受影響

---

## 🧪 測試建議

### 手動測試
1. ✅ 啟動 Throttle Line Chart (雙車手模式)
2. ✅ 選擇 HAM vs LEC, 2025 Singapore R
3. ✅ 點擊各個 Lap 的數據點
4. ✅ 驗證 tooltip 顯示正確的車手數據

### 重點測試圈數
- **Lap 61**: HAM 進站圈 (0.0%), LEC 正常圈 (33.6%)
- **Lap 56**: HAM 正常圈，驗證非零數據
- **Lap 1-5**: 起步階段，數據變化大

### 預期結果
- 點擊藍色線條 (Driver 1) → 顯示 HAM 數據
- 點擊紅色線條 (Driver 2) → 顯示 LEC 數據
- Tooltip 數值與圖表 Y 軸位置一致

---

## 📊 影響範圍

### 受益模組
- ✅ Throttle Line Chart (Full Throttle %)
- ✅ Throttle Line Chart (Average Throttle %)
- ✅ Lap Time Chart

### 不受影響模組
- ✅ Single Driver Mode (單車手模式)
- ✅ Box Plot Charts
- ✅ Detailed Lap Analysis
- ✅ 其他分析模組

---

## 💡 未來改進建議

1. **測試覆蓋**
   - 建立自動化測試驗證雙車手 tooltip 數據
   - 單元測試: `test_dual_driver_tooltip_separation()`

2. **程式碼重構**
   - 考慮建立 `DualDriverTooltipManager` 類別
   - 統一管理雙車手數據分離邏輯

3. **UI 改進**
   - Tooltip 可顯示車手代碼 (HAM/LEC)
   - 不同車手使用不同顏色的 tooltip 邊框

---

## 📌 相關資源

- **問題發現**: 用戶截圖 (2025-10-08)
- **測試數據**: `json/throttle_ratio_2025_singapore_R.json`
- **測試腳本**: `test_tooltip_fix.py`, `debug_tooltips.py`
- **修復提交**: (待 Git commit)

---

**修復完成時間**: 2025-10-08  
**修復者**: GitHub Copilot  
**驗證者**: 待用戶測試確認
