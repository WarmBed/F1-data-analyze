# Ideal Lap Ranking Table - 車隊欄位多國語言化修復報告

**日期**: 2025-10-22  
**問題**: `ideal_lap_ranking_table` 的車隊欄位仍然沒有多國語言支援  
**狀態**: ✅ **已修復**

---

## 📋 問題分析

### 原始問題
在 `ideal_lap_ranking_table_widget.py` 中，車隊欄位直接顯示從 API 獲取的英文原始名稱（如 "Red Bull Racing", "Ferrari", "McLaren"），沒有使用 `tr()` 函數進行多國語言轉換。

### 受影響的代碼位置
- **檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_widget.py`
- **行號**: 414-423（`_set_row_data` 方法）

---

## 🔧 修復實施

### 1. **新增車隊名稱翻譯系統**

#### 修改檔案: `core/gui_i18n.py`

新增內容：
```python
# F1 車隊名稱的完整翻譯對應
TEAM_NAMES = {
    'Red Bull': {'zh': '紅牛', 'en': 'Red Bull', 'ja': 'レッドブル'},
    'Red Bull Racing': {'zh': '紅牛車隊', 'en': 'Red Bull Racing', 'ja': 'レッドブル・レーシング'},
    'Ferrari': {'zh': '法拉利', 'en': 'Ferrari', 'ja': 'フェラーリ'},
    'Mercedes': {'zh': '梅賽德斯', 'en': 'Mercedes', 'ja': 'メルセデス'},
    'McLaren': {'zh': '麥拉倫', 'en': 'McLaren', 'ja': 'マクラーレン'},
    'Aston Martin': {'zh': '奧斯頓馬丁', 'en': 'Aston Martin', 'ja': 'アストンマーティン'},
    'Alpine': {'zh': '阿爾派', 'en': 'Alpine', 'ja': 'アルピーヌ'},
    'Williams': {'zh': '威廉斯', 'en': 'Williams', 'ja': 'ウィリアムズ'},
    'RB': {'zh': 'RB', 'en': 'RB', 'ja': 'RB'},
    'Haas': {'zh': '哈斯', 'en': 'Haas', 'ja': 'ハース'},
    'Sauber': {'zh': '索伯', 'en': 'Sauber', 'ja': 'ザウバー'},
    'Kick Sauber': {'zh': 'Kick 索伯', 'en': 'Kick Sauber', 'ja': 'キック・ザウバー'},
    'AlphaTauri': {'zh': '紅牛二隊', 'en': 'AlphaTauri', 'ja': 'アルファタウリ'},
    'Alfa Romeo': {'zh': '愛快羅密歐', 'en': 'Alfa Romeo', 'ja': 'アルファロメオ'},
    'Unknown': {'zh': '未知車隊', 'en': 'Unknown', 'ja': '不明'},
}

def get_team_name_text(team_key, language=None):
    """
    取得車隊名稱的翻譯文字
    
    Args:
        team_key: 車隊名稱（英文原始名稱）
        language: 語言代碼 ('zh', 'en', 'ja')，若為 None 則使用當前語言
    
    Returns:
        str: 翻譯後的車隊名稱
    """
    if language is None:
        language = _gui_translator.get_language()
    
    # 完全匹配
    if team_key in TEAM_NAMES:
        return TEAM_NAMES[team_key].get(language, team_key)
    
    # 模糊匹配（處理可能包含 "F1 Team" 後綴的情況）
    team_key_normalized = team_key.replace(" F1 Team", "").strip()
    if team_key_normalized in TEAM_NAMES:
        return TEAM_NAMES[team_key_normalized].get(language, team_key)
    
    # 部分匹配（檢查是否包含已知車隊名稱）
    for known_team in TEAM_NAMES.keys():
        if known_team in team_key or team_key in known_team:
            return TEAM_NAMES[known_team].get(language, team_key)
    
    # 找不到匹配，返回原始名稱
    return team_key
```

### 2. **修改 Widget 以使用翻譯**

#### 修改檔案: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_widget.py`

#### 變更 1: 導入新函數
```python
# 修改前
from core.gui_i18n import tr

# 修改後
from core.gui_i18n import tr, get_team_name_text
```

#### 變更 2: 修改 `_set_row_data` 方法
```python
# 修改前
# 1. 車手（套用車手背景色，自動選擇文字顏色）
driver_code = driver.get("driver", "N/A")
team = driver.get("team", "Unknown")
driver_color = self._get_driver_color(driver_code)
driver_item = self._create_colored_item(driver_code, driver_color)
driver_item.setToolTip(f"{driver_code} - {team}")
self.table.setItem(row, 1, driver_item)

# 2. 車隊（套用車手背景色，自動選擇文字顏色）
team_item = self._create_colored_item(team, driver_color)
team_item.setToolTip(team)
self.table.setItem(row, 2, team_item)

# 修改後
# 1. 車手（套用車手背景色，自動選擇文字顏色）
driver_code = driver.get("driver", "N/A")
team = driver.get("team", "Unknown")
driver_color = self._get_driver_color(driver_code)
driver_item = self._create_colored_item(driver_code, driver_color)
# ✅ 使用多國語言翻譯的車隊名稱
team_translated = get_team_name_text(team)
driver_item.setToolTip(f"{driver_code} - {team_translated}")
self.table.setItem(row, 1, driver_item)

# 2. 車隊（套用車手背景色，自動選擇文字顏色，使用多國語言翻譯）
team_item = self._create_colored_item(team_translated, driver_color)
team_item.setToolTip(team_translated)
self.table.setItem(row, 2, team_item)
```

