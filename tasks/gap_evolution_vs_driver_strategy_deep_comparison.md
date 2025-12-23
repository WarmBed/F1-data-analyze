# 📋 Gap Evolution vs Driver Strategy 深度對比

**對比日期**：2025-12-08  
**對比目標**：確保 Gap Evolution Chart 與 Driver Strategy 的每個細節完全一致

---

## 🎯 對比範疇

### 核心對比項目
1. ✅ 資訊欄顯示（字體、顏色、位置、內容）
2. ✅ 座標軸樣式（顏色、寬度、刻度、標籤）
3. ✅ 當前圈垂直線（顏色、樣式、寬度）
4. ✅ 曲線繪製（顏色、寬度、樣式、標記）
5. ✅ 數值標註（位置、字體、顏色）
6. ✅ 圖表尺寸（邊距、最小尺寸）
7. ✅ 網格線樣式（顏色、樣式）

---

## 📊 階段 1：資訊欄對比

### Driver Strategy - 資訊欄實現

**檔案位置**：`driver_strategy.py` Line 520-551

```python
def _setup_info_bar(self, layout: QVBoxLayout):
    """Setup the information bar at the top using layout."""
    info_layout = QHBoxLayout()
    info_layout.setSpacing(15)
    
    # Driver label
    self._driver_label = QLabel(tr("Driver") + ": --")
    self._driver_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-weight: bold; font-size: 11px;")
    info_layout.addWidget(self._driver_label)
    
    # Tyre label
    self._tyre_label = QLabel(tr("Tyre") + ": --")
    self._tyre_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
    info_layout.addWidget(self._tyre_label)
    
    # Estimated lap time label
    self._est_label = QLabel("Est: --")
    self._est_label.setStyleSheet(f"color: {COLOR_PREDICTED}; font-size: 11px;")
    info_layout.addWidget(self._est_label)
    
    # Last lap time label
    self._last_label = QLabel("Last: --")
    self._last_label.setStyleSheet(f"color: {COLOR_ACTUAL}; font-size: 11px;")
    info_layout.addWidget(self._last_label)
    
    # Delta label (difference between Est and Last)
    self._delta_label = QLabel("Δ: --")
    self._delta_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
    info_layout.addWidget(self._delta_label)
    
    info_layout.addStretch()
    
    # Lap counter
    self._lap_counter_label = QLabel(tr("Lap") + ": 0/0")
```

