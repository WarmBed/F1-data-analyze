# download_all_cache.py 下載位置說明

## 📁 預設下載位置

```
f1_analysis_cache/
```

**完整路徑**: 
```
C:\Users\mike2\OneDrive\Code\F1-data-analyze\f1_analysis_cache\
```

---

## 🎯 與 CLI 使用相同的緩存目錄

`download_all_cache.py` 下載到的位置 **與 CLI 使用的緩存目錄完全相同**！

### 數據共享機制

```
download_all_cache.py 下載
         ↓
   f1_analysis_cache/
         ↓
CLI 分析命令使用 ← 同一個目錄！
```

**好處**:
- ✅ 避免重複下載
- ✅ 節省儲存空間
- ✅ 加速 CLI 執行

---

## 📊 下載的內容

### 目錄結構
```
f1_analysis_cache/
├── 2020/
│   ├── {race1}/
│   │   ├── Race/
│   │   ├── Qualifying/
│   │   └── ...
│   └── {race2}/
├── 2021/
├── 2022/
├── 2023/
├── 2024/
├── 2025/
├── f1_data_2020_{race}_{session}.pkl
├── f1_data_2021_{race}_{session}.pkl
├── ...
└── fastf1_http_cache.sqlite  (HTTP 緩存數據庫)
```

### 檔案類型

1. **年度子目錄** (`2020/`, `2021/`, etc.)
   - FastF1 內部管理的詳細數據
   - 包含每場賽事的所有會話數據

2. **賽事 PKL 檔案** (`f1_data_{year}_{race}_{session}.pkl`)
   - 完整的會話數據物件
   - 大小: 50-150 MB/檔案

3. **SQLite 數據庫** (`fastf1_http_cache.sqlite`)
   - HTTP 響應緩存
   - 大小: ~1.3 GB

---

## 🔧 自訂下載位置

### 使用命令行參數

```powershell
# 下載到自訂目錄
python download_all_cache.py --cache-dir "D:\F1_Data"

# 下載到當前目錄的子資料夾
python download_all_cache.py --cache-dir "my_custom_cache"
```

### 範例：下載到外接硬碟

```powershell
# 下載到 D 槽 (假設有更大空間)
python download_all_cache.py --cache-dir "D:\F1_Analysis_Cache"
```

**注意**: 如果修改下載位置，CLI 也需要相應配置才能使用這些緩存

---

## ✅ 驗證下載位置

### 檢查預設位置
```powershell
# 列出緩存目錄內容
Get-ChildItem "f1_analysis_cache" | Select-Object Name, Length, LastWriteTime

# 查看目錄大小
$size = (Get-ChildItem "f1_analysis_cache" -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Host "總大小: $([math]::Round($size / 1GB, 2)) GB"
```

### 檢查最近下載的檔案
```powershell
Get-ChildItem "f1_analysis_cache" -File | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 10 Name, @{Name="Size(MB)"; Expression={[math]::Round($_.Length / 1MB, 2)}}, LastWriteTime
```

---

## 🚀 使用範例

### 基本使用 (下載到預設位置)
```powershell
# 下載所有年份的所有會話
python download_all_cache.py

# 執行時會顯示:
# ===================================================================
# 🏎️  F1 分析緩存批量下載工具
# ===================================================================
# 📁 緩存目錄: C:\Users\mike2\OneDrive\Code\F1-data-analyze\f1_analysis_cache
# ⏰ 開始時間: 2025-10-07 01:30:00
# ===================================================================
```

### 指定年份和會話類型
```powershell
# 只下載 2024-2025 年的正賽和排位賽
python download_all_cache.py --years 2024 2025 --sessions R Q

# 下載 2023 年，跳過練習賽
python download_all_cache.py --years 2023 --skip-practice
```

### 自訂目錄 + 指定年份
```powershell
# 下載 2025 年所有數據到 D 槽
python download_all_cache.py --cache-dir "D:\F1_Cache_2025" --years 2025
```

---

## 📈 預期下載大小

| 年份範圍 | 會話類型 | 預估大小 |
|---------|---------|---------|
| 單一年份 (2025) | 所有會話 | ~2-3 GB |
| 單一年份 (2025) | 僅正賽 (R) | ~1.5 GB |
| 2020-2025 | 所有會話 | **~15-20 GB** |
| 2020-2025 | 僅正賽 + 排位賽 | ~8-10 GB |

**實際下載時間** (取決於網路速度):
- 單一賽季: 30-60 分鐘
- 全部賽季 (2020-2025): 2-4 小時

---

## 🔄 與 CLI 整合

### 下載後立即使用

```powershell
# 步驟 1: 下載緩存
python download_all_cache.py --years 2023

# 步驟 2: 立即執行 CLI 分析 (使用緩存，非常快速)
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R

# 預期輸出:
# [INFO] FastF1 快取已啟用: C:\...\f1_analysis_cache
# 📦 使用緩存數據  ← 立即使用剛下載的數據！
# ✅ 分析完成！
```

---

## ⚠️ 重要注意事項

### 儲存空間需求
- 確保有足夠的磁碟空間 (建議至少 30 GB 可用空間)
- 下載所有年份前檢查可用空間

### 網路穩定性
- 下載過程中保持網路連接
- 如果中斷，重新執行會自動跳過已下載的會話

### 權限問題
- 確保對目標目錄有寫入權限
- OneDrive 同步可能減慢下載速度

---

## 🗑️ 清理下載的緩存

### 清理所有緩存
```powershell
Remove-Item -Path "f1_analysis_cache" -Recurse -Force
```

### 清理特定年份
```powershell
Remove-Item -Path "f1_analysis_cache\2020" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\f1_data_2020_*.pkl" -Force
```

### 僅保留最近兩個賽季
```powershell
# 刪除 2020-2023 年的數據
Remove-Item -Path "f1_analysis_cache\2020" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2021" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2022" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2023" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\f1_data_202[0-3]_*.pkl" -Force
```

---

## 📚 相關文檔

- **儲存架構**: `CLI_DATA_STORAGE_STRUCTURE.md` - 完整的數據儲存說明
- **快速參考**: `CLI_DATA_STORAGE_QUICKREF.md` - 儲存位置速查
- **下載工具**: `download_all_cache.py` - 本工具的源碼

---

## 🎯 總結

**問題**: `download_all_cache.py` 下載到哪邊？

**答案**: 
- **預設位置**: `f1_analysis_cache/` (專案根目錄)
- **完整路徑**: `C:\Users\mike2\OneDrive\Code\F1-data-analyze\f1_analysis_cache\`
- **與 CLI 共享**: ✅ 是的，CLI 使用同一個緩存目錄
- **可自訂**: 使用 `--cache-dir` 參數指定其他位置

---

**文檔版本**: 1.0  
**最後更新**: 2025-10-07  
**工具版本**: download_all_cache.py v1.0
