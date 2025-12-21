# CLI 數據儲存架構完整說明

**文檔版本**: 1.0  
**最後更新**: 2025-10-07  
**適用範圍**: F1T CLI 模組 (f1_analysis_modular_main.py)

---

## 📋 概述

CLI 讀取 FastF1 後採用 **三層儲存架構**，每層有不同的用途和格式：

```
FastF1 API 數據
      ↓
┌─────────────────────────────────────────┐
│ 1️⃣ FastF1 HTTP 緩存 (原始 F1 數據)      │
│    📁 f1_analysis_cache/                │
│    📄 格式: .pkl + SQLite               │
│    💾 大小: ~10 GB (持續增長)            │
└─────────────────────────────────────────┘
      ↓ (CLI 處理)
┌─────────────────────────────────────────┐
│ 2️⃣ Pickle 緩存 (處理後的分析數據)       │
│    📁 cache/                            │
│    📄 格式: .pkl (Python Pickle)        │
│    💾 大小: ~幾 KB 到幾 MB              │
└─────────────────────────────────────────┘
      ↓ (格式化輸出)
┌─────────────────────────────────────────┐
│ 3️⃣ JSON 輸出 (最終分析結果)             │
│    📁 json/                             │
│    📄 格式: .json (標準 JSON)           │
│    💾 大小: ~幾 KB 到幾百 KB            │
└─────────────────────────────────────────┘
      ↓
GUI / API / 用戶使用
```

---

## 1️⃣ FastF1 HTTP 緩存層

### 📁 目錄位置
```
f1_analysis_cache/
```

### 🎯 用途
- **FastF1 庫的 HTTP 緩存**：儲存從 F1 官方 API 下載的原始數據
- **避免重複下載**：同一場賽事的數據只需下載一次
- **離線分析**：有緩存後可在無網路環境下進行分析

### 📄 檔案格式

#### A. 年度子目錄
```
f1_analysis_cache/
├── 2019/
├── 2020/
├── 2021/
├── 2022/
├── 2023/
├── 2024/
└── 2025/
```

**內容**: 每個年度目錄包含該年所有賽事的詳細遙測數據（由 FastF1 管理）

#### B. 賽事 Pickle 檔案
```
f1_data_{year}_{race}_{session}.pkl
```

**範例**:
```
f1_data_2023_Japan_R.pkl              95 MB    (2023 日本站正賽)
f1_data_2024_Bahrain_R.pkl            94 MB    (2024 巴林站正賽)
f1_data_2025_Monaco_R.pkl             94 MB    (2025 摩納哥站正賽)
```

**內容結構** (Python Pickle 序列化的 FastF1 Session 物件):
```python
{
    'session': fastf1.core.Session,  # 會話物件
    'laps': pandas.DataFrame,         # 圈速數據
    'telemetry': pandas.DataFrame,    # 遙測數據 (速度、油門、煞車等)
    'car_data': pandas.DataFrame,     # 車輛數據
    'pos_data': pandas.DataFrame,     # 位置數據
    'weather_data': pandas.DataFrame, # 天氣數據
    'race_control': pandas.DataFrame  # 賽會控制訊息
}
```

#### C. SQLite 數據庫
```
fastf1_http_cache.sqlite              ~1.3 GB
```

**用途**: FastF1 庫的 HTTP 響應緩存
**內容**: 
- API 端點響應
- 時間戳和版本控制
- 確保數據一致性

### 📊 儲存統計 (當前實際數據)

| 類型 | 數量 | 總大小 |
|------|------|--------|
| **年度目錄** | 7 個 (2019-2025) | - |
| **賽事 PKL 檔案** | 32 個 | ~9 GB |
| **SQLite 數據庫** | 1 個 | ~1.3 GB |
| **總計** | - | **~10.4 GB** |

### 🔧 管理機制

**自動建立** (來自 `CLI_modules/cli/core/base.py`):
```python
def _enable_fastf1_cache(cache_dir_name: str = "cache") -> None:
    cache_path = _resolve_cache_directory(cache_dir_name)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path.resolve()))
    print(f"[INFO] FastF1 快取已啟用: {cache_path.resolve()}")
```

