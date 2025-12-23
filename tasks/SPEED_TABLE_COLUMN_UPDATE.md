# 全車手直線速度表格視圖 - 欄位更新報告

## 📅 更新日期
2025-10-14

## 🎯 更新目標
根據用戶需求，在表格視圖中增加以下欄位：
1. **車隊**
2. **距離 (100→300)**
3. **平均加速度 (100→300)**

## ✅ 完成的更新

### 1. 表格欄位配置（`_create_table`）
**原始欄位（6 個）：**
0. 排名
1. 車手
2. 最高速度
3. 加速時間 (100→300)
4. 最高時速時間
5. 加速性能視覺化

**更新後欄位（9 個）：**
0. 排名 (60px)
1. 車手 (100px) - 含車隊背景色
2. **車隊** (120px) ⭐ 新增
3. 最高速度 (120px) - 顏色編碼
4. 加速時間 (100→300) (140px)
5. **距離 (100→300)** (120px) ⭐ 新增
6. **平均加速度 (100→300)** (160px) ⭐ 新增
7. 最高時速時間 (120px)
8. 加速性能視覺化 (550px) - 專業藍灰棒狀圖

### 2. 欄位寬度優化
- 總表格寬度：1490px（適合 1920x1080 顯示器）
- 視覺化欄位保持 550px 以容納完整的棒狀圖和時間標籤

### 3. 委託更新
- 加速棒狀圖委託從欄位 5 移動到欄位 8
- 保持深藍 + 淺灰的專業配色

### 4. 數據填充（`_populate_row`）
**新增欄位的數據來源：**
```python
# 車隊（欄位 2）
team_item = QTableWidgetItem(team)

# 距離（欄位 5）
accel_distance = accel_data.get("distance_meters", accel_data.get("distance", 0))
distance_item = QTableWidgetItem(f"{accel_distance:.1f}m")

# 平均加速度（欄位 6）
accel_avg = accel_data.get("avg_acceleration_ms2", accel_data.get("avg_acceleration", 0))
avg_accel_item = QTableWidgetItem(f"{accel_avg:.3f} m/s²")
```

## 📊 數據格式支援

### JSON 數據結構
```json
{
  "driver_speeds": [
    {
      "driver": "VER",
      "team": "Red Bull Racing",
      "max_speed_kmh": 328.5,
      "acceleration_100_300": {
        "time_seconds": 1.234,
        "distance_meters": 123.4,
        "avg_acceleration_ms2": 5.678
      }
    }
  ]
}
```

### 鍵名兼容性
系統支援兩種 JSON 鍵名格式：
- **標準格式**：`time_seconds`, `distance_meters`, `avg_acceleration_ms2`
- **簡短格式**：`time`, `distance`, `avg_acceleration`

## 🎨 視覺效果

### 欄位顏色編碼
1. **車手欄位**：車隊背景色 + 白色文字
2. **最高速度**：
   - 綠色：> 325 km/h（快）
   - 黃色：320-325 km/h（中等）
   - 橙色：< 320 km/h（慢）
3. **最高時速時間**：深藍色粗體
4. **加速視覺化**：
   - 深藍實心：100→300 km/h
   - 淺灰實心：300→最高速
   - 右側時間標籤："1.20s → 1.37s"

## 🔧 技術細節

### 相對時間比例算法
棒狀圖寬度使用相對時間比例，讓快慢車手的差異更明顯：
```python
relative_ratio = (time_to_max - min_time) / (max_time - min_time)
bar_width = total_width * relative_ratio
```

### 委託繪製邏輯
```python
# 100-300 km/h 區間（深藍）
solid_rect = QRectF(base_x, base_y, speed_300_pos, bar_height)
painter.fillRect(solid_rect, QBrush(QColor(50, 100, 180)))

# 300-最高速區間（淺灰）
extension_rect = QRectF(base_x + speed_300_pos, base_y, 
                        speed_max_pos - speed_300_pos, bar_height)
painter.fillRect(extension_rect, QBrush(QColor(200, 200, 200)))
```

## 📁 修改的檔案
1. `all_drivers_straight_line_speed_table_widget.py` - 主要更新
   - `_create_table()` - 欄位定義和寬度
   - `_populate_table()` - 委託欄位索引
   - `_populate_row()` - 新增欄位數據填充

## 🧪 測試建議

### 測試案例 1：2025 Japan Qualifying
```bash
cd "d:\OneDrive\Code\F1-data-analyze"
python modules\gui\all_drivers_straight_line_speed_analysis\demo_japan_q.py
```

**預期結果：**
- ✅ 顯示 20 位車手
- ✅ 車隊欄位顯示車隊全名
- ✅ 距離欄位顯示 100-300 km/h 的加速距離（例如："123.4m"）
- ✅ 平均加速度欄位顯示 m/s² 單位（例如："5.678 m/s²"）
- ✅ 棒狀圖正確顯示在第 8 欄

### 測試案例 2：手動數據載入
```python
from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import AllDriversStraightLineSpeedTableWidget

widget = AllDriversStraightLineSpeedTableWidget()
widget.update_data({
    "driver_speeds": [
        {
            "driver": "VER",
            "team": "Red Bull Racing",
            "max_speed_kmh": 328.5,
            "acceleration_100_300": {
                "time_seconds": 1.234,
                "distance_meters": 123.4,
                "avg_acceleration_ms2": 5.678
            }
        }
    ]
})
```

## 🔄 與雙視圖整合

### 架構整合狀態
- ✅ 表格視圖（AllDriversStraightLineSpeedTableWidget）- 已更新
- ✅ 圖表視圖（AllDriversStraightLineSpeedWidget）- Matplotlib 視覺化
- ✅ 雙視圖容器（AllDriversStraightLineSpeedDualView）- QTabWidget 切換
- ⚠️ 延遲載入機制：Matplotlib widget 在首次切換到圖表 tab 時才創建

### MDI 配置
```python
# all_drivers_straight_line_speed_mdi.py
def create_chart_widget(self):
    return AllDriversStraightLineSpeedDualView()  # 雙視圖容器
```

## 📝 注意事項

### 數據兼容性
- JSON 數據必須包含 `acceleration_100_300` 物件
- 支援舊版和新版鍵名格式
- 缺失數據顯示為 0.0 或空白

### 性能優化
- 表格排序啟用（按任意欄位排序）
- 統一行高 35px 減少渲染開銷
- 委託只在有數據的欄位才繪製棒狀圖

### 已知問題
- ⚠️ 模組初始化時可能遇到 Matplotlib 載入阻塞（已通過延遲載入緩解）
- ⚠️ `__init__.py` 中的 Matplotlib widget 導入已註釋，避免自動載入

## 🎯 下一步建議

1. **測試雙視圖切換**：確認表格和圖表視圖能正常切換
2. **驗證數據完整性**：檢查所有 20 位車手的新欄位數據是否正確
3. **UI 調整**：根據實際顯示效果微調欄位寬度
4. **國際化**：為新欄位添加多語言支援（`gui_i18n`）

## ✅ 總結

成功將表格從 **6 欄位擴展至 9 欄位**，新增：
- 車隊資訊
- 加速距離（100→300 km/h）
- 平均加速度（100→300 km/h）

保持了專業的藍灰配色和清晰的數據視覺化，與 ideal_lap_sector_comparison 的 QTableWidget 架構完全一致。
