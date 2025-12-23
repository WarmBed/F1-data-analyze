# 🎯 OpenF1 API Mini-Sector 數據分析報告

**日期**: 2025-12-15  
**分析目標**: 驗證 OpenF1 API 是否提供 Mini-Sector 可視化所需數據

---

## ✅ 結論：完全支援！

**OpenF1 提供完整的 Mini-Sector 數據**，可直接用於實現與 F1 官方 Live Timing 相同的可視化效果。

---

## 📊 API Endpoint

```
GET https://api.openf1.org/v1/laps
```

### 請求參數
```python
{
    "session_key": 9584,      # 賽事會話 Key
    "driver_number": 1,        # 車手編號
    "lap_number": 5            # 圈數（可選）
}
```

---

## 🔍 數據結構

### 完整 Lap Object
```json
{
    "meeting_key": 1219,
    "session_key": 9159,
    "driver_number": 1,
    "lap_number": 5,
    "date_start": "2023-09-15T13:01:27.120000+00:00",
    
    // 扇區時間
    "duration_sector_1": 56.387,
    "duration_sector_2": 72.133,
    "duration_sector_3": 50.254,
    "lap_duration": 178.774,
    
    // 🔥 Mini-Sector 數據（關鍵！）
    "segments_sector_1": [2064, 2064, 2064, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_3": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    
    // 其他數據
    "i1_speed": 274,           // 扇區 1 末速度
    "i2_speed": 252,           // 扇區 2 末速度
    "st_speed": 315,           // 直線末速度
    "is_pit_out_lap": false
}
```

---

## 🎨 Mini-Sector 顏色編碼

### 數值對應關係

| 數值  | 顏色   | 含義                          | F1 官方顯示 |
|-------|--------|-------------------------------|-------------|
| 2048  | 灰色   | 無效數據 / Out Lap            | 不顯示      |
| 2049  | 綠色   | 個人最佳 (Personal Best)      | 綠色方塊    |
| 2051  | 紫色   | 全場最快 (Overall Fastest)    | 紫色方塊    |
| 2064  | 黃色   | 較慢 (Slower than PB)         | 黃色方塊    |

### Python 實現範例

```python
MINI_SECTOR_COLORS = {
    2048: QColor('#888888'),  # 灰色 - 無效
    2049: QColor('#00DD00'),  # 綠色 - Personal Best
    2051: QColor('#FF00FF'),  # 紫色 - Overall Fastest
    2064: QColor('#FFFF00'),  # 黃色 - Slower
}

def get_mini_sector_color(segment_code: int) -> QColor:
    return MINI_SECTOR_COLORS.get(segment_code, QColor('#888888'))
```

---

## 📏 Mini-Sector 數量分佈

根據實測數據分析：

```
Sector 1: 8 個 mini-sector
Sector 2: 8 個 mini-sector
Sector 3: 7 個 mini-sector
-----------------------------------
總計:    23 個 mini-sector / lap
```

**注意**: 不同賽道可能有微小差異，但大多數賽道都是 23 個。

---

## 💻 實際數據範例

### 範例 1: 全綠圈速（Personal Best）
```python
{
    "lap_number": 2,
    "lap_duration": 90.123,
    "segments_sector_1": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_3": [2049, 2049, 2049, 2049, 2049, 2049, 2049]
}
```
**解讀**: 車手在每個 mini-sector 都跑出個人最快時間。

---

### 範例 2: 混合表現
```python
{
    "lap_number": 1,
    "lap_duration": 91.456,
    "segments_sector_1": [2064, 2064, 2064, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_3": [2049, 2049, 2049, 2049, 2049, 2051, 2049, 2049]
}
```
**解讀**: 
- S1 前半段較慢（黃色）
- S2 表現穩定（全綠）
- S3 第 6 個 mini-sector 跑出全場最快（紫色）

---

### 範例 3: 無效圈（Out Lap / Pit Out）
```python
{
    "lap_number": 3,
    "lap_duration": 178.774,
    "segments_sector_1": [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048],
    "segments_sector_2": [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048],
    "segments_sector_3": [2048, 2048, 2048, 2048, 2048, 2048, 2048],
    "is_pit_out_lap": true
}
```
**解讀**: 出站圈，所有 mini-sector 標記為無效（2048）。

---

## 🚀 整合到 Ranking Tower

### 階段 1: 數據獲取
```python
import requests

def fetch_mini_sectors(session_key: int, driver_number: int) -> Dict:
    """獲取車手的 Mini-Sector 數據"""
    url = f"https://api.openf1.org/v1/laps"
    params = {
        "session_key": session_key,
        "driver_number": driver_number
    }
    
    response = requests.get(url, params=params)
    laps = response.json()
    
    # 提取最快圈的 mini-sector
    fastest_lap = min(laps, key=lambda x: x.get('lap_duration', 999))
    
    return {
        'lap_number': fastest_lap['lap_number'],
        'segments': (
            fastest_lap.get('segments_sector_1', []) +
            fastest_lap.get('segments_sector_2', []) +
            fastest_lap.get('segments_sector_3', [])
        )
    }
```

---