**環境變數覆蓋**:
```powershell
# 自訂 FastF1 緩存位置
$env:F1T_FASTF1_CACHE_DIR = "D:\F1_Cache"
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R

# 停用 FastF1 緩存
$env:F1T_DISABLE_FASTF1_CACHE = "1"
```

**打包模式特殊處理**:
- **Windows**: `%LOCALAPPDATA%\F1TelemetryStationPro\fastf1_cache`
- **其他平台**: `~/.f1t/fastf1_cache`

---

## 2️⃣ Pickle 緩存層 (分析結果緩存)

### 📁 目錄位置
```
cache/
```

### 🎯 用途
- **儲存處理後的分析結果**：避免重複計算
- **加速 CLI 執行**：第二次執行同樣的分析只需 1-2 秒
- **GUI 快速載入**：GUI 可直接讀取這些緩存

### 📄 檔案格式

#### 命名規則
```
{analysis_type}_{year}_{event_name}_{session}.pkl
```

#### 實際範例
```
cache/
├── accident_statistics_2025_Japanese_Grand_Prix_Race.pkl     344 B
├── all_incidents_summary_2022_Japanese_Grand_Prix_Race.pkl   9.9 KB
├── all_incidents_summary_2023_Japanese_Grand_Prix_Race.pkl   17 KB
├── driver_detailed_pitstops_2023_Japanese_Grand_Prix.pkl     (功能 5)
├── track_position_analysis_2024_Monaco_Race.pkl              (功能 2)
└── rain_intensity_analysis_2025_Belgium_Race.pkl             (功能 1)
```

### 📦 Pickle 內容結構

**範例：功能 5 (車手進站詳細記錄)**
```python
{
    "VER": [
        {
            "pitstop_number": 1,
            "lap_number": 12,
            "pit_duration": 2.3,
            "session_time": "Unknown",
            "team": "Red Bull Racing"
        },
        {
            "pitstop_number": 2,
            "lap_number": 32,
            "pit_duration": 2.5,
            "session_time": "Unknown",
            "team": "Red Bull Racing"
        }
    ],
    "LEC": [
        # ...
    ]
    # ... 其他車手
}
```

### 🔄 緩存使用流程

```python
# CLI 分析器中的標準模式 (來自功能 5)
def run_driver_detailed_pitstop_records(data_loader, show_detailed_output=True):
    # 1. 生成緩存鍵
    cache_key = f"driver_detailed_pitstops_{year}_{event_name}"
    
    # 2. 檢查緩存
    cached_data = check_cache(cache_key)
    
    if cached_data:
        print("📦 使用緩存數據")
        return {
            "success": True,
            "data": cached_data,
            "cache_used": True,
            "cache_key": cache_key
        }
    
    # 3. 無緩存則執行分析
    print("🔄 重新計算 - 開始數據分析...")
    detailed_records = analyze_driver_detailed_pitstops(data_loader, session_info)
    
    # 4. 保存緩存
    save_cache(detailed_records, cache_key)
    
    return {
        "success": True,
        "data": detailed_records,
        "cache_used": False
    }
```

### 🧹 緩存清理

**手動清理**:
```powershell
# 清理所有 Pickle 緩存
Remove-Item -Path "cache\*.pkl" -Force

# 清理特定賽事緩存
Remove-Item -Path "cache\*2023_Japan*.pkl" -Force
```

**使用 VS Code 任務**:
```
🧹 清理緩存檔案
```

**緩存大小管理**:
- 單個檔案通常 < 1 MB
- 總大小取決於分析過的賽事數量
- 建議定期清理舊賽季的緩存

---

## 3️⃣ JSON 輸出層 (最終結果)

### 📁 目錄位置
```
json/
```

### 🎯 用途
- **用戶可讀的分析結果**：標準 JSON 格式
- **GUI 數據源**：GUI 模組讀取這些 JSON 檔案
- **API 響應**：API 服務器返回這些數據
- **數據交換**：可輕鬆導入其他工具或語言

### 📄 檔案格式

#### 命名規則
```
{analysis_name}_{year}_{event_name}_{session}.json
```

