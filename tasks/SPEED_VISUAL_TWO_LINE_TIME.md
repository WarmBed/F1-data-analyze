# 加速性能視覺化更新 - 兩行時間顯示

## 📅 更新日期
2025-10-14

## 🎯 更新目標
根據用戶需求：
1. ✅ **取消圖表視圖**（Matplotlib）- 只保留表格視圖
2. ✅ **在加速性能視覺化棒狀圖右側顯示兩個時間**（分兩行）：
   - 第一行：100→300 km/h 的時間（深藍色）
   - 第二行：100→最高速的時間（深灰色）

## ✅ 完成的更新

### 1. 取消雙視圖架構
**修改檔案：** `all_drivers_straight_line_speed_mdi.py`

**變更內容：**
```python
# 前：導入雙視圖容器
from .all_drivers_straight_line_speed_dual_view import AllDriversStraightLineSpeedDualView
widget = AllDriversStraightLineSpeedDualView(parent=None)

# 後：只導入表格視圖
from .all_drivers_straight_line_speed_table_widget import AllDriversStraightLineSpeedTableWidget
widget = AllDriversStraightLineSpeedTableWidget(parent=None)
```

**效果：**
- ❌ 移除 Matplotlib 圖表視圖
- ❌ 移除 QTabWidget 切換功能
- ✅ 只保留專業的表格視圖
- ✅ 避免 Matplotlib 初始化阻塞問題

### 2. 修改時間標籤顯示
**修改檔案：** `all_drivers_straight_line_speed_table_widget.py`

**AccelerationBarDelegate.paint() 方法變更：**

#### 原始版本（單行合併顯示）：
```python
# 顯示格式: "1.20s → 1.37s"
painter.drawText(text_x, text_y, f"{accel_100_300_time:.2f}s → {time_to_max:.2f}s")
```

#### 更新版本（兩行分開顯示）：
```python
# 第一行：100→300 km/h 時間（深藍色）
painter.setFont(QFont("Arial", 9, QFont.Bold))
painter.setPen(QPen(QColor(50, 100, 180)))  # 深藍色
text_y_line1 = int(base_y + 6)
painter.drawText(text_x, text_y_line1, f"{accel_100_300_time:.3f}s")

# 第二行：100→最高速時間（深灰色）
painter.setFont(QFont("Arial", 9, QFont.Bold))
painter.setPen(QPen(QColor(80, 80, 80)))  # 深灰色
text_y_line2 = int(base_y + 20)
painter.drawText(text_x, text_y_line2, f"{time_to_max:.3f}s")
```

#### 視覺化效果：
```
┌─────────────────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░     1.234s  ← 深藍色       │
│                          1.567s  ← 深灰色       │
│  └─深藍──┘└─淺灰─┘                             │
│  (100-300) (300-max)                            │
└─────────────────────────────────────────────────┘
```

### 3. 優化欄位配置
**修改內容：**
```python
# 欄位 8 寬度調整
table.setColumnWidth(8, 450)  # 前：550px，後：450px（優化空間）

# 行高調整
table.verticalHeader().setDefaultSectionSize(40)  # 前：35px，後：40px（容納兩行）
```

**原因：**
- 兩行時間需要更多垂直空間（40px）
- 棒狀圖寬度可以稍微縮小（450px 已足夠）
- X 軸位置精確對齊：
  - 第一行時間：Y = base_y + 6px
  - 第二行時間：Y = base_y + 20px

## 📊 完整欄位結構

### 表格欄位列表（9 個欄位）
| 索引 | 欄位名稱 | 寬度 | 說明 |
|------|---------|------|------|
| 0 | 排名 | 60px | 位置排序 |
| 1 | 車手 | 100px | 車手代碼 + 車隊背景色 |
| 2 | 車隊 | 120px | 車隊全名 |
| 3 | 最高速度 | 120px | km/h，顏色編碼 |
| 4 | 加速時間 (100→300) | 140px | 秒數 |
| 5 | 距離 (100→300) | 120px | 米 |
| 6 | 平均加速度 (100→300) | 160px | m/s² |
| 7 | 最高時速時間 | 120px | 100→最高速秒數 |
| 8 | 加速性能視覺化 | 450px | **棒狀圖 + 兩行時間** |

### 欄位 8 詳細說明
**視覺元素：**
1. **深藍實心棒**：100→300 km/h 區間
2. **淺灰實心棒**：300→最高速區間
3. **第一行時間**（深藍色粗體）：100→300 km/h 時間（例如："1.234s"）
4. **第二行時間**（深灰色粗體）：100→最高速時間（例如："1.567s"）

