# CLI 數據儲存快速參考

## 📁 三層儲存結構

```
f1_analysis_cache/  →  FastF1 原始數據 (10+ GB)
       ↓
cache/              →  分析結果緩存 (~50 MB)
       ↓
json/               →  最終 JSON 輸出 (~5 MB)
```

---

## 🗂️ 目錄說明

| 目錄 | 用途 | 格式 | 大小 | 管理 |
|------|------|------|------|------|
| **f1_analysis_cache/** | FastF1 HTTP 緩存 | `.pkl` + SQLite | ~10 GB | FastF1 自動 |
| **cache/** | 分析結果緩存 | `.pkl` | ~50 MB | CLI 分析器 |
| **json/** | 最終輸出 | `.json` | ~5 MB | function_mapper |

---

## 📄 檔案命名規則

### f1_analysis_cache/
```
f1_data_{year}_{race}_{session}.pkl
範例: f1_data_2023_Japan_R.pkl (95 MB)
```

### cache/
```
{analysis_type}_{year}_{event_name}_{session}.pkl
範例: driver_detailed_pitstops_2023_Japanese_Grand_Prix.pkl (9 KB)
```

### json/
```
{analysis_name}_{year}_{event_name}_{session}.json
範例: driver_detailed_pitstop_records_2023_Japanese_Grand_Prix.json (8 KB)
```

---

## 🔄 數據流程

```
執行 CLI 命令
    ↓
① 檢查 f1_analysis_cache/ → 存在: 載入 (< 1秒)
                           → 不存在: 下載 (30-60秒)
    ↓
② 檢查 cache/ → 存在: 使用緩存 (< 1秒)
              → 不存在: 執行分析 (5-10秒)
    ↓
③ 生成 json/ → 保存最終結果 (立即)
```

---

## 🧹 常用清理命令

### 清理所有緩存
```powershell
Remove-Item -Path "cache\*.pkl" -Force
```

### 清理特定賽事
```powershell
Remove-Item "cache\*2023*Japan*.pkl" -Force
```

### 清理舊賽季 FastF1 數據
```powershell
Remove-Item -Path "f1_analysis_cache\2020" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2021" -Recurse -Force
```

### 使用 VS Code 任務
```
任務: 🧹 清理緩存檔案
```

---

## 📊 當前儲存狀態

**總計**: ~10.5 GB

- f1_analysis_cache/: 10.4 GB (32 場賽事)
- cache/: ~50 MB (分析緩存)
- json/: ~5 MB (最終結果)

---

## ⚡ 快速查看命令

### 查看 JSON 檔案
```powershell
Get-ChildItem "json\*.json" | Select-Object -First 10 Name, Length, LastWriteTime
```

### 查看緩存使用量
```powershell
Get-ChildItem "f1_analysis_cache","cache","json" -Recurse -File | 
    Measure-Object -Property Length -Sum
```

### 找出最大的檔案
```powershell
Get-ChildItem "f1_analysis_cache" -File | 
    Sort-Object Length -Descending | 
    Select-Object -First 5 Name, @{Name="Size(MB)"; Expression={[math]::Round($_.Length / 1MB, 2)}}
```

---

## 🎯 使用建議

### 保留什麼
- ✅ **f1_analysis_cache/**: 當前賽季 (2025)
- ✅ **json/**: 所有分析結果（檔案小）
- ⚠️ **cache/**: 定期清理舊緩存

### 清理什麼
- 🗑️ 2-3 年前的 FastF1 緩存
- 🗑️ 30 天以上的 Pickle 緩存
- ✅ 保留所有 JSON 輸出

### 重新生成
```powershell
# 刪除特定緩存強制重新分析
Remove-Item "cache\driver_detailed_pitstops_2023_Japanese_Grand_Prix.pkl" -Force
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R
```

---

## 📚 詳細文檔

完整說明請參閱: `CLI_DATA_STORAGE_STRUCTURE.md`

---

**快速參考版本**: 1.0  
**最後更新**: 2025-10-07
