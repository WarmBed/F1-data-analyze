# F1T Race Weather Widget - 5 種風格展示

**作者**: F1T Team  
**日期**: 2025-10-13  
**狀態**: ✅ 完成並測試

---

## 📋 概述

為 F1T 主 GUI 創建了 **5 種不同風格** 的天氣預報 Widget，用於展示比賽週末的天氣數據。所有 Demo 已完成並可正常運行。

---

## 🎨 Demo 1: 卡片式布局 (Card Style)

**檔案**: `demo_weather_widget_01_card_style.py`

### 特點
- ✅ 3 個獨立天氣卡片橫向排列
- ✅ 大型天氣圖示 (☀️🌦️🌧️☁️⛅)
- ✅ 顯示溫度範圍、降雨量、風速風向
- ✅ 底部顯示歷史天氣對比 (2024/2023)
- ✅ 比賽日無特殊突出顯示

### 適用場景
- 視覺優先的用戶
- 需要快速識別天氣狀況
- 橫向空間充足的介面

### 視覺風格
```
┌────────────┐  ┌────────────┐  ┌────────────┐
│ 比賽前2天   │  │ 比賽前1天   │  │ 比賽當天    │
│     ☀️     │  │     🌦️     │  │     🌧️     │
│  20°C~28°C │  │  18°C~25°C │  │  15°C~22°C │
│  降雨: 0mm │  │ 降雨: 2.5mm │  │ 降雨: 8.3mm │
│ 風速: 15km/h│  │ 風速: 18km/h│  │ 風速: 25km/h│
└────────────┘  └────────────┘  └────────────┘
歷史天氣對比: 2024年: 27.5°C, 0.0mm | 2023年: 26.2°C, 1.2mm
```

---

## 📅 Demo 2: 時間軸式布局 (Timeline Style)

**檔案**: `demo_weather_widget_02_timeline.py`

### 特點
- ✅ 橫向時間軸展示，節點連接線
- ✅ 每個節點包含日期、天氣圖示、溫度、降雨、風向
- ✅ 比賽日使用紅色突出顯示 (●)
- ✅ 可水平滾動查看完整時間軸
- ✅ 圖例說明預報與比賽日

### 適用場景
- 強調時間順序的用戶
- 需要視覺化天氣變化趨勢
- 適合展示多日預報

### 視覺風格
```
前2天        前1天        比賽日
2025-10-17   2025-10-18   2025-10-19
    ●───────────●───────────●
  25.2°C      23.8°C      21.5°C
    ☀️          🌦️          🌧️
   0mm        2.5mm       8.3mm
  ↓ 15km/h   ↓ 18km/h    ↓ 25km/h
```

---

## 📊 Demo 3: 資料表式布局 (Table Style)

**檔案**: `demo_weather_widget_03_table.py`

### 特點
- ✅ 傳統表格式布局，完整數據展示
- ✅ 8 個欄位：類型、日期、天氣、溫度範圍、降雨、雲量、風速、濕度
- ✅ 包含預報 (3 天) + 歷史 (2024/2023 各 3 天)
- ✅ 比賽日使用紅色突出顯示
- ✅ 歷史數據使用灰色標註
- ✅ 表格可排序、滾動

### 適用場景
- 需要詳細數據的分析用戶
- 數據對比需求
- 適合導出或截圖分享

### 視覺風格
```
┌───────────┬────────────┬──────┬───────────┬─────┬──────┬────────┬──────┐
│ 類型      │ 日期       │ 天氣 │ 溫度範圍  │降雨 │ 雲量 │ 風速   │ 濕度 │
├───────────┼────────────┼──────┼───────────┼─────┼──────┼────────┼──────┤
│預報(前2天)│2025-10-17  │☀️晴天│20.1°~28.3°│0mm  │ 15%  │NE 15km │ 45%  │
│預報(前1天)│2025-10-18  │🌦️陣雨│18.5°~25.7°│2.5mm│ 42%  │NE 18km │ 58%  │
│預報(比賽日)│2025-10-19  │🌧️降雨│15.2°~22.1°│8.3mm│ 78%  │N 25km  │ 72%  │
│歷史(2024) │2024-10-20  │☀️晴天│19.8°~27.5°│0mm  │ 12%  │E 12km  │ 42%  │
│歷史(2023) │2023-10-22  │⛅局部雲│18.2°~26.2°│1.2mm│ 28%  │NE 14km │ 48%  │
└───────────┴────────────┴──────┴───────────┴─────┴──────┴────────┴──────┘
```

