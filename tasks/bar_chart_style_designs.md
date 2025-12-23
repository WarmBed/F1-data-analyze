# 棒狀圖風格設計方案

## 當前風格（風格 A）- 雙色實心/虛線

### 視覺效果
```
▓▓▓▓▓▓▓▓░░░░  1.20s → 1.37s
└─實心─┘└虛線┘
```

### 特點
- 100-300: 深綠色實心 `RGB(40, 180, 80)`
- 300-最高速: 淺綠色虛線填充 `RGB(220, 245, 220)`
- 邊框: 3px 粗邊框

### 代碼
```python
# 實心棒
painter.fillRect(solid_rect, QBrush(QColor(40, 180, 80)))
painter.setPen(QPen(QColor(20, 120, 50), 3))
painter.drawRect(solid_rect)

# 虛線棒
painter.fillRect(dashed_rect, QBrush(QColor(220, 245, 220)))
painter.setPen(QPen(QColor(100, 160, 120), 3, Qt.DashLine))
painter.drawRect(dashed_rect)
```

---

## 風格 B - 漸層色棒狀圖

### 視覺效果
```
████████████░░░  1.20s → 1.37s
└─深綠漸層淺綠─┘
```

### 特點
- 使用 QLinearGradient 從深綠到淺綠
- 無虛線，整體為實心漸層
- 視覺上更流暢

### 代碼
```python
from PyQt5.QtGui import QLinearGradient

gradient = QLinearGradient(base_x, base_y, base_x + speed_max_pos, base_y)
gradient.setColorAt(0.0, QColor(30, 180, 80))   # 深綠（100 km/h）
gradient.setColorAt(0.5, QColor(80, 200, 120))  # 中綠（200 km/h）
gradient.setColorAt(1.0, QColor(150, 220, 180)) # 淺綠（最高速）

painter.fillRect(bar_rect, QBrush(gradient))
painter.setPen(QPen(QColor(20, 100, 60), 2))
painter.drawRect(bar_rect)
```

---

## 風格 C - 分段色塊（推薦）

### 視覺效果
```
██████████▒▒▒  1.20s → 1.37s
└─深藍─┘└淺灰┘
```

### 特點
- 100-300: 深藍色實心 `RGB(50, 100, 180)`
- 300-最高速: 淺灰色實心 `RGB(200, 200, 200)`
- 對比更強，視覺更清晰
- 更專業的數據視覺化風格

### 代碼
```python
# 實心棒（100-300）: 深藍色
painter.fillRect(solid_rect, QBrush(QColor(50, 100, 180)))
painter.setPen(QPen(QColor(30, 70, 140), 2))
painter.drawRect(solid_rect)

# 延伸棒（300-最高速）: 淺灰色
painter.fillRect(dashed_rect, QBrush(QColor(200, 200, 200)))
painter.setPen(QPen(QColor(150, 150, 150), 2))
painter.drawRect(dashed_rect)
```

---

## 風格 D - 圓角現代風格

### 視覺效果
```
╔════════════╗░░  1.20s → 1.37s
╚════════════╝
```

### 特點
- 圓角矩形（更現代）
- 柔和的陰影效果
- 100-300: 青色 `RGB(70, 150, 200)`
- 300-最高速: 半透明灰 `RGBA(180, 180, 180, 100)`

### 代碼
```python
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor

# 實心圓角棒
solid_rect = QRectF(base_x, base_y, speed_300_pos, bar_height)
painter.setBrush(QBrush(QColor(70, 150, 200)))
painter.setPen(QPen(QColor(50, 120, 170), 2))
painter.drawRoundedRect(solid_rect, 5, 5)  # 圓角半徑 5px

# 延伸圓角棒
dashed_rect = QRectF(base_x + speed_300_pos, base_y, speed_max_pos - speed_300_pos, bar_height)
painter.setBrush(QBrush(QColor(180, 180, 180, 100)))
painter.setPen(QPen(QColor(150, 150, 150), 2))
painter.drawRoundedRect(dashed_rect, 5, 5)
```

---

## 風格 E - 進度條風格（Material Design）

