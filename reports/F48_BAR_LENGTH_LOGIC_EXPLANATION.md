# F48 棒狀圖長度計算邏輯詳解

## 📊 棒狀圖視覺設計

```
┌─────────────────────────────────────────────────────────────┐
│  100 km/h      統一終點      最高速                          │
│    ↓            ↓            ↓                               │
│    ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  7.119s                          │
│    └─ 深藍實心 ─┘└─ 淺灰 ─┘  8.400s                          │
│   (100-320)    (320-最高速)                                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔢 核心計算公式

### 1. 空間分配邏輯（Line 78-86）

```python
# 總可用寬度
total_width = option.rect.width()  # 假設 = 800px

# 空間分配
text_reserved_width = 100  # 預留給時間文字
left_margin = 10           # 左邊距
text_margin = 10           # 棒狀圖與文字間距

# 棒狀圖最大可用寬度
bar_max_width = total_width - left_margin - text_reserved_width
# bar_max_width = 800 - 10 - 100 = 690px
```

**空間分配示意圖**：
```
┌──────────────────────────────────────────────────────────┐
│ 10px │←────── 690px 棒狀圖空間 ────→│ 10px │ 100px 文字 │
│ 邊距  │                              │ 間距 │           │
└──────────────────────────────────────────────────────────┘
```

### 2. 相對時間比例計算（Line 88-95）

這是**關鍵邏輯**，決定棒狀圖長度：

```python
# 計算時間範圍
self.min_time = 7.119   # 最快車手 (STR)
self.max_time = 14.920  # 最慢車手 (DOO)
self.time_range = 14.920 - 7.119 = 7.801 秒

# 當前車手的相對時間比例
time_to_max = 8.400  # 當前車手到達最高速的時間

relative_ratio = (time_to_max - self.min_time) / self.time_range
               = (8.400 - 7.119) / 7.801
               = 1.281 / 7.801
               = 0.164  # 16.4% 的範圍
```

**公式解釋**：
- `time_to_max - min_time`：當前車手比最快車手慢多少
- `/ time_range`：轉換為百分比（0.0 到 1.0）
- 結果：最快車手 = 0.0（0%），最慢車手 = 1.0（100%）

### 3. 棒狀圖總長度計算（Line 97-98）

```python
speed_max_pos = min(bar_max_width * relative_ratio, bar_max_width)
              = min(690 * 0.164, 690)
              = min(113.16, 690)
              = 113.16px
```

**強制限制**：
- `bar_max_width * relative_ratio`：按比例計算長度
- `min(..., bar_max_width)`：確保不超過最大寬度
- 最慢車手（ratio=1.0）會佔滿整個 690px

### 4. 深藍棒（100→統一終點）計算（Line 100-107）

```python
# 假設當前車手：max_speed = 328 km/h，統一終點 = 320 km/h

if max_speed > 100:
    speed_300_ratio = (320 - 100) / (328 - 100)
                    = 220 / 228
                    = 0.965  # 96.5% 的速度範圍
    
    speed_300_pos = speed_max_pos * speed_300_ratio
                  = 113.16 * 0.965
                  = 109.2px  # 深藍棒的長度
```

**公式解釋**：
- `(320 - 100)`：統一終點速度範圍（100→320 km/h）
- `(max_speed - 100)`：最高速度範圍（100→328 km/h）
- 比例：統一終點在整個速度範圍中佔 96.5%
- 深藍棒長度 = 總長度 × 96.5%

### 5. 淺灰棒（統一終點→最高速）計算（Line 120-129）

```python
extension_rect_width = speed_max_pos - speed_300_pos
                     = 113.16 - 109.2
                     = 3.96px  # 淺灰棒的長度
```

**公式解釋**：
- 淺灰棒 = 總長度 - 深藍棒
- 代表從統一終點（320 km/h）加速到最高速（328 km/h）的部分

## 📐 完整計算範例

### 範例 1: STR（最快車手）

**數據**：
- `time_to_max` = 7.119s
- `max_speed` = 336 km/h
- 統一終點 = 320 km/h

**計算**：
```python
# 步驟 1: 相對比例
relative_ratio = (7.119 - 7.119) / 7.801 = 0.0  # 0%

