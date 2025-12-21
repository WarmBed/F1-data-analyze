# 🎨 F1T 車隊顏色配置中央化任務

## 📋 任務概述

**任務名稱**: 建立中央化車隊顏色配置系統  
**優先級**: Medium  
**狀態**: 📝 待開發 (Pending)  
**建立日期**: 2025-10-08  
**預計完成**: TBD  

---

## 🎯 任務目標

將系統中分散在多個檔案的車隊顏色定義整合至單一中央配置檔案，提升維護性和一致性。

### 核心需求
1. ✅ 建立中央顏色配置模組 `modules/gui/themes/team_colors.py`
2. ✅ 支援 RGB (`QColor`) 和 十六進位 (Hex) 兩種格式
3. ✅ 重構現有 3 個模組使用中央配置
4. ✅ 保持向下相容性
5. ✅ 支援多賽季配色 (2024, 2025, 未來...)

---

## 🔍 現狀分析

### 重複定義位置

目前系統中有 **3 個地方** 重複定義了車隊顏色：

| 檔案 | 行數 | 格式 | 用途 |
|------|------|------|------|
| `modules/gui/laptime_analysis/laptime_boxplot_widget.py` | 836 | 十六進位字串 | 舊版 Lap Time Box Plot |
| `modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py` | 42 | `QColor` 物件 | 新版 Lap Box Plot |
| `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_chart_widget.py` | 41 | `QColor` 物件 | Throttle Box Plot |

### 顏色格式對照

#### 十六進位格式 (Hex)
```python
team_colors = {
    'VER': '#3671C6',  # Red Bull
    'PER': '#3671C6',
    'LEC': '#E8002D',  # Ferrari
    'SAI': '#E8002D',
    'HAM': '#27F4D2',  # Mercedes
    'RUS': '#27F4D2',
    'NOR': '#FF8000',  # McLaren
    'PIA': '#FF8000',
    # ... 其他 12 位車手
}
```

#### RGB 格式 (QColor)
```python
TEAM_COLORS = {
    'VER': QColor(54, 113, 198),    # Red Bull Racing - 藍色
    'PER': QColor(54, 113, 198),
    'LEC': QColor(232, 0, 45),      # Ferrari - 紅色
    'SAI': QColor(232, 0, 45),
    'HAM': QColor(39, 244, 210),    # Mercedes - 青綠色
    'RUS': QColor(39, 244, 210),
    'NOR': QColor(255, 128, 0),     # McLaren - 橘色
    'PIA': QColor(255, 128, 0),
    # ... 其他 12 位車手
}
```

### 完整車隊配色表 (2025 賽季)

| 車隊 | 十六進位 | RGB | 車手 |
|------|----------|-----|------|
| Red Bull Racing | `#3671C6` | `(54, 113, 198)` | VER, PER |
| Ferrari | `#E8002D` | `(232, 0, 45)` | LEC, SAI |
| Mercedes | `#27F4D2` | `(39, 244, 210)` | HAM, RUS |
| McLaren | `#FF8000` | `(255, 128, 0)` | NOR, PIA |
| Aston Martin | `#229971` | `(34, 153, 113)` | ALO, STR |
| Alpine | `#5E8FAA` | `(94, 143, 170)` | GAS, OCO |
| Haas | `#B6BABD` | `(182, 186, 189)` | HUL, MAG |
| RB (AlphaTauri) | `#6692FF` | `(102, 146, 255)` | TSU, RIC |
| Kick Sauber | `#52E252` | `(82, 226, 82)` | BOT, ZHO |
| Williams | `#64C4FF` | `(100, 196, 255)` | ALB, SAR |

---

## 🏗️ 設計方案

### 檔案結構
```
modules/gui/themes/
├── __init__.py
├── team_colors.py          # 中央顏色配置
└── color_utils.py          # 顏色轉換工具 (可選)
```

### 核心配置檔案: `team_colors.py`