### 視覺效果
```
█████████████░░░░  1.20s → 1.37s
└── 橙色進度 ─┘
```

### 特點
- Material Design 風格
- 100-300: 橙色 `RGB(255, 152, 0)`
- 300-最高速: 淺灰背景 `RGB(224, 224, 224)`
- 高度較矮（12px），更像進度條

### 代碼
```python
bar_height = 12  # 較矮的進度條

# 背景灰色條（全寬）
bg_rect = QRectF(base_x, base_y, total_width, bar_height)
painter.fillRect(bg_rect, QBrush(QColor(224, 224, 224)))

# 前景橙色進度（100-300）
fg_rect = QRectF(base_x, base_y, speed_300_pos, bar_height)
painter.fillRect(fg_rect, QBrush(QColor(255, 152, 0)))

# 延伸淺橙色（300-最高速）
ext_rect = QRectF(base_x + speed_300_pos, base_y, speed_max_pos - speed_300_pos, bar_height)
painter.fillRect(ext_rect, QBrush(QColor(255, 200, 100)))

# 無邊框
```

---

## 風格 F - 雙條對比（數據分析風格）

### 視覺效果
```
████████████      100-300: 1.20s
░░░░░░░░░░░░░░░░  100-最高速: 1.37s
```

### 特點
- 兩條平行的棒狀圖
- 上條: 100-300 時間（深色）
- 下條: 100-最高速 時間（淺色）
- 直觀比較兩個時間段

### 代碼
```python
bar_height = 8  # 較矮的雙條

# 上條: 100-300 時間
top_y = base_y
top_width = (accel_100_300_time / self.max_time) * total_width
top_rect = QRectF(base_x, top_y, top_width, bar_height)
painter.fillRect(top_rect, QBrush(QColor(60, 120, 180)))

# 下條: 100-最高速 時間
bottom_y = base_y + bar_height + 4
bottom_width = speed_max_pos
bottom_rect = QRectF(base_x, bottom_y, bottom_width, bar_height)
painter.fillRect(bottom_rect, QBrush(QColor(180, 200, 220)))
```

---

## 推薦排序

### 1. **風格 C - 分段色塊**（最推薦）
   - ✅ 對比最強，視覺最清晰
   - ✅ 專業的數據視覺化風格
   - ✅ 藍灰配色更商務

### 2. **風格 E - 進度條風格**
   - ✅ 現代 Material Design
   - ✅ 簡潔明瞭
   - ⚠️ 較矮，適合顯示多行

### 3. **風格 D - 圓角現代風格**
   - ✅ 最美觀
   - ✅ 柔和的視覺效果
   - ⚠️ 可能不夠專業

### 4. **風格 B - 漸層色**
   - ✅ 流暢的視覺過渡
   - ⚠️ 可能對比不夠明顯

### 5. **風格 F - 雙條對比**
   - ✅ 數據對比清晰
   - ⚠️ 佔用垂直空間較多

### 6. **風格 A - 當前風格**
   - ⚠️ 虛線可能不夠清晰
   - ⚠️ 綠色系不夠專業

---

## 配色建議

### 專業商務風格（推薦）
```python
實心: RGB(50, 100, 180)   # 深藍
延伸: RGB(200, 200, 200)  # 淺灰
邊框: RGB(30, 70, 140)    # 深藍邊框
```

### 科技風格
```python
實心: RGB(0, 188, 212)    # Cyan
延伸: RGB(224, 247, 250)  # 淺 Cyan
邊框: RGB(0, 151, 167)    # 深 Cyan
```

### 暖色風格
```python
實心: RGB(255, 152, 0)    # 橙色
延伸: RGB(255, 224, 178)  # 淺橙
邊框: RGB(230, 120, 0)    # 深橙
```

---

## 實現方式

我會創建所有 6 種風格的實現代碼，每個風格一個獨立的 `paint_style_X()` 方法，然後你可以選擇一個。或者我可以在同一個 Demo 中顯示所有風格供你比較。

**請告訴我你想要：**
1. 直接實現某一種風格（告訴我風格代號 A-F）
2. 創建一個 Demo 展示所有風格
3. 混合幾種風格的特點創造新風格
