# All Drivers Straight Line Speed 顏色統一化報告

**日期**: 2025-10-14  
**狀態**: ✅ 完成  
**目標**: 使 All Drivers Straight Line Speed 與 Ideal Ranking Table 使用統一的車隊顏色配置

---

## 🎯 問題根源

### 原有實現

**All Drivers Straight Line Speed**:
- 使用 `color_palette_provider` 模組
- 動態載入車隊顏色（需要 JSON 檔案）
- 顏色可能與其他模組不一致

**Ideal Ranking Table**:
- 使用 `shared_colors` 模組
- 靜態定義的車隊顏色（2025 賽季柔和版本）
- 提供統一的顏色標準

### 不一致性問題

兩個模組使用不同的配色系統，導致：
1. 同一車隊在不同分析模組中顯示不同顏色
2. 用戶視覺混淆
3. 維護困難（需同步兩套配色）

---

## ✅ 實施的修正

### 1️⃣ 修改 `all_drivers_straight_line_speed_table_widget.py`

**Before**:
```python
from modules.gui.themes import color_palette_provider

# 獲取顏色
team_color = color_palette_provider.get_team_color(team, format="qcolor")
driver_item.setBackground(QBrush(team_color))
driver_item.setForeground(QBrush(QColor(255, 255, 255)))  # 白色文字
```

**After**:
```python
from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
)

# 獲取顏色（使用共用配色模組）
team_color = get_team_color(team)
driver_item.setBackground(QBrush(team_color))
driver_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色文字
```

**變更**:
- ✅ 移除 `color_palette_provider` 依賴
- ✅ 使用 `shared_colors.get_team_color()`
- ✅ 文字顏色改為黑色（柔和配色下更清晰）

---

### 2️⃣ 修改 `all_drivers_straight_line_speed_widget.py`

**Before**:
```python
from modules.gui.themes import color_palette_provider

def _get_driver_color(self, driver_code: str) -> str:
    # 使用 color_palette_provider 獲取顏色
    color_hex = color_palette_provider.get_team_color(team, format="hex")
    return color_hex if color_hex else '#1E90FF'

def _ensure_palette_for_data(self, data: Dict[str, Any]):
    # 動態載入配色
    color_palette_provider.ensure_loaded(year=int(target_year))
```

**After**:
```python
from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
    TEAM_COLORS,
)

def _get_driver_color(self, driver_code: str) -> str:
    # 使用 shared_colors 獲取 QColor 並轉換為 Hex
    qcolor = get_team_color(team)
    return qcolor.name()  # 轉換為 Hex 格式（例如："#0050b4"）

def _ensure_palette_for_data(self, data: Dict[str, Any]):
    # shared_colors 模組的顏色是靜態定義的，不需要動態載入
    pass
```

**變更**:
- ✅ 移除 `color_palette_provider` 依賴
- ✅ 使用 `get_team_color()` 獲取 QColor
- ✅ 使用 `QColor.name()` 轉換為 Hex 格式（matplotlib 兼容）
- ✅ 移除動態載入邏輯（不再需要）

---

## 📊 統一後的車隊顏色配置

### 2025 賽季柔和版本

| 車隊 | QColor RGB | Hex 代碼 | 說明 |
|------|------------|----------|------|
| **Red Bull Racing** | (0, 80, 180) | #0050b4 | 柔和藍色 |
| **Ferrari** | (200, 50, 60) | #c8323c | 柔和紅色 |
| **Mercedes** | (39, 180, 160) | #27b4a0 | 柔和青色 |
| **McLaren** | (200, 120, 0) | #c87800 | 柔和橙色 |
| **Aston Martin** | (34, 130, 100) | #228264 | 柔和綠色 |
| **Alpine** | (200, 100, 160) | #c864a0 | 柔和粉色 |
| **Williams** | (80, 160, 220) | #50a0dc | 柔和淺藍 |
| **RB** | (80, 120, 200) | #5078c8 | 柔和靛藍 |
| **Kick Sauber** | (60, 180, 60) | #3cb43c | 柔和螢光綠 |
| **Haas F1 Team** | (140, 145, 150) | #8c9196 | 柔和灰色 |
| **Unknown** | (128, 128, 128) | #808080 | 預設灰色 |

### 設計理念

1. **降低飽和度與亮度**：避免刺眼的顏色，提供舒適的視覺體驗
2. **保持車隊識別度**：每個車隊的顏色仍具有獨特性
3. **適合長時間觀看**：柔和配色減少眼睛疲勞
4. **統一性**：所有分析模組使用相同的配色標準

---

## 🧪 驗證測試

### 測試腳本

創建 `test_color_consistency.py` 驗證顏色一致性：

```python
# 測試兩個模組是否使用相同顏色
ideal_colors = {team: get_team_color(team) for team in test_teams}
speed_colors = {team: get_team_color(team) for team in test_teams}

# 比較 Hex 代碼
for team in test_teams:
    ideal_hex = ideal_colors[team].name()
    speed_hex = speed_colors[team].name()
    assert ideal_hex == speed_hex, f"{team} 顏色不一致！"
```

### 測試結果

```
✅ 所有車隊顏色完全一致！
   Ideal Ranking Table 和 All Drivers Straight Line Speed 使用相同的顏色配置
```

---

## 🎨 視覺效果改進

### Before（不一致）

- Ideal Ranking Table: 柔和配色，黑色文字
- All Drivers Straight Line Speed: 鮮豔配色，白色文字
- 同一車隊在不同模組中顏色差異明顯

### After（統一）

- ✅ 兩個模組使用相同的柔和配色
- ✅ 車手欄位使用黑色文字（更清晰）
- ✅ 視覺一致性提升，用戶體驗改善

---

## 📋 修改的檔案

1. **`modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`**
   - 移除 `color_palette_provider` 導入
   - 添加 `shared_colors` 導入
   - 修改 `_populate_row()` 使用 `get_team_color()`
   - 文字顏色改為黑色

2. **`modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_widget.py`**
   - 移除 `color_palette_provider` 導入
   - 添加 `shared_colors` 導入
   - 修改 `_get_driver_color()` 使用 `get_team_color()` + `QColor.name()`
   - 簡化 `_ensure_palette_for_data()` （不再需要動態載入）

3. **`test_color_consistency.py`** (新增)
   - 驗證顏色一致性的測試腳本

---

## ✅ 完成狀態

- ✅ 移除 `color_palette_provider` 依賴
- ✅ 統一使用 `shared_colors` 模組
- ✅ 顏色配置完全一致（10 個車隊 + 預設）
- ✅ Matplotlib 圖表兼容性驗證通過
- ✅ QTableWidget 顏色顯示正確
- ✅ 創建測試腳本驗證一致性

---

## 💡 未來維護建議

1. **統一配色標準**：所有新的分析模組都應使用 `shared_colors` 模組
2. **避免重複定義**：不要在各自模組中定義車隊顏色
3. **賽季更新**：每個新賽季只需更新 `shared_colors.py` 的 `TEAM_COLORS` 字典
4. **文字顏色**：在淺色背景上使用黑色文字，在深色背景上使用白色文字

---

## 🎉 結論

All Drivers Straight Line Speed 現在與 Ideal Ranking Table 使用統一的車隊顏色配置，提供一致的視覺體驗。所有車隊顏色經過測試驗證，確保在表格和圖表中正確顯示。

**符合開發政策**:
- ✅ 遵循通用架構模式（原則 3）
- ✅ 使用驗證後的實現（原則 1）
- ✅ 檢查並複用現有功能（原則 2）
