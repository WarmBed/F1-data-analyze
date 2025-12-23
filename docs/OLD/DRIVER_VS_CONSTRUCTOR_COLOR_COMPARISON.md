# 🔍 Driver Standings vs Constructor Standings 深度比較報告
**日期**: 2025-10-19  
**比較範圍**: 顏色讀取邏輯與數據流向

---

## 📊 **一、架構對比總覽**

| 比較維度 | Driver Standings | Constructor Standings |
|---------|------------------|----------------------|
| **DataLoader 類別** | `DriverStandingsDataLoader` | `ConstructorStandingsDataLoader` |
| **Widget 類別** | `DriverStandingsWidget` | `ConstructorStandingsWidget` |
| **CLI 功能** | Function 97 | Function 97 |
| **JSON 來源** | `championship_standings_{year}_R{round}.json` | 同左（共用） |
| **資料欄位** | `data.drivers[]` | `data.constructors[]` |
| **是否需要 team_slug 映射** | ❌ **否** | ✅ **是** |
| **顏色查詢 API** | `get_driver_color(driver_code)` | `get_team_color(team_slug)` |

---

## 🔄 **二、數據流向對比**

### 🏎️ **Driver Standings 數據流**

```
championship_standings JSON
         ↓
    drivers[] 陣列
         ↓
 {
   "driver": {"code": "VER"},
   "constructors": [{"name": "Red Bull"}]
 }
         ↓
 DataLoader._transform_data_for_display()
         ↓
 {
   "driver_code": "VER",     ← 直接使用，無需映射
   "team": "Red Bull"         ← 僅用於顯示
 }
         ↓
 Widget.populate_table()
         ↓
 color_palette_provider.get_driver_color("VER")  ← 直接查詢
         ↓
 顯示車手顏色 ✅
```

### 🏁 **Constructor Standings 數據流**

```
championship_standings JSON
         ↓
  constructors[] 陣列
         ↓
 {
   "constructor": {
     "constructor_id": "red_bull",
     "name": "Red Bull"
   }
 }
         ↓
 DataLoader._load_team_slug_mapping()  ← ✅ 關鍵步驟
         ↓
 team_colors JSON: data.teams{}
         ↓
 建立映射表:
 {
   "Red Bull" → "red bull",
   "RB" → "racing bulls",
   "Sauber" → "kick sauber"
 }
         ↓
 DataLoader._transform_data_for_display()
         ↓
 {
   "constructor_name": "RB",            ← 顯示名稱
   "team_slug": "racing bulls"          ← ✅ 新增：用於顏色查詢
 }
         ↓
 Widget.populate_table()
         ↓
 color_palette_provider.get_team_color("racing bulls")  ← 使用 team_slug
         ↓
 顯示車隊顏色 ✅
```

---

## 🔑 **三、關鍵差異分析**

### ✅ **差異 1: DataLoader 的 import 差異**

#### Driver Standings DataLoader
```python
from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List
# ❌ 不需要額外 import
```

#### Constructor Standings DataLoader
```python
from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List
import json        # ✅ 需要讀取 team_colors JSON
from pathlib import Path  # ✅ 需要檔案系統操作
```

**原因**: Constructor Standings 需要載入 `team_colors` JSON 建立映射表。

---

### ✅ **差異 2: DataLoader 方法差異**

#### Driver Standings DataLoader
```python
def _transform_data_for_display(self, raw_data):
    drivers = data.get("drivers", [])
    
    for entry in drivers:
        driver_info = entry.get("driver", {})
        team_name = constructors[0].get("name", "Unknown")
        
        transformed_rows.append({
            "driver_code": driver_info.get("code", "N/A"),  # ← 直接使用
            "team": team_name,  # ← 僅用於顯示
            # ❌ 不需要 team_slug
        })
```