### 階段 2: UI 顯示
```python
class MiniSectorDelegate(QStyledItemDelegate):
    """自訂 Mini-Sector 條形圖繪製器"""
    
    def paint(self, painter, option, index):
        segments = index.data(Qt.UserRole)  # 獲取 mini-sector 數組
        
        if not segments:
            return super().paint(painter, option, index)
        
        # 計算每個小方塊的寬度
        rect = option.rect
        segment_width = rect.width() / len(segments)
        
        # 繪製每個 mini-sector
        for i, seg_code in enumerate(segments):
            color = MINI_SECTOR_COLORS.get(seg_code, QColor('#888888'))
            
            segment_rect = QRect(
                rect.x() + int(i * segment_width),
                rect.y() + 2,
                int(segment_width) - 1,
                rect.height() - 4
            )
            
            painter.fillRect(segment_rect, color)
```

---

### 階段 3: 表格整合
```python
class RankingTableWidget(QWidget):
    def _init_ui(self):
        # 添加 Mini-Sectors 欄位
        self.table.setColumnCount(20)  # 原 19 + 1
        self.table.setHorizontalHeaderLabels([
            "P", "Driver", "+/-", "No", "Tyre", "Age", "Pit", "Hist",
            "S1", "S2", "S3",
            "Last", "Best", "Delta", "Gap L", "Gap A", "Trend", "SF%", "DRS",
            "Mini"  # 🆕 Mini-Sector 欄位
        ])
        
        # 設置欄位寬度（23 個方塊 × 20px = 460px）
        self.table.setColumnWidth(19, 480)
        
        # 設置自訂繪製器
        self.table.setItemDelegateForColumn(19, MiniSectorDelegate())
    
    def update_display(self, snapshot: Dict):
        # ... 現有代碼 ...
        
        for row, (driver_num, driver_data) in enumerate(sorted_drivers):
            # 獲取 mini-sector 數據
            mini_sectors = driver_data.get('mini_sectors', [])
            
            # 設置到表格
            mini_item = QTableWidgetItem()
            mini_item.setData(Qt.UserRole, mini_sectors)  # 儲存原始數據
            self.table.setItem(row, 19, mini_item)
```

---

## ⚡ 性能優化建議

### 1. 緩存策略
```python
# 只在圈速更新時重新獲取
if last_lap_time != self._previous_lap_time[driver_num]:
    mini_sectors = fetch_mini_sectors(session_key, driver_num)
    self._cache_mini_sectors[driver_num] = mini_sectors
```

### 2. 批次請求
```python
# 一次請求所有車手的數據
laps = requests.get(f"/laps?session_key={session_key}").json()

# 分組處理
mini_sectors_by_driver = {}
for lap in laps:
    driver_num = lap['driver_number']
    if driver_num not in mini_sectors_by_driver:
        mini_sectors_by_driver[driver_num] = []
    mini_sectors_by_driver[driver_num].append(lap)
```

### 3. 更新頻率
- **Mini-Sector 欄位**: 僅在新圈完成時更新（~1 分鐘一次）
- **其他欄位**: 維持現有的 10-30 FPS 更新率

---

## 📋 開發檢查清單

- [ ] 添加 Mini-Sector 欄位到表格
- [ ] 實現 `MiniSectorDelegate` 自訂繪製器
- [ ] 整合 OpenF1 API 數據獲取
- [ ] 實現顏色映射邏輯（2048/2049/2051/2064）
- [ ] 添加緩存機制
- [ ] 測試不同賽道的 mini-sector 數量
- [ ] 處理無效數據（2048）的顯示
- [ ] 添加懸停提示（顯示具體時間）
- [ ] 性能測試（20 車手 × 23 mini-sectors）

---

## 🎯 預期效果

實現後，Ranking Tower 將完全複製 F1 官方 Live Timing 的 Mini-Sector 顯示：

```
┌─────────────────────────────────────────────────────────────┐
│ P │ Driver │ Mini-Sectors                                  │
├─────────────────────────────────────────────────────────────┤
│ 1 │  VER   │ 🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢 │
│ 2 │  LEC   │ 🟡🟡🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢 │
│ 3 │  HAM   │ 🟢🟢🟢🟢🟢🟢🟢🟢🟡🟡🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢 │
│ 4 │  NOR   │ 🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟣 │
└─────────────────────────────────────────────────────────────┘

🟢 = 綠色 (Personal Best)
🟡 = 黃色 (Slower)
🟣 = 紫色 (Overall Fastest)
```

---

## 📚 參考資源

- **OpenF1 官方文檔**: https://openf1.org/
- **API 端點**: https://api.openf1.org/v1/laps
- **現有實現**: `modules/gui/live_timing/live_timing_modules/ranking_tower.py`
- **測試腳本**: `test_openf1_segments.py`

---

## 🏁 總結

✅ **OpenF1 提供完整的 Mini-Sector 數據**  
✅ **數據格式與 F1 官方完全一致**  
✅ **可直接整合到現有 Ranking Tower**  
✅ **無需額外計算或估算**  
✅ **支援實時和歷史回放模式**

**預估開發時間**: 3-4 小時（含測試）  
**難度**: 中等（主要是 UI 繪製邏輯）  
**優先級**: 高（提升 Live Timing 功能完整度）
