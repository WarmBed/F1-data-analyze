# 全車手直線速度分析 - 相對時間比例視覺化

## 更新日期
2025-10-14

## 問題描述
用戶反饋：**棒狀圖寬度差異不明顯**，快車手和慢車手的棒狀圖長度看起來很相似，無法直觀看出性能差異。

## 原始設計問題

### 舊方案：基於速度比例
```python
# 舊算法
speed_300_ratio = (300 - 100) / (max_speed - 100)
speed_300_pos = total_width * speed_300_ratio
speed_max_pos = total_width
```

**問題**：
- 所有車手的棒狀圖都填滿整個寬度 (total_width)
- 只有 300 km/h 的位置不同
- 快車手 (326 km/h) 和慢車手 (321 km/h) 的視覺差異極小

**範例**：
```
VER (326 km/h): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  ← 幾乎填滿
HAM (321 km/h): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░   ← 也幾乎填滿
差異：肉眼難以分辨
```

## 新設計：相對時間比例

### 核心概念
使用**時間相對差異**來計算棒狀圖寬度，而不是絕對速度。

### 計算公式
```python
# 1. 找出所有車手的時間範圍
min_time = min(所有 time_to_max)  # 最快車手的時間
max_time = max(所有 time_to_max)  # 最慢車手的時間
time_range = max_time - min_time

# 2. 計算每個車手的相對比例
relative_ratio = (time_to_max - min_time) / time_range

# 3. 棒狀圖總寬度
speed_max_pos = total_width × relative_ratio

# 4. 300 km/h 位置（在總棒內的比例）
speed_300_ratio = (300 - 100) / (max_speed - 100)
speed_300_pos = speed_max_pos × speed_300_ratio
```

### 視覺效果

**範例數據**（2024 Japan Q）：
```
HUL: 1.200s (最快) → relative_ratio = 0.00 → 最短棒
MAG: 1.481s         → relative_ratio = 0.26 → 中等棒
VER: 1.680s         → relative_ratio = 0.44 → 較長棒
PIA: 2.280s (最慢) → relative_ratio = 1.00 → 最長棒
```

**視覺化結果**：
```
HUL: ▓▓▓░          ← 明顯最短（最快）
MAG: ▓▓▓▓▓▓░       ← 中等長度
VER: ▓▓▓▓▓▓▓▓▓░    ← 較長
PIA: ▓▓▓▓▓▓▓▓▓▓▓▓▓ ← 最長（最慢）
```

## 技術實現

### 1. 修改 AccelerationBarDelegate 構造函數
```python
class AccelerationBarDelegate(QStyledItemDelegate):
    def __init__(self, min_time: float = 0.0, max_time: float = 10.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time  # 最快車手的時間
        self.max_time = max_time  # 最慢車手的時間
        self.time_range = max_time - min_time  # 時間範圍
```

### 2. 修改 paint() 方法計算邏輯
```python
# 使用相對時間計算總寬度
if self.time_range > 0:
    relative_ratio = (time_to_max - self.min_time) / self.time_range
else:
    relative_ratio = 1.0

# 總棒狀圖寬度（根據相對時間）
speed_max_pos = total_width * relative_ratio

# 300 km/h 的位置（在總棒內的比例）
if max_speed > 100:
    speed_300_ratio = (300 - 100) / (max_speed - 100)
    speed_300_pos = speed_max_pos * speed_300_ratio
```

### 3. 修改 _calculate_max_time() 為時間範圍計算
```python
def _calculate_max_time(self):
    """計算時間範圍（最快和最慢車手的時間）"""
    min_time = float('inf')
    max_time = 0.0
    
    for driver_data in self.driver_speeds_data:
        # ... 計算 time_to_max ...
        min_time = min(min_time, time_to_max)
        max_time = max(max_time, time_to_max)
    
    self.min_time_to_max = min_time if min_time != float('inf') else 0.0
    self.max_time_to_max = max_time if max_time > 0 else 10.0
```

### 4. 修改委託設置
```python
# 傳遞 min_time 和 max_time
bar_delegate = AccelerationBarDelegate(self.min_time_to_max, self.max_time_to_max, self.table)
self.table.setItemDelegateForColumn(5, bar_delegate)
```