#### Constructor Standings DataLoader
```python
def _load_team_slug_mapping(self) -> Dict[str, str]:
    """✅ 新增方法：建立 team_name → team_slug 映射"""
    team_slug_map = {}
    team_color_files = list(json_dir.glob(f"team_colors_{self.year}_*.json"))
    
    with open(latest_file, "r", encoding="utf-8") as f:
        color_data = json.load(f)
    
    teams_data = color_data.get("data", {}).get("teams", {})
    for team_slug, info in teams_data.items():
        team_name = info.get("team_name")
        if team_name:
            team_slug_map[team_name] = team_slug  # ✅ 建立映射
    
    return team_slug_map

def _transform_data_for_display(self, raw_data):
    team_slug_map = self._load_team_slug_mapping()  # ✅ 載入映射
    constructors = data.get("constructors", [])
    
    for entry in constructors:
        team_name = constructor_info.get("name", "Unknown")
        team_slug = team_slug_map.get(team_name, team_name.lower())  # ✅ 查詢映射
        
        transformed_rows.append({
            "constructor_name": team_name,      # ← 顯示名稱
            "team_slug": team_slug,             # ✅ 新增：用於顏色查詢
        })
```

**原因**: 
- Driver Standings 使用 `driver_code` 直接查詢顏色，無需映射
- Constructor Standings 使用 `team_name`（顯示名稱）無法直接查詢，需要映射到 `team_slug`

---

### ✅ **差異 3: Widget 顏色查詢方式**

#### Driver Standings Widget
```python
def populate_table(self):
    for row_idx, entry in enumerate(self.standings_data):
        # 1. 車手代碼
        driver_code = entry.get("driver_code", "")
        driver_color = color_palette_provider.get_driver_color(driver_code, fallback=True)
        # ✅ 直接使用 driver_code 查詢
        
        # 2. 車手姓名
        driver_name_item = self._create_colored_item(driver_name, driver_color)
        # ✅ 使用同樣的車手顏色
        
        # 3. 車隊
        team_color = color_palette_provider.get_driver_color(driver_code, fallback=True)
        # ✅ 仍使用車手顏色（車隊欄位）
```

#### Constructor Standings Widget
```python
def populate_table(self):
    for row_idx, entry in enumerate(self.standings_data):
        # 1. 車隊名稱
        team_name = entry.get("constructor_name", "Unknown")
        team_slug = entry.get("team_slug", team_name.lower())  # ✅ 從 DataLoader 獲取
        team_color = color_palette_provider.get_team_color(team_slug)  # ✅ 使用 team_slug 查詢
        # ❌ 不能使用 team_name 查詢（會失敗）
```

**關鍵差異**:
- Driver: `get_driver_color(driver_code)` → 車手代碼直接對應
- Constructor: `get_team_color(team_slug)` → 需要從 team_name 映射到 team_slug

---

## 🎨 **四、ColorPaletteProvider 的內部查詢邏輯**

### 🔍 **get_driver_color() 查詢流程**

```python
def get_driver_color(self, driver_code: str):
    """
    查詢順序：
    1. _driver_palette[driver_code]  ← 直接查詢
    2. DEFAULT_DRIVER_MAP[driver_code] → team_slug → _team_palette[team_slug]
    3. _team_palette[normalize(driver_code)]  ← 嘗試作為車隊名稱
    4. 預設顏色
    """
    code = self._normalize_driver_code(driver_code)  # VER → ver
    entry = self._driver_palette.get(code)  # ✅ 直接查詢
    
    if entry is None and fallback:
        # 嘗試從 DEFAULT_DRIVER_MAP 獲取車隊顏色
        if code in DEFAULT_DRIVER_MAP:
            team_slug, _ = DEFAULT_DRIVER_MAP[code]
            team_entry = self._team_palette.get(team_slug)
            if team_entry:
                return self._format_entry(team_entry, format)
    
    return self._format_entry(entry, format)
```

**範例**:
```python
get_driver_color("VER")
  → _driver_palette["ver"]  # ✅ 找到
  → 返回 Red Bull 顏色 #0600EF
```

### 🔍 **get_team_color() 查詢流程**

```python
def get_team_color(self, team_identifier: str):
    """
    查詢順序：
    1. _team_palette[normalize(team_identifier)]  ← 正規化後查詢
    2. 預設顏色
    """
    slug = self._normalize_team_slug(team_identifier)  # Red Bull → red bull
    entry = self._team_palette.get(slug)  # ✅ 查詢
    
    if entry is None and fallback:
        return self._default_color(format)
    
    return self._format_entry(entry, format)
```

