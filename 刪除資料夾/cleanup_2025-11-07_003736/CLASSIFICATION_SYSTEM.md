# 🔍 F1 主要部件變更類型自動分類系統

## 📊 系統概述

現在生成的 `2025_f1_major_upgrades_organized.json` 包含**自動變更類型分類**功能，每筆升級記錄都會被自動分類為以下四種類型：

## 🏷️ 變更類型定義

### 1. 升級套件 (Upgrade Package)
**定義**: 新設計、需 re-presented / re-homologated、性能提升

**關鍵字**:
- `new` (但不含 previously)
- `re-presented`
- `re-homologated`
- `after modification`
- `new specification`
- `upgrade`
- `development`

**範例**:
```json
{
  "更換部件": "CE (powerbox, new)",
  "變更類型": "升級套件 (Upgrade Package)",
  "變更類型說明": "新設計、需 re-presented / re-homologated、性能提升",
  "分類信心度": 0.8
}
```

### 2. 重大更新 (Major Update)
**定義**: 結構性改動、觸發 FIA 重新檢驗、但非全新套件

**關鍵字**:
- `floor assembly`
- `sidepod`
- `survival cell`
- `monocoque`
- `chassis` (非 saver plate)
- `gearbox assembly`
- `ICE`, `MGU-H`, `MGU-K` (非 previously used)
- `turbo`
- `energy store`

**範例**:
```json
{
  "更換部件": "Floor assembly (excluding skids and plank)",
  "變更類型": "重大更新 (Major Update)",
  "變更類型說明": "結構性改動、觸發 FIA 重新檢驗、但非全新套件",
  "分類信心度": 0.65
}
```

### 3. 變更 (Change)
**定義**: Parc Fermé 內合法調整、空力/配置切換

**關鍵字**:
- `wing assembly`
- `front wing`, `rear wing`
- `floor edge`
- `floor stay`
- `suspension closing panel`
- `suspension fairing`
- `brake duct`
- `endplate`
- `flap`
- `diveplane`
- `winglet`
- `bodywork`
- `engine cover`
- `parameter changes`

**範例**:
```json
{
  "更換部件": "Front wing / nose assembly",
  "變更類型": "變更 (Change)",
  "變更類型說明": "Parc Fermé 內合法調整、空力/配置切換",
  "分類信心度": 0.8
}
```

### 4. 維修 (Repair)
**定義**: 損壞後更換舊件或備件

**關鍵字**:
- `previously used`
- `damaged`
- `replacement` (非 new)
- `outboard suspension`
- `inboard suspension`
- `sensor`
- `hose`, `pipe`
- `seal`, `gasket`
- `rubber`, `foam`
- `fixings`, `fastener`
- `bearing`
- `clutch friction`, `brake friction`
- `plank`, `skid`

**範例**:
```json
{
  "更換部件": "ICE (previously used)",
  "變更類型": "維修 (Repair)",
  "變更類型說明": "損壞後更換舊件或備件",
  "分類信心度": 0.65
}
```

### 5. 未分類 (Unclassified)
**定義**: 無法根據現有規則分類

**特徵**:
- 沒有匹配任何關鍵字
- 信心度: 0.0

## 📈 2025 賽季統計（截至 2025-11-06）

### 全局分佈
| 變更類型 | 數量 | 百分比 |
|---------|------|--------|
| 變更 (Change) | 39 次 | 32.5% |
| 重大更新 (Major Update) | 38 次 | 31.7% |
| 維修 (Repair) | 28 次 | 23.3% |
| 未分類 (Unclassified) | 13 次 | 10.8% |
| 升級套件 (Upgrade Package) | 2 次 | 1.7% |

### 主要發現
1. **變更 (Change)** 是最常見的類型（32.5%），反映 Parc Fermé 規則下的空力配置調整
2. **重大更新** 占 31.7%，顯示車隊持續進行結構性升級
3. **升級套件** 僅 2 次（1.7%），顯示真正的「全新設計」相對罕見
4. **未分類** 占 10.8%，可能需要進一步改進分類規則

## 💻 JSON 結構範例

```json
{
  "metadata": {
    "全局統計": {
      "總升級次數": 120,
      "變更類型分佈": {
        "變更 (Change)": 39,
        "重大更新 (Major Update)": 38,
        "維修 (Repair)": 28,
        "未分類 (Unclassified)": 13,
        "升級套件 (Upgrade Package)": 2
      }
    }
  },
  "車隊升級記錄": {
    "Williams": {
      "車手": {
        "Alexander Albon": {
          "升級記錄": [
            {
              "賽事名稱": "Saudi Arabian",
              "比賽日期": "2025-05-18",
              "更換部件": "Front wing / nose assembly",
              "部件類別": "前翼系統",
              "變更類型": "變更 (Change)",
              "變更類型說明": "Parc Fermé 內合法調整、空力/配置切換",
              "分類信心度": 0.8,
              "資料來源": {
                "文件名稱": "2025 Saudi Arabian GP - Parc Fermé.pdf",
                "頁碼": 2
              }
            }
          ]
        }
      }
    }
  }
}
```