#### 實際範例
```
json/
├── driver_detailed_pitstop_records_2023_Japanese_Grand_Prix.json     8 KB
├── all_drivers_telemetry_analysis_2025_Australia_R.json             37 KB
├── all_drivers_telemetry_analysis_2025_China_R.json                 39 KB
├── all_incidents_summary_2022_Japanese_Grand_Prix_RACE.json         61 KB
└── season_calendar_2020-2025_20251007_012807.json                  156 KB
```

### 📋 JSON 結構

**標準化格式** (所有功能統一):
```json
{
  "function_id": 5,
  "function_name": "Driver Detailed Pitstop Records",
  "analysis_type": "driver_detailed_pitstop_records",
  "session_info": {
    "event_name": "Japanese Grand Prix",
    "circuit_name": "Suzuka",
    "session_type": "Race",
    "year": 2023
  },
  "timestamp": "2025-10-07T01:47:07.886826",
  "data": {
    // 實際分析數據 (格式因功能而異)
  }
}
```

### 🔧 生成機制

**來自 `function_mapper.py`**:
```python
def _export_to_json(self, result: Dict[str, Any], function_id: Union[str, int], 
                    analysis_name: str) -> bool:
    """統一的 JSON 導出工具函數"""
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    # 獲取賽事資訊
    year = getattr(self.data_loader, 'year', 'Unknown')
    race_name = getattr(self.data_loader, 'race_name', 'Unknown')
    session_type = getattr(self.data_loader, 'session_type', 'Unknown')
    
    json_filename = f"{analysis_name}_{year}_{race_name}_{session_type}.json"
    json_path = os.path.join(json_dir, json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 JSON 分析報告已保存: {json_path}")
    return True
```

### 📊 JSON 特性

| 特性 | 說明 |
|------|------|
| **編碼** | UTF-8 (支援中文) |
| **縮排** | 2 空格 (易讀) |
| **ASCII** | `ensure_ascii=False` (保留中文字符) |
| **日期處理** | `default=str` (自動轉換 datetime) |
| **大小** | 通常 < 100 KB，最大 ~1 MB |

---

## 🔄 完整數據流程範例

### 執行命令
```powershell
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R
```

### 數據處理流程

#### 階段 1: FastF1 數據載入
```
[INFO] FastF1 快取已啟用: C:\...\f1_analysis_cache
[INFO] 正在載入 2023 年 Japan 站 Race 會話...
```

**檢查**: `f1_analysis_cache/f1_data_2023_Japan_R.pkl`
- **存在** → 從緩存載入 (< 1 秒)
- **不存在** → 從 F1 API 下載 (30-60 秒) + 保存到緩存

#### 階段 2: 分析執行與 Pickle 緩存
```
🚀 開始執行車手進站詳細記錄分析...
```

**檢查**: `cache/driver_detailed_pitstops_2023_Japanese_Grand_Prix.pkl`
- **存在** → 使用緩存 (< 1 秒)
  ```
  📦 使用緩存數據
  ✅ 車手進站詳細記錄分析完成！
  ```
- **不存在** → 執行完整分析 (5-10 秒) + 保存緩存
  ```
  🔄 重新計算 - 開始數據分析...
  ✅ 車手進站詳細記錄分析完成！
  ```

#### 階段 3: JSON 輸出
```
📄 JSON 分析報告已保存: json/driver_detailed_pitstop_records_2023_Japanese_Grand_Prix.json
```

**生成**: `json/driver_detailed_pitstop_records_2023_Japanese_Grand_Prix.json`
```json
{
  "function_id": 5,
  "data": {
    "VER": [...],
    "LEC": [...],
    // ...
  }
}
```

---

## 📈 儲存空間需求

### 當前實際使用量

