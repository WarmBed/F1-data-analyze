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
1. **統一架構**: 100% 模組採用 UniversalAnalysisMDI 通用架構
2. **清晰組織**: 按功能類型重新組織資料夾結構
3. **消除重複**: 移除所有重複和廢棄代碼
4. **提升維護性**: 降低 40% 維護成本，提升 50% 開發效率

### 成功指標
- ✅ 資料夾層級減少：從平均 4 層 → 3 層
- ✅ 模組數量優化：從 43 個 → 35 個（整合重複）
- ✅ 代碼行數減少：~25%
- ✅ 導入路徑一致性：100%
- ✅ 所有功能測試通過：100%

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
├── 📁 live_timing/                    # ✅ 即時系統（保持）
│   ├── core/
│   ├── widgets/
│   └── live_timing_modules/
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

## ⚠️ 風險管理

### 高風險項目

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|---------|
| 導入路徑遺漏 | 高 | 中 | 使用自動化腳本 + 手動檢查 |
| 模組功能回歸 | 高 | 中 | 完整的測試套件 |
| 整合後效能下降 | 中 | 低 | 效能基準測試 |
| Git 合併衝突 | 中 | 高 | 使用專用分支，小步提交 |
| 用戶介面變更 | 低 | 中 | 保持 UI 一致性 |

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

**端對端測試**:
- [ ] 完整用戶流程可以執行
- [ ] 真實數據載入和顯示
- [ ] 所有功能按鈕正常工作

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
| **發布** | **Day 20** | ⬜ |

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

### 工具腳本
- `scripts/cleanup_gui_modules.py` - 清理腳本
- `scripts/update_imports.py` - 導入更新腳本（待建立）
- `scripts/generate_refactor_report.py` - 報告生成腳本（待建立）

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

2. **代碼品質**
   - ✅ 100% 模組採用通用架構
   - ✅ 無重複代碼
   - ✅ 無舊版本檔案殘留

3. **測試覆蓋**
   - ✅ 單元測試通過率 100%
   - ✅ 整合測試通過率 100%
   - ✅ E2E 測試通過

4. **文檔完整**
   - ✅ 開發文檔已更新
   - ✅ API 文檔已更新
   - ✅ 遷移指南已完成

5. **團隊確認**
   - ✅ Code Review 通過
   - ✅ QA 測試通過
   - ✅ 產品驗收通過

---

**最後更新**: 2025-12-15
**維護者**: F1T 開發團隊
**版本**: 1.0