# 步驟 2: 總長度
speed_max_pos = 690 * 0.0 = 0px  # ❗ 最快車手棒狀圖幾乎看不見！

# 步驟 3: 深藍棒
speed_300_ratio = (320 - 100) / (336 - 100) = 220 / 236 = 0.932
speed_300_pos = 0 * 0.932 = 0px

# 步驟 4: 淺灰棒
extension_width = 0 - 0 = 0px
```

**問題**：最快車手的棒狀圖長度為 **0px**，完全看不見！

### 範例 2: DOO（最慢車手）

**數據**：
- `time_to_max` = 14.920s
- `max_speed` = 310 km/h
- 統一終點 = 320 km/h（❗ 注意：最高速低於統一終點）

**計算**：
```python
# 步驟 1: 相對比例
relative_ratio = (14.920 - 7.119) / 7.801 = 1.0  # 100%

# 步驟 2: 總長度
speed_max_pos = 690 * 1.0 = 690px  # 佔滿整個可用空間

# 步驟 3: 深藍棒
speed_300_ratio = (320 - 100) / (310 - 100) = 220 / 210 = 1.048
speed_300_pos = 690 * 1.048 = 723.12px  # ❗ 超過總長度！

# 實際：max(speed_300_pos, speed_max_pos) = 690px

# 步驟 4: 淺灰棒
extension_width = 690 - 690 = 0px  # 沒有延伸棒
```

**問題**：最高速低於統一終點時，深藍棒會超出總長度（被強制裁剪）

### 範例 3: ALO（中等車手）

**數據**：
- `time_to_max` = 8.400s
- `max_speed` = 328 km/h
- 統一終點 = 320 km/h

**計算**：
```python
# 步驟 1: 相對比例
relative_ratio = (8.400 - 7.119) / 7.801 = 0.164  # 16.4%

# 步驟 2: 總長度
speed_max_pos = 690 * 0.164 = 113.16px

# 步驟 3: 深藍棒
speed_300_ratio = (320 - 100) / (328 - 100) = 220 / 228 = 0.965
speed_300_pos = 113.16 * 0.965 = 109.2px

# 步驟 4: 淺灰棒
extension_width = 113.16 - 109.2 = 3.96px
```

**結果**：
- 深藍棒：109.2px（100→320 km/h）
- 淺灰棒：3.96px（320→328 km/h）
- 總長度：113.16px

## ⚠️ 當前問題分析

### 問題 1: 最快車手棒狀圖不可見

**原因**：
```python
relative_ratio = (7.119 - 7.119) / 7.801 = 0.0
speed_max_pos = 690 * 0.0 = 0px  # 完全看不見！
```

**解決方案**：
- 方案 A：設置最小長度（如 30px）
- 方案 B：改用絕對時間映射（不使用相對比例）
- 方案 C：使用對數刻度（壓縮極端值）

### 問題 2: 時間差異不明顯

**原因**：
```python
# STR vs ALO 的時間差異
time_diff = 8.400 - 7.119 = 1.281s  # 18% 差異

# 但棒狀圖長度差異
bar_diff = 113.16 - 0 = 113.16px  # 看起來很明顯

# 問題：時間範圍過大（7.801s），導致小差異被放大
```

**解決方案**：
- 使用加速時間（100→320）而非總時間（100→最高速）
- 縮小時間範圍，讓差異更線性

### 問題 3: 最高速低於統一終點的車手

**原因**：
```python
# DOO: max_speed = 310 km/h < 320 km/h (統一終點)
speed_300_ratio = (320 - 100) / (310 - 100) = 1.048  # > 1.0！

# 深藍棒會超過總長度
speed_300_pos = 690 * 1.048 = 723.12px > 690px
```

**當前處理**：強制裁剪到總長度（不正確）

**正確處理**：
```python
if max_speed < unified_end_speed:
    # 最高速低於統一終點，只繪製深藍棒到最高速
    speed_300_pos = speed_max_pos  # 深藍棒佔滿
    extension_width = 0  # 沒有淺灰棒
```

## 🎯 推薦改進方案

### 方案 A: 使用加速時間而非總時間（推薦）

```python
# 當前（Line 88-95）
relative_ratio = (time_to_max - self.min_time) / self.time_range

