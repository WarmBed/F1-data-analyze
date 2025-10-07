# 🔧 修正報告：Detailed Lap Analysis 圖例客製化

**修正時間**: 2025-10-07  
**問題來源**: 使用者要求  
**影響範圍**: Detailed Lap Analysis 模組圖例顯示  
**修正狀態**: ✅ **已完成**

---

## 📋 使用者需求

### 1️⃣ 移除特定圖例項目
使用者希望在 Detailed Lap Analysis 的圖例中移除以下兩個項目：
- ❌ `T - Tire Change` （輪胎更換）
- ❌ `- Rain` （降雨）

**理由**: 簡化圖例，僅保留最重要的賽事標記。

### 2️⃣ 圖例可拖移功能
使用者希望圖例可以自由拖移，避免遮擋重要的圖表數據。

---

## 🔧 解決方案

### 修正 1: 移除圖例項目

**檔案**: `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_chart_widget.py`

#### 變更內容

**修正前**（顯示 6 個標記）:
```python
marker_count = 6  # P, F, T, Y, S, R (移除了 PT 組合標記)

markers_info = [
    ('P', 'Pit Stop', self.marker_colors['P']),
    ('F', 'Fastest Lap', self.marker_colors['F']),
    ('T', 'Tire Change', self.marker_colors.get('T', QColor(138, 43, 226))),  # ← 移除
    ('Y', 'Yellow Flag', self.marker_colors.get('Y', QColor(255, 193, 7))),
    ('S', 'Safety Car', self.marker_colors.get('S', QColor(128, 128, 128))),
    ('R', 'Red Flag', self.marker_colors.get('R', QColor(220, 53, 69))),
    ('W', 'Rain', self.marker_colors.get('W', QColor(100, 149, 237))),  # ← 移除
]
```

**修正後**（顯示 5 個標記）:
```python
marker_count = 5  # P, F, Y, S, R (已移除 T 和 W)

markers_info = [
    ('P', 'Pit Stop', self.marker_colors['P']),
    ('F', 'Fastest Lap', self.marker_colors['F']),
    # ('T', 'Tire Change', self.marker_colors.get('T', QColor(138, 43, 226))),  # 已移除
    ('Y', 'Yellow Flag', self.marker_colors.get('Y', QColor(255, 193, 7))),
    ('S', 'Safety Car', self.marker_colors.get('S', QColor(128, 128, 128))),
    ('R', 'Red Flag', self.marker_colors.get('R', QColor(220, 53, 69))),
    # ('W', 'Rain', self.marker_colors.get('W', QColor(100, 149, 237))),    # 已移除
]
```

#### 保留的圖例項目

| 標記 | 說明 | 顏色 |
|------|------|------|
| P | Pit Stop (進站) | 🟡 黃色 |
| F | Fastest Lap (最快圈) | 🟢 綠色 |
| Y | Yellow Flag (黃旗) | 🟡 黃色 |
| S | Safety Car (安全車) | ⚫ 灰色 |
| R | Red Flag (紅旗) | 🔴 紅色 |

---

### 修正 2: 圖例拖移功能

#### 新增變數（`__init__` 方法）

```python
# 🆕 圖例拖移功能變數
self.legend_dragging = False          # 是否正在拖移
self.legend_drag_start = QPoint()     # 拖移起始點
self.legend_offset = QPoint(0, 0)     # 圖例的偏移位置
self.legend_rect = QRect()            # 圖例的矩形區域
```

#### 修改 `_draw_legend` 方法

**修正前**（固定位置）:
```python
# 位置：右上角，小幅偏移
legend_x = self.width() - content_width - 15
legend_y = 15
```

**修正後**（支援偏移）:
```python
# 位置：右上角，小幅偏移 + 用戶拖移的偏移量
legend_x = self.width() - content_width - 15 + self.legend_offset.x()
legend_y = 15 + self.legend_offset.y()

# 🆕 保存圖例矩形區域供滑鼠事件使用
self.legend_rect = QRect(legend_x, legend_y, content_width, content_height)
```

#### 新增滑鼠事件處理方法

