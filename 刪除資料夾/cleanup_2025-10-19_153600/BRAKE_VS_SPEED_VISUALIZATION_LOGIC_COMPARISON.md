# All Drivers Brake Performance vs Straight Line Speed - 視覺化邏輯比對報告

## 📊 執行時間
**2025-10-19 01:05**

---

## 🎯 比對目的

深入比對 **All Drivers Brake Performance** 和 **All Drivers Straight Line Speed** 兩個模組的視覺化邏輯，
確認兩者的實現一致性和差異點。

---

## 📁 比對檔案

### Brake Performance（煞車性能）
- **主檔案**：`modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_table_widget.py`
- **Delegate 類別**：`DecelerationBarDelegate`
- **數據欄位**：`brake_time`, `max_deceleration`

### Straight Line Speed（直線速度）
- **主檔案**：`modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`
- **Delegate 類別**：`AccelerationBarDelegate`
- **數據欄位**：`segment_accel_time`, `max_speed`

---

## 🔍 核心視覺化邏輯比對

### 1. **Delegate 類別結構**

| 項目 | Brake Performance | Straight Line Speed | 一致性 |
|------|------------------|-------------------|-------|
| **類別名稱** | `DecelerationBarDelegate` | `AccelerationBarDelegate` | ✅ 命名一致（對應功能） |
| **繼承** | `QStyledItemDelegate` | `QStyledItemDelegate` | ✅ 完全一致 |
| **初始化參數** | `min_time`, `max_time` | `min_time`, `max_time` | ✅ 完全一致 |
| **時間範圍計算** | `time_range = max_time - min_time` | `time_range = max_time - min_time` | ✅ 完全一致 |

---

### 2. **數據讀取邏輯**

#### Brake Performance (第 68-72 行)
```python
# ✅ 獲取賽道段煞車時間數據
brake_time = index.data(Qt.UserRole)  # 賽道段煞車時間（排序和繪圖依據）
max_deceleration = index.data(Qt.UserRole + 1)  # 最大減速度（顯示用）

# 檢查數據有效性
if brake_time is None or brake_time == 9999:
    # N/A 數據，顯示灰色 N/A
    super().paint(painter, option, index)
    return
```

#### Straight Line Speed (第 68-72 行)
```python
# ✅ 獲取賽道段加速時間數據
segment_accel_time = index.data(Qt.UserRole)  # 賽道段加速時間（排序和繪圖依據）
max_speed = index.data(Qt.UserRole + 1)  # 最高速度（顯示用）

# 檢查數據有效性
if segment_accel_time is None or segment_accel_time == 9999:
    # N/A 數據，顯示灰色 N/A
    super().paint(painter, option, index)
    return
```

**比對結果：** ✅ **完全一致** - 只有變數名稱不同（`brake_time` vs `segment_accel_time`）

---

### 3. **相對比例計算（核心邏輯）**

#### Brake Performance (第 106-118 行)
```python
# ⭐ 使用相對時間計算棒狀圖長度（關鍵邏輯）
if self.time_range > 0:
    # 相對於最快車手的時間差異比例
    # 例如：最快 1.480s，最慢 1.820s，範圍 0.340s
    # HAM 1.659s: (1.659 - 1.480) / 0.340 = 0.526 (52.6%)
    # LEC 1.820s: (1.820 - 1.480) / 0.340 = 1.000 (100%)
    relative_ratio = (brake_time - self.min_time) / self.time_range
else:
    # 所有車手時間相同
    relative_ratio = 0.0

# ✅ 棒狀圖寬度（按比例縮放）
# 時間短 = relative_ratio 小 = 棒狀圖短 = 性能好 ✅
bar_width = min(bar_max_width * relative_ratio, bar_max_width)
```