# 改進
accel_100_300_time = 7.119  # 使用加速時間（100→320）
self.min_accel = 7.119  # 最快加速
self.max_accel = 14.920  # 最慢加速
accel_range = 14.920 - 7.119 = 7.801

relative_ratio = (accel_100_300_time - self.min_accel) / accel_range
```

**優點**：
- 所有車手都有統一的測量標準（100→320 km/h）
- 不受最高速度影響，差異更一致
- 避免最高速低於統一終點的問題

### 方案 B: 設置最小棒狀圖長度

```python
# Line 97-98 修改
MIN_BAR_WIDTH = 30  # 最小 30px

speed_max_pos = max(
    MIN_BAR_WIDTH,  # 確保最小長度
    min(bar_max_width * relative_ratio, bar_max_width)
)
```

**優點**：
- 確保所有車手都可見
- 簡單易實現

**缺點**：
- 破壞了比例一致性
- 最快車手會顯得比實際更慢

### 方案 C: 使用對數刻度

```python
import math

# 對數映射（壓縮極端值）
log_min = math.log(self.min_time)
log_max = math.log(self.max_time)
log_current = math.log(time_to_max)

relative_ratio = (log_current - log_min) / (log_max - log_min)
```

**優點**：
- 小差異更明顯
- 極端值不會過分突出

**缺點**：
- 不直觀（用戶可能不理解）
- 需要額外說明

## 📋 當前代碼位置索引

| 功能 | 行數 | 說明 |
|------|------|------|
| 空間分配 | 78-86 | 計算 `bar_max_width = 690px` |
| 相對比例 | 88-95 | `relative_ratio = (time - min) / range` |
| 總長度 | 97-98 | `speed_max_pos = max_width × ratio` |
| 深藍棒 | 100-107 | 100→統一終點速度 |
| 深藍棒繪製 | 112-116 | `fillRect` + 邊框 |
| 淺灰棒 | 120-129 | 統一終點→最高速 |
| 文字標籤 | 131-147 | 固定位置，避免重疊 |

## 🔍 調試建議

### 打印關鍵變量

```python
# 在 paint() 方法中添加（Line 95 後）
print(f"[BAR_DEBUG] {index.row()}")
print(f"  time_to_max: {time_to_max:.3f}s")
print(f"  min_time: {self.min_time:.3f}s")
print(f"  max_time: {self.max_time:.3f}s")
print(f"  relative_ratio: {relative_ratio:.3f}")
print(f"  bar_max_width: {bar_max_width}px")
print(f"  speed_max_pos: {speed_max_pos:.1f}px")
print(f"  speed_300_pos: {speed_300_pos:.1f}px")
print(f"  extension: {speed_max_pos - speed_300_pos:.1f}px")
```

### 視覺化時間範圍

```python
# 創建測試腳本
import matplotlib.pyplot as plt

times = [7.119, 8.400, 9.920, 14.920]  # 範例時間
names = ['STR', 'ALO', 'TSU', 'DOO']

min_time = 7.119
max_time = 14.920
time_range = max_time - min_time

ratios = [(t - min_time) / time_range for t in times]
bar_widths = [690 * r for r in ratios]

plt.barh(names, bar_widths)
plt.xlabel('棒狀圖寬度 (px)')
plt.title('當前棒狀圖長度分布')
plt.show()
```

## 🎨 視覺效果對比

### 當前邏輯（相對時間）

```
STR (7.119s):  ▓ (0px - 看不見)
ALO (8.400s):  ▓▓▓▓▓▓▓▓ (113px)
TSU (9.920s):  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (245px)
DOO (14.920s): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (690px - 佔滿)
```

### 改進後（使用加速時間 + 最小長度）

```
STR (7.119s):  ▓▓ (30px - 可見)
ALO (8.400s):  ▓▓▓▓▓▓▓▓ (113px)
TSU (9.920s):  ▓▓▓▓▓▓▓▓▓▓▓▓ (180px)
DOO (14.920s): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (320px)
```

**差異**：
- 所有車手都可見（最小 30px）
- 差異更均勻（不會有極端值）
- 時間標籤清晰顯示實際數據

---

**結論**：當前邏輯使用**相對時間比例**，導致最快車手棒狀圖不可見。推薦使用**加速時間**（100→320 km/h）作為基準，並設置**最小棒狀圖長度**。