```python
"""
F1 車隊官方配色中央配置
支援多賽季和多種顏色格式
"""
from PyQt5.QtGui import QColor
from typing import Dict, Union

# ==================== 2025 賽季 ====================

F1_TEAM_COLORS_2025_RGB = {
    # Red Bull Racing
    'VER': QColor(54, 113, 198),
    'PER': QColor(54, 113, 198),
    
    # Ferrari
    'LEC': QColor(232, 0, 45),
    'SAI': QColor(232, 0, 45),
    
    # Mercedes
    'HAM': QColor(39, 244, 210),
    'RUS': QColor(39, 244, 210),
    
    # McLaren
    'NOR': QColor(255, 128, 0),
    'PIA': QColor(255, 128, 0),
    
    # Aston Martin
    'ALO': QColor(34, 153, 113),
    'STR': QColor(34, 153, 113),
    
    # Alpine
    'GAS': QColor(94, 143, 170),
    'OCO': QColor(94, 143, 170),
    
    # Haas
    'HUL': QColor(182, 186, 189),
    'MAG': QColor(182, 186, 189),
    
    # RB (AlphaTauri)
    'TSU': QColor(102, 146, 255),
    'RIC': QColor(102, 146, 255),
    
    # Kick Sauber
    'BOT': QColor(82, 226, 82),
    'ZHO': QColor(82, 226, 82),
    
    # Williams
    'ALB': QColor(100, 196, 255),
    'SAR': QColor(100, 196, 255),
}

F1_TEAM_COLORS_2025_HEX = {
    # Red Bull Racing
    'VER': '#3671C6',
    'PER': '#3671C6',
    
    # Ferrari
    'LEC': '#E8002D',
    'SAI': '#E8002D',
    
    # Mercedes
    'HAM': '#27F4D2',
    'RUS': '#27F4D2',
    
    # McLaren
    'NOR': '#FF8000',
    'PIA': '#FF8000',
    
    # Aston Martin
    'ALO': '#229971',
    'STR': '#229971',
    
    # Alpine
    'GAS': '#5E8FAA',
    'OCO': '#5E8FAA',
    
    # Haas
    'HUL': '#B6BABD',
    'MAG': '#B6BABD',
    
    # RB (AlphaTauri)
    'TSU': '#6692FF',
    'RIC': '#6692FF',
    
    # Kick Sauber
    'BOT': '#52E252',
    'ZHO': '#52E252',
    
    # Williams
    'ALB': '#64C4FF',
    'SAR': '#64C4FF',
}

# ==================== 2024 賽季 (保留歷史資料) ====================
# TODO: 如需支援 2024 賽季回放，在此定義

# ==================== 預設配色 ====================

# 預設使用 2025 賽季
DEFAULT_TEAM_COLORS_RGB = F1_TEAM_COLORS_2025_RGB
DEFAULT_TEAM_COLORS_HEX = F1_TEAM_COLORS_2025_HEX

# 預設顏色 (未知車手)
DEFAULT_COLOR_RGB = QColor(204, 204, 204)  # 灰色
DEFAULT_COLOR_HEX = '#CCCCCC'

# ==================== 工具函數 ====================

def get_driver_color(
    driver_code: str, 
    year: int = 2025,
    format: str = 'rgb'
) -> Union[QColor, str]:
    """
    獲取車手顏色
    
    Args:
        driver_code: 車手代碼 (例如: "VER", "LEC")
        year: 賽季年份
        format: 'rgb' 或 'hex'
    
    Returns:
        QColor 物件或十六進位字串
    """
    if format == 'rgb':
        color_map = F1_TEAM_COLORS_2025_RGB if year == 2025 else {}
        return color_map.get(driver_code.upper(), DEFAULT_COLOR_RGB)
    else:  # hex
        color_map = F1_TEAM_COLORS_2025_HEX if year == 2025 else {}
        return color_map.get(driver_code.upper(), DEFAULT_COLOR_HEX)

def get_team_colors_for_drivers(
    driver_codes: list,
    year: int = 2025,
    format: str = 'rgb'
) -> list:
    """
    批次獲取多位車手的顏色
    
    Args:
        driver_codes: 車手代碼列表
        year: 賽季年份
        format: 'rgb' 或 'hex'
    
    Returns:
        顏色列表
    """
    return [get_driver_color(code, year, format) for code in driver_codes]
```