---

## 📈 Demo 4: 圖表式布局 (Chart Style)

**檔案**: `demo_weather_widget_04_chart.py`

### 特點
- ✅ 溫度趨勢曲線圖 (實線 + 漸變填充)
- ✅ 降雨柱狀圖 (半透明藍色)
- ✅ 歷史數據虛線對比 (2024/2023)
- ✅ 比賽日溫度標籤使用紅色突出
- ✅ 完整圖例說明

### 適用場景
- 視覺化分析需求
- 需要快速識別趨勢變化
- 適合演示和報告

### 視覺風格
```
°C
30 ┼─────────────────────────────
   │           ●───────────  2023 (虛線)
25 ┼────●──────────●────────  2024 (虛線)
   │   ╱ ╲      ╱   ╲
20 ┼──●───●────●─────●────── 2025 預報 (實線)
   │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (漸變填充)
15 ┼─────────────────────────
   │ ▄▄  ▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄  (降雨柱狀圖)
   └─────┬──────┬──────┬─────
      前2天    前1天   比賽日
```

---

## 📦 Demo 5: 緊湊式布局 (Compact Style)

**檔案**: `demo_weather_widget_05_compact.py`

### 特點
- ✅ 最小化空間佔用 (單行顯示)
- ✅ 可折疊區塊 (預報 / 歷史)
- ✅ 快速瀏覽模式
- ✅ 適合嵌入側邊欄或小型面板
- ✅ 預報區默認展開，歷史區默認折疊

### 適用場景
- 空間受限的介面
- 次要資訊顯示
- 需要摺疊功能的場景

### 視覺風格
```
▼ 2025 預報
  ┌─────────────────────────────────┐
  │ 前2天  ☀️  20°~28°C  雨 0mm  風 15km/h │
  │ 前1天  🌦️  18°~25°C  雨 2.5mm 風 18km/h│
  │ 比賽日 🌧️  15°~22°C  雨 8.3mm 風 25km/h│
  └─────────────────────────────────┘

▶ 歷史數據 (點擊展開)
```

---

## 🚀 執行方式

### 1. 單獨執行個別 Demo

```powershell
# Demo 1: 卡片式
python demo_weather_widget_01_card_style.py

# Demo 2: 時間軸式
python demo_weather_widget_02_timeline.py

# Demo 3: 資料表式
python demo_weather_widget_03_table.py

# Demo 4: 圖表式
python demo_weather_widget_04_chart.py

# Demo 5: 緊湊式
python demo_weather_widget_05_compact.py
```

### 2. 使用展示廳一次查看所有 Demo

```powershell
python demo_weather_widget_gallery.py
```

---

## 📁 數據格式

所有 Demo 讀取 CLI 生成的天氣 JSON 檔案：

**檔案路徑**: `json/weather/race_weather_forecast_{year}_{event}_{timestamp}.json`

**數據結構**:
```json
{
  "success": true,
  "data": {
    "forecast": {
      "days": [
        {
          "label": "race_minus_2",
          "date": "2025-10-17",
          "summary": {
            "temperature_max": 28.3,
            "temperature_min": 20.1,
            "precipitation_sum": 0.0,
            "cloudcover_mean": 15.2,
            "windspeed_max": 15.4,
            "winddirection_cardinal": "NE",
            "relativehumidity_mean": 45.0
          }
        }
      ]
    },
    "historical": {
      "entries": {
        "2024_race_minus_0": {
          "date": "2024-10-20",
          "summary": { ... }
        },
        "2023_race_minus_0": {
          "date": "2023-10-22",
          "summary": { ... }
        }
      }
    },
    "calendar_event": {
      "year": 2025,
      "EventName": "United States Grand Prix"
    },
    "circuit_info": {
      "location": "Austin, Texas"
    }
  }
}
```

