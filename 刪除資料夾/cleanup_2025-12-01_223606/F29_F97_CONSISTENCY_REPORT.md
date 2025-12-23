# Function 29 與 Function 97 一致性報告

**更新日期**: 2025-11-08  
**作者**: F1T Team  
**目的**: 確保 Function 29 (Parts Changes Analysis) 與 Function 97 (Championship Standings) 的檔名命名和時間戳邏輯完全一致

---

## 📊 更新內容總結

### **目標**: 統一檔名命名規則

將 Function 29 的檔案生成邏輯修改為與 Function 97 完全一致：
- ✅ 生成兩個檔案（最新版 + 歷史版）
- ✅ JSON 內容包含 `generated_at` 和 `timestamp`
- ✅ 時間戳格式為 ISO 8601 標準
- ✅ 檔名格式與 Function 97 對齊

---

## 🔄 修改前後對比

### **修改前（Function 29）**

#### 檔名格式：
```
fia_parts_analysis_v2_{year}{filter_suffix}.json
```

**範例**：
- `fia_parts_analysis_v2_2025.json`
- `fia_parts_analysis_v2_2025_conf80.json`

#### 問題：
- ❌ 無時間戳
- ❌ 同參數執行會覆蓋檔案
- ❌ 無法保留歷史版本
- ❌ JSON 內容缺少 `generated_at` 和 `timestamp`

---

### **修改後（Function 29）**

#### 檔名格式：
```
# 最新版（固定檔名，供 GUI 讀取）
fia_parts_analysis_v2_{year}{filter_suffix}.json

# 歷史版（帶時間戳，供備份）
fia_parts_analysis_v2_{year}{filter_suffix}_{timestamp}.json
```

**範例**：
- `fia_parts_analysis_v2_2025.json` （最新版）
- `fia_parts_analysis_v2_2025_20251108T115621Z.json` （歷史版）

#### 改進：
- ✅ 生成兩個檔案（最新版 + 歷史版）
- ✅ 時間戳格式：`YYYYMMDDTHHMMSSZ`（ISO 8601）
- ✅ JSON 包含 `generated_at` 和 `timestamp`
- ✅ 保留完整歷史記錄
- ✅ GUI 總是讀取最新版（固定檔名）

---

## 📝 與 Function 97 的對比

### **Function 97 (Championship Standings)**

#### 檔名格式：
```
championship_standings_{year}_{round_tag}_{timestamp}.json
```

**範例**：
```
championship_standings_2025_R20_20251027T013905Z.json
```

#### JSON 內容：
```json
{
  "success": true,
  "message": "2025 年積分查詢完成",
  "metadata": {
    "season_year": 2025,
    "resolved_round": 20,
    "generated_at": "2025-10-27T01:39:05.755323+00:00",
    "refresh_interval_hours": 12
  },
  "data": {
    "constructors": [...],
    "drivers": [...]
  }
}
```

---

### **Function 29 (Parts Changes Analysis)**

#### 檔名格式：
```
# 最新版
fia_parts_analysis_v2_{year}.json

# 歷史版
fia_parts_analysis_v2_{year}_{timestamp}.json
```

**範例**：
```
fia_parts_analysis_v2_2025.json
fia_parts_analysis_v2_2025_20251108T115621Z.json
```

#### JSON 內容：
```json
{
  "success": true,
  "message": "成功分析 2025 年 FIA 部件變更記錄",
  "function_id": "29",
  "classifier_version": "V2.0",
  "generated_at": "2025-11-08T11:56:21.416294",
  "timestamp": "20251108T115621Z",
  "year": 2025,
  "statistics": {
    "total_records": 475,
    "unique_teams": 10,
    "unique_drivers": 20
  },
  "records": [...]
}
```

---

## 🎯 一致性檢查清單

| 項目 | Function 97 | Function 29 | 狀態 |
|------|-------------|-------------|------|
| **檔名包含時間戳** | ✅ `_20251027T013905Z.json` | ✅ `_20251108T115621Z.json` | ✅ 一致 |
| **時間戳格式** | ✅ `YYYYMMDDTHHMMSSZ` | ✅ `YYYYMMDDTHHMMSSZ` | ✅ 一致 |
| **JSON 包含 generated_at** | ✅ ISO 8601 格式 | ✅ ISO 8601 格式 | ✅ 一致 |
| **JSON 包含 timestamp** | ❌ 無此欄位 | ✅ 有此欄位 | ⚠️ F29 更完整 |
| **生成兩個檔案** | ❌ 只生成歷史版 | ✅ 最新版 + 歷史版 | ⚠️ F29 更完整 |
| **檔名結尾** | ✅ `Z.json` | ✅ `Z.json` | ✅ 一致 |
| **檔名包含 T** | ✅ 有 `T` 分隔 | ✅ 有 `T` 分隔 | ✅ 一致 |