#### Straight Line Speed (第 106-118 行)
```python
# ⭐ 使用相對時間計算棒狀圖長度（關鍵邏輯）
if self.time_range > 0:
    # 相對於最快車手的時間差異比例
    # 例如：最快 9.480s，最慢 10.120s，範圍 0.640s
    # HAM 9.759s: (9.759 - 9.480) / 0.640 = 0.436 (43.6%)
    # LEC 10.120s: (10.120 - 9.480) / 0.640 = 1.000 (100%)
    relative_ratio = (segment_accel_time - self.min_time) / self.time_range
else:
    # 所有車手時間相同
    relative_ratio = 0.0

# ✅ 棒狀圖寬度（按比例縮放）
# 時間短 = relative_ratio 小 = 棒狀圖短 = 性能好 ✅
bar_width = min(bar_max_width * relative_ratio, bar_max_width)
```

**比對結果：** ✅ **完全一致** - 只有範例數值和變數名稱不同

**視覺化邏輯：**
- ✅ 兩者都使用 **相對比例** 計算棒狀圖長度
- ✅ 時間短 → `relative_ratio` 小 → 棒狀圖短 → 性能好
- ✅ 最快車手：`relative_ratio = 0.0`（棒最短）
- ✅ 最慢車手：`relative_ratio = 1.0`（棒最長）

---

### 4. **棒狀圖繪製邏輯**

#### Brake Performance (第 120-132 行)
```python
# ===== 繪製減速棒（簡化設計：單一深藍色實心棒）=====
# ⭐ 棒狀圖設計：
# - 深藍色實心棒，長度代表煞車時間
# - 棒越短 = 時間越短 = 性能越好
# - 無需分段顯示（已移除速度範圍概念）

bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
painter.fillRect(bar_rect, QBrush(QColor(50, 100, 180)))  # 深藍色實心
painter.setPen(QPen(QColor(30, 70, 140), 2))  # 深藍邊框
painter.drawRect(bar_rect)
```

#### Straight Line Speed (第 120-132 行)
```python
# ===== 繪製加速棒（簡化設計：單一深藍色實心棒）=====
# ⭐ 棒狀圖設計：
# - 深藍色實心棒，長度代表加速時間
# - 棒越短 = 時間越短 = 性能越好
# - 無需分段顯示（已移除速度範圍概念）

bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
painter.fillRect(bar_rect, QBrush(QColor(50, 100, 180)))  # 深藍色實心
painter.setPen(QPen(QColor(30, 70, 140), 2))  # 深藍邊框
painter.drawRect(bar_rect)
```

**比對結果：** ✅ **完全一致**

**共同特點：**
- ✅ 使用相同的 **深藍色** (`QColor(50, 100, 180)`)
- ✅ 使用相同的 **深藍邊框** (`QColor(30, 70, 140)`)
- ✅ 相同的 **棒高度** (`bar_height = 20`)
- ✅ 相同的 **佈局邏輯** (左邊棒狀圖，右邊文字)

---

### 5. **文字標籤繪製**

#### Brake Performance (第 134-143 行)
```python
# ===== 繪製時間標籤（固定位置）=====
# ✅ 文字使用固定起始位置（棒狀圖最大寬度後）
text_x = int(base_x + bar_max_width + text_margin)

# 顯示賽道段煞車時間
painter.setFont(QFont("Arial", 10, QFont.Bold))
painter.setPen(QPen(QColor(50, 100, 180)))  # 深藍色
text_y = int(base_y + 15)
painter.drawText(text_x, text_y, f"{brake_time:.3f} s")
```

#### Straight Line Speed (第 134-143 行)
```python
# ===== 繪製時間標籤（固定位置）=====
# ✅ 文字使用固定起始位置（棒狀圖最大寬度後）
text_x = int(base_x + bar_max_width + text_margin)

# 顯示賽道段加速時間
painter.setFont(QFont("Arial", 10, QFont.Bold))
painter.setPen(QPen(QColor(50, 100, 180)))  # 深藍色
text_y = int(base_y + 15)
painter.drawText(text_x, text_y, f"{segment_accel_time:.3f} s")
```

**比對結果：** ✅ **完全一致**

**共同特點：**
- ✅ 文字固定在棒狀圖右側（`text_x = base_x + bar_max_width + text_margin`）
- ✅ 使用相同字體（`Arial, 10, Bold`）
- ✅ 使用相同顏色（深藍色）
- ✅ 顯示格式一致（`{time:.3f} s`）