**範例（修正前的問題）**:
```python
# ❌ 錯誤：使用 team_name 查詢
get_team_color("RB")
  → normalize("RB") → "rb"
  → _team_palette["rb"]  # ❌ 找不到（實際鍵是 "racing bulls"）
  → 返回預設顏色 #CCCCCC

# ✅ 正確：使用 team_slug 查詢
get_team_color("racing bulls")
  → normalize("racing bulls") → "racing bulls"
  → _team_palette["racing bulls"]  # ✅ 找到
  → 返回 RB 顏色 #FCD700
```

---

## 🔧 **五、_normalize_team_slug() 的影響**

### 📝 **正規化規則**

```python
@staticmethod
def _normalize_team_slug(identifier: str) -> str:
    """正規化車隊名稱為小寫 slug，移除常見後綴"""
    normalized = str(identifier or "").strip().lower()
    
    suffixes_to_remove = [
        " f1 team",  # ✅ 移除
        " racing",   # ⚠️ 問題：會破壞 "racing bulls"
        " f1",       # ✅ 移除
    ]
    
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized
```

### 🚨 **潛在問題案例**

| 輸入 | 正規化結果 | 預期結果 | 狀態 |
|-----|----------|---------|------|
| `"Red Bull"` | `"red bull"` ✅ | `"red bull"` | ✅ 正確 |
| `"RB F1 Team"` | `"rb"` ✅ | `"rb"` | ✅ 正確 |
| `"Racing Bulls"` | `"racing"` ❌ | `"racing bulls"` | ❌ **錯誤** |
| `"racing bulls"` | `"racing"` ❌ | `"racing bulls"` | ❌ **錯誤** |

**解決方案**: 已透過 DataLoader 提供正確的 `team_slug`，跳過正規化陷阱。

---

## 📦 **六、JSON 數據結構對比**

### 🏎️ **championship_standings JSON (Function 97 輸出)**

```json
{
  "data": {
    "drivers": [
      {
        "driver": {
          "code": "VER",         ← Driver Widget 直接使用
          "full_name": "Max Verstappen"
        },
        "constructors": [
          {
            "constructor_id": "red_bull",
            "name": "Red Bull"    ← 僅用於顯示
          }
        ]
      }
    ],
    "constructors": [
      {
        "constructor": {
          "constructor_id": "racing_bulls",  ← 無法直接用於顏色查詢
          "name": "RB"                       ← 用於顯示 + 映射查詢
        }
      }
    ]
  }
}
```

### 🎨 **team_colors JSON (Function 98 輸出)**

```json
{
  "data": {
    "teams": {
      "racing bulls": {           ← ✅ team_slug (查詢鍵)
        "team_name": "RB",        ← 顯示名稱
        "selected_hex": "#FCD700"
      },
      "kick sauber": {            ← ✅ team_slug (查詢鍵)
        "team_name": "Sauber",    ← 顯示名稱
        "selected_hex": "#00E700"
      }
    },
    "drivers": {
      "VER": {                    ← ✅ driver_code (查詢鍵)
        "team_slug": "red bull",
        "hex": "#0600EF"
      }
    }
  }
}
```

---

## ⚠️ **七、為什麼 Constructor 需要映射而 Driver 不需要？**

### 🔍 **根本原因分析**

#### **Driver Standings 的優勢**
1. **一致性鍵值**: JSON 中的 `driver.code` 與顏色配置中的 `drivers[code]` 完全一致
2. **無歧義**: 車手代碼（例如 `VER`）全球唯一，不會有命名變化
3. **直接映射**: `driver_code` → `_driver_palette[code]` 一步到位

#### **Constructor Standings 的挑戰**
1. **不一致鍵值**: 
   - JSON 使用 `constructor_id` (例如: `"rb"`, `"red_bull"`)
   - 顯示使用 `name` (例如: `"RB"`, `"Red Bull"`)
   - 顏色配置使用 `team_slug` (例如: `"racing bulls"`, `"red bull"`)
2. **多重命名**: 同一車隊有多種表示方式
3. **間接映射**: `team_name` → 映射表查詢 → `team_slug` → `_team_palette[slug]`

### 📊 **映射需求對比**

| 查詢路徑 | Driver Standings | Constructor Standings |
|---------|------------------|----------------------|
| **JSON 欄位** | `driver.code` | `constructor.name` |
| **顯示名稱** | `driver.full_name` | `constructor.name` |
| **顏色鍵值** | `driver_code` | `team_slug` |
| **是否一致** | ✅ 是 | ❌ 否 |
| **需要映射** | ❌ 否 | ✅ 是 |