---

## ✅ 測試驗證

### 測試腳本
創建了 `test_team_i18n.py` 來驗證車隊名稱翻譯功能。

### 測試結果

#### 繁體中文 (zh)
| 原始名稱 | 翻譯結果 |
|---------|---------|
| Red Bull Racing | 紅牛車隊 |
| Ferrari | 法拉利 |
| Mercedes | 梅賽德斯 |
| McLaren | 麥拉倫 |
| Aston Martin | 奧斯頓馬丁 |
| Alpine | 阿爾派 |
| Williams | 威廉斯 |
| RB | RB |
| Haas | 哈斯 |
| Sauber | 索伯 |

#### English (en)
| 原始名稱 | 翻譯結果 |
|---------|---------|
| Red Bull Racing | Red Bull Racing |
| Ferrari | Ferrari |
| Mercedes | Mercedes |
| McLaren | McLaren |
| Aston Martin | Aston Martin |
| Alpine | Alpine |
| Williams | Williams |
| RB | RB |
| Haas | Haas |
| Sauber | Sauber |

#### 日本語 (ja)
| 原始名稱 | 翻譯結果 |
|---------|---------|
| Red Bull Racing | レッドブル・レーシング |
| Ferrari | フェラーリ |
| Mercedes | メルセデス |
| McLaren | マクラーレン |
| Aston Martin | アストンマーティン |
| Alpine | アルピーヌ |
| Williams | ウィリアムズ |
| RB | RB |
| Haas | ハース |
| Sauber | ザウバー |

### 特殊情況處理
✅ **自動去除 "F1 Team" 後綴**
- `"Red Bull Racing F1 Team"` → `"紅牛車隊"` (zh)
- `"McLaren F1 Team"` → `"麥拉倫"` (zh)

---

## 🎯 功能特點

### 1. **智能匹配系統**
- ✅ 完全匹配（精確車隊名稱）
- ✅ 模糊匹配（自動去除 "F1 Team" 後綴）
- ✅ 部分匹配（包含關係檢測）
- ✅ 回退機制（找不到翻譯時返回原始名稱）

### 2. **多語言支援**
- ✅ 繁體中文 (zh)
- ✅ English (en)
- ✅ 日本語 (ja)

### 3. **與現有系統整合**
- ✅ 使用全域 `_gui_translator` 自動偵測當前語言
- ✅ 與 `tr()` 函數保持一致的 API 設計
- ✅ 支援語言切換時即時更新

---

## 📂 修改的檔案清單

1. ✅ `core/gui_i18n.py`
   - 新增 `TEAM_NAMES` 翻譯字典
   - 新增 `get_team_name_text()` 函數

2. ✅ `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_widget.py`
   - 導入 `get_team_name_text` 函數
   - 修改 `_set_row_data()` 方法使用翻譯

3. ✅ `test_team_i18n.py`（新建）
   - 車隊名稱翻譯測試腳本

---

## 🔍 使用範例

### 在 GUI 模組中使用
```python
from core.gui_i18n import get_team_name_text

# 自動使用當前語言
team_name = "Red Bull Racing"
translated = get_team_name_text(team_name)
# 中文環境: "紅牛車隊"
# 英文環境: "Red Bull Racing"
# 日文環境: "レッドブル・レーシング"

# 明確指定語言
translated_zh = get_team_name_text(team_name, language='zh')  # "紅牛車隊"
translated_en = get_team_name_text(team_name, language='en')  # "Red Bull Racing"
translated_ja = get_team_name_text(team_name, language='ja')  # "レッドブル・レーシング"
```

---

## 📊 影響範圍

### 直接影響
- ✅ `ideal_lap_ranking_table` 模組的車隊欄位顯示
- ✅ Tooltip 中的車隊名稱

### 潛在擴展
此翻譯系統可用於其他所有顯示車隊名稱的模組：
- `constructor_standings` - 車隊積分榜
- `pitstop_analysis` - 進站分析
- `accident_analysis` - 事故分析
- 等等...

---

## ✅ 驗證檢查清單

- [x] ✅ 車隊名稱翻譯字典已建立
- [x] ✅ `get_team_name_text()` 函數已實現
- [x] ✅ Widget 已修改使用翻譯
- [x] ✅ 測試腳本已建立並通過
- [x] ✅ 繁體中文翻譯正確
- [x] ✅ 英文原始名稱保留
- [x] ✅ 日文翻譯正確
- [x] ✅ "F1 Team" 後綴自動處理
- [x] ✅ Tooltip 顯示翻譯名稱
- [x] ✅ 與語言切換系統整合

---

## 🎉 總結

**問題**: `ideal_lap_ranking_table` 的車隊欄位沒有多國語言支援  
**解決方案**: 在 `gui_i18n.py` 中建立車隊名稱翻譯系統，並修改 widget 使用翻譯  
**結果**: ✅ **已完全修復**

### 關鍵改進
1. **統一的車隊翻譯系統** - 可供全專案使用
2. **智能匹配機制** - 處理各種車隊名稱格式
3. **三語支援** - 中文、英文、日文
4. **向後兼容** - 不影響現有功能

---

**修復完成日期**: 2025-10-22  
**測試狀態**: ✅ 全部通過  
**部署狀態**: ✅ 可立即使用