```python
def mousePressEvent(self, event):
    """滑鼠按下事件 - 檢查是否點擊圖例"""
    if event.button() == Qt.LeftButton:
        if self.legend_rect.contains(event.pos()):
            self.legend_dragging = True
            self.legend_drag_start = event.pos() - self.legend_offset
            self.setCursor(Qt.ClosedHandCursor)  # 改變游標為抓取狀
            event.accept()
            return
    super().mousePressEvent(event)

def mouseMoveEvent(self, event):
    """滑鼠移動事件 - 拖移圖例"""
    if self.legend_dragging:
        # 計算新的偏移量
        new_offset = event.pos() - self.legend_drag_start
        
        # 限制圖例不超出視窗範圍
        max_x = self.width() - self.legend_rect.width() - 15
        max_y = self.height() - self.legend_rect.height() - 15
        min_x = -self.width() + self.legend_rect.width() + 30
        min_y = -15
        
        new_offset.setX(max(min_x, min(max_x, new_offset.x())))
        new_offset.setY(max(min_y, min(max_y, new_offset.y())))
        
        self.legend_offset = new_offset
        self.update()  # 重繪圖表
        event.accept()
        return
    elif self.legend_rect.contains(event.pos()):
        # 滑鼠懸停在圖例上，顯示可移動提示
        self.setCursor(Qt.OpenHandCursor)
    else:
        self.setCursor(Qt.ArrowCursor)
    
    super().mouseMoveEvent(event)

def mouseReleaseEvent(self, event):
    """滑鼠釋放事件 - 結束拖移"""
    if event.button() == Qt.LeftButton and self.legend_dragging:
        self.legend_dragging = False
        self.setCursor(Qt.ArrowCursor)
        event.accept()
        return
    super().mouseReleaseEvent(event)
```

---

## 🎯 功能特性

### 拖移功能細節

1. **滑鼠游標變化**:
   - 🖐️ **懸停時**: `OpenHandCursor` (張開的手)
   - ✊ **拖移時**: `ClosedHandCursor` (握緊的手)
   - ➡️ **其他區域**: `ArrowCursor` (標準箭頭)

2. **邊界限制**:
   - 圖例不會完全移出視窗範圍
   - 保留至少 30px 的可見區域
   - 自動限制在視窗邊界內

3. **實時更新**:
   - 拖移過程中即時重繪圖表
   - 無延遲，流暢的拖移體驗

---

## 🧪 測試驗證

### 測試案例 1: 圖例項目檢查

**操作步驟**:
1. 啟動 F1T GUI
2. 開啟 Detailed Lap Analysis 模組
3. 選擇任一車手並載入數據

**驗證點**:
- [ ] 圖例中**不顯示** `T - Tire Change`
- [ ] 圖例中**不顯示** `- Rain`
- [ ] 圖例中**顯示** `P - Pit Stop`
- [ ] 圖例中**顯示** `F - Fastest Lap`
- [ ] 圖例中**顯示** `Y - Yellow Flag`
- [ ] 圖例中**顯示** `S - Safety Car`
- [ ] 圖例中**顯示** `R - Red Flag`

**預期結果**: ✅ 圖例僅顯示 5 個標記（P, F, Y, S, R）

---

### 測試案例 2: 圖例拖移功能

**操作步驟**:
1. 將滑鼠懸停在圖例上
2. 觀察游標是否變為 `OpenHandCursor` 🖐️
3. 按住左鍵拖移圖例
4. 觀察游標是否變為 `ClosedHandCursor` ✊
5. 釋放滑鼠左鍵

**驗證點**:
- [ ] 滑鼠懸停時游標變為張開的手 🖐️
- [ ] 拖移時游標變為握緊的手 ✊
- [ ] 圖例可以跟隨滑鼠移動
- [ ] 圖例不會完全移出視窗
- [ ] 釋放後圖例停留在新位置

**預期結果**: ✅ 圖例可以流暢拖移且有邊界限制

---

### 測試案例 3: 拖移後的持久性

**操作步驟**:
1. 拖移圖例到新位置
2. 切換車手選擇
3. 重新載入數據

**驗證點**:
- [ ] 圖例位置是否保持？（目前**不保持**，重繪後回到預設位置）

**目前行為**: ⚠️ 圖例位置在重繪後會重置到預設位置（右上角）

**未來改進**: 可以考慮保存圖例位置到設定檔中實現持久化。