---

## 🔄 生成測試數據

```powershell
# 執行 CLI -f96 生成天氣 JSON
python f1_analysis_modular_main.py -f 96 -y 2025 -r "United States" -s R
```

---

## 🎯 整合建議

### 推薦順序

1. **首選**: **Demo 1 (卡片式)** 或 **Demo 2 (時間軸式)**
   - 視覺化效果好
   - 資訊密度適中
   - 符合主 GUI 風格

2. **次選**: **Demo 4 (圖表式)**
   - 專業分析感強
   - 但需要更多垂直空間

3. **特殊場景**: **Demo 5 (緊湊式)**
   - 僅在空間極度受限時使用

4. **數據導向**: **Demo 3 (資料表式)**
   - 適合專業分析用戶
   - 但與主 GUI 卡片風格不太一致

### 整合到 Season Progress Widget

建議位置：`season_progress_widget.py` 的底部，在統計數據之後

```python
# 在 Season Progress Widget 中添加
self.weather_widget = RaceWeatherDemo1CardStyle()  # 或選擇其他 Demo
layout.addWidget(self.weather_widget)

# 載入數據
self.weather_widget.load_weather_data(json_path)
```

---

## ✅ 測試狀態

| Demo | 檔案 | 狀態 | 測試結果 |
|------|------|------|---------|
| Demo 1 | `demo_weather_widget_01_card_style.py` | ✅ 完成 | 成功載入數據 |
| Demo 2 | `demo_weather_widget_02_timeline.py` | ✅ 完成 | 成功載入數據 |
| Demo 3 | `demo_weather_widget_03_table.py` | ✅ 完成 | 成功載入數據 |
| Demo 4 | `demo_weather_widget_04_chart.py` | ✅ 完成 | 成功載入數據 |
| Demo 5 | `demo_weather_widget_05_compact.py` | ✅ 完成 | 成功載入數據 |
| Gallery | `demo_weather_widget_gallery.py` | ✅ 完成 | 成功啟動所有 Demo |

---

## 📝 已知問題

✅ **已解決**:
- ~~Demo 1-5 中 `from core.gui_i18n import tr` 導入錯誤~~ → 已移除
- ~~歷史數據結構不匹配~~ → 已修正為字典格式
- ~~Demo 4 圖表繪製錯誤~~ → 已修正歷史數據迭代邏輯

---

## 🎨 設計原則遵循

所有 Demo 遵循 F1T GUI 設計原則：

- ✅ 使用 QGroupBox、QLabel 等一致性組件
- ✅ 字體大小 11-18px (小型標籤 11px，標題 16-18px)
- ✅ 間距 8-16px
- ✅ 主題色 `#0066cc` (藍色)
- ✅ 比賽日突出色 `#dc3545` (紅色)
- ✅ 灰色標註 `#6c757d`
- ✅ 背景色 `#f8f9fa`、邊框色 `#dee2e6`

---

## 📸 截圖建議

建議使用展示廳拍攝所有 5 個 Demo 的截圖，以便用戶選擇喜歡的風格。

**執行**:
```powershell
python demo_weather_widget_gallery.py
```

**Tab 切換**查看不同風格，選擇最符合主 GUI 風格的 Demo 進行整合。

---

## 🔮 後續工作

1. **用戶選擇風格** - 根據此文件中的截圖和說明選擇喜歡的 Demo
2. **整合至 Season Progress** - 將選定的 Demo 整合至 `season_progress_widget.py`
3. **API 整合** - 添加自動載入最新天氣預報的功能
4. **刷新機制** - 添加手動/自動刷新天氣數據的按鈕
5. **多語言化** - 使用 `tr()` 包裹所有用戶可見字串

---

**完成時間**: 2025-10-13  
**測試環境**: Windows + PowerShell + Python 3.x + PyQt5  
**狀態**: ✅ 所有 Demo 可正常運行