---

## 📝 開發清單

### Phase 1: 建立中央配置
- [ ] 建立 `modules/gui/themes/` 目錄
- [ ] 建立 `team_colors.py` 核心配置檔案
- [ ] 建立 `__init__.py` 導出介面
- [ ] 撰寫單元測試 `tests/test_team_colors.py`

### Phase 2: 重構現有模組
- [ ] 重構 `laptime_boxplot_widget.py` 的 `_get_team_colors()` 方法
- [ ] 重構 `lap_box_plot_chart_widget.py` 的 `TEAM_COLORS` 常數
- [ ] 重構 `throttle_box_plot_chart_widget.py` 的 `TEAM_COLORS` 常數

### Phase 3: 測試與驗證
- [ ] 單元測試：顏色格式轉換正確性
- [ ] 整合測試：Box Plot 圖表顯示正確
- [ ] 回歸測試：確保舊功能不受影響
- [ ] 手動測試：多賽季顏色切換

### Phase 4: 文檔更新
- [ ] 更新開發者文檔
- [ ] 更新 API 文檔
- [ ] 更新 CHANGELOG

---

## 🔧 重構範例

### Before (舊程式碼)
```python
# laptime_boxplot_widget.py
def _get_team_colors(self, drivers):
    team_colors = {
        'VER': '#3671C6',
        'LEC': '#E8002D',
        # ... 重複定義 20 位車手
    }
    colors = []
    for driver in drivers:
        colors.append(team_colors.get(driver, '#CCCCCC'))
    return colors
```

### After (新程式碼)
```python
# laptime_boxplot_widget.py
from modules.gui.themes.team_colors import get_team_colors_for_drivers

def _get_team_colors(self, drivers):
    """使用中央配置獲取車手顏色"""
    return get_team_colors_for_drivers(
        driver_codes=drivers,
        year=self.year,  # 從資料中取得年份
        format='hex'
    )
```

---

## ✅ 驗收標準

1. **功能性**
   - ✅ 所有 Box Plot 圖表顏色顯示正確
   - ✅ 支援 RGB 和 Hex 兩種格式
   - ✅ 未知車手顯示預設灰色

2. **程式碼品質**
   - ✅ 移除所有重複的顏色定義
   - ✅ 通過所有單元測試
   - ✅ 符合 DRY 原則

3. **可維護性**
   - ✅ 顏色定義集中在單一檔案
   - ✅ 易於新增新賽季配色
   - ✅ 文檔完整清晰

---

## ⚠️ 注意事項

1. **向下相容性**: 必須確保舊程式碼不會因此重構而失效
2. **賽季切換**: 考慮未來支援 2024/2026 賽季的擴展性
3. **顏色準確性**: 顏色應基於 F1 官方車隊視覺識別
4. **效能考量**: 避免重複建立 `QColor` 物件，考慮快取

---

## 🔗 相關資源

- **F1 官方車隊配色**: https://www.formula1.com/en/teams.html
- **PyQt5 QColor 文檔**: https://doc.qt.io/qt-5/qcolor.html
- **顏色轉換工具**: RGB ↔ Hex 轉換器

---

## 📊 進度追蹤

| Phase | 任務 | 狀態 | 負責人 | 完成日期 |
|-------|------|------|--------|----------|
| 1 | 建立中央配置 | 📝 待開發 | - | - |
| 2 | 重構現有模組 | 📝 待開發 | - | - |
| 3 | 測試與驗證 | 📝 待開發 | - | - |
| 4 | 文檔更新 | 📝 待開發 | - | - |

**總體進度**: 0% (0/4 完成)

---

## 💡 未來擴展

1. **動態顏色主題**: 支援淺色/深色模式自動調整顏色亮度
2. **自訂配色**: 允許使用者自訂車手顏色
3. **API 整合**: 從 F1 API 動態獲取官方配色 (如果可用)
4. **顏色無障礙**: 支援色盲友善配色方案

---

**最後更新**: 2025-10-08  
**任務建立者**: GitHub Copilot  
**相關任務**: 無
