# F1T GUI 完整重構計畫書
## GUI Module Refactoring Master Plan

**版本**: 1.0
**建立日期**: 2025-12-15
**預計完成時間**: 2-3 週
**風險等級**: 高（需謹慎執行）

---

## 📋 目錄
1. [重構目標](#重構目標)
2. [整體架構設計](#整體架構設計)
3. [詳細執行步驟](#詳細執行步驟)
4. [風險管理](#風險管理)
5. [測試策略](#測試策略)
6. [回滾方案](#回滾方案)

---

## 🎯 重構目標

### 主要目標
1. **雙架構統一**: 90% 模組採用 UniversalAnalysisMDI 通用架構
   - ⚠️ **例外**: Live Timing 模組使用 BaseLiveTimingMDI（獨立架構，已完成）
2. **清晰組織**: 按功能類型重新組織資料夾結構
3. **消除重複**: 移除所有重複和廢棄代碼
4. **提升維護性**: 降低 40% 維護成本，提升 50% 開發效率
5. **Live Timing 整合驗證**: 確保 20+ 個 Live Timing 子模組與主 GUI 完全兼容

### 成功指標
- ✅ 資料夾層級減少：從平均 4 層 → 3 層
- ✅ 模組數量優化：從 43 個 → 35 個（整合重複）
- ✅ 代碼行數減少：~25%
- ✅ 導入路徑一致性：100%
- ✅ 所有功能測試通過：100%
- ✅ **Live Timing 20+ 個子模組全部可用**
- ✅ **雙架構系統（Universal + Live Timing）無衝突**
- ✅ **Demo 檔案明確分類（工具/參考/整合）**

---

## 🏗️ 整體架構設計

### 新的資料夾結構（方案 A - 推薦）

```
modules/gui/
│
├── 📁 base/                           # 通用基類（不變）
│   ├── universal_analysis_mdi_base.py
│   ├── universal_chart_widget_base.py
│   └── universal_data_loader_base.py
│
├── 📁 interfaces/                     # 介面定義（不變）
│   └── analysis_module.py
│
├── 📁 telemetry/                      # 🆕 單車手遙測分析
│   ├── speed/
│   │   ├── speed_analysis_mdi.py
│   │   ├── speed_analysis_chart_widget.py
│   │   └── speed_analysis_data_loader.py
│   ├── brake/
│   ├── throttle/                      # 整合 3 個油門模組
│   │   ├── throttle_analysis_mdi.py
│   │   ├── line_chart_widget.py       # 折線圖
│   │   └── boxplot_widget.py          # 盒鬚圖
│   ├── gear/
│   ├── rpm/
│   ├── acceleration/
│   ├── speed_diff/                    # 重命名 speeddiff
│   ├── distance_diff/                 # 重命名 distancediff
│   └── time_diff/                     # 重命名 timediff
│
├── 📁 all_drivers/                    # 🆕 全車手對比分析
│   ├── brake/                         # 整合 3 個煞車模組
│   │   ├── brake_analysis_mdi.py
│   │   ├── performance_widget.py
│   │   ├── chart_widget.py
│   │   └── all_laps_widget.py
│   ├── acceleration/
│   ├── corner_performance/
│   ├── straight_line_speed/
│   └── max_speed/
│
├── 📁 lap_analysis/                   # 🆕 圈速相關分析
│   ├── detailed_laptime/              # 從 driver_race 移動
│   ├── laptime_boxplot/               # 整合 2 個盒鬚圖模組
│   ├── ideal_lap_ranking/
│   ├── ideal_lap_sector_comparison/
│   └── ideal_lap_sector_heatmap/
│
├── 📁 race_analysis/                  # 🆕 賽事相關分析
│   ├── pitstop/
│   ├── accident/
│   ├── weather/
│   ├── rain_intensity/
│   └── tire_strategy/
│
├── 📁 track/                          # 🔄 賽道分析（重命名）
│   ├── track_map/
│   ├── track_elevation/
│   └── historical_track_map/
│
├── 📁 standings/                      # 🆕 積分榜相關
│   ├── driver_standings/
│   ├── constructor_standings/
│   ├── season_progress/
│   └── championship_summary/
│
├── 📁 prediction/                     # 🔄 預測系統（整合）
│   ├── qualifying/
│   ├── race/
│   └── laptime/
│
├── 📁 live_timing/                    # ✅ Live Timing 系統（已完成 - 特殊架構）
│   ├── core/                          # 核心系統
│   │   ├── data_manager.py            # 數據管理器（單例）
│   │   ├── module_factory.py          # 模組工廠
│   │   ├── base_live_mdi.py           # Live Timing MDI 基類
│   │   ├── local_source.py            # 本地數據源
│   │   ├── position_processor.py      # 位置數據處理
│   │   ├── f1_api_downloader.py       # API 下載器
│   │   ├── api_client.py              # API 客戶端
│   │   ├── realtime_database.py       # 即時資料庫
│   │   └── database_reader.py         # 資料庫讀取器
│   └── live_timing_modules/           # 20+ 個子模組
│       ├── control_panel.py           # 控制面板（主要入口）
│       ├── control_dock.py            # Dock 控制面板
│       ├── track_map.py               # 賽道地圖
│       ├── ranking_tower.py           # 即時排名塔
│       ├── pit_window.py              # 進站策略
│       ├── tyre_strategy.py           # 輪胎策略
│       ├── lap_time_distribution.py   # 圈速分佈
│       ├── circle_map.py              # 圓形地圖
│       ├── race_control_messages.py   # 比賽控制訊息
│       ├── lap_history.py             # 圈速歷史（含 S1/S2/S3）
│       ├── speed_trace.py             # 速度追蹤
│       ├── throttle_trace.py          # 油門追蹤
│       ├── brake_trace.py             # 煞車追蹤
│       ├── gear_trace.py              # 檔位追蹤
│       ├── rpm_trace.py               # 轉速追蹤
│       ├── sector_comparison.py       # 區段比較（S1/S2/S3）
│       ├── driver_strategy.py         # 車手策略
│       ├── battle_insight.py          # 對戰洞察
│       ├── chase_strategy.py          # 追趕策略
│       └── track_weather.py           # 賽道天氣
│
├── 📁 utilities/                      # 🆕 工具與輔助
│   ├── diagnostics/
│   ├── settings/
│   ├── themes/
│   └── parts_analysis/
│
└── 📁 shared/                         # 🆕 共用組件
    ├── linkage/
    ├── season_calendar/
    └── universal_chart_widget.py
```

### 架構分層

```
Layer 1: 基礎層 (base, interfaces)
         ↓
Layer 2: 功能模組層 (telemetry, all_drivers, lap_analysis, etc.)
         ↓
Layer 3: UI 層 (MDI, widgets)
         ↓
Layer 4: 數據層 (data_loader, API)
```

---

## 📝 詳細執行步驟

### 階段 0：準備工作（1天）

#### 0.1 建立安全分支
```bash
# 建立重構專用分支
git checkout -b refactor/gui-modules-restructure

# 建立備份標籤
git tag backup-before-refactor

# 確保工作目錄乾淨
git status
```

#### 0.2 安裝測試工具
```bash
# 安裝依賴
pip install pytest pytest-qt pytest-cov

# 建立測試框架
mkdir -p tests/gui/integration
mkdir -p tests/gui/unit
```

#### 0.3 記錄當前狀態
```bash
# 生成模組清單
python scripts/cleanup_gui_modules.py --dry-run > docs/modules_before_refactor.txt

# 記錄所有導入
grep -r "from modules.gui" modules/gui > docs/imports_before_refactor.txt
```

**檢查點**: ✅ Git 分支已建立，測試環境已準備

---

### 階段 1：清理無用檔案（0.5天）

#### 1.1 執行自動化清理
```bash
# 預覽
python scripts/cleanup_gui_modules.py --dry-run

# 執行清理
python scripts/cleanup_gui_modules.py --yes

# 提交變更
git add .
git commit -m "refactor(gui): 清理備份和舊版本檔案 (81 files)"
```

#### 1.2 手動檢查遺漏
```bash
# 搜尋可能的遺漏
find modules/gui -name "*backup*"
find modules/gui -name "*old*" -o -name "*OLD*"
find modules/gui -name "demo_*"
```

**檢查點**: ✅ 81 個無用檔案已刪除，Git 已提交

---

### 階段 2：建立新的資料夾結構（0.5天）

#### 2.1 建立新目錄
```bash
# 建立主要目錄
mkdir -p modules/gui/telemetry/{speed,brake,throttle,gear,rpm,acceleration,speed_diff,distance_diff,time_diff}
mkdir -p modules/gui/all_drivers/{brake,acceleration,corner_performance,straight_line_speed,max_speed}
mkdir -p modules/gui/lap_analysis/{detailed_laptime,laptime_boxplot,ideal_lap_ranking,ideal_lap_sector_comparison,ideal_lap_sector_heatmap}
mkdir -p modules/gui/race_analysis/{pitstop,accident,weather,rain_intensity,tire_strategy}
mkdir -p modules/gui/track/{track_map,track_elevation,historical_track_map}
mkdir -p modules/gui/standings/{driver_standings,constructor_standings,season_progress,championship_summary}
mkdir -p modules/gui/prediction/{qualifying,race,laptime}
mkdir -p modules/gui/utilities/{diagnostics,settings,themes,parts_analysis}
mkdir -p modules/gui/shared/{linkage,season_calendar}
```

#### 2.2 建立 __init__.py
```bash
# 為所有新目錄建立 __init__.py
find modules/gui/telemetry -type d -exec touch {}/__init__.py \;
find modules/gui/all_drivers -type d -exec touch {}/__init__.py \;
find modules/gui/lap_analysis -type d -exec touch {}/__init__.py \;
find modules/gui/race_analysis -type d -exec touch {}/__init__.py \;
# ... 其他目錄
```

**檢查點**: ✅ 新資料夾結構已建立

---

### 階段 3：遷移遙測分析模組（2-3天）

#### 3.1 Speed 模組遷移（範例）

**原路徑**: `modules/gui/lap_analysis/speed_analysis/`
**新路徑**: `modules/gui/telemetry/speed/`

**步驟**:
```bash
# 1. 複製檔案到新位置
cp -r modules/gui/lap_analysis/speed_analysis/* modules/gui/telemetry/speed/

# 2. 更新檔案內的導入路徑
# 在 speed_analysis_mdi.py 中：
# 舊: from modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader import ...
# 新: from modules.gui.telemetry.speed.speed_analysis_data_loader import ...

# 3. 更新模組註冊
# 在 speed_analysis_mdi.py 中確認 module_type = "speed"

# 4. 測試模組
python -m pytest tests/gui/telemetry/test_speed_analysis.py

# 5. 刪除舊目錄（確認測試通過後）
# git rm -r modules/gui/lap_analysis/speed_analysis/
```

#### 3.2 其他遙測模組遷移清單

**優先順序**（由簡到繁）:
1. ✅ Speed (參考範例)
2. ⬜ Brake
3. ⬜ Gear
4. ⬜ RPM
5. ⬜ Acceleration
6. ⬜ Throttle（需整合 3 個模組）
7. ⬜ Speed_diff (重命名 speeddiff)
8. ⬜ Distance_diff (重命名 distancediff)
9. ⬜ Time_diff (重命名 timediff)

**每個模組遷移檢查清單**:
- [ ] 複製檔案到新位置
- [ ] 更新內部導入路徑
- [ ] 更新模組註冊資訊
- [ ] 編寫/更新單元測試
- [ ] 執行測試確認功能正常
- [ ] 更新外部引用（在其他模組中）
- [ ] 刪除舊目錄
- [ ] Git 提交變更

**檢查點**: ✅ 9 個遙測模組已遷移並測試通過

---

### 階段 4：整合全車手分析模組（2-3天）

#### 4.1 煞車分析整合（重點項目）

**需整合的模組**:
1. `all_drivers_brake_chart/`
2. `all_drivers_brake_performance_analysis/`
3. `all_drivers_brake_all_laps_analysis/`

**整合策略**:
```python
# 新的統一模組: modules/gui/all_drivers/brake/

# 檔案結構:
brake/
├── __init__.py
├── brake_analysis_mdi.py          # 主 MDI 視窗
├── brake_data_loader.py           # 統一數據載入器
├── performance_view_widget.py     # 效能視圖（來自 brake_performance）
├── chart_view_widget.py           # 圖表視圖（來自 brake_chart）
├── all_laps_view_widget.py        # 全圈速視圖（來自 brake_all_laps）
└── brake_view_switcher.py         # 視圖切換器（新增）

# MDI 視窗整合多視圖:
class AllDriversBrakeAnalysisMDI(UniversalAnalysisMDIBase):
    def _create_chart_widget(self):
        # 建立標籤視圖，包含三個子視圖
        tab_widget = QTabWidget()
        tab_widget.addTab(PerformanceViewWidget(), "效能對比")
        tab_widget.addTab(ChartViewWidget(), "詳細圖表")
        tab_widget.addTab(AllLapsViewWidget(), "全圈速分析")
        return tab_widget
```

**遷移步驟**:
```bash
# 1. 建立新模組目錄
mkdir -p modules/gui/all_drivers/brake

# 2. 提取共用邏輯
# - 合併三個 data_loader 的功能
# - 建立統一的 API 調用介面

# 3. 重構視圖組件
# - 將每個模組的圖表組件改為獨立 widget
# - 建立標籤切換介面

# 4. 測試整合
python -m pytest tests/gui/all_drivers/test_brake_analysis.py

# 5. 更新引用
# 搜尋所有引用舊模組的地方並更新
grep -r "all_drivers_brake" modules/gui
grep -r "all_drivers_brake" f1t_gui_main.py

# 6. 刪除舊模組
git rm -r modules/gui/all_drivers_brake_chart/
git rm -r modules/gui/all_drivers_brake_performance_analysis/
git rm -r modules/gui/all_drivers_brake_all_laps_analysis/
```

#### 4.2 其他全車手模組

**遷移清單**:
1. ✅ Brake（參考上方）
2. ⬜ Acceleration
3. ⬜ Corner Performance
4. ⬜ Straight Line Speed
5. ⬜ Max Speed

**檢查點**: ✅ 全車手分析模組已整合，從 7 個減少到 5 個

---

### 階段 5：重組圈速分析模組（2天）

#### 5.1 圈速盒鬚圖整合

**需整合的模組**:
1. `driver_race/lap_box_plot_analysis/`
2. `lap_box_plot_analysis/`

**目標**: `modules/gui/lap_analysis/laptime_boxplot/`

#### 5.2 理想圈速模組遷移

**原路徑**: `ideal_lap_analysis/*`
**新路徑**: `lap_analysis/*`

**模組清單**:
1. ideal_lap_ranking_table → lap_analysis/ideal_lap_ranking
2. ideal_lap_sector_comparison → lap_analysis/ideal_lap_sector_comparison
3. ideal_lap_sector_heatmap → lap_analysis/ideal_lap_sector_heatmap

#### 5.3 詳細圈速分析

**原路徑**: `driver_race/detailed_lap_analysis/`
**新路徑**: `lap_analysis/detailed_laptime/`

**檢查點**: ✅ 圈速分析模組已重組並整合

---

### 階段 6：整合賽事分析模組（2天）

#### 6.1 模組遷移清單

| 原路徑 | 新路徑 | 需整合 |
|--------|--------|--------|
| `pitstop_analysis/` | `race_analysis/pitstop/` | 否 |
| `accident_analysis/` | `race_analysis/accident/` | 否 |
| `weather_timeline/` | `race_analysis/weather/` | 否 |
| `rain_analysis/` | `race_analysis/rain_intensity/` | 否 |
| `tire_analysis/` | `race_analysis/tire_strategy/` | 否 |

#### 6.2 遷移策略

這些模組大多已經是獨立模組，主要工作是：
1. 移動到新位置
2. 更新導入路徑
3. 確保通用架構一致性

**檢查點**: ✅ 賽事分析模組已整合

---

### 階段 7：更新所有導入路徑（1-2天）

#### 7.1 自動化導入路徑更新

建立自動化腳本：

```python
# scripts/update_imports.py

import re
from pathlib import Path

# 導入路徑映射表
IMPORT_MAPPINGS = {
    # 遙測分析
    "modules.gui.lap_analysis.speed_analysis": "modules.gui.telemetry.speed",
    "modules.gui.lap_analysis.brake_analysis": "modules.gui.telemetry.brake",
    "modules.gui.lap_analysis.throttle_analysis": "modules.gui.telemetry.throttle",
    # ... 其他映射

    # 全車手分析
    "modules.gui.all_drivers_brake_chart": "modules.gui.all_drivers.brake",
    "modules.gui.all_drivers_brake_performance_analysis": "modules.gui.all_drivers.brake",
    # ... 其他映射
}

def update_imports_in_file(file_path: Path):
    """更新單個檔案中的導入路徑"""
    content = file_path.read_text(encoding='utf-8')

    for old_path, new_path in IMPORT_MAPPINGS.items():
        # 處理 from ... import ...
        content = re.sub(
            rf'from {re.escape(old_path)}',
            f'from {new_path}',
            content
        )
        # 處理 import ...
        content = re.sub(
            rf'import {re.escape(old_path)}',
            f'import {new_path}',
            content
        )

    file_path.write_text(content, encoding='utf-8')

def main():
    # 掃描所有 Python 檔案
    for py_file in Path('modules').rglob('*.py'):
        update_imports_in_file(py_file)

    # 也更新主程式
    update_imports_in_file(Path('f1t_gui_main.py'))
```

#### 7.2 手動檢查關鍵檔案

**需檢查的檔案**:
1. `f1t_gui_main.py` - 主程式
2. `modules/gui/base/*.py` - 基類
3. `modules/gui/interfaces/*.py` - 介面
4. 所有 `*_mdi.py` - MDI 視窗

#### 7.3 驗證導入

```bash
# 檢查是否有遺漏的舊路徑
grep -r "lap_analysis.speed_analysis" modules/
grep -r "all_drivers_brake_chart" modules/

# 執行語法檢查
python -m py_compile modules/gui/**/*.py
```

**檢查點**: ✅ 所有導入路徑已更新並驗證

---

### 階段 8：執行完整測試和驗證（2-3天）

#### 8.1 單元測試

**建立測試套件**:
```python
# tests/gui/test_all_modules.py

import pytest
from PyQt5.QtWidgets import QApplication

# 測試所有模組是否可以正常導入
def test_import_all_modules():
    """測試所有模組導入"""
    # 遙測分析
    from modules.gui.telemetry.speed import speed_analysis_mdi
    from modules.gui.telemetry.brake import brake_analysis_mdi
    # ... 測試所有模組

def test_all_mdi_initialization():
    """測試所有 MDI 視窗初始化"""
    app = QApplication([])

    # 測試 Speed 分析
    from modules.gui.telemetry.speed.speed_analysis_mdi import SpeedAnalysisMDI
    mdi = SpeedAnalysisMDI()
    assert mdi is not None

    # ... 測試所有 MDI
```

#### 8.2 整合測試

**測試流程**:
```bash
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 手動測試清單
- [ ] 主視窗正常啟動
- [ ] 左側模組樹正常顯示
- [ ] 所有模組圖標和名稱正確
- [ ] 選擇 2025 Abu Dhabi R
- [ ] 開啟每個模組檢查是否正常載入
- [ ] 測試數據載入
- [ ] 測試圖表渲染
- [ ] 測試參數更新
- [ ] 測試模組間切換
```

#### 8.3 效能測試

```python
# tests/performance/test_module_load_time.py

import time
from modules.gui.telemetry.speed.speed_analysis_mdi import SpeedAnalysisMDI

def test_module_load_performance():
    """測試模組載入效能"""
    start = time.time()
    mdi = SpeedAnalysisMDI()
    load_time = time.time() - start

    # 應該在 1 秒內載入
    assert load_time < 1.0
```

**檢查點**: ✅ 所有測試通過，無回歸問題

---

### 階段 9：更新文檔和清理工作（1天）

#### 9.1 更新開發文檔

**需更新的文檔**:
1. `docs/GUI_MODULE_STRUCTURE.md` - 模組結構說明
2. `docs/DEVELOPMENT_GUIDE.md` - 開發指南
3. `README.md` - 專案說明

#### 9.2 生成遷移報告

```bash
# 自動生成變更報告
python scripts/generate_refactor_report.py > docs/REFACTOR_REPORT.md
```

#### 9.3 最終清理

```bash
# 刪除所有舊目錄（已遷移）
git status | grep "deleted:" | wc -l

# 確認沒有遺留的舊檔案
find modules/gui -name "*_old*"
find modules/gui -name "*_backup*"

# 清理 __pycache__
find modules/gui -name "__pycache__" -exec rm -rf {} +

# 最終提交
git add .
git commit -m "refactor(gui): 完成模組重構 - 新架構已上線"
```

**檢查點**: ✅ 文檔已更新，清理工作完成

---

### 階段 10：Live Timing 模組整合驗證（2-3天）⚠️ 新增

#### 10.1 Live Timing 架構審查

**現狀評估**:
```markdown
✅ **已完成項目**：
- 20+ 個子模組全部實現
- 使用獨立的 BaseLiveTimingMDI 架構
- LiveTimingModuleFactory 工廠模式管理模組創建
- LiveTimingDataManager 單例管理數據流
- 支援即時模式（SignalR）和歷史回放模式（本地 JSON）

⚠️ **需要驗證**：
- 與主 GUI MDI Area 的兼容性
- 模組註冊表（MODULE_REGISTRY）完整性
- 雙架構（UniversalAnalysisMDI + BaseLiveTimingMDI）共存
```

**整合策略**:
```bash
# 1. 檢查 Live Timing 模組註冊
python -c "
from modules.gui.live_timing import LiveTimingModuleFactory
factory = LiveTimingModuleFactory.get_instance()
implemented = factory.get_implemented_modules()
print(f'✅ 已實現模組數量: {len(implemented)}')
for key, meta in implemented.items():
    print(f'  - {meta[\"display_name\"]} ({key})')
"

# 2. 驗證數據管理器
python -c "
from modules.gui.live_timing import LiveTimingDataManager
dm = LiveTimingDataManager.get_instance()
print('✅ LiveTimingDataManager 初始化成功')
print(f'   支援模式: 即時/歷史回放')
"

# 3. 測試模組創建
python -c "
from modules.gui.live_timing import create_live_timing_module
module = create_live_timing_module('Track Map')
print(f'✅ 模組創建成功: {module.__class__.__name__}')
"
```

#### 10.2 Live Timing 子模組清單

**已實現模組（20+ 個）**:

| # | 模組鍵值 | 顯示名稱 | 狀態 | 說明 |
|---|----------|----------|------|------|
| 1 | `track_map` | Track Map | ✅ | 賽道地圖（主要可視化） |
| 2 | `ranking_tower` | Live Ranking | ✅ | 即時排名塔 |
| 3 | `control_panel` | Control Panel | ✅ | 控制面板（必開） |
| 4 | `pit_window` | Pit Window | ✅ | 進站策略 |
| 5 | `tyre_strategy` | Tyre Strategy | ✅ | 輪胎策略 |
| 6 | `lap_time_distribution` | Lap Time Distribution | ✅ | 圈速分佈 |
| 7 | `circle_map` | Circle Map | ✅ | 圓形地圖 |
| 8 | `race_control_messages` | Race Control Messages | ✅ | 比賽控制訊息 |
| 9-12 | `lap_history_*` | Lap History (Lap/S1/S2/S3) | ✅ | 圈速歷史 |
| 13-17 | `*_trace` | Speed/Throttle/Brake/Gear/RPM Trace | ✅ | 遙測追蹤 |
| 18-20 | `sector_comparison_*` | Sector Comparison (S1/S2/S3) | ✅ | 區段比較 |
| 21 | `driver_strategy` | Driver Strategy | ✅ | 車手策略 |
| 22 | `battle_insight` | Battle Insight | ✅ | 對戰洞察 |
| 23 | `chase_strategy` | Chase Strategy | ✅ | 追趕策略 |
| 24 | `track_weather` | Track Weather | ✅ | 賽道天氣 |

**待實現模組（2 個）**:
| # | 模組鍵值 | 顯示名稱 | 狀態 | 說明 |
|---|----------|----------|------|------|
| 25 | `gap_chart` | Gap Chart | ⬜ | 差距圖表 |
| 26 | `battle_tracker` | Battle Tracker | ⬜ | 對戰追蹤 |

#### 10.3 Live Timing 測試檢查清單

**功能測試**:
```bash
# 建立測試腳本
cat > tests/gui/live_timing/test_integration.py << 'EOF'
import pytest
from PyQt5.QtWidgets import QApplication
from modules.gui.live_timing import (
    LiveTimingModuleFactory,
    LiveTimingDataManager,
    create_live_timing_module
)

def test_factory_initialization():
    """測試工廠初始化"""
    factory = LiveTimingModuleFactory.get_instance()
    assert factory is not None
    
def test_implemented_modules_count():
    """測試已實現模組數量"""
    factory = LiveTimingModuleFactory.get_instance()
    implemented = factory.get_implemented_modules()
    assert len(implemented) >= 20, f"預期至少 20 個模組，實際: {len(implemented)}"
    
def test_data_manager_singleton():
    """測試數據管理器單例"""
    dm1 = LiveTimingDataManager.get_instance()
    dm2 = LiveTimingDataManager.get_instance()
    assert dm1 is dm2
    
def test_create_track_map(qtbot):
    """測試創建 Track Map 模組"""
    module = create_live_timing_module('Track Map')
    assert module is not None
    assert 'Track Map' in module.windowTitle()
EOF

# 執行測試
python -m pytest tests/gui/live_timing/test_integration.py -v
```

**整合測試**（手動）:
- [ ] 啟動主 GUI: `python f1t_gui_main.py`
- [ ] 從選單開啟 Live Timing → Control Panel
- [ ] 選擇 2025 Abu Dhabi Race
- [ ] 點擊「Load Race Data」
- [ ] 開啟 Track Map、Ranking Tower、Tyre Strategy
- [ ] 驗證三個模組顯示相同時間點數據
- [ ] 使用時間軸控制播放/暫停
- [ ] 調整播放速度（0.5x, 1x, 2x）
- [ ] 跳轉到特定時間點
- [ ] 關閉一個模組，確認其他模組不受影響
- [ ] 重新開啟已關閉的模組，確認狀態正確

**效能測試**:
```python
# tests/performance/test_live_timing_performance.py
import time
from modules.gui.live_timing import LiveTimingDataManager

def test_snapshot_update_performance():
    """測試快照更新效能（目標: 60 FPS = 16ms）"""
    dm = LiveTimingDataManager.get_instance()
    
    start = time.perf_counter()
    for _ in range(100):
        dm._on_playback_tick()  # 模擬 100 次更新
    elapsed = time.perf_counter() - start
    
    avg_time_ms = (elapsed / 100) * 1000
    assert avg_time_ms < 16, f"更新時間 {avg_time_ms:.2f}ms 超過 16ms 目標"
```

**檢查點**: ✅ Live Timing 所有模組測試通過，與主 GUI 整合無衝突

---

### 階段 11：Demo 資料夾重構（1天）⚠️ 新增

#### 11.1 Live_timing_test 資料夾處理

**當前狀態分析**:
```bash
Live_timing_test/
├── demo_driver_trajectory_comparison.py  # 850 行 - 2025-12-15 完成
├── TRAJECTORY_COMPARISON_DEMO_README.md  # Demo 文檔
├── demo_live_position_tracking.py        # 8,761 行 - 原始大型 Demo
└── json/LiveF1/                          # Live Timing 數據源
    └── 2025/Abu_Dhabi_Race/              # 示例數據
```

**處理策略**:

**保留檔案**（獨立測試工具）:
```markdown
✅ **保留並維護**：
- demo_driver_trajectory_comparison.py
  - 用途: 車手軌跡比較獨立測試工具
  - 狀態: 完整功能，已測試通過
  - 數據: Position.json (689K), TimingData.json (66K), CarData.json (673K)
  - 保留原因: 獨立於主 GUI 的專業分析工具
  
- TRAJECTORY_COMPARISON_DEMO_README.md
  - 用途: Demo 使用說明文檔
  - 保留原因: 完整的使用指南和技術文檔

- json/LiveF1/
  - 用途: Live Timing 數據源（主 GUI 和 Demo 共用）
  - 保留原因: 必需的數據檔案
```

**整合或移除**:
```markdown
⚠️ **需要決策**：
- demo_live_position_tracking.py (8,761 行)
  
  選項 A: 移動到 tools/legacy/ 作為參考
  ```bash
  mkdir -p tools/legacy/live_timing/
  mv Live_timing_test/demo_live_position_tracking.py tools/legacy/live_timing/
  git add tools/legacy/live_timing/
  git commit -m "refactor: 將 Live Timing 原型 Demo 移至 legacy"
  ```
  
  選項 B: 完全移除（推薦）
  ```bash
  # 功能已完全整合到 modules/gui/live_timing/
  git rm Live_timing_test/demo_live_position_tracking.py
  git commit -m "refactor: 移除已整合的 Live Timing Demo"
  ```
  
  **推薦選項 B**，理由：
  - 所有 22 個類別已整合到主 GUI
  - 保留會造成維護負擔
  - 可以從 Git 歷史中找回
```

#### 11.2 建立 Demo 索引文檔

建立 `Live_timing_test/README.md`:
```markdown
# Live Timing 測試與 Demo 工具

## 🎯 目錄說明

本目錄包含 Live Timing 相關的獨立測試工具和 Demo。

### 📊 可用 Demo

#### 1. 車手軌跡比較 Demo
**檔案**: `demo_driver_trajectory_comparison.py`  
**功能**: 基於 Live F1 Position API 的車手軌跡視覺化比較  
**文檔**: [TRAJECTORY_COMPARISON_DEMO_README.md](./TRAJECTORY_COMPARISON_DEMO_README.md)  
**使用**:
```bash
python Live_timing_test\demo_driver_trajectory_comparison.py
```

**數據需求**: 
- Position.json (X/Y/Z 座標)
- TimingData.json (圈速數據)
- CarData.json (速度數據)

### 📁 數據目錄

- `json/LiveF1/`: Live Timing 數據源（與主 GUI 共用）
  - `2025/Abu_Dhabi_Race/`: 2025 阿布達比大獎賽示例數據

### 🔗 相關模組

完整的 Live Timing 功能已整合到主 GUI:
- 路徑: `modules/gui/live_timing/`
- 啟動: `python f1t_gui_main.py` → Live Timing 選單

### 📝 開發狀態

- ✅ 軌跡比較 Demo - 完成（2025-12-15）
- ✅ Live Timing 主模組 - 完成（20+ 子模組）
- ⬜ 即時 SignalR 連接測試 - 待開發
```

#### 11.3 清理檢查清單

**執行步驟**:
```bash
# 1. 決定 demo_live_position_tracking.py 的處理方式
# （建議選項 B: 完全移除）

# 2. 建立 Demo 索引文檔
cat > Live_timing_test/README.md << 'EOF'
# （見上方內容）
EOF

# 3. 確認數據目錄完整性
ls -R json/LiveF1/2025/Abu_Dhabi_Race/
# 應包含: Position.json, TimingData.json, CarData.json

# 4. 提交變更
git add Live_timing_test/README.md
git commit -m "docs: 新增 Live Timing Demo 索引文檔"

# 5. 如果選擇移除大型 Demo
git rm Live_timing_test/demo_live_position_tracking.py
git commit -m "refactor: 移除已整合的 Live Timing Demo (8,761 行)"
```

**檢查點**: ✅ Demo 資料夾結構清晰，文檔完整

---

## ⚠️ 風險管理

### 高風險項目

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|---------|
| 導入路徑遺漏 | 高 | 中 | 使用自動化腳本 + 手動檢查 |
| 模組功能回歸 | 高 | 中 | 完整的測試套件 |
| **Live Timing 雙架構衝突** | **高** | **中** | **獨立測試 Live Timing 模組** |
| **SignalR 即時連接穩定性** | **中** | **低** | **完整的即時模式測試** |
| 整合後效能下降 | 中 | 低 | 效能基準測試 |
| Git 合併衝突 | 中 | 高 | 使用專用分支，小步提交 |
| 用戶介面變更 | 低 | 中 | 保持 UI 一致性 |
| **Demo 檔案處理不當** | **低** | **中** | **明確分類保留/移除** |

### 應變措施

**如果遇到嚴重問題**:
```bash
# 方案 A: 回滾到特定階段
git log --oneline | grep "refactor(gui)"
git reset --hard <commit-hash>

# 方案 B: 完全回滾
git checkout backup-before-refactor
git checkout -b refactor/gui-modules-restructure-v2

# 方案 C: 暫停重構，修復問題
git stash
# 修復問題
git stash pop
```

---

## 🧪 測試策略

### 測試金字塔

```
           /\
          /  \  E2E 測試 (5%)
         /----\
        /      \ 整合測試 (25%)
       /--------\
      /          \ 單元測試 (70%)
     /------------\
```

### 測試檢查清單

**單元測試** (每個模組):
- [ ] 模組可以正常導入
- [ ] MDI 視窗可以初始化
- [ ] 數據載入器可以載入測試數據
- [ ] 圖表組件可以渲染

**整合測試**:
- [ ] 模組可以在主視窗中開啟
- [ ] 參數更新正常傳遞
- [ ] 模組間切換無異常
- [ ] API 調用正常
- [ ] **Live Timing 模組與主 GUI 共存**
- [ ] **Live Timing 數據管理器正常廣播**
- [ ] **即時模式 SignalR 連接測試**
- [ ] **歷史模式本地 JSON 載入測試**

**端對端測試**:
- [ ] 完整用戶流程可以執行
- [ ] 真實數據載入和顯示
- [ ] 所有功能按鈕正常工作
- [ ] **Live Timing 20+ 個模組全部可開啟**
- [ ] **多個 Live Timing 模組同時運行無衝突**

### Live Timing 專項測試 ⚠️ 新增

**工廠模式測試**:
```bash
# 測試模組註冊表
python -c "
from modules.gui.live_timing import LiveTimingModuleFactory
factory = LiveTimingModuleFactory.get_instance()
all_modules = factory.get_all_modules()
implemented = factory.get_implemented_modules()
print(f'📊 總註冊模組: {len(all_modules)}')
print(f'✅ 已實現模組: {len(implemented)}')
print(f'⬜ 待實現模組: {len(all_modules) - len(implemented)}')
"

# 測試多語言支援
python -c "
from modules.gui.live_timing import LiveTimingModuleFactory
factory = LiveTimingModuleFactory.get_instance()
assert factory.is_live_timing_module('Track Map')
assert factory.is_live_timing_module('賽道地圖')
assert factory.is_live_timing_module('トラックマップ')
print('✅ 多語言模組識別測試通過')
"
```

**數據管理器測試**:
```bash
# 測試單例模式
python -c "
from modules.gui.live_timing import LiveTimingDataManager
dm1 = LiveTimingDataManager.get_instance()
dm2 = LiveTimingDataManager.get_instance()
assert dm1 is dm2
print('✅ DataManager 單例模式正常')
"

# 測試信號系統
python tests/gui/live_timing/test_data_manager_signals.py
```

**模組創建測試**:
```python
# tests/gui/live_timing/test_module_creation.py
import pytest
from PyQt5.QtWidgets import QApplication
from modules.gui.live_timing import create_live_timing_module

IMPLEMENTED_MODULES = [
    'Track Map', 'Live Ranking', 'Control Panel',
    'Pit Window', 'Tyre Strategy', 'Lap Time Distribution',
    'Circle Map', 'Race Control Messages',
    'Lap History - Lap Time', 'Speed Trace', 'Brake Trace',
    # ... 所有已實現模組
]

@pytest.mark.parametrize("module_name", IMPLEMENTED_MODULES)
def test_create_module(qtbot, module_name):
    """測試創建每個已實現的模組"""
    module = create_live_timing_module(module_name)
    assert module is not None
    assert module_name in module.windowTitle()
```

**整合測試清單**（手動）:
```markdown
### Live Timing 完整流程測試

#### 測試環境準備
- [ ] 確認 json/LiveF1/2025/Abu_Dhabi_Race/ 數據完整
- [ ] 確認主 GUI 可以正常啟動

#### 歷史回放模式測試
1. [ ] 開啟主 GUI: `python f1t_gui_main.py`
2. [ ] Live Timing → Control Panel
3. [ ] 選擇「歷史回放」模式
4. [ ] 選擇 2025 Abu Dhabi Race
5. [ ] 點擊「Load Race Data」
6. [ ] 觀察載入狀態（應顯示載入進度）
7. [ ] 載入完成後，開啟以下模組：
   - [ ] Track Map（賽道地圖）
   - [ ] Live Ranking（即時排名）
   - [ ] Tyre Strategy（輪胎策略）
   - [ ] Pit Window（進站策略）
   - [ ] Race Control Messages（比賽訊息）
8. [ ] 驗證所有模組顯示初始狀態數據
9. [ ] 使用時間軸控制播放
10. [ ] 驗證所有模組同步更新
11. [ ] 調整播放速度（0.5x, 1x, 2x, 5x）
12. [ ] 跳轉到不同時間點
13. [ ] 暫停/繼續播放
14. [ ] 關閉任一模組，確認其他模組不受影響
15. [ ] 重新開啟已關閉的模組

#### 效能測試
- [ ] 同時開啟 10 個 Live Timing 模組
- [ ] 播放速度設為 5x
- [ ] 觀察 CPU 使用率（應 < 50%）
- [ ] 觀察記憶體使用（應無明顯洩漏）
- [ ] UI 響應流暢（無卡頓）

#### 錯誤處理測試
- [ ] 載入不存在的賽事（應顯示錯誤訊息）
- [ ] 數據檔案缺失（應正常降級）
- [ ] 快速切換賽事（應正常卸載舊數據）
```

---

## 🔄 回滾方案

### 情境 1: 單一模組遷移失敗

```bash
# 只回滾該模組的變更
git log --oneline modules/gui/telemetry/speed/
git revert <commit-hash>

# 恢復舊模組
git checkout HEAD~1 modules/gui/lap_analysis/speed_analysis/
```

### 情境 2: 整個階段失敗

```bash
# 回滾到階段開始
git log --oneline | grep "階段"
git reset --hard <stage-start-commit>
```

### 情境 3: 完全失敗，需要重新開始

```bash
# 切換到備份標籤
git checkout backup-before-refactor

# 建立新分支重新開始
git checkout -b refactor/gui-modules-restructure-v2

# 分析失敗原因，調整策略
```

---

## 📊 進度追蹤

### 里程碑

| 里程碑 | 預計完成日期 | 完成狀態 |
|--------|-------------|---------|
| M0: 準備工作 | Day 1 | ⬜ |
| M1: 清理完成 | Day 2 | ⬜ |
| M2: 結構建立 | Day 3 | ⬜ |
| M3: 遙測模組完成 | Day 6 | ⬜ |
| M4: 全車手模組完成 | Day 9 | ⬜ |
| M5: 圈速模組完成 | Day 11 | ⬜ |
| M6: 賽事模組完成 | Day 13 | ⬜ |
| M7: 導入更新完成 | Day 15 | ⬜ |
| M8: 測試完成 | Day 18 | ⬜ |
| M9: 文檔完成 | Day 19 | ⬜ |
| **M10: Live Timing 驗證完成** | **Day 22** | ⬜ |
| **M11: Demo 重構完成** | **Day 23** | ⬜ |
| **發布** | **Day 24** | ⬜ |

### 每日檢查清單

**每天結束前**:
- [ ] 執行所有測試
- [ ] 提交當天變更
- [ ] 更新進度追蹤
- [ ] 記錄遇到的問題

**每週檢查**:
- [ ] 審查整體進度
- [ ] 評估風險和問題
- [ ] 調整計畫（如需要）

---

## 📚 參考資源

### 相關文檔
- [GUI 模組架構分析報告](./GUI_MODULE_ANALYSIS_REPORT.md)
- [通用架構設計文檔](./UNIVERSAL_ARCHITECTURE_DESIGN.md)
- [API 整合指南](./API_INTEGRATION_GUIDE.md)
- **[Live Timing 整合計畫](./develop_task/GUI_Develop_task/LIVE_TIMING_INTEGRATION_PLAN.md)** ⚠️ 新增
- **[軌跡比較 Demo 說明](../Live_timing_test/TRAJECTORY_COMPARISON_DEMO_README.md)** ⚠️ 新增

### 工具腳本
- `scripts/cleanup_gui_modules.py` - 清理腳本
- `scripts/update_imports.py` - 導入更新腳本（待建立）
- `scripts/generate_refactor_report.py` - 報告生成腳本（待建立）
- **`Live_timing_test/demo_driver_trajectory_comparison.py` - 軌跡比較測試工具** ⚠️ 新增

### 聯絡資訊
- 技術問題: 查看 `docs/FAQ.md`
- Bug 回報: 使用 GitHub Issues

---

## ✅ 完成標準

重構完成需滿足以下條件:

1. **功能完整性**
   - ✅ 所有原有功能正常運作
   - ✅ 無新增的 Bug
   - ✅ 效能無明顯下降
   - ✅ **Live Timing 20+ 個模組全部可用**

2. **代碼品質**
   - ✅ 90% 模組採用通用架構（UniversalAnalysisMDI）
   - ✅ 10% 模組採用 Live Timing 架構（BaseLiveTimingMDI）
   - ✅ 無重複代碼
   - ✅ 無舊版本檔案殘留
   - ✅ **雙架構系統清晰分離**

3. **測試覆蓋**
   - ✅ 單元測試通過率 100%
   - ✅ 整合測試通過率 100%
   - ✅ E2E 測試通過
   - ✅ **Live Timing 專項測試通過**

4. **文檔完整**
   - ✅ 開發文檔已更新
   - ✅ API 文檔已更新
   - ✅ 遷移指南已完成
   - ✅ **Live Timing 模組文檔完整**
   - ✅ **Demo 工具使用說明完整**

5. **團隊確認**
   - ✅ Code Review 通過
   - ✅ QA 測試通過
   - ✅ 產品驗收通過

---

**最後更新**: 2025-12-15
**維護者**: F1T 開發團隊
**版本**: 1.1 ⚠️ 更新（新增 Live Timing 整合驗證）

---

## 漸進式測試 TODO List（逐步可驗證）

> **核心原則**: 每一步都是獨立可執行的小測試，確認通過後再進入下一步
> **失敗策略**: 任何一步失敗，立即停止並修復，不要繼續
> **執行順序**: 先驗證普通模組（穩定），最後才驗證 Live Timing（複雜）

### 🔄 測試分層設計

| 層級 | 執行者 | 說明 |
|------|--------|------|
| **A 層：自動化測試** | AI（Copilot） | 可用 `python -c` 或腳本獨立執行，無需 GUI |
| **B 層：無頭 GUI 測試** | AI（Copilot） | 創建 Widget 但不顯示，驗證初始化 |
| **C 層：手動 GUI 測試** | 使用者 | 需要實際操作 GUI，驗證完整功能 |

**執行策略**：AI 先完成 A+B 層確認無誤 → 使用者再執行 C 層

---

### Phase 0: 環境確認（5 分鐘）🅰️ 自動化

在開始任何重構前，確認當前環境正常運作。

#### 0.1 Python 環境
```powershell
python --version
# 預期: Python 3.10+ 
# 通過標準: 顯示版本號，無錯誤
```
- [ ] 執行通過

#### 0.2 主要依賴
```powershell
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
# 預期: PyQt5 OK
```
- [ ] 執行通過

#### 0.3 專案結構完整性
```powershell
python -c "
from pathlib import Path
required = ['modules/gui/base', 'modules/gui/rain_analysis', 'modules/gui/live_timing']
missing = [p for p in required if not Path(p).exists()]
if missing:
    print(f'MISSING: {missing}')
else:
    print('Project structure OK')
"
```
- [ ] 執行通過

**Phase 0 檢查點**: 環境正常，可以繼續。

---

### Phase 1: 基礎模組導入驗證（10 分鐘）🅰️ 自動化

#### 1.1 UniversalDataLoader 基類
```powershell
python -c "from modules.gui.base.universal_data_loader_base import UniversalDataLoader; print('UniversalDataLoader OK')"
```
- [ ] 執行通過

#### 1.2 UniversalChartWidget 基類
```powershell
python -c "from modules.gui.base.universal_chart_widget_base import UniversalChartWidgetBase; print('UniversalChartWidgetBase OK')"
```
- [ ] 執行通過

#### 1.3 UniversalAnalysisMDI 基類
```powershell
python -c "from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDIBase; print('UniversalAnalysisMDIBase OK')"
```
- [ ] 執行通過

**Phase 1 檢查點**: 基類導入正常，可以繼續。

---

### Phase 2: 普通分析模組導入驗證（15 分鐘）🅰️ 自動化

#### 2.1 批量導入測試（一次驗證所有）
```powershell
python -c "
modules = [
    ('Rain Analysis', 'modules.gui.rain_analysis', 'RainAnalysisMDI'),
    ('Speed Analysis', 'modules.gui.lap_analysis.speed_analysis', 'SpeedAnalysisMDI'),
    ('Brake Analysis', 'modules.gui.lap_analysis.brake_analysis', 'BrakeAnalysisMDI'),
    ('Tire Analysis', 'modules.gui.tire_analysis', 'TireAnalysisMDI'),
    ('Pitstop Analysis', 'modules.gui.pitstop_analysis', 'PitstopAnalysisMDI'),
    ('Accident Analysis', 'modules.gui.accident_analysis', 'AccidentAnalysisMDI'),
]
passed = 0
for name, path, cls in modules:
    try:
        exec(f'from {path} import {cls}')
        print(f'OK: {name}')
        passed += 1
    except Exception as e:
        print(f'FAIL: {name} - {e}')
print(f'Result: {passed}/{len(modules)} passed')
"
```
- [ ] 6/6 通過

**Phase 2 檢查點**: 普通模組導入正常。

---

### Phase 3: 無頭 GUI 創建測試（15 分鐘）🅱️ 無頭 GUI

> **說明**: 創建 QApplication 和 Widget，但不呼叫 show()，驗證初始化邏輯

#### 3.1 批量創建測試（無需顯示）
```powershell
python -c "
import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

modules = [
    ('Rain Analysis', 'modules.gui.rain_analysis', 'RainAnalysisMDI'),
    ('Tire Analysis', 'modules.gui.tire_analysis', 'TireAnalysisMDI'),
    ('Pitstop Analysis', 'modules.gui.pitstop_analysis', 'PitstopAnalysisMDI'),
    ('Accident Analysis', 'modules.gui.accident_analysis', 'AccidentAnalysisMDI'),
]

passed = 0
for name, path, cls in modules:
    try:
        exec(f'from {path} import {cls}')
        widget = eval(f'{cls}()')
        print(f'OK: {name} - {widget.__class__.__name__}')
        passed += 1
    except Exception as e:
        print(f'FAIL: {name} - {e}')

print(f'Result: {passed}/{len(modules)} created')
"
```
- [ ] 4/4 創建成功

#### 3.2 MDI 視窗屬性驗證
```powershell
python -c "
import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from modules.gui.rain_analysis import RainAnalysisMDI
mdi = RainAnalysisMDI()

# 驗證基本屬性
checks = [
    ('has windowTitle', hasattr(mdi, 'windowTitle') and mdi.windowTitle()),
    ('has chart_widget', hasattr(mdi, 'chart_widget')),
    ('has data_loader', hasattr(mdi, 'data_loader')),
]

for desc, result in checks:
    status = 'OK' if result else 'FAIL'
    print(f'{status}: {desc}')
"
```
- [ ] 所有屬性驗證通過

**Phase 3 檢查點**: 無頭 GUI 創建正常，AI 驗證完成。

---

### Phase 4: 全車手分析模組驗證（10 分鐘）🅰️ 自動化

#### 4.1 批量導入測試
```powershell
python -c "
modules = [
    ('All Drivers Brake', 'modules.gui.all_drivers_brake_chart', 'AllDriversBrakeChartMDI'),
    ('All Drivers Acceleration', 'modules.gui.all_drivers_acceleration_chart', 'AllDriversAccelerationChartMDI'),
    ('All Drivers Max Speed', 'modules.gui.all_drivers_max_speed_analysis', 'AllDriversMaxSpeedMDI'),
]
passed = 0
for name, path, cls in modules:
    try:
        exec(f'from {path} import {cls}')
        print(f'OK: {name}')
        passed += 1
    except Exception as e:
        print(f'FAIL: {name} - {e}')
print(f'Result: {passed}/{len(modules)} passed')
"
```
- [ ] 3/3 通過

**Phase 4 檢查點**: 全車手模組導入正常。

---

### Phase 5: 圈速與預測模組驗證（10 分鐘）🅰️ 自動化

#### 5.1 批量導入測試
```powershell
python -c "
modules = [
    ('Lap Box Plot', 'modules.gui.lap_box_plot_analysis', 'LapBoxPlotMDI'),
    ('Ideal Lap Ranking', 'modules.gui.ideal_lap_analysis.ideal_lap_ranking_table', 'IdealLapRankingMDI'),
    ('Race Prediction', 'modules.gui.race_prediction', 'RacePredictionMDI'),
]
passed = 0
for name, path, cls in modules:
    try:
        exec(f'from {path} import {cls}')
        print(f'OK: {name}')
        passed += 1
    except Exception as e:
        print(f'FAIL: {name} - {e}')
print(f'Result: {passed}/{len(modules)} passed')
"
```
- [ ] 3/3 通過

**Phase 5 檢查點**: 圈速與預測模組導入正常。

---

### Phase 6: 效能基準測試（10 分鐘）🅱️ 無頭 GUI

#### 6.1 模組載入時間
```powershell
python -c "
import sys
import time
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

modules = [
    ('Rain', 'modules.gui.rain_analysis', 'RainAnalysisMDI'),
    ('Tire', 'modules.gui.tire_analysis', 'TireAnalysisMDI'),
    ('Pitstop', 'modules.gui.pitstop_analysis', 'PitstopAnalysisMDI'),
]

for name, path, cls in modules:
    exec(f'from {path} import {cls}')
    start = time.perf_counter()
    widget = eval(f'{cls}()')
    elapsed = (time.perf_counter() - start) * 1000
    status = 'OK' if elapsed < 500 else 'SLOW'
    print(f'{name}: {elapsed:.0f}ms [{status}]')
"
```
- [ ] 每個模組載入 < 500ms

**Phase 6 檢查點**: AI 效能驗證完成。

---

### Phase 7: Live Timing 核心驗證（10 分鐘）🅰️ 自動化

> **注意**: 此階段開始驗證 Live Timing 系統

#### 7.1 模組工廠導入
```powershell
python -c "from modules.gui.live_timing import LiveTimingModuleFactory; print('Factory import OK')"
```
- [ ] 執行通過

#### 7.2 工廠單例正常
```powershell
python -c "from modules.gui.live_timing import LiveTimingModuleFactory; f1 = LiveTimingModuleFactory.get_instance(); f2 = LiveTimingModuleFactory.get_instance(); assert f1 is f2; print('Factory singleton OK')"
```
- [ ] 執行通過

#### 7.3 已實現模組數量
```powershell
python -c "from modules.gui.live_timing import LiveTimingModuleFactory; factory = LiveTimingModuleFactory.get_instance(); count = len(factory.get_implemented_modules()); print(f'Implemented modules: {count}'); assert count >= 20"
```
- [ ] 數量 >= 20

#### 7.4 DataManager 單例
```powershell
python -c "from modules.gui.live_timing import LiveTimingDataManager; dm1 = LiveTimingDataManager.get_instance(); dm2 = LiveTimingDataManager.get_instance(); assert dm1 is dm2; print('DataManager singleton OK')"
```
- [ ] 執行通過

**Phase 7 檢查點**: Live Timing 核心驗證通過。

---

### Phase 8: Live Timing 模組創建測試（15 分鐘）🅱️ 無頭 GUI

#### 8.1 批量創建測試
```powershell
python -c "
import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from modules.gui.live_timing import create_live_timing_module

modules = ['Track Map', 'Live Ranking', 'Control Panel', 'Tyre Strategy', 'Pit Window']
passed = 0

for name in modules:
    try:
        module = create_live_timing_module(name)
        if module is not None:
            print(f'OK: {name} - {module.__class__.__name__}')
            passed += 1
        else:
            print(f'FAIL: {name} - returned None')
    except Exception as e:
        print(f'FAIL: {name} - {e}')

print(f'Result: {passed}/{len(modules)} created')
"
```
- [ ] 5/5 創建成功

**Phase 8 檢查點**: Live Timing 模組創建成功。

---

### Phase 9: 數據檔案驗證（5 分鐘）🅰️ 自動化

#### 9.1 確認測試數據存在
```powershell
python -c "
from pathlib import Path
data_dir = Path('json/LiveF1/2025/Abu_Dhabi_Race')
files = ['Position.json', 'TimingData.json', 'CarData.json']

for f in files:
    path = data_dir / f
    if path.exists():
        size_mb = path.stat().st_size / 1024 / 1024
        print(f'OK: {f} ({size_mb:.1f} MB)')
    else:
        print(f'MISSING: {f}')
"
```
- [ ] 3 個數據檔案都存在

**Phase 9 檢查點**: 測試數據就緒。

---

## 🔵 以上為 AI 可獨立執行的測試（Phase 0-9）
## 🟢 以下為使用者手動 GUI 測試（Phase 10-12）

---

### Phase 10: 主 GUI 啟動測試（10 分鐘）🅲 手動 GUI

> **執行者**: 使用者
> **前提**: Phase 0-9 全部通過

#### 10.1 啟動主 GUI
```powershell
python f1t_gui_main.py
```
- [ ] GUI 正常啟動，無錯誤訊息
- [ ] 左側模組樹顯示正確
- [ ] 選單列完整

#### 10.2 選擇測試賽事
- [ ] 選擇 Year: 2025
- [ ] 選擇 Race: Abu Dhabi
- [ ] 選擇 Session: R

**Phase 10 檢查點**: 主 GUI 啟動正常。

---

### Phase 11: 普通模組功能測試（15 分鐘）🅲 手動 GUI

#### 11.1 開啟 Rain Analysis
- [ ] 從選單開啟 Rain Analysis
- [ ] 視窗正常顯示
- [ ] 無 Python 錯誤

#### 11.2 開啟 Tire Analysis
- [ ] 從選單開啟 Tire Analysis
- [ ] 輪胎策略圖表正常顯示

#### 11.3 開啟 Speed Analysis（需選車手）
- [ ] 選擇車手（如 VER）
- [ ] 開啟 Speed Analysis
- [ ] 圖表正常繪製

#### 11.4 多視窗共存
- [ ] 同時開啟 3 個以上分析視窗
- [ ] 視窗可自由拖曳、縮放
- [ ] 互不干擾

**Phase 11 檢查點**: 普通模組功能正常。

---

### Phase 12: Live Timing 完整測試（15 分鐘）🅲 手動 GUI

#### 12.1 開啟 Live Timing Control Panel
- [ ] 從選單開啟 Control Panel
- [ ] 視窗正常顯示

#### 12.2 載入測試賽事
- [ ] 選擇 2025 Abu Dhabi Race
- [ ] 點擊 Load 載入成功
- [ ] 無錯誤訊息

#### 12.3 開啟多個 Live Timing 模組
- [ ] Track Map 顯示賽道
- [ ] Live Ranking 顯示排名
- [ ] Tyre Strategy 顯示策略

#### 12.4 時間軸控制
- [ ] Play 播放功能正常
- [ ] Pause 暫停功能正常
- [ ] 速度調整正常

#### 12.5 雙架構共存測試
- [ ] 同時開啟 Live Timing + 普通分析模組
- [ ] 互不干擾

**Phase 12 檢查點**: Live Timing 完整測試通過。

---

## 🎯 總結

### 測試分層執行

| 層級 | Phase | 執行者 | 說明 |
|------|-------|--------|------|
| 🅰️ 自動化 | 0, 1, 2, 4, 5, 7, 9 | AI (Copilot) | `python -c` 命令，無需 GUI |
| 🅱️ 無頭 GUI | 3, 6, 8 | AI (Copilot) | 創建 Widget 但不顯示 |
| 🅲 手動 GUI | 10, 11, 12 | 使用者 | 實際操作完整 GUI |

### 執行順序

```
AI 執行 Phase 0-9（約 80 分鐘）
    ↓ 全部通過
使用者執行 Phase 10-12（約 40 分鐘）
    ↓ 全部通過
✅ 重構驗證完成
```

### AI 驗證完成後的狀態

完成 Phase 0-9 後，AI 已確認：
1. ✅ Python 環境和依賴正常
2. ✅ 所有基礎類別可導入
3. ✅ 所有普通模組可導入和創建
4. ✅ 所有全車手模組可導入
5. ✅ 所有圈速/預測模組可導入
6. ✅ 模組載入效能符合標準
7. ✅ Live Timing 核心系統正常
8. ✅ Live Timing 模組可創建
9. ✅ 測試數據檔案就緒

### 使用者驗證項目

Phase 10-12 驗證：
- 主 GUI 啟動和基本操作
- 普通模組實際功能（圖表、數據載入）
- Live Timing 完整功能（播放、時間軸控制）
- 雙架構共存

**如果 AI 測試失敗**：
- 停止測試，修復問題
- 從失敗的 Phase 重新開始
- 不要讓使用者測試有問題的代碼

---

**最後更新**: 2025-12-15
**維護者**: F1T 開發團隊
**版本**: 1.3 (分層測試：AI 自動化 + 使用者手動)