---

## 🛠️ **八、修復前後對比**

### ❌ **修復前 (Constructor Standings 顏色錯誤)**

```python
# DataLoader
def _transform_data_for_display(self, raw_data):
    transformed_rows.append({
        "constructor_name": "RB",
        # ❌ 缺少 team_slug
    })

# Widget
team_name = entry.get("constructor_name", "Unknown")  # "RB"
team_color = color_palette_provider.get_team_color(team_name)  # ❌ "RB" 查不到
# → 返回預設顏色 #CCCCCC
```

**結果**: RB 和 Sauber 顯示灰色 ❌

### ✅ **修復後 (正確顏色)**

```python
# DataLoader
def _load_team_slug_mapping(self):
    # ✅ 新增：建立映射表
    return {"RB": "racing bulls", "Sauber": "kick sauber"}

def _transform_data_for_display(self, raw_data):
    team_slug_map = self._load_team_slug_mapping()
    team_slug = team_slug_map.get("RB", "rb")  # ✅ "racing bulls"
    
    transformed_rows.append({
        "constructor_name": "RB",
        "team_slug": "racing bulls",  # ✅ 新增
    })

# Widget
team_slug = entry.get("team_slug", team_name.lower())  # ✅ "racing bulls"
team_color = color_palette_provider.get_team_color(team_slug)  # ✅ 正確查詢
# → 返回 RB 顏色 #FCD700
```

**結果**: RB 顯示金色 #FCD700 ✅, Sauber 顯示綠色 #00E700 ✅

---

## 🎯 **九、最佳實踐建議**

### ✅ **Driver Standings 開發建議**
1. **直接使用 driver_code**: 無需額外映射
2. **車隊欄位顏色**: 使用 `get_driver_color(driver_code)` 保持一致
3. **簡潔實現**: 不需要載入額外的映射表

### ✅ **Constructor Standings 開發建議**
1. **必須建立映射表**: `_load_team_slug_mapping()` 是必要的
2. **傳遞 team_slug**: DataLoader 必須提供 `team_slug` 欄位給 Widget
3. **使用正確 API**: Widget 使用 `get_team_color(team_slug)` 而非 `team_name`

### ✅ **未來新模組開發指南**
```python
# 如果模組需要顯示車隊顏色：
if uses_team_colors:
    # ✅ 方案 1: 如果有 driver_code
    color = color_palette_provider.get_driver_color(driver_code)
    
    # ✅ 方案 2: 如果只有 team_name
    team_slug_map = self._load_team_slug_mapping()
    team_slug = team_slug_map.get(team_name, team_name.lower())
    color = color_palette_provider.get_team_color(team_slug)
```

---

## 📈 **十、性能影響分析**

### 🔢 **Driver Standings**
- **映射表載入**: ❌ 無
- **查詢複雜度**: O(1) - 直接字典查詢
- **記憶體開銷**: 低

### 🔢 **Constructor Standings**
- **映射表載入**: ✅ 需要讀取 team_colors JSON (~10-50 KB)
- **映射表大小**: ~10 個車隊映射
- **查詢複雜度**: O(1) + O(1) = O(1) - 雙重字典查詢
- **記憶體開銷**: 中等（額外 ~1KB 映射表）

**結論**: 性能影響可忽略不計，映射表載入只在初始化時執行一次。

---

## 🔗 **十一、總結**

### 核心差異
1. **Driver Standings**: 使用 `driver_code` 直接查詢，無需額外映射
2. **Constructor Standings**: 使用 `team_name` 顯示，需要映射到 `team_slug` 查詢顏色

### 設計原因
- **車手代碼全球唯一**: `VER`, `HAM`, `LEC` 無歧義
- **車隊名稱多變**: `"RB"` vs `"racing bulls"` vs `"rb"` 需要統一

### 修復關鍵
✅ Constructor Standings 新增 `_load_team_slug_mapping()` 方法  
✅ DataLoader 提供 `team_slug` 欄位  
✅ Widget 使用 `team_slug` 查詢顏色

### 覆寫系統整合
✅ Function 97 已整合 `driver_team_overrides.json`  
✅ Function 98 已整合覆寫系統  
✅ TSU → Red Bull, LAW → RB 覆寫正常生效

---

**報告完成** 🏁