## 🔧 自動化流程

### 使用自動更新腳本
```powershell
# 自動檢測新 PDF 並重新分類
python auto_update_upgrades.py

# 強制重新分析所有文件（包含重新分類）
python auto_update_upgrades.py --force
```

執行後會自動：
1. 掃描 `fiadoc/` 資料夾
2. 分析部件變更
3. **自動分類每筆變更**
4. 生成包含分類資訊的 JSON

### 查看分類統計
```powershell
python show_classification_stats.py
```

顯示：
- 全局變更類型分佈
- 各車隊變更類型分佈
- 各類型範例
- 變更類型定義

## 📊 分類器工作原理

### 優先級系統
分類器使用**優先級**來處理關鍵字衝突：

1. **升級套件** (優先級 1) - 最高優先
2. **重大更新** (優先級 2)
3. **變更** (優先級 3)
4. **維修** (優先級 4) - 最低優先

### 信心度計算
```python
信心度 = 0.5 + (匹配關鍵字數量 × 0.15)
最大值 = 0.99
```

範例：
- 匹配 1 個關鍵字 → 65% 信心度
- 匹配 2 個關鍵字 → 80% 信心度
- 匹配 3+ 個關鍵字 → 95% 信心度

### 正則表達式匹配
使用進階正則表達式避免誤判：

```python
# ✅ 匹配 "ICE" 但排除 "previously used"
r'\bICE\b(?!.*previously)'

# ✅ 匹配 "new" 但排除 "previously"
r'\bnew\b(?!.*previously)'

# ✅ 匹配 "chassis" 但排除 "saver"
r'\bchassis\b(?!.*saver)'
```

## 🎯 實際應用案例

### 案例 1: Ferrari 的 CE 升級
```json
{
  "車隊": "Ferrari",
  "車手": "Charles Leclerc",
  "更換部件": "CE (powerbox, new)",
  "變更類型": "升級套件 (Upgrade Package)",
  "匹配關鍵字": ["new"],
  "信心度": 0.65
}
```
**分析**: 包含 "new" 且非 "previously used"，判定為全新升級套件

### 案例 2: McLaren 的引擎維修
```json
{
  "車隊": "McLaren",
  "車手": "Lando Norris",
  "更換部件": "ICE (previously used)",
  "變更類型": "維修 (Repair)",
  "匹配關鍵字": ["previously used"],
  "信心度": 0.65
}
```
**分析**: 包含 "previously used"，判定為舊件更換（維修）

### 案例 3: Williams 的底板更新
```json
{
  "車隊": "Williams",
  "車手": "Alexander Albon",
  "更換部件": "Floor assembly (excluding skids and plank)",
  "變更類型": "重大更新 (Major Update)",
  "匹配關鍵字": ["floor assembly"],
  "信心度": 0.65
}
```
**分析**: 底板組件屬於重大結構性部件，需 FIA 檢驗

## 🔍 改進分類準確度

### 添加新關鍵字
編輯 `upgrade_classifier.py` 的 `CLASSIFICATIONS` 字典：

```python
"升級套件 (Upgrade Package)": {
    "keywords": [
        r'\byour_new_keyword\b',  # 添加新關鍵字
        # ... 現有關鍵字
    ]
}
```

### 調整優先級
如果發現分類衝突，可調整 `priority` 值：
- 數字越小 = 優先級越高
- 優先級高的規則會優先匹配

### 強制重新分類
```powershell
# 清除緩存並重新分析
python auto_update_upgrades.py --clear-cache
python auto_update_upgrades.py --force
```

## 📝 技術文件

### 相關腳本
- `upgrade_classifier.py` - 分類器核心邏輯
- `reorganize_major_upgrades.py` - 整合分類器的 JSON 重組
- `show_classification_stats.py` - 分類統計視覺化
- `auto_update_upgrades.py` - 自動化完整流程

### 輸出檔案
- `2025_f1_major_upgrades_organized.json` - 包含分類的完整 JSON
- `.pdf_cache.json` - PDF 文件緩存（避免重複處理）

## ✅ 總結

**變更類型自動分類系統**提供：
1. ✅ 自動識別 4 種變更類型
2. ✅ 基於 FIA 規則的關鍵字匹配
3. ✅ 優先級系統處理衝突
4. ✅ 信心度評估
5. ✅ 完整的統計分析
6. ✅ 自動化工作流程

這使得分析 F1 車隊技術發展策略變得更加簡單和精確！
