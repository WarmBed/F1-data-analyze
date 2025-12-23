# 自動化 F1 主要部件升級分析器

## 📋 功能說明

`auto_update_upgrades.py` 是一個智能化的分析腳本，可以：

1. **自動掃描** `fiadoc/` 資料夾中的所有 Parc Fermé PDF 文件
2. **檢測變化** 使用 MD5 雜湊值追蹤新增、修改或刪除的 PDF
3. **智能更新** 僅在有變化時重新分析，避免重複計算
4. **完整流程** 自動執行三步驟分析並生成所有 JSON 文件

## 🚀 使用方法

### 基本用法（自動檢測）
```powershell
python auto_update_upgrades.py
```
- 自動掃描 PDF 文件
- 檢測是否有新增或修改
- 僅在有變化時才重新分析

### 強制重新分析
```powershell
python auto_update_upgrades.py --force
```
或
```powershell
python auto_update_upgrades.py -f
```
- 忽略緩存，強制重新分析所有 PDF
- 適用於修改了分析邏輯後需要重新處理

### 清除緩存
```powershell
python auto_update_upgrades.py --clear-cache
```
- 刪除 `.pdf_cache.json` 緩存文件
- 下次執行會將所有 PDF 視為新文件

## 📊 輸出文件

執行後會生成 3 個 JSON 文件：

1. **`2025_f1_parts_changes_complete.json`**
   - 所有部件變更記錄（包括小零件）
   - 共 488 筆記錄

2. **`2025_f1_major_upgrades.json`**
   - 僅主要部件升級（引擎、底板、前翼等）
   - 共 120 筆記錄
   - 包含統計資訊

3. **`2025_f1_major_upgrades_organized.json`** ⭐ 推薦
   - 按車隊 → 車手 → 賽事組織的結構化數據
   - 包含完整的統計和來源資訊
   - 最易於分析和使用

## 🔍 緩存機制

腳本會自動創建 `.pdf_cache.json` 追蹤已處理的文件：

```json
{
  "last_update": "2025-11-06T21:12:13",
  "total_pdfs": 27,
  "processed_files": {
    "檔案名稱": {
      "hash": "MD5 雜湊值",
      "first_seen": "首次發現時間",
      "last_processed": "最後處理時間"
    }
  }
}
```

### 緩存優點
- ✅ 避免重複分析未變化的 PDF（節省時間）
- ✅ 自動檢測新增的 FIA 文件
- ✅ 追蹤文件修改（例如 FIA 更新文件）
- ✅ 記錄處理歷史

## 📝 使用場景

### 場景 1: 首次執行
```powershell
python auto_update_upgrades.py
```
- 掃描所有 PDF（27 個）
- 分析並生成 3 個 JSON
- 創建緩存記錄

### 場景 2: FIA 發布新的 Parc Fermé 文件
1. 下載新的 PDF 到 `fiadoc/` 資料夾
2. 執行腳本：
```powershell
python auto_update_upgrades.py
```
3. 腳本自動檢測新文件並重新分析

### 場景 3: 修改了分析邏輯
```powershell
# 清除緩存
python auto_update_upgrades.py --clear-cache

# 強制重新分析
python auto_update_upgrades.py --force
```

### 場景 4: 定期檢查更新
```powershell
# 設置 Windows 排程任務每天執行
python auto_update_upgrades.py
```
- 如果沒有新 PDF，腳本會直接跳過
- 如果有新 PDF，自動分析並更新 JSON

## 🎯 工作流程

```
開始
  ↓
掃描 fiadoc/ 資料夾
  ↓
計算每個 PDF 的 MD5 雜湊值
  ↓
與緩存比對 ──→ 沒有變化 ──→ 輸出「數據已是最新」
  ↓
有新增/修改/刪除
  ↓
步驟 1: 分析所有部件變更 (analyze_2025_parts_changes_v2.py)
  ↓
步驟 2: 提取主要部件升級 (extract_major_upgrades_2025.py)
  ↓
步驟 3: 重組為結構化 JSON (reorganize_major_upgrades.py)
  ↓
更新緩存記錄
  ↓
完成！
```

## 📦 依賴的模組

腳本內部使用以下現有模組：
- `analyze_2025_parts_changes_v2.py` - PDF 解析和部件變更提取
- `extract_major_upgrades_2025.py` - 主要部件篩選
- `reorganize_major_upgrades.py` - JSON 結構重組

## ⚙️ 配置選項

可以在腳本中修改以下參數：

```python
analyzer = AutoUpdateUpgradeAnalyzer(
    fiadoc_dir="fiadoc",                    # PDF 來源資料夾
    cache_file=".pdf_cache.json",           # 緩存檔案名稱
    output_complete="2025_f1_parts_changes_complete.json",
    output_major="2025_f1_major_upgrades.json",
    output_organized="2025_f1_major_upgrades_organized.json"
)
```

## 💡 提示

1. **首次執行較慢** - 需要分析所有 27 個 PDF
2. **後續執行快速** - 僅在有變化時才重新分析
3. **建議加入版本控制** - 將 `.pdf_cache.json` 加入 `.gitignore`
4. **Windows 排程任務** - 可設置自動每日執行

## 🔧 故障排除

### 問題: 腳本報告「沒有找到 PDF」
解決: 確認 `fiadoc/` 資料夾存在且包含 Parc Fermé PDF

### 問題: 想要強制重新分析
解決: 使用 `--force` 參數或先清除緩存

### 問題: JSON 文件沒有更新
解決: 檢查是否真的有新的或修改過的 PDF

## 📊 輸出範例

```
====================================================================================================
🤖 自動化 F1 主要部件升級分析器
====================================================================================================
執行時間: 2025-11-06 21:12:17

====================================================================================================
📂 掃描 Parc Fermé 文件
====================================================================================================
資料夾: C:\Users\mike2\OneDrive\Code\F1-data-analyze\fiadoc
找到 PDF: 27 個

🔍 檢測文件變化...

📊 變化統計:
  🆕 新增文件: 0 個
  🔄 修改文件: 0 個
  ⚪ 未變化: 27 個
  🗑️  已刪除: 0 個

⚪ 沒有檢測到文件變化
✅ 數據已是最新，無需更新
```