---

### 6. **時間顏色編碼（輔助功能）**

#### Brake Performance (第 145-156 行)
```python
def _get_time_color(self, time: float) -> QColor:
    """
    根據煞車時間返回顏色
    
    綠色: < 1.5 秒 (快)
    黃色: 1.5 - 1.7 秒 (中等)
    橙色: > 1.7 秒 (慢)
    """
    if time < 1.5:
        return QColor(100, 200, 100)  # 綠色
    elif time < 1.7:
        return QColor(255, 220, 100)  # 黃色
    else:
        return QColor(255, 150, 100)  # 橙色
```

#### Straight Line Speed (第 145-156 行)
```python
def _get_time_color(self, time: float) -> QColor:
    """
    根據加速時間返回顏色
    
    綠色: < 7.0 秒 (快)
    黃色: 7.0 - 8.0 秒 (中等)
    橙色: > 8.0 秒 (慢)
    """
    if time < 7.0:
        return QColor(100, 200, 100)  # 綠色
    elif time < 8.0:
        return QColor(255, 220, 100)  # 黃色
    else:
        return QColor(255, 150, 100)  # 橙色
```

**比對結果：** ✅ **邏輯一致，閾值不同**

**差異分析：**
| 項目 | Brake Performance | Straight Line Speed | 原因 |
|------|------------------|-------------------|------|
| **快速閾值** | < 1.5 秒 | < 7.0 秒 | 煞車時間較短（秒級 vs 10秒級） |
| **中等閾值** | 1.5 - 1.7 秒 | 7.0 - 8.0 秒 | 加速時間較長 |
| **顏色** | 綠/黃/橙 | 綠/黃/橙 | ✅ 完全一致 |

**結論：** ⚠️ **閾值需根據實際數據範圍調整**（但目前並未使用此顏色編碼，棒狀圖統一為深藍色）

---

## 🎨 佈局參數比對

| 參數 | Brake Performance | Straight Line Speed | 一致性 |
|------|------------------|-------------------|-------|
| **text_reserved_width** | 80 | 80 | ✅ |
| **left_margin** | 10 | 10 | ✅ |
| **text_margin** | 10 | 10 | ✅ |
| **bar_height** | 20 | 20 | ✅ |
| **base_x** | `option.rect.x() + 10` | `option.rect.x() + 10` | ✅ |
| **base_y** | `option.rect.y() + 10` | `option.rect.y() + 10` | ✅ |
| **棒狀圖顏色** | `QColor(50, 100, 180)` | `QColor(50, 100, 180)` | ✅ |
| **邊框顏色** | `QColor(30, 70, 140)` | `QColor(30, 70, 140)` | ✅ |

**結論：** ✅ **所有佈局參數完全一致**

---

## 📦 Widget 主類別比對

### 1. **類別結構**

| 項目 | Brake Performance | Straight Line Speed | 一致性 |
|------|------------------|-------------------|-------|
| **類別名稱** | `AllDriversBrakePerformanceTableWidget` | `AllDriversStraightLineSpeedTableWidget` | ✅ |
| **繼承** | `QWidget` | `QWidget` | ✅ |
| **數據屬性** | `driver_brakes_data` | `driver_speeds_data` | ✅ (命名對應) |
| **時間範圍** | `min_time_to_max`, `max_time_to_max` | `min_time_to_max`, `max_time_to_max` | ✅ |
| **速度範圍** | `unified_start_speed`, `unified_end_speed` | `unified_start_speed`, `unified_end_speed` | ✅ |
| **Distance 範圍** | `segment_distance_start/end/length` | `segment_distance_start/end/length` | ✅ |

---

### 2. **UI 佈局**

兩者都使用相同的 UI 結構：
```python
def _init_ui(self):
    """初始化 UI"""
    layout = QVBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # ✅ 創建 Distance 範圍資訊標籤
    # ...
```

**結論：** ✅ **佈局邏輯完全一致**

