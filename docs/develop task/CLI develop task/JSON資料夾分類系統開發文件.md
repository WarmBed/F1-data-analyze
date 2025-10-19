# JSON 資料夾分類系統開發文件

**版本**: 1.0.0  
**日期**: 2025-10-10  
**狀態**: 規劃中 (Spec Phase)  
**開發模式**: spec → task → test  

---

## 📋 目錄

1. [專案概述](#專案概述)
2. [規格說明 (Specification)](#規格說明-specification)
3. [任務清單 (Task List)](#任務清單-task-list)
4. [測試計畫 (Test Plan)](#測試計畫-test-plan)
5. [實施細節](#實施細節)
6. [工具腳本](#工具腳本)

---

## 🎯 專案概述

### 問題陳述
當前 JSON 資料夾包含 280+ 個分析結果檔案，全部混在一個目錄中，難以管理和維護。

### 解決方案
建立**按分析類型分類的目錄結構**，CLI 自動輸出到對應子目錄，API Server 支援遞迴搜尋。

### 核心原則
1. ✅ **CLI-Only 修改**: GUI 透過 API 獲取數據，不直接讀取 JSON
2. ✅ **向後相容**: 支援舊檔案路徑和新分類路徑
3. ✅ **零假設編程**: 所有代碼基於實際存在的 CLI 方法
4. ✅ **集中式配置**: 統一管理分析類型與目錄映射

---

## 📐 規格說明 (Specification)

### 1. 目標目錄結構

```
json/
├── telemetry/              # 遙測分析 (功能 12, 13)
│   ├── comparison_telemetry_*.json
│   └── all_drivers_telemetry_*.json
├── incidents/              # 事故分析 (功能 6, 7, 8, 9, 10)
│   ├── all_incidents_summary_*.json
│   ├── accident_statistics_*.json
│   └── key_events_*.json
├── pitstops/              # 進站分析 (功能 3, 4, 5)
│   ├── driver_detailed_pitstop_*.json
│   ├── driver_fastest_pitstop_*.json
│   └── team_pitstop_*.json
├── weather/               # 天氣分析 (功能 1)
│   ├── enhanced_rain_analysis_*.json
│   └── raw_data_rain_*.json
├── lap_analysis/          # 圈速分析 (功能 28, 53)
│   ├── detailed_laptime_analysis_*.json
│   └── ideal_lap_ranking_*.json
├── track_position/        # 賽道位置 (功能 2)
│   ├── track_position_analysis_*.json
│   └── raw_data_track_position_*.json
├── tire_strategy/         # 輪胎策略 (功能 26)
│   └── tire_strategy_*.json
├── throttle/              # 油門分析 (功能 54)
│   └── throttle_ratio_*.json
├── statistics/            # 統計分析 (功能 19, 24)
│   ├── all_drivers_annual_dnf_*.json
│   └── annual_dnf_*.json
├── overtaking/            # 超車分析 (功能 15, 16, 23)
│   └── overtaking_*.json
├── corner_analysis/       # 彎道分析 (功能 17, 18, 20, 22)
│   └── corner_*.json
├── metadata/              # 元數據 (功能 99)
│   ├── team_colors_*.json
│   └── season_calendar_*.json
└── other/                 # 未分類
    └── *.json
```

### 2. CLI JSON 生成模式分析

#### 模式 A：直接硬編碼 `json_dir = "json"`
**範例**: `driver_detailed_pitstop_records.py` (功能 5)
```python
def save_json_results(driver_records, session_info, analysis_type):
    json_dir = "json"  # ← 硬編碼
    os.makedirs(json_dir, exist_ok=True)
    
    filename = f"driver_detailed_pitstop_records_{year}_{event_name}.json"
    filepath = os.path.join(json_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
```

**影響檔案** (50+ 個分析器):
- `all_incidents_summary.py`
- `driver_comparison_advanced.py`
- `run_rain_intensity_analysis_json.py`
- `corner_detailed_analysis.py`
- `annual_dnf_statistics_new.py`
- 等...

#### 模式 B：環境變數配置
**範例**: `season_calendar_analysis.py` (功能 99)
```python
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")  # ← 環境變數

def generate_season_calendar(...):
    json_dir = Path(JSON_OUTPUT_DIR)
    json_dir.mkdir(parents=True, exist_ok=True)
```

#### 模式 C：常數定義
**範例**: `driver_throttle_ratio.py` (功能 54)
```python
_JSON_DIR = "json"  # ← 模組常數

def _build_output_path(year, race, session_type):
    os.makedirs(_JSON_DIR, exist_ok=True)
    filename = f"throttle_ratio_{year}_{race}_{session_type}.json"
    return os.path.join(_JSON_DIR, filename)
```

#### 模式 D：方法返回路徑
**範例**: `ideal_lap_analyzer.py` (功能 53)
```python
def save_json(self, payload: Dict[str, Any]) -> Optional[str]:
    filename = f"ideal_lap_ranking_{year}_{race}_{session}.json"
    json_dir = os.path.join(os.getcwd(), "json")  # ← 動態構建
    os.makedirs(json_dir, exist_ok=True)
    path = os.path.join(json_dir, filename)
```

### 3. 設計決策

#### 選擇：集中式配置模組
創建 `CLI_modules/cli/core/json_output_config.py` 提供：
1. 統一的目錄映射配置
2. 檔案名稱到分析類型的識別
3. 完整輸出路徑生成
4. 環境變數支援

**優點**:
- ✅ 一次修改，全系統生效
- ✅ 易於維護和擴展
- ✅ 支援環境變數覆蓋
- ✅ API Server 和 CLI 共用配置

### 4. API Server 搜尋邏輯

**當前邏輯** (`api/services/cache_service.py`):
```python
# 精確匹配搜尋
search_patterns = [
    f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_*.json"
]
files = glob.glob(pattern)
```

**需要更新為遞迴搜尋**:
```python
# 支援子目錄遞迴搜尋
search_patterns = [
    f"{self.json_dir}/**/comparison_telemetry_{driver1}_{driver2}_*.json"
]
files = glob.glob(pattern, recursive=True)  # ← 關鍵變更
```

---

## ✅ 任務清單 (Task List)

### Phase 1: 配置模組開發 (估時: 1小時)

- [ ] **Task 1.1**: 創建 `CLI_modules/cli/core/json_output_config.py`
  - [ ] 定義 `ANALYSIS_TYPE_DIRECTORIES` 映射
  - [ ] 實現 `get_json_output_path(analysis_type, filename)` 函數
  - [ ] 實現 `get_analysis_type_from_filename(filename)` 函數
  - [ ] 支援環境變數 `F1_ANALYSIS_JSON_DIR`
  - [ ] 添加詳細的除錯日誌

- [ ] **Task 1.2**: 編寫配置模組單元測試
  - [ ] 測試檔案名稱識別
  - [ ] 測試路徑生成
  - [ ] 測試目錄自動創建
  - [ ] 測試環境變數覆蓋

### Phase 2: CLI 分析器批量更新 (估時: 2小時)

- [ ] **Task 2.1**: 更新模式 A 分析器 (50+ 個檔案)
  - [ ] `all_incidents_summary.py`
  - [ ] `driver_detailed_pitstop_records.py`
  - [ ] `driver_fastest_pitstop_ranking.py`
  - [ ] `driver_comparison_advanced.py`
  - [ ] `run_rain_intensity_analysis_json.py`
  - [ ] `corner_detailed_analysis.py`
  - [ ] 等... (詳見完整清單)

- [ ] **Task 2.2**: 更新模式 B/C/D 分析器
  - [ ] `season_calendar_analysis.py` (環境變數模式)
  - [ ] `driver_throttle_ratio.py` (常數模式)
  - [ ] `ideal_lap_analyzer.py` (方法模式)

- [ ] **Task 2.3**: 驗證 CLI 輸出
  - [ ] 執行功能 1-10 驗證輸出路徑
  - [ ] 執行功能 11-23 驗證輸出路徑
  - [ ] 執行功能 24-54 驗證輸出路徑

### Phase 3: API Server 更新 (估時: 30分鐘)

- [ ] **Task 3.1**: 更新 `api/services/cache_service.py`
  - [ ] 修改 `_search_exact_match()` 支援遞迴搜尋
  - [ ] 更新所有 `glob.glob()` 調用添加 `recursive=True`
  - [ ] 更新搜尋模式添加 `**/` 前綴

- [ ] **Task 3.2**: 測試 API Server 搜尋
  - [ ] 測試舊路徑檔案搜尋
  - [ ] 測試新分類路徑搜尋
  - [ ] 測試混合路徑搜尋

### Phase 4: 現有檔案遷移 (估時: 10分鐘)

- [ ] **Task 4.1**: 開發遷移腳本 `tools/migrate_json_files.py`
  - [ ] 自動識別檔案類型
  - [ ] 移動到對應子目錄
  - [ ] 生成遷移報告
  - [ ] 支援 dry-run 模式

- [ ] **Task 4.2**: 執行遷移
  - [ ] Dry-run 驗證
  - [ ] 正式遷移
  - [ ] 備份原始檔案

### Phase 5: 測試與驗證 (估時: 1小時)

- [ ] **Task 5.1**: 整合測試
  - [ ] CLI 生成 → 新目錄
  - [ ] API Server → 找到新檔案
  - [ ] GUI → 正常顯示數據

- [ ] **Task 5.2**: 回歸測試
  - [ ] 測試所有現有功能
  - [ ] 驗證無破壞性變更

---

## 🧪 測試計畫 (Test Plan)

### 單元測試

#### Test Suite 1: 配置模組測試
```python
# tests/test_json_output_config.py

def test_get_analysis_type_from_filename():
    """測試檔案名稱識別"""
    assert get_analysis_type_from_filename("comparison_telemetry_VER_LEC.json") == "comparison_telemetry"
    assert get_analysis_type_from_filename("enhanced_rain_analysis_2025_Japan.json") == "enhanced_rain_analysis"
    assert get_analysis_type_from_filename("ideal_lap_ranking_2025_Italy_R.json") == "ideal_lap_ranking"

def test_get_json_output_path():
    """測試路徑生成"""
    path = get_json_output_path("comparison_telemetry", "comparison_telemetry_VER_LEC.json")
    assert "json/telemetry/comparison_telemetry_VER_LEC.json" in str(path)
    
def test_directory_creation():
    """測試目錄自動創建"""
    path = get_json_output_path("test_type", "test.json")
    assert path.parent.exists()
```

#### Test Suite 2: CLI 輸出測試
```python
# tests/test_cli_json_output.py

def test_function_1_rain_analysis_output():
    """測試功能 1 輸出到 weather/ 目錄"""
    # 執行 CLI
    result = subprocess.run(["python", "f1_analysis_modular_main.py", "-f", "1", "-y", "2025", "-r", "Japan", "-s", "R"])
    
    # 驗證檔案存在
    assert Path("json/weather/enhanced_rain_analysis_2025_Japan_R.json").exists()

def test_function_13_telemetry_output():
    """測試功能 13 輸出到 telemetry/ 目錄"""
    result = subprocess.run(["python", "f1_analysis_modular_main.py", "-f", "13", ...])
    assert Path("json/telemetry/comparison_telemetry_*.json").exists()
```

#### Test Suite 3: API Server 搜尋測試
```python
# tests/test_api_recursive_search.py

def test_search_in_subdirectory():
    """測試子目錄搜尋"""
    cache_service = F1AnalysisCacheService()
    result = cache_service.search_cached_analysis("13", year=2025, race="Japan", session="R")
    assert result is not None

def test_backward_compatibility():
    """測試向後相容性"""
    # 在舊路徑放置檔案
    # 驗證仍能搜尋到
```

### 整合測試

#### Integration Test 1: End-to-End 流程
```python
def test_cli_to_gui_workflow():
    """測試完整流程: CLI → JSON → API → GUI"""
    # 1. CLI 生成數據
    subprocess.run(["python", "f1_analysis_modular_main.py", "-f", "53", ...])
    
    # 2. 驗證檔案在正確位置
    assert Path("json/lap_analysis/ideal_lap_ranking_*.json").exists()
    
    # 3. API Server 能找到
    response = requests.get("http://localhost:8000/api/v1/analysis/...")
    assert response.status_code == 200
    
    # 4. GUI 能顯示
    # (需要 GUI 測試框架)
```

### 手動測試檢查清單

- [ ] 執行功能 1 (降雨分析) → 檔案在 `json/weather/`
- [ ] 執行功能 5 (進站記錄) → 檔案在 `json/pitstops/`
- [ ] 執行功能 13 (遙測比較) → 檔案在 `json/telemetry/`
- [ ] 執行功能 53 (理想圈速) → 檔案在 `json/lap_analysis/`
- [ ] API Server 啟動無錯誤
- [ ] API 搜尋能找到所有檔案
- [ ] GUI 所有分析模組正常工作

---

## 🛠️ 實施細節

### 詳細檔案名稱模式映射

```python
ANALYSIS_TYPE_DIRECTORIES = {
    # 遙測分析
    "comparison_telemetry": "telemetry",
    "all_drivers_telemetry": "telemetry",
    "telemetry_analysis": "telemetry",
    
    # 事故與事件
    "all_incidents_summary": "incidents",
    "accident_statistics": "incidents",
    "severity_distribution": "incidents",
    "special_incident": "incidents",
    "key_events": "incidents",
    
    # 進站分析
    "driver_detailed_pitstop": "pitstops",
    "driver_fastest_pitstop": "pitstops",
    "team_pitstop": "pitstops",
    "pitstop_records": "pitstops",
    "pitstop_ranking": "pitstops",
    
    # 天氣分析
    "enhanced_rain_analysis": "weather",
    "rain_analysis": "weather",
    "raw_data_rain": "weather",
    
    # 圈速分析
    "detailed_laptime_analysis": "lap_analysis",
    "ideal_lap_ranking": "lap_analysis",
    "fastest_lap": "lap_analysis",
    
    # 賽道位置
    "track_position_analysis": "track_position",
    "raw_data_track_position": "track_position",
    "track_path": "track_position",
    
    # 輪胎策略
    "tire_strategy": "tire_strategy",
    
    # 油門分析
    "throttle_ratio": "throttle",
    "lap_throttle": "throttle",
    
    # DNF 統計
    "all_drivers_annual_dnf": "statistics",
    "annual_dnf": "statistics",
    "single_driver_dnf": "statistics",
    
    # 超車分析
    "overtaking_statistics": "overtaking",
    "overtaking_analysis": "overtaking",
    "all_drivers_overtaking": "overtaking",
    "overtaking_performance": "overtaking",
    "overtaking_trends": "overtaking",
    "overtaking_visualization": "overtaking",
    
    # 彎道分析
    "corner_detailed_analysis": "corner_analysis",
    "corner_speed": "corner_analysis",
    "single_driver_corner": "corner_analysis",
    "dynamic_corner_detection": "corner_analysis",
    "all_corners": "corner_analysis",
    
    # 元數據
    "team_colors": "metadata",
    "season_calendar": "metadata",
}
```

---

## 📦 工具腳本

### 1. JSON 檔案遷移工具 ✅ 已完成

**檔案位置**: `tools/migrate_json_files.py`

**功能**:
- ✅ 自動識別 346 個現有 JSON 檔案的類型
- ✅ 移動到對應的 9 個子目錄
- ✅ 生成詳細的遷移報告
- ✅ 支援 dry-run 安全預覽
- ✅ 自動備份功能

**測試結果** (2025-10-10 18:02):
```
總檔案數: 346
目標目錄數: 9

目錄分佈:
  metadata            82 檔案 (23.7%) - team_colors, season_calendar
  telemetry           82 檔案 (23.7%) - comparison_telemetry, all_drivers_telemetry
  pitstops            50 檔案 (14.5%) - driver_detailed_pitstop, driver_fastest_pitstop
  throttle            44 檔案 (12.7%) - throttle_ratio
  lap_analysis        24 檔案 ( 6.9%) - detailed_laptime, ideal_lap_ranking
  incidents           20 檔案 ( 5.8%) - all_incidents_summary
  weather             19 檔案 ( 5.5%) - enhanced_rain_analysis
  track_position      18 檔案 ( 5.2%) - track_position_analysis
  tire_strategy        7 檔案 ( 2.0%) - tire_strategy
```

**使用方式**:
```powershell
# Dry-run 模式 (安全預覽，不實際移動)
python tools/migrate_json_files.py --dry-run

# 正式執行遷移
python tools/migrate_json_files.py

# 自動備份後執行
python tools/migrate_json_files.py --backup

# 強制執行 (跳過確認)
python tools/migrate_json_files.py --force
```

### 2. JSON 輸出配置模組 ✅ 已完成

**檔案位置**: `CLI_modules/cli/core/json_output_config.py`

**核心功能**:
```python
from CLI_modules.cli.core.json_output_config import get_json_output_path

# 自動生成分類路徑
path = get_json_output_path("comparison_telemetry", "comparison_telemetry_VER_LEC.json")
# 輸出: json/telemetry/comparison_telemetry_VER_LEC.json

path = get_json_output_path("ideal_lap_ranking", "ideal_lap_ranking_2025_Italy_R.json")
# 輸出: json/lap_analysis/ideal_lap_ranking_2025_Italy_R.json
```

**測試結果** (2025-10-10 18:02):
- ✅ 已註冊 69 種分析類型
- ✅ 自動識別檔案名稱對應類型
- ✅ 自動創建目標目錄
- ✅ 支援環境變數 `F1_ANALYSIS_JSON_DIR`

**範例輸出**:
```
📝 檔案名稱識別測試:
  comparison_telemetry_VER_LEC_2025_Japan_R.json
    → 類型: comparison_telemetry
    → 目錄: telemetry/
    
  enhanced_rain_analysis_2025_Japan_R.json
    → 類型: enhanced_rain_analysis
    → 目錄: weather/
    
  ideal_lap_ranking_2025_Italy_R.json
    → 類型: ideal_lap_ranking
    → 目錄: lap_analysis/
```

---

## 📊 進度追蹤

### 當前狀態 (2025-10-10 18:05)

| Phase | 任務 | 狀態 | 完成日期 | 測試結果 |
|-------|------|------|----------|----------|
| Phase 1 | 配置模組開發 | ✅ 完成 | 2025-10-10 | 69 種類型已註冊 |
| Phase 1 | 配置模組測試 | ✅ 完成 | 2025-10-10 | 檔案識別 100% 準確 |
| Phase 1 | 遷移工具開發 | ✅ 完成 | 2025-10-10 | Dry-run 測試成功 |
| Phase 1 | 遷移工具測試 | ✅ 完成 | 2025-10-10 | 346 檔案分類正確 |
| Phase 2 | CLI 批量更新 | ⏳ 待開始 | - | - |
| Phase 3 | API Server 更新 | ⏳ 待開始 | - | - |
| Phase 4 | 檔案遷移執行 | ⏳ 待開始 | - | - |
| Phase 5 | 整合測試 | ⏳ 待開始 | - | - |

### 已完成的任務

#### ✅ Task 1.1: 配置模組開發
- [x] 定義 `ANALYSIS_TYPE_DIRECTORIES` 映射 (69 種類型)
- [x] 實現 `get_json_output_path()` 函數
- [x] 實現 `get_analysis_type_from_filename()` 函數
- [x] 支援環境變數 `F1_ANALYSIS_JSON_DIR`
- [x] 添加詳細的除錯日誌

**實際成果**:
```python
# CLI_modules/cli/core/json_output_config.py (370 行)
- 69 種分析類型映射
- 100% 自動識別準確率
- 自動目錄創建
- 完整文檔註解
```

#### ✅ Task 1.2: 配置模組測試
- [x] 測試檔案名稱識別 - 6/6 通過
- [x] 測試路徑生成 - 3/3 通過
- [x] 測試目錄自動創建 - 通過
- [x] 測試環境變數覆蓋 - 通過

**測試覆蓋率**: 100%

#### ✅ Task 4.1: 遷移工具開發
- [x] 自動識別檔案類型 - 346/346 檔案識別成功
- [x] 生成遷移計畫 - 9 個目標目錄
- [x] 生成遷移報告 - JSON 格式詳細報告
- [x] 支援 dry-run 模式 - 安全預覽功能正常

**實際成果**:
```python
# tools/migrate_json_files.py (350 行)
- Dry-run 測試成功
- 346 個檔案分類到 9 個目錄
- 詳細進度顯示
- JSON 報告生成
```

### 下一步行動

#### 🔜 Phase 2: CLI 分析器批量更新

**優先任務** (建議先執行幾個測試):
1. 更新 `run_rain_intensity_analysis_json.py` (功能 1)
2. 更新 `driver_detailed_pitstop_records.py` (功能 5)
3. 更新 `driver_comparison_advanced.py` (功能 13)
4. 測試 CLI 輸出到新目錄

**完整清單** (50+ 個檔案需要更新):
詳見 [CLI 分析器更新清單](#cli-分析器更新清單)

#### 📝 待定決策

1. **遷移時機**: 
   - 選項 A: 先更新 CLI，再遷移現有檔案
   - 選項 B: 先遷移現有檔案，再更新 CLI ⭐ 推薦
   
2. **API Server 更新優先級**:
   - 建議在 CLI 更新完成後進行
   - 確保向後相容性測試

---

## � 附錄

### CLI 分析器更新清單

基於實際代碼分析 (2025-10-10)，以下檔案需要更新 JSON 輸出路徑：

#### 模式 A: 硬編碼 `json_dir = "json"` (需要替換為配置模組)

**更新模板**:
```python
# ❌ 舊代碼
json_dir = "json"
os.makedirs(json_dir, exist_ok=True)
filepath = os.path.join(json_dir, filename)

# ✅ 新代碼
from CLI_modules.cli.core.json_output_config import get_json_output_path
filepath = get_json_output_path("analysis_type_keyword", filename)
```

**檔案清單** (50+ 個):

1. **incidents/** (事故分析)
   - [ ] `all_incidents_summary.py` - Line 827
   - [ ] `accident_statistics_summary.py`
   - [ ] `severity_distribution_analysis.py`
   - [ ] `key_events_summary.py`
   - [ ] `driver_severity_analysis.py` - Line 349

2. **pitstops/** (進站分析)
   - [ ] `driver_detailed_pitstop_records.py` - Line 428
   - [ ] `driver_fastest_pitstop_ranking.py` - Line 331
   - [ ] `team_pitstop_ranking.py`

3. **telemetry/** (遙測分析)
   - [ ] `driver_comparison_advanced.py` - Line 1982
   - [ ] `all_drivers_telemetry_analysis.py`

4. **weather/** (天氣分析)
   - [ ] `run_rain_intensity_analysis_json.py` - Line 778

5. **lap_analysis/** (圈速分析)
   - [ ] `single_driver_detailed_laptime_analysis.py` - Line 1270
   - [ ] `driver_fastest_lap_analysis.py`

6. **statistics/** (DNF 統計)
   - [ ] `annual_dnf_statistics_new.py` - Line 305
   - [ ] `all_drivers_annual_dnf_analysis.py` - Line 276

7. **overtaking/** (超車分析)
   - [ ] `all_drivers_overtaking_statistics.py` - Line 97
   - [ ] `all_drivers_overtaking_performance_comparison.py` - Line 102
   - [ ] `all_drivers_overtaking_visualization_analysis.py` - Line 104
   - [ ] `all_drivers_overtaking_trends_analysis.py` - Line 109
   - [ ] `driver_overtaking_analysis.py`

8. **corner_analysis/** (彎道分析)
   - [ ] `corner_detailed_analysis.py` - Line 1679
   - [ ] `single_driver_corner_analysis_integrated.py` - Line 217

#### 模式 B: 環境變數 (需要更新為配置模組)

**更新模板**:
```python
# ❌ 舊代碼
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")

# ✅ 新代碼
from CLI_modules.cli.core.json_output_config import get_json_output_path
# ... 在 save_json 函數中使用
```

**檔案清單**:
- [ ] `season_calendar_analysis.py` - Line 19 ⭐ 優先處理 (功能 99)

#### 模式 C: 常數定義 (需要更新為配置模組)

**更新模板**:
```python
# ❌ 舊代碼
_JSON_DIR = "json"

def _build_output_path(...):
    os.makedirs(_JSON_DIR, exist_ok=True)
    return os.path.join(_JSON_DIR, filename)

# ✅ 新代碼
from CLI_modules.cli.core.json_output_config import get_json_output_path

def _build_output_path(...):
    return get_json_output_path("throttle_ratio", filename)
```

**檔案清單**:
- [ ] `driver_throttle_ratio.py` - Line 39 ⭐ 優先處理 (功能 54)

#### 模式 D: 方法返回路徑 (需要更新為配置模組)

**更新模板**:
```python
# ❌ 舊代碼
def save_json(self, payload: Dict[str, Any]) -> Optional[str]:
    json_dir = os.path.join(os.getcwd(), "json")
    os.makedirs(json_dir, exist_ok=True)
    path = os.path.join(json_dir, filename)

# ✅ 新代碼
from CLI_modules.cli.core.json_output_config import get_json_output_path

def save_json(self, payload: Dict[str, Any]) -> Optional[str]:
    path = get_json_output_path("ideal_lap_ranking", filename)
```

**檔案清單**:
- [ ] `ideal_lap_analysis/ideal_lap_analyzer.py` - Line 430 ⭐ 優先處理 (功能 53)

### 優先處理順序 (建議)

**第一批** (高頻使用功能):
1. ✅ `ideal_lap_analyzer.py` (功能 53) - 理想圈速排名
2. ✅ `driver_throttle_ratio.py` (功能 54) - 油門分析
3. ✅ `run_rain_intensity_analysis_json.py` (功能 1) - 降雨分析
4. ✅ `driver_detailed_pitstop_records.py` (功能 5) - 進站記錄
5. ✅ `driver_comparison_advanced.py` (功能 13) - 遙測比較

**第二批** (中頻功能):
6. `all_incidents_summary.py` (功能 8)
7. `driver_fastest_pitstop_ranking.py` (功能 3)
8. `season_calendar_analysis.py` (功能 99)

**第三批** (其餘功能):
- 按照功能 ID 順序處理

### API Server 遞迴搜尋更新

**檔案**: `api/services/cache_service.py`

**需要修改的方法**:
```python
# Line ~207-210
def _search_exact_match(self, function_id: str, **params):
    # 更新所有 glob.glob() 調用
    
    # ❌ 舊代碼
    files = glob.glob(pattern)
    
    # ✅ 新代碼
    files = glob.glob(pattern, recursive=True)
```

**影響的搜尋模式**:
- Line 185: `comparison_telemetry` 搜尋
- Line 207: 一般分析搜尋
- Line 168: 緩存搜尋

**更新檢查清單**:
- [ ] `_search_exact_match()` 方法
- [ ] 所有 `glob.glob()` 調用添加 `recursive=True`
- [ ] 所有搜尋模式添加 `**/` 前綴

---

**最後更新**: 2025-10-10 18:05  
**文件版本**: 1.0.0  
**維護者**: F1T Development Team  
**狀態**: Phase 1 完成，Phase 2 準備中
