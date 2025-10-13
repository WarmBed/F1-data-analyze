# 積分榜 Demo 顏色功能說明

## ✅ 顏色系統已整合

三個 demo 現在都使用 **ColorPaletteProvider** 系統，自動為車隊與車手套用官方顏色。

### 🎨 顏色來源

1. **優先**: API 動態獲取 (Function 98)
   - 從 `https://api.f1telemetrystationpro.org` 獲取最新顏色
   - 支援多賽季、多配色方案（FastF1/Official）

2. **Fallback**: 內建預設色票
   - 當 API 無法連線時自動啟用
   - 包含 2025 賽季 10 支車隊顏色
   - 涵蓋約 24 位車手的顏色映射

### 📊 Demo 顏色應用

#### Demo 1: 車隊積分表 (`demo_01_constructor_standings.py`)
- **車隊名稱欄位**: 套用車隊背景色
- **前景文字**: 黑色（確保可讀性）
- **顏色邏輯**: `color_palette_provider.get_team_color(constructor_name)`

#### Demo 2: 車手積分表 (`demo_02_driver_standings.py`)
- **車手代碼欄位**: 套用車手顏色（自動 fallback 到車隊色）
- **車手姓名欄位**: 套用車手顏色
- **前景文字**: 黑色（確保可讀性）
- **顏色邏輯**: `color_palette_provider.get_driver_color(driver_code)`

#### Demo 3: 賽季進度摘要 (`demo_03_season_progress.py`)
- **純文字顯示**: 暫無顏色編碼（可擴展）

### 🔧 技術實現

```python
# 1. 匯入顏色系統
from modules.gui.themes import color_palette_provider

# 2. 初始化（載入賽季顏色）
season_year = metadata.get("season_year", 2024)
color_palette_provider.ensure_loaded(year=season_year)

# 3. 獲取顏色並套用
driver_color = color_palette_provider.get_driver_color(
    driver_code, format="qcolor", fallback=True
)
item.setBackground(QBrush(driver_color))
item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色前景
```

### 🛡️ 容錯機制

- ✅ **API 失敗時**: 自動使用內建預設色票
- ✅ **未知車隊/車手**: 返回灰色 `#808080`
- ✅ **無網路時**: Demo 仍可正常顯示（使用預設色）

### 📝 參考實現

顏色系統與其他分析模組一致：
- `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/` - Ideal Lap 排名表
- `modules/gui/Throttle_analysis/throttle_box_plot_analysis/` - 油門箱型圖
- `modules/gui/lap_box_plot_analysis/` - 單圈箱型圖

### 🎯 顏色效果

執行 demo 時，你將看到：
- **McLaren** - 橘色 `#FF8000`
- **Ferrari** - 紅色 `#E80020`
- **Red Bull** - 藍色 `#0600EF`
- **Mercedes** - 青色 `#27F4D2`
- **其他車隊** - 依預設色票顯示

---

**最後更新**: 2025-10-13  
**版本**: 1.0.0  
**作者**: F1T Team