**數據來源：**
```python
accel_100_300_time = index.data(Qt.UserRole + 2)  # 100-300 時間
time_to_max = index.data(Qt.UserRole)             # 100-最高速時間
```

## 🎨 配色方案

### 時間標籤配色
- **第一行時間**：RGB(50, 100, 180) - 深藍色
  - 對應深藍色棒狀圖（100→300 km/h）
  - 字體：Arial 9pt Bold
  
- **第二行時間**：RGB(80, 80, 80) - 深灰色
  - 對應整體加速性能（100→最高速）
  - 字體：Arial 9pt Bold

### 棒狀圖配色（保持不變）
- **深藍實心**：RGB(50, 100, 180) - 100→300 km/h
- **淺灰實心**：RGB(200, 200, 200) - 300→最高速

## 📐 佈局計算

### 時間標籤位置
```python
text_x = int(base_x + speed_max_pos + 15)  # 棒狀圖右側 15px
text_y_line1 = int(base_y + 6)             # 第一行，上方 6px
text_y_line2 = int(base_y + 20)            # 第二行，下方 20px
```

### 相對時間比例（保持不變）
```python
relative_ratio = (time_to_max - min_time) / (max_time - min_time)
speed_max_pos = total_width * relative_ratio
```

**效果：**
- 快車手：棒狀圖較短，時間標籤靠左
- 慢車手：棒狀圖較長，時間標籤靠右
- 差異對比清晰可見

## 🔧 技術實現細節

### QPainter 繪製順序
1. 繪製背景（白色/高亮）
2. 繪製深藍實心棒（100→300）
3. 繪製淺灰實心棒（300→最高速）
4. **繪製第一行時間（深藍色）**
5. **繪製第二行時間（深灰色）**

### 字體設定
```python
painter.setFont(QFont("Arial", 9, QFont.Bold))
```

### 顏色設定
```python
# 第一行時間
painter.setPen(QPen(QColor(50, 100, 180)))

# 第二行時間
painter.setPen(QPen(QColor(80, 80, 80)))
```

## 🧪 測試驗證

### 測試案例：2025 Japan Qualifying
```bash
python modules\gui\all_drivers_straight_line_speed_analysis\demo_japan_q.py
```

### 預期結果
✅ **視覺效果：**
- 每行棒狀圖右側顯示兩行時間
- 第一行時間（深藍色）：100→300 km/h
- 第二行時間（深灰色）：100→最高速
- 行高 40px 足夠容納兩行文字

✅ **數據正確性：**
- 第一行時間 ≤ 第二行時間（100→300 必然快於 100→最高速）
- 時間格式：3 位小數（例如："1.234s"）
- 顏色對應正確

✅ **佈局一致性：**
- 20 位車手所有行的時間標籤 X 位置對齊
- 棒狀圖長度反映相對時間差異
- 無重疊或錯位

## 📝 架構簡化說明

### 移除的組件
- ❌ `AllDriversStraightLineSpeedDualView` - 雙視圖容器
- ❌ `AllDriversStraightLineSpeedWidget` - Matplotlib 圖表視圖
- ❌ QTabWidget 切換功能
- ❌ 延遲載入機制

### 保留的組件
- ✅ `AllDriversStraightLineSpeedTableWidget` - 表格視圖（主要元件）
- ✅ `AccelerationBarDelegate` - 自定義委託（更新為兩行時間）
- ✅ `AllDriversStraightLineSpeedMDI` - MDI 管理器
- ✅ `StraightLineSpeedDataLoader` - 資料載入器

### 優點
1. **簡化架構**：移除 Matplotlib 依賴，避免初始化阻塞
2. **載入更快**：只需初始化 QTableWidget
3. **視覺清晰**：兩行時間分開顯示，對比更直觀
4. **維護簡單**：單一視圖元件，減少複雜度

## 📋 修改檔案清單
1. ✅ `all_drivers_straight_line_speed_mdi.py`
   - 移除雙視圖導入
   - 改用表格視圖

2. ✅ `all_drivers_straight_line_speed_table_widget.py`
   - 修改 `AccelerationBarDelegate.paint()` 方法
   - 兩行時間標籤繪製
   - 欄位 8 寬度調整：450px
   - 行高調整：40px

## ✅ 總結

成功實現：
1. ✅ 取消圖表視圖，只保留專業表格視圖
2. ✅ 在加速性能視覺化棒狀圖右側顯示兩行時間
3. ✅ 第一行：100→300 km/h（深藍色）
4. ✅ 第二行：100→最高速（深灰色）
5. ✅ 優化欄位寬度和行高以容納新佈局
6. ✅ 簡化架構，移除 Matplotlib 依賴

視覺化效果清晰，時間對比直觀，架構簡潔高效！🎉