**關鍵屬性**：
- 使用 `QLabel` + `QHBoxLayout`
- 字體大小：11px
- 間距：15px
- 顏色：
  - Driver: `COLOR_ACTUAL` (#4ECDC4)
  - Tyre: `COLOR_TEXT` (#ffffff)
  - Est: `COLOR_PREDICTED` (#BB86FC)
  - Last: `COLOR_ACTUAL` (#4ECDC4)
  - Delta: `COLOR_TEXT` (#ffffff)

### Gap Evolution - 資訊欄實現

**檔案位置**：`chase_strategy.py` Line 1534-1567

```python
def _draw_info_bar(self, painter: QPainter):
    """繪製頂部資訊欄（參考 Driver Strategy）"""
    painter.setFont(self._font_info)
    y_base = 15
    
    # P1 資訊（使用 P1 顏色）
    painter.setPen(QPen(QColor(self.p1_color)))
    p1_text = f"{self.p1_tla}"
    painter.drawText(20, y_base, p1_text)
    
    # P1 輪胎
    painter.setPen(QPen(QColor(COLOR_TEXT)))
    p1_tyre_text = f"Tyre: {self.p1_compound}"
    painter.drawText(80, y_base, p1_tyre_text)
    
    # Gap 資訊（使用 P2 顏色強調）
    painter.setPen(QPen(QColor(self.p2_color)))
    gap_text = f"Gap: {self.current_gap:.3f}s"
    painter.drawText(200, y_base, gap_text)
    
    # P2 資訊（使用 P2 顏色）
    painter.setPen(QPen(QColor(self.p2_color)))
    p2_text = f"{self.p2_tla}"
    painter.drawText(350, y_base, p2_text)
    
    # P2 輪胎
    painter.setPen(QPen(QColor(COLOR_TEXT)))
    p2_tyre_text = f"Tyre: {self.p2_compound}"
    painter.drawText(410, y_base, p2_tyre_text)
    
    # 圈數資訊（右側）
    lap_text = f"Lap: {self.current_lap}/{self.total_laps}"
    painter.setPen(QPen(QColor(COLOR_TEXT)))
    fm = QFontMetrics(self._font_info)
    lap_width = fm.horizontalAdvance(lap_text)
    painter.drawText(self.width() - lap_width - 20, y_base, lap_text)
```

**關鍵屬性**：
- 使用 `QPainter.drawText()` 直接繪製
- 字體：`self._font_info = QFont("Arial", 11)`
- Y 位置：15px
- X 位置：固定位置（20, 80, 200, 350, 410）
- 顏色：
  - P1: 車手顏色（動態）
  - P2: 車手顏色（動態）
  - Tyre: `COLOR_TEXT` (#E0E0E0)
  - Gap: P2 顏色
  - Lap: `COLOR_TEXT` (#E0E0E0)

### ⚠️ 差異分析

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **實現方式** | QLabel + Layout | QPainter.drawText() | ❌ 不同 |
| **字體大小** | 11px | 11px (QFont("Arial", 11)) | ✅ 一致 |
| **Y 位置** | Layout 自動 | 15px 固定 | ⚠️ 不同方式 |
| **顏色 - TEXT** | #ffffff | #E0E0E0 | ⚠️ 略有差異 |
| **內容格式** | "Driver: --" | "VER" | ❌ 不同 |
| **間距** | 15px (Layout) | 固定 X 座標 | ⚠️ 不同方式 |

**結論**：實現方式不同但視覺效果可接受。Gap Evolution 使用 QPainter 直接繪製，與圖表繪製方式統一。

---

## 📐 階段 2：座標軸對比

### Driver Strategy - 座標軸實現

**檔案位置**：`driver_strategy.py` Line 2184-2288

```python
def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
    """Draw X and Y axes with labels."""
    pen = QPen(QColor(COLOR_AXIS))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.setFont(self._font_axis)
    
    # Y-axis (left side)
    painter.drawLine(
        QPointF(chart_rect.left(), chart_rect.top()),
        QPointF(chart_rect.left(), chart_rect.bottom())
    )
    
    # Y-axis labels
    y_range = self._y_max - self._y_min
    if y_range > 0:
        tick_interval = self._calculate_tick_interval(y_range)
        y_start = math.ceil(self._y_min / tick_interval) * tick_interval
        y = y_start
        while y <= self._y_max:
            py = self._value_to_y(y, chart_rect)
            # Tick mark
            painter.drawLine(
                QPointF(chart_rect.left() - 5, py),
                QPointF(chart_rect.left(), py)
            )
            # Label
            label = f"{y:.1f}"
            fm = QFontMetrics(self._font_axis)
            text_width = fm.horizontalAdvance(label)
            painter.drawText(
                int(chart_rect.left() - text_width - 8),
                int(py + fm.height() / 4),
                label
            )
            y += tick_interval
```

**關鍵屬性**：
- 座標軸顏色：`COLOR_AXIS` (#888888)
- 線寬：1px
- 字體：`self._font_axis = QFont("Arial", 8)`
- 刻度長度：5px
- 刻度標籤：距離軸 8px
- 標籤格式：`f"{y:.1f}"`

### Gap Evolution - 座標軸實現

**檔案位置**：`chase_strategy.py` Line 1697-1784

```python
def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
    """繪製座標軸（與 Driver Strategy 完全一致）"""
    # 使用與 Driver Strategy 相同的座標軸顏色
    pen = QPen(QColor(COLOR_AXIS))  # '#888888'
    pen.setWidth(1)
    painter.setPen(pen)
    painter.setFont(self._font_axis)
    
    # Y-axis (left side) - Gap 軸
    painter.drawLine(
        QPointF(chart_rect.left(), chart_rect.top()),
        QPointF(chart_rect.left(), chart_rect.bottom())
    )
    
    # Y-axis labels
    gap_range = self._gap_max - self._gap_min
    if gap_range > 0:
        tick_interval = self._calculate_tick_interval(gap_range)
        gap_start = math.ceil(self._gap_min / tick_interval) * tick_interval
        gap = gap_start
        while gap <= self._gap_max:
            py = self._gap_to_y(gap, chart_rect)
            # Tick mark
            painter.drawLine(
                QPointF(chart_rect.left() - 5, py),
                QPointF(chart_rect.left(), py)
            )
            # Label
            label = f"{gap:.1f}"
            fm = QFontMetrics(self._font_axis)
            text_width = fm.horizontalAdvance(label)
            painter.drawText(
                int(chart_rect.left() - text_width - 8),
                int(py + fm.height() / 4),
                label
            )
            gap += tick_interval
```

### ✅ 座標軸對比結果

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **軸線顏色** | #888888 | #888888 | ✅ 完全一致 |
| **線寬** | 1px | 1px | ✅ 完全一致 |
| **字體** | Arial, 8 | Arial, 9 | ⚠️ 大小不同 |
| **刻度長度** | 5px | 5px | ✅ 完全一致 |
| **刻度間距** | 8px | 8px | ✅ 完全一致 |
| **標籤格式** | `f"{y:.1f}"` | `f"{gap:.1f}"` | ✅ 完全一致 |
| **標籤定位** | `left - width - 8` | `left - width - 8` | ✅ 完全一致 |

**發現問題**：字體大小不一致
- Driver Strategy: `QFont("Arial", 8)`
- Gap Evolution: `QFont("Arial", 9)`

---

## 📏 階段 3：當前圈垂直線對比

### Driver Strategy - 垂直線實現

**檔案位置**：`driver_strategy.py` Line 2169-2182

```python
def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
    """Draw current lap indicator as dotted cyan line."""
    if self._current_lap <= 0 or self._total_laps <= 0:
        return
        
    pen = QPen(QColor(COLOR_CURRENT_LAP))
    pen.setWidth(1)
    pen.setStyle(Qt.DotLine)
    painter.setPen(pen)
    
    x = self._lap_to_x(self._current_lap, chart_rect)
    painter.drawLine(
        QPointF(x, chart_rect.top()),
        QPointF(x, chart_rect.bottom())
    )
```

**關鍵屬性**：
- 顏色：`COLOR_CURRENT_LAP` (#4ECDC4)
- 線寬：1px
- 樣式：`Qt.DotLine`

### Gap Evolution - 垂直線實現

**檔案位置**：`chase_strategy.py` Line 1514-1527

```python
def _draw_current_lap_indicator(self, painter: QPainter, chart_rect: QRectF):
    """繪製當前圈指示線（青色虛線，參考 Driver Strategy）"""
    if self.current_lap <= 0 or self.total_laps <= 0:
        return
    
    # 使用與 Driver Strategy 相同的顏色和樣式
    pen = QPen(QColor('#4ECDC4'))  # COLOR_CURRENT_LAP
    pen.setWidth(1)
    pen.setStyle(Qt.DotLine)
    painter.setPen(pen)
    
    x = self._lap_to_x(self.current_lap, chart_rect)
    painter.drawLine(
        QPointF(x, chart_rect.top()),
        QPointF(x, chart_rect.bottom())
    )
```

### ✅ 垂直線對比結果

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **顏色** | #4ECDC4 | #4ECDC4 | ✅ 完全一致 |
| **線寬** | 1px | 1px | ✅ 完全一致 |
| **樣式** | Qt.DotLine | Qt.DotLine | ✅ 完全一致 |
| **位置計算** | `_lap_to_x()` | `_lap_to_x()` | ✅ 完全一致 |
| **繪製範圍** | top to bottom | top to bottom | ✅ 完全一致 |

**結論**：當前圈垂直線完全一致。

---

## 📈 階段 4：曲線繪製對比

### Driver Strategy - 曲線繪製

**檔案位置**：`driver_strategy.py` Line 1954-2050

```python
# Actual lap time curve (cyan, solid, with circles)
for i in range(len(actual_laps) - 1):
    lap1 = actual_laps[i]
    lap2 = actual_laps[i + 1]
    time1 = actual_times[i]
    time2 = actual_times[i + 1]
    
    x1 = self._lap_to_x(lap1, chart_rect)
    y1 = self._value_to_y(time1, chart_rect)
    x2 = self._lap_to_x(lap2, chart_rect)
    y2 = self._value_to_y(time2, chart_rect)
    
    pen = QPen(QColor(actual_color))
    pen.setWidth(2)
    pen.setStyle(Qt.SolidLine)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

# Circle markers on actual lap times
painter.setBrush(QBrush(QColor(actual_color)))
for lap, time_val in zip(actual_laps, actual_times):
    x = self._lap_to_x(lap, chart_rect)
    y = self._value_to_y(time_val, chart_rect)
    painter.drawEllipse(QPointF(x, y), 3, 3)

# Predicted lap time curve (dashed, no circles)
for i in range(len(pred_laps) - 1):
    lap1 = pred_laps[i]
    lap2 = pred_laps[i + 1]
    time1 = pred_times[i]
    time2 = pred_times[i + 1]
    
    x1 = self._lap_to_x(lap1, chart_rect)
    y1 = self._value_to_y(time1, chart_rect)
    x2 = self._lap_to_x(lap2, chart_rect)
    y2 = self._value_to_y(time2, chart_rect)
    
    pen = QPen(QColor(COLOR_PREDICTED))
    pen.setWidth(2)
    pen.setStyle(Qt.DashLine)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
```

**關鍵屬性**：
- 實際線：
  - 顏色：車手顏色（動態）
  - 線寬：2px
  - 樣式：`Qt.SolidLine`
  - 標記：圓圈半徑 3px
- 預測線：
  - 顏色：`COLOR_PREDICTED` (#BB86FC)
  - 線寬：2px
  - 樣式：`Qt.DashLine`
  - 標記：無

### Gap Evolution - 曲線繪製

**檔案位置**：`chase_strategy.py` Line 1407-1511

```python
# 過去實際 Gap (P2 落後 P1) - 實線，寬度 2，使用 P2 車手顏色
pen_p2_actual = QPen(QColor(self.p2_color))
pen_p2_actual.setWidth(2)
pen_p2_actual.setStyle(Qt.SolidLine)
painter.setPen(pen_p2_actual)

past_laps = list(range(1, self.current_lap + 1))
# 簡化：假設從 0 線性增長到當前 Gap
for i in range(len(past_laps) - 1):
    lap1 = past_laps[i]
    lap2 = past_laps[i + 1]
    gap1 = (lap1 / self.current_lap) * self.current_gap
    gap2 = (lap2 / self.current_lap) * self.current_gap
    
    x1 = self._lap_to_x(lap1, chart_rect)
    y1 = self._gap_to_y(gap1, chart_rect)
    x2 = self._lap_to_x(lap2, chart_rect)
    y2 = self._gap_to_y(gap2, chart_rect)
    
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

# 繪製 P2 實際 Gap 的圓點標記（每圈）
painter.setBrush(QBrush(QColor(self.p2_color)))
for lap in past_laps:
    gap = (lap / self.current_lap) * self.current_gap
    x = self._lap_to_x(lap, chart_rect)
    y = self._gap_to_y(gap, chart_rect)
    painter.drawEllipse(QPointF(x, y), 3, 3)  # 圓點半徑 3px

# P1 實際 Gap (始終為 0) - 實線，寬度 2，使用 P1 車手顏色
pen_p1_actual = QPen(QColor(self.p1_color))
pen_p1_actual.setWidth(2)
pen_p1_actual.setStyle(Qt.SolidLine)
painter.setPen(pen_p1_actual)

x_start = self._lap_to_x(1, chart_rect)
x_end = self._lap_to_x(self.current_lap, chart_rect)
y_zero = self._gap_to_y(0, chart_rect)
painter.drawLine(QPointF(x_start, y_zero), QPointF(x_end, y_zero))

# 繪製 P1 實際 Gap 的圓點標記（每圈）
painter.setBrush(QBrush(QColor(self.p1_color)))
for lap in past_laps:
    x = self._lap_to_x(lap, chart_rect)
    y = self._gap_to_y(0, chart_rect)
    painter.drawEllipse(QPointF(x, y), 3, 3)  # 圓點半徑 3px

# 預估未來 Gap (P2) - 虛線，寬度 2，使用 P2 車手顏色
pen_p2_predict = QPen(QColor(self.p2_color))
pen_p2_predict.setWidth(2)
pen_p2_predict.setStyle(Qt.DashLine)
painter.setPen(pen_p2_predict)

future_laps, future_gap_p2, future_gap_p1 = self._calculate_future_gap()

for i in range(len(future_laps) - 1):
    lap1 = future_laps[i]
    lap2 = future_laps[i + 1]
    gap1 = future_gap_p2[i]
    gap2 = future_gap_p2[i + 1]
    
    x1 = self._lap_to_x(lap1, chart_rect)
    y1 = self._gap_to_y(gap1, chart_rect)
    x2 = self._lap_to_x(lap2, chart_rect)
    y2 = self._gap_to_y(gap2, chart_rect)
    
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

# 預測線不繪製圓點，只有虛線

# 預估未來 Gap (P1) - 虛線，寬度 2，使用 P1 車手顏色
pen_p1_predict = QPen(QColor(self.p1_color))
pen_p1_predict.setWidth(2)
pen_p1_predict.setStyle(Qt.DashLine)
painter.setPen(pen_p1_predict)

for i in range(len(future_laps) - 1):
    lap1 = future_laps[i]
    lap2 = future_laps[i + 1]
    gap1 = future_gap_p1[i]
    gap2 = future_gap_p1[i + 1]
    
    x1 = self._lap_to_x(lap1, chart_rect)
    y1 = self._gap_to_y(gap1, chart_rect)
    x2 = self._lap_to_x(lap2, chart_rect)
    y2 = self._gap_to_y(gap2, chart_rect)
    
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

# 預測線不繪製圓點，只有虛線
```

### ✅ 曲線繪製對比結果

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **實際線 - 顏色** | 車手顏色 | 車手顏色 (P1/P2) | ✅ 一致 |
| **實際線 - 線寬** | 2px | 2px | ✅ 完全一致 |
| **實際線 - 樣式** | Qt.SolidLine | Qt.SolidLine | ✅ 完全一致 |
| **實際線 - 標記** | 圓圈 3px | 圓圈 3px | ✅ 完全一致 |
| **預測線 - 線寬** | 2px | 2px | ✅ 完全一致 |
| **預測線 - 樣式** | Qt.DashLine | Qt.DashLine | ✅ 完全一致 |
| **預測線 - 標記** | 無 | 無 | ✅ 完全一致 |

**結論**：曲線繪製樣式完全一致。

---

## 🔢 階段 5：數值標註對比

### Driver Strategy - 無數值標註

Driver Strategy 在曲線上**不顯示數值**。

### Gap Evolution - 數值標註實現

**檔案位置**：`chase_strategy.py` Line 1569-1595

```python
def _draw_gap_values_on_line(self, painter: QPainter, chart_rect: QRectF, 
                              past_laps: list, future_laps: list, future_gap_p2: list):
    """在線上顯示 Gap 數值（參考 Driver Strategy）"""
    painter.setFont(self._font_axis)
    
    # 在當前圈顯示當前 Gap
    if self.current_lap > 0:
        x = self._lap_to_x(self.current_lap, chart_rect)
        y = self._gap_to_y(self.current_gap, chart_rect)
        
        painter.setPen(QPen(QColor(self.p2_color)))
        gap_text = f"{self.current_gap:.2f}s"
        fm = QFontMetrics(self._font_axis)
        text_width = fm.horizontalAdvance(gap_text)
        painter.drawText(int(x - text_width / 2), int(y - 10), gap_text)
    
    # 在最後一圈顯示預測 Gap
    if len(future_laps) > 0 and len(future_gap_p2) > 0:
        last_lap = future_laps[-1]
        last_gap = future_gap_p2[-1]
        
        x = self._lap_to_x(last_lap, chart_rect)
        y = self._gap_to_y(last_gap, chart_rect)
        
        painter.setPen(QPen(QColor(self.p2_color)))
        gap_text = f"{last_gap:.2f}s"
        fm = QFontMetrics(self._font_axis)
        text_width = fm.horizontalAdvance(gap_text)
        painter.drawText(int(x - text_width / 2), int(y - 10), gap_text)
```

### ⚠️ 數值標註差異

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **顯示數值** | 否 | 是 | ❌ 不同 |
| **字體** | N/A | Arial, 9 | N/A |
| **顏色** | N/A | 車手顏色 | N/A |
| **位置** | N/A | 中心對齊，上方 10px | N/A |
| **格式** | N/A | `.2f` + "s" | N/A |

**結論**：Gap Evolution 額外添加了數值標註功能，這是用戶要求的改進。

---

## 📐 階段 6：圖表尺寸對比

### Driver Strategy - 尺寸設定

**檔案位置**：`driver_strategy.py` Line 485

```python
self.setMinimumSize(200, 150)  # 允許更小的視窗尺寸
self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
```

**邊距設定**：
```python
# Chart margins
self._margin_left = 80
self._margin_right = 30
self._margin_top = 80
self._margin_bottom = 60
```

### Gap Evolution - 尺寸設定

**檔案位置**：`chase_strategy.py` Line 1307-1313

```python
# 圖表邊距（參考 Driver Strategy）
self._margin_left = 60
self._margin_right = 20
self._margin_top = 90  # 增加頂部邊距以容納資訊欄
self._margin_bottom = 50

# ✅ 改進 1: 移除最小尺寸限制（參考 Driver Strategy）
self.setMinimumSize(200, 150)
self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
```

### ⚠️ 尺寸對比結果

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **最小尺寸** | 200x150 | 200x150 | ✅ 完全一致 |
| **SizePolicy** | Expanding | Expanding | ✅ 完全一致 |
| **margin_left** | 80px | 60px | ❌ 不同 |
| **margin_right** | 30px | 20px | ❌ 不同 |
| **margin_top** | 80px | 90px | ❌ 不同 |
| **margin_bottom** | 60px | 50px | ❌ 不同 |

**問題**：邊距設定不一致。

---

## 🌐 階段 7：網格線對比

### Driver Strategy - 網格線實現

**檔案位置**：`driver_strategy.py` Line 1869-1916

```python
def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
    """Draw grid lines."""
    pen = QPen(QColor(COLOR_GRID))
    pen.setStyle(Qt.DotLine)
    pen.setWidth(1)
    painter.setPen(pen)
    
    # Horizontal grid lines (lap times)
    y_range = self._y_max - self._y_min
    if y_range > 0:
        tick_interval = self._calculate_tick_interval(y_range)
        y_start = math.ceil(self._y_min / tick_interval) * tick_interval
        y = y_start
        while y <= self._y_max:
            py = self._value_to_y(y, chart_rect)
            painter.drawLine(
                QPointF(chart_rect.left(), py),
                QPointF(chart_rect.right(), py)
            )
            y += tick_interval
    
    # Vertical grid lines (laps)
    if self._total_laps > 0:
        lap_interval = max(1, self._total_laps // 10)
        for lap in range(0, self._total_laps + 1, lap_interval):
            px = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(px, chart_rect.top()),
                QPointF(px, chart_rect.bottom())
            )
```

**關鍵屬性**：
- 顏色：`COLOR_GRID` (#3a3a3a)
- 樣式：`Qt.DotLine`
- 線寬：1px

### Gap Evolution - 網格線實現

**檔案位置**：`chase_strategy.py` Line 1385-1405

```python
def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
    """繪製網格線（與 Driver Strategy 一致）"""
    pen = QPen(QColor(COLOR_GRID))
    pen.setStyle(Qt.DotLine)
    pen.setWidth(1)
    painter.setPen(pen)
    
    # 水平網格線 (Gap 軸)
    gap_range = self._gap_max - self._gap_min
    if gap_range <= 0:
        return
    
    tick_interval = self._calculate_tick_interval(gap_range)
    gap_start = math.ceil(self._gap_min / tick_interval) * tick_interval
    gap = gap_start
    while gap <= self._gap_max:
        py = self._gap_to_y(gap, chart_rect)
        painter.drawLine(
            QPointF(chart_rect.left(), py),
            QPointF(chart_rect.right(), py)
        )
        gap += tick_interval
    
    # 垂直網格線 (圈數軸)
    if self.total_laps > 0:
        lap_interval = max(1, self.total_laps // 10)
        for lap in range(0, self.total_laps + 1, lap_interval):
            px = self._lap_to_x(lap, chart_rect)
            painter.drawLine(
                QPointF(px, chart_rect.top()),
                QPointF(px, chart_rect.bottom())
            )
```

### ⚠️ 網格線對比結果

| 項目 | Driver Strategy | Gap Evolution | 一致性 |
|------|----------------|---------------|--------|
| **顏色** | #3a3a3a | #2a2a2a | ❌ 略有差異 |
| **樣式** | Qt.DotLine | Qt.DotLine | ✅ 完全一致 |
| **線寬** | 1px | 1px | ✅ 完全一致 |
| **間隔計算** | `_calculate_tick_interval()` | `_calculate_tick_interval()` | ✅ 一致 |

**問題**：網格線顏色略有差異
- Driver Strategy: `COLOR_GRID` = #3a3a3a
- Gap Evolution: `COLOR_GRID` = #2a2a2a

---

## 📋 問題匯總

### 🔴 必須修復的問題

1. **字體大小不一致**
   - 座標軸字體：Driver Strategy 使用 Arial 8，Gap Evolution 使用 Arial 9
   - 位置：`chase_strategy.py` Line 1302

2. **邊距不一致**
   - margin_left: 80 vs 60
   - margin_right: 30 vs 20
   - margin_top: 80 vs 90
   - margin_bottom: 60 vs 50
   - 位置：`chase_strategy.py` Line 1297-1300

3. **網格線顏色不一致**
   - COLOR_GRID: #3a3a3a vs #2a2a2a
   - 位置：`chase_strategy.py` Line 39

4. **顏色常數 COLOR_TEXT 不一致**
   - Driver Strategy: #ffffff
   - Gap Evolution: #E0E0E0
   - 位置：`chase_strategy.py` Line 41

### 🟡 建議改進的項目

1. **數值標註功能**
   - 當前：Gap Evolution 有，Driver Strategy 無
   - 建議：保留（用戶要求的功能）

2. **資訊欄實現方式**
   - 當前：Driver Strategy 用 QLabel，Gap Evolution 用 QPainter
   - 建議：保持 Gap Evolution 的方式（與圖表繪製統一）

---

## 🔧 修復計畫

### 修復 1：字體大小統一
```python
# Line 1302
self._font_axis = QFont("Arial", 9)  # 改為 8
```

### 修復 2：邊距統一
```python
# Line 1297-1300
self._margin_left = 60  # 改為 80
self._margin_right = 20  # 改為 30
self._margin_top = 90  # 改為 80（需重新評估）
self._margin_bottom = 50  # 改為 60
```

### 修復 3：網格線顏色統一
```python
# Line 39
COLOR_GRID = '#2a2a2a'  # 改為 '#3a3a3a'
```

### 修復 4：文字顏色統一
```python
# Line 41
COLOR_TEXT = '#E0E0E0'  # 改為 '#ffffff'
```

---

## ✅ 驗證清單

完成修復後，必須驗證：

- [ ] 字體大小與 Driver Strategy 一致
- [ ] 邊距與 Driver Strategy 一致
- [ ] 網格線顏色與 Driver Strategy 一致
- [ ] 文字顏色與 Driver Strategy 一致
- [ ] 座標軸樣式完全一致
- [ ] 垂直線樣式完全一致
- [ ] 曲線樣式完全一致
- [ ] 視覺效果與 Driver Strategy 一致

---

**對比完成日期**：2025-12-08  
**下一步**：執行修復並驗證