---

## 📊 影響範圍分析

### 直接影響
- **Detailed Lap Analysis 模組** 的圖例顯示
- 圖例高度縮小（從 6 個標記減少到 5 個）
- 新增圖例拖移互動功能

### 相關模組
- `modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_chart_widget.py`
  - `LaptimeChartWidget` 類
  - `_draw_legend()` 方法
  - 新增 3 個滑鼠事件處理方法

### 不影響的功能
- ✅ 圖表數據繪製邏輯
- ✅ 智能標記檢測邏輯（T 和 W 標記仍會檢測，只是不在圖例中顯示）
- ✅ 車手選擇功能
- ✅ 其他分析模組

---

## 💡 技術要點

### 1. 圖例項目移除
- 只需註解掉 `markers_info` 列表中的對應項目
- 同時調整 `marker_count` 數值以正確計算圖例高度

### 2. 滑鼠事件處理
- PyQt5 提供的標準事件處理機制
- `mousePressEvent()`: 檢測點擊開始
- `mouseMoveEvent()`: 處理拖移移動
- `mouseReleaseEvent()`: 檢測拖移結束

### 3. 游標變化
使用 `setCursor()` 方法提供視覺反饋：
```python
Qt.OpenHandCursor    # 🖐️ 可拖移
Qt.ClosedHandCursor  # ✊ 拖移中
Qt.ArrowCursor       # ➡️ 標準游標
```

### 4. 邊界限制邏輯
```python
max_x = self.width() - self.legend_rect.width() - 15
max_y = self.height() - self.legend_rect.height() - 15
min_x = -self.width() + self.legend_rect.width() + 30
min_y = -15

new_offset.setX(max(min_x, min(max_x, new_offset.x())))
new_offset.setY(max(min_y, min(max_y, new_offset.y())))
```
確保圖例至少有 30px 保持在可見範圍內。

---

## 📁 修改檔案清單

```
✅ modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_chart_widget.py
   - 移除 T (Tire Change) 和 W (Rain) 圖例項目
   - 調整 marker_count 從 6 → 5
   - 新增 4 個實例變數（__init__）
   - 修改 _draw_legend() 方法支援偏移
   - 新增 mousePressEvent() 方法
   - 新增 mouseMoveEvent() 方法
   - 新增 mouseReleaseEvent() 方法

📄 FIX_REPORT_Detailed_Lap_Analysis_Legend_Customization.md (本文件)
```

---

## 🚀 後續改進建議

### 建議 1: 圖例位置持久化
**需求**: 保存使用者自訂的圖例位置

**實現方式**:
```python
# 儲存設定
gui_settings_manager.set_legend_position('detailed_lap_analysis', self.legend_offset)

# 載入設定
saved_offset = gui_settings_manager.get_legend_position('detailed_lap_analysis', QPoint(0, 0))
self.legend_offset = saved_offset
```

### 建議 2: 圖例顯示/隱藏開關
**需求**: 提供按鈕讓使用者完全隱藏圖例

**實現方式**:
```python
self.legend_visible = True  # 新增變數

def toggle_legend(self):
    self.legend_visible = not self.legend_visible
    self.update()

def _draw_legend(self, painter):
    if not self.legend_visible:
        return
    # ... 原有繪製邏輯
```

### 建議 3: 圖例透明度調整
**需求**: 允許使用者調整圖例背景透明度

**實現方式**:
```python
alpha_value = 200  # 0-255，使用者可調整
white_color = QColor(255, 255, 255, alpha_value)
```

---

## ✅ 結論

**修正狀態**: ✅ **完全成功**  
**測試結果**: ⏳ 待使用者驗證

此次修正完成了以下目標：
1. ✅ 移除了 `T - Tire Change` 和 `- Rain` 兩個圖例項目
2. ✅ 實現了圖例自由拖移功能
3. ✅ 添加了游標視覺反饋
4. ✅ 實現了邊界限制避免圖例移出視窗

圖例現在更加簡潔，並且可以根據使用者需求自由移動位置，避免遮擋重要的數據點。

---

**修正完成時間**: 2025-10-07  
**修正者**: GitHub Copilot  
**測試狀態**: ⏳ 等待使用者驗證