---

## 🎯 關鍵差異總結

### ✅ **完全一致的部分**

1. **視覺化核心邏輯**：
   - 相對比例計算公式：`(time - min_time) / time_range`
   - 棒狀圖長度映射：時間短 = 棒短 = 性能好
   - 最快/最慢車手的視覺化效果

2. **繪圖實現**：
   - 棒狀圖顏色（深藍色）
   - 邊框顏色（深藍色）
   - 佈局參數（margin, padding, 高度）
   - 文字字體和位置

3. **代碼結構**：
   - Delegate 類別架構
   - 數據讀取邏輯
   - 錯誤處理機制
   - Widget 主類別設計

### ⚠️ **有意義的差異**

1. **數據欄位名稱**：
   - Brake: `brake_time`, `max_deceleration`
   - Speed: `segment_accel_time`, `max_speed`
   - **原因：** 對應不同的分析維度（煞車 vs 加速）

2. **時間顏色閾值**：
   - Brake: 1.5s / 1.7s（煞車較快）
   - Speed: 7.0s / 8.0s（加速較慢）
   - **原因：** 實際數據範圍不同
   - **影響：** ⚠️ 目前未使用，棒狀圖統一為深藍色

3. **數據來源**：
   - Brake: `reference_brake_zone`（參考煞車區）
   - Speed: `reference_segment`（參考賽道段）
   - **原因：** CLI 分析功能不同（Function 12 vs Function 48）

---

## ✅ 一致性驗證結論

### 🎉 **高度一致**

兩個模組的視覺化邏輯 **幾乎完全一致**：

1. ✅ **核心算法一致**：相對比例計算邏輯完全相同
2. ✅ **繪圖實現一致**：棒狀圖、文字、顏色完全相同
3. ✅ **佈局參數一致**：所有 margin、padding、高度完全相同
4. ✅ **代碼結構一致**：Delegate 和 Widget 架構一致

### 📝 **差異合理**

所有差異都是**有意義且必要**的：
- 數據欄位名稱對應不同分析維度
- 時間閾值對應實際數據範圍
- 數據來源對應不同 CLI 功能

---

## 🔬 測試建議

### 手動測試驗證

1. **啟動 F1T GUI**：`python f1t_gui_main.py`

2. **測試 Brake Performance**：
   - 開啟 All Drivers Brake Performance 視窗
   - 驗證棒狀圖：最快車手棒最短，最慢車手棒最長
   - 驗證顏色：所有棒統一為深藍色
   - 驗證文字：時間標籤顯示正確（例如 `1.480 s`）

3. **測試 Straight Line Speed**：
   - 開啟 All Drivers Straight Line Speed 視窗
   - 驗證棒狀圖：最快車手棒最短，最慢車手棒最長
   - 驗證顏色：所有棒統一為深藍色
   - 驗證文字：時間標籤顯示正確（例如 `9.480 s`）

4. **交叉驗證**：
   - 兩個視窗並排顯示
   - 確認視覺化風格完全一致
   - 確認棒狀圖比例邏輯一致

---

## 📊 最終結論

### ✅ **視覺化邏輯一致性：100%**

**All Drivers Brake Performance** 和 **All Drivers Straight Line Speed** 的視覺化邏輯 **完全一致**：

1. ✅ 核心算法：相對比例計算完全相同
2. ✅ 視覺設計：棒狀圖、顏色、字體完全相同
3. ✅ 代碼結構：Delegate 和 Widget 架構完全相同
4. ✅ 佈局參數：所有參數完全相同

**差異僅在**：
- 數據欄位名稱（對應不同分析維度）
- 時間閾值（對應實際數據範圍，且未使用）

### 🎯 **設計一致性優秀**

兩個模組的實現顯示出 **優秀的設計一致性**：
- 遵循相同的視覺化原則
- 使用相同的繪圖技術
- 保持統一的用戶體驗

---

**比對完成時間：** 2025-10-19 01:10

**比對狀態：** ✅ **完成**

**結論：** 視覺化邏輯 **完全一致** 🎉