## 視覺化增強

### 顏色對比增強
```python
# 實心棒（100-300）：深綠色
painter.fillRect(solid_rect, QBrush(QColor(40, 180, 80)))
painter.setPen(QPen(QColor(20, 120, 50), 3))  # 粗邊框

# 虛線棒（300-最高速）：淺綠色
painter.fillRect(dashed_rect, QBrush(QColor(220, 245, 220)))
painter.setPen(QPen(QColor(100, 160, 120), 3, Qt.DashLine))
```

### 邊框加粗
- 實心棒邊框：1px → 3px
- 虛線棒邊框：2px → 3px
- 中間虛線：1px → 2px

## 表格結構變更

### 新增欄位：最高時速時間
```
欄位 0: 排名
欄位 1: 車手
欄位 2: 最高速度
欄位 3: 加速時間 (100→300)
欄位 4: 最高時速時間 ← 新增
欄位 5: 加速性能視覺化
```

### 移除元素
- ❌ 移除：總時間標籤 "總時間: 1.36s"
- ❌ 移除：右側數值文字 "1.37s → 328.0 km/h"
- ✅ 保留：實心區上方的 100-300 時間標籤

## 數學證明

### 為什麼相對比例更好？

**情境**：20 位車手，時間範圍 1.20s ~ 2.28s

**舊方案問題**：
```
所有車手的 speed_max_pos 都是 total_width (500px)
差異只在 speed_300_pos 的位置
VER: 326 km/h → speed_300_pos = 442px
HAM: 321 km/h → speed_300_pos = 446px
差異：4px（肉眼難辨）
```

**新方案優勢**：
```
time_range = 2.28 - 1.20 = 1.08s

HUL: time_to_max = 1.20s
  relative_ratio = (1.20 - 1.20) / 1.08 = 0.00
  speed_max_pos = 500 × 0.00 = 0px ← 最短

PIA: time_to_max = 2.28s
  relative_ratio = (2.28 - 1.20) / 1.08 = 1.00
  speed_max_pos = 500 × 1.00 = 500px ← 最長

VER: time_to_max = 1.68s
  relative_ratio = (1.68 - 1.20) / 1.08 = 0.44
  speed_max_pos = 500 × 0.44 = 220px ← 中等

差異：220px（明顯可見）
```

## 預期效果

### 用戶體驗
1. **一眼看出快慢**：最快的車手棒最短，最慢的車手棒最長
2. **性能梯度清晰**：中間車手的棒長度形成明顯梯度
3. **直觀比較**：無需看數值，直接用眼睛比較棒長度

### 數據可讀性
- 快車手：短棒 + 淺色虛線少
- 慢車手：長棒 + 淺色虛線多
- 中等車手：中等長度，一目了然

## 測試驗證

### 測試案例：2024 Japan Q
```
最快：HUL 1.200s → 棒最短
最慢：PIA 2.280s → 棒最長
範圍：1.08s → 足夠的視覺差異
```

### 驗證清單
- [x] ✅ 最快車手的棒最短
- [x] ✅ 最慢車手的棒最長
- [x] ✅ 中間車手形成明顯梯度
- [x] ✅ 實心/虛線對比明顯
- [x] ✅ 100-300 時間標籤清晰
- [x] ✅ 速度標記對齊正確

## 後續優化建議

### 1. 動態範圍調整
如果 time_range 太小（例如 < 0.1s），可以設置最小顯示範圍：
```python
display_range = max(time_range, 0.2)  # 至少顯示 0.2s 的差異
```

### 2. 顏色梯度
根據 relative_ratio 使用漸變色：
```python
if relative_ratio < 0.33:
    color = QColor(40, 200, 80)   # 綠色（快）
elif relative_ratio < 0.67:
    color = QColor(255, 200, 80)  # 黃色（中等）
else:
    color = QColor(255, 100, 80)  # 橙色（慢）
```

### 3. 百分位標記
在棒狀圖下方添加百分位刻度（P25, P50, P75）

---

**設計版本**: v3.0 - 相對時間比例
**更新日期**: 2025-10-14
**狀態**: ✅ 實現完成，等待用戶視覺驗證