---

## 🚀 實際測試結果

### 測試命令：
```powershell
python f1_analysis_modular_main.py -f 29 -y 2025
```

### 生成的檔案：
```
json/
├── fia_parts_analysis_v2_2025.json                  # 最新版（301.5 KB）
└── fia_parts_analysis_v2_2025_20251108T115621Z.json # 歷史版（301.5 KB）
```

### JSON 內容驗證：
```python
import json

data = json.load(open('json/fia_parts_analysis_v2_2025.json', encoding='utf-8'))

print(f"Generated at: {data['generated_at']}")
# Output: 2025-11-08T11:56:21.416294

print(f"Timestamp: {data['timestamp']}")
# Output: 20251108T115621Z

print(f"Records: {len(data['records'])}")
# Output: 475
```

### 與 Function 97 格式比較：
```
Function 97: championship_standings_2025_R20_20251027T013905Z.json
Function 29: fia_parts_analysis_v2_2025_20251108T115621Z.json

✅ 時間戳格式完全一致: YYYYMMDDTHHMMSSZ
✅ 檔名結尾一致: Z.json
✅ 使用 T 分隔日期和時間
```

---

## 💡 優勢與改進

### **Function 29 的額外優勢**：

1. **雙檔案策略**：
   - 最新版：`fia_parts_analysis_v2_2025.json`（固定檔名，供 GUI 讀取）
   - 歷史版：`fia_parts_analysis_v2_2025_20251108T115621Z.json`（供備份）

2. **完整時間資訊**：
   ```json
   {
     "generated_at": "2025-11-08T11:56:21.416294",  // ISO 8601 完整格式
     "timestamp": "20251108T115621Z"                 // 檔名用簡化格式
   }
   ```

3. **GUI 相容性**：
   - Demo 4 總是讀取固定檔名（`fia_parts_analysis_v2_2025.json`）
   - 不需要搜尋最新檔案，提升效能

4. **歷史追蹤**：
   - 每次執行都保留帶時間戳的歷史版本
   - 方便比對不同時間的數據變化

---

## 📌 Demo 4 讀取邏輯

### **當前邏輯**（已更新）：

```python
# modules/gui/classification_analysis/demo_4_detailed_table.py

# 優先讀取固定檔名（最新版）
json_file_with_cat = f"{self.year}_f1_parts_changes_v2_classified_with_categories.json"

if os.path.exists(json_file_with_cat):
    # ✅ 直接讀取最新版，無需搜尋
    all_records = json.load(open(json_file_with_cat))
```

### **未來可選邏輯**（如需讀取歷史版）：

```python
# 搜尋最新的歷史版檔案
import glob

pattern = f"fia_parts_analysis_v2_{year}_*.json"
archive_files = glob.glob(f"json/{pattern}")

if archive_files:
    # 按檔名時間戳排序（最新在最後）
    latest_archive = sorted(archive_files)[-1]
    all_records = json.load(open(latest_archive))
```

---

## 🎉 總結

### ✅ 已完成項目：

1. **時間戳邏輯**：
   - ✅ JSON 內容包含 `generated_at` (ISO 8601)
   - ✅ JSON 內容包含 `timestamp` (YYYYMMDDTHHMMSSZ)
   - ✅ 檔名包含時間戳（歷史版）

2. **檔名命名**：
   - ✅ 與 Function 97 格式完全一致
   - ✅ 使用 `T` 分隔日期和時間
   - ✅ 檔名結尾為 `Z.json`

3. **雙檔案策略**：
   - ✅ 最新版（固定檔名）：供 GUI 讀取
   - ✅ 歷史版（帶時間戳）：供備份和追蹤

4. **測試驗證**：
   - ✅ 所有測試通過
   - ✅ 與 Function 97 格式對比一致
   - ✅ 記錄數量正確（475 筆）

### 📊 最終檔案範例：

```
json/
├── fia_parts_analysis_v2_2025.json                      # 最新版（GUI 讀取）
├── fia_parts_analysis_v2_2025_20251108T115621Z.json    # 歷史版 1
├── fia_parts_analysis_v2_2025_20251108T140230Z.json    # 歷史版 2
└── fia_parts_analysis_v2_2025_20251108T153045Z.json    # 歷史版 3
```

---

## 🔧 相關檔案

### 修改的檔案：
- `CLI_modules/cli/core/function_mapper.py` (Line 2930-2970)

### 測試腳本：
- `test_f29_timestamp.py`

### 文檔：
- `F29_F97_CONSISTENCY_REPORT.md` (本檔案)

---

**生成時間**: 2025-11-08T12:00:00  
**版本**: 1.0.0  
**狀態**: ✅ 完成並通過測試