| 目錄 | 檔案數量 | 總大小 | 增長速度 |
|------|---------|--------|---------|
| **f1_analysis_cache/** | 32 PKL + 1 SQLite | **10.4 GB** | 高 (~500 MB/賽事) |
| **cache/** | ~50+ PKL | **~50 MB** | 中 (~1 MB/分析) |
| **json/** | ~100+ JSON | **~5 MB** | 低 (~50 KB/分析) |
| **總計** | - | **~10.5 GB** | - |

### 空間優化建議

**1. 清理舊賽季數據** (釋放 ~2 GB/年):
```powershell
# 清理 2020-2022 年的 FastF1 緩存
Remove-Item -Path "f1_analysis_cache\2020" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2021" -Recurse -Force
Remove-Item -Path "f1_analysis_cache\2022" -Recurse -Force
```

**2. 僅保留當前賽季** (僅需 ~2 GB):
```powershell
# 僅保留 2025 賽季
Get-ChildItem "f1_analysis_cache" -Directory | 
    Where-Object { $_.Name -ne "2025" } | 
    Remove-Item -Recurse -Force
```

**3. 定期清理 Pickle 緩存**:
```powershell
# 清理 30 天前的緩存
Get-ChildItem "cache\*.pkl" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
    Remove-Item -Force
```

---

## 🔍 檔案格式詳細比較

| 特性 | FastF1 PKL | Pickle 緩存 | JSON 輸出 |
|------|-----------|------------|-----------|
| **格式** | Python Pickle | Python Pickle | JSON |
| **可讀性** | ❌ 二進制 | ❌ 二進制 | ✅ 文字格式 |
| **跨語言** | ❌ 僅 Python | ❌ 僅 Python | ✅ 通用 |
| **檔案大小** | 🔴 大 (50-150 MB) | 🟡 中 (1-100 KB) | 🟢 小 (1-100 KB) |
| **載入速度** | 🟢 快 (< 1 秒) | 🟢 快 (< 0.1 秒) | 🟡 中 (< 0.5 秒) |
| **用途** | FastF1 原始數據 | 分析結果緩存 | 用戶/GUI 使用 |
| **管理** | FastF1 自動 | CLI 分析器 | CLI function_mapper |

---

## 🛠️ 常用管理命令

### 查看儲存狀態
```powershell
# 查看所有目錄大小
Get-ChildItem -Path "f1_analysis_cache","cache","json" -Recurse -File | 
    Measure-Object -Property Length -Sum | 
    Select-Object @{Name="TotalSize(GB)"; Expression={[math]::Round($_.Sum / 1GB, 2)}}

# 查看最近生成的 JSON
Get-ChildItem "json\*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 10 Name, @{Name="Size(KB)"; Expression={[math]::Round($_.Length / 1KB, 2)}}, LastWriteTime
```

### 清理特定賽事
```powershell
# 清理 2023 日本站的所有數據
Remove-Item "f1_analysis_cache\f1_data_2023_Japan_*.pkl" -Force
Remove-Item "cache\*2023*Japan*.pkl" -Force
Remove-Item "json\*2023*Japan*.json" -Force
```

### 重新生成數據
```powershell
# 強制重新分析（忽略緩存）
Remove-Item "cache\driver_detailed_pitstops_2023_Japanese_Grand_Prix.pkl" -Force
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R
```

---

## 📚 相關文檔

- **功能映射器**: `CLI_modules/cli/core/function_mapper.py` - JSON 輸出邏輯
- **緩存管理**: `CLI_modules/cli/core/base.py` - FastF1 緩存配置
- **分析器範例**: `CLI_modules/cli/analyzer/driver_detailed_pitstop_records.py` - Pickle 緩存實現
- **功能 5 格式**: `FUNCTION_5_JSON_FORMAT.md` - 詳細 JSON 結構說明

---

## ⚠️ 重要注意事項

### 數據完整性
- ✅ **FastF1 緩存**: 由 FastF1 庫管理，高度可靠
- ⚠️ **Pickle 緩存**: 可能因代碼更新而失效（建議定期清理）
- ✅ **JSON 輸出**: 與程式版本無關，長期穩定

### 跨平台兼容性
- ❌ **Pickle 檔案**: 不可跨 Python 版本使用
- ✅ **JSON 檔案**: 完全跨平台、跨語言

### 版本升級
當升級 CLI 版本時，建議：
1. 保留 `f1_analysis_cache/` (原始數據)
2. 清理 `cache/` (Pickle 緩存可能不兼容)
3. 保留 `json/` (最終結果仍可用)

---

**最後更新**: 2025-10-07  
**系統版本**: F1T CLI v1.0  
**緩存總量**: ~10.5 GB (32 場賽事)
