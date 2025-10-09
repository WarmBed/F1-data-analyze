# 理想圈分析 GUI 模組 - 通用架構總覽

**建立日期**: 2025-10-09  
**最後更新**: 2025-10-09  
**狀態**: 📋 架構設計完成

---

## 🎯 專案概述

理想圈分析 GUI 系統由 **3 個獨立子模組** 組成，所有子模組共享相同的 **通用模組架構** (IAnalysisModule → UniversalAnalysisMDI → UniversalDataLoader → UniversalChartWidget)，確保與現有 F1T GUI 系統無縫整合。

### 子模組列表

| 模組名稱 | 顯示名稱 | 文件 | 視覺化類型 |
|---------|---------|------|-----------|
| **IdealLapRankingTable** | 🏁 Ideal Lap Ranking Table | [開發文件](./IdealLap_RankingTable_AllDrivers_開發文件.md) | QTableWidget 表格 |
| **IdealLapSectorHeatmap** | 🔥 Sector Heatmap | [開發文件](./IdealLap_SectorHeatmap_AllDrivers_開發文件.md) | Seaborn Heatmap |
| **IdealLapSectorComparison** | 📈 Sector Comparison | [開發文件](./IdealLap_SectorComparison_AllDrivers_開發文件.md) | Matplotlib 堆疊棒狀圖 |

### 共享資料來源

所有子模組使用相同的 CLI Function 53 JSON 輸出：
```
json/ideal_lap_ranking_{year}_{race}_{session}.json
```

JSON 結構：
```json
{
  "success": true,
  "analysis_result": {
    "ranking": [...],           // 車手排名資料
    "summary": {...},           // 統計摘要
    "team_analysis": {...},     // 車隊分析
    "sector_comparison": {...}  // 分段統計
  }
}
```

---

## 🏗️ 通用架構模式

### 四層架構 (Universal Module Architecture)

所有子模組遵循相同的架構分層：

```
┌──────────────────────────────────────────────────────┐
│ Layer 1: IAnalysisModule 介面層                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ • IdealLapRankingTableModule                        │
│ • IdealLapSectorHeatmapModule                       │
│ • IdealLapSectorComparisonModule                    │
│                                                      │
│ 職責: 模組註冊、參數管理、生命週期控制              │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Layer 2: UniversalAnalysisMDI 子類                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ • IdealLapRankingTableMDI                           │
│ • IdealLapSectorHeatmapMDI                          │
│ • IdealLapSectorComparisonMDI                       │
│                                                      │
│ 職責: MDI 視窗管理、UI 佈局、事件協調               │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Layer 3: UniversalDataLoader 子類                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ • IdealLapRankingTableDataLoader                    │
│ • IdealLapSectorHeatmapDataLoader                   │
│ • IdealLapSectorComparisonDataLoader                │
│                                                      │
│ 職責: 資料載入、JSON 驗證、格式轉換、API 整合      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Layer 4: UniversalChartWidget 子類                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ • IdealLapRankingTableWidget (QTableWidget)         │
│ • IdealLapSectorHeatmapWidget (Seaborn)             │
│ • IdealLapSectorComparisonWidget (Matplotlib)       │
│                                                      │
│ 職責: 資料視覺化、圖表繪製、互動事件                │
└──────────────────────────────────────────────────────┘
```

---

## 📂 檔案結構規劃

```
modules/gui/ideal_lap_analysis/
├── __init__.py
│
├── ideal_lap_options_dialog.py          # 🎬 統一選項對話框
│   └── IdealLapAnalysisOptionsDialog    # QListWidget 多選對話框
│
├── ideal_lap_ranking_table/             # 📊 排名表格模組
│   ├── __init__.py
│   ├── ideal_lap_ranking_table_module.py
│   │   └── IdealLapRankingTableModule (IAnalysisModule)
│   ├── ideal_lap_ranking_table_mdi.py
│   │   └── IdealLapRankingTableMDI (UniversalAnalysisMDI)
│   ├── ideal_lap_ranking_table_data_loader.py
│   │   └── IdealLapRankingTableDataLoader (UniversalDataLoader)
│   └── ideal_lap_ranking_table_widget.py
│       └── IdealLapRankingTableWidget (QWidget + QTableWidget)
│
├── ideal_lap_sector_heatmap/            # 🔥 分段熱力圖模組
│   ├── __init__.py
│   ├── ideal_lap_sector_heatmap_module.py
│   │   └── IdealLapSectorHeatmapModule (IAnalysisModule)
│   ├── ideal_lap_sector_heatmap_mdi.py
│   │   └── IdealLapSectorHeatmapMDI (UniversalAnalysisMDI)
│   ├── ideal_lap_sector_heatmap_data_loader.py
│   │   └── IdealLapSectorHeatmapDataLoader (UniversalDataLoader)
│   └── ideal_lap_sector_heatmap_widget.py
│       └── IdealLapSectorHeatmapWidget (UniversalChartWidget + Seaborn)
│
└── ideal_lap_sector_comparison/         # 📈 分段比較圖模組
    ├── __init__.py
    ├── ideal_lap_sector_comparison_module.py
    │   └── IdealLapSectorComparisonModule (IAnalysisModule)
    ├── ideal_lap_sector_comparison_mdi.py
    │   └── IdealLapSectorComparisonMDI (UniversalAnalysisMDI)
    ├── ideal_lap_sector_comparison_data_loader.py
    │   └── IdealLapSectorComparisonDataLoader (UniversalDataLoader)
    └── ideal_lap_sector_comparison_widget.py
        └── IdealLapSectorComparisonWidget (UniversalChartWidget + Matplotlib)
```

---

## 🎬 統一選項對話框

### IdealLapAnalysisOptionsDialog

所有理想圈分析模組的**統一入口**，允許使用者多選開啟的視圖。

**參考範例**: `modules/gui/driver_race/detailed_lap_analysis/detailed_lap_options_dialog.py`

#### 對話框結構
```python
class IdealLapAnalysisOptionsDialog(QDialog):
    """理想圈分析選項對話框"""
    
    # 分析類型常數
    TYPE_RANKING_TABLE = "ranking_table"
    TYPE_SECTOR_HEATMAP = "sector_heatmap"
    TYPE_SECTOR_COMPARISON = "sector_comparison"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏁 選擇理想圈分析類型")
        
        # QListWidget 多選清單
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        # 添加選項
        self.list_widget.addItem("📊 排名表格 (Ranking Table)")
        self.list_widget.addItem("🔥 分段熱力圖 (Sector Heatmap)")
        self.list_widget.addItem("📈 分段比較圖 (Sector Comparison)")
    
    def get_selected_types(self) -> list:
        """返回選中的分析類型清單"""
        selected_indices = [i.row() for i in self.list_widget.selectedIndexes()]
        type_map = [
            self.TYPE_RANKING_TABLE,
            self.TYPE_SECTOR_HEATMAP,
            self.TYPE_SECTOR_COMPARISON
        ]
        return [type_map[i] for i in selected_indices]
```

#### UI Mock (對話框)
```
┌────────────────────────────────────────────┐
│ 🏁 選擇理想圈分析類型                      │
├────────────────────────────────────────────┤
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ ☑ 📊 排名表格 (Ranking Table)         │ │
│ │ ☑ 🔥 分段熱力圖 (Sector Heatmap)      │ │
│ │ ☐ 📈 分段比較圖 (Sector Comparison)   │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ [全選]  [清空]                             │
│                                            │
│           [確認]      [取消]               │
└────────────────────────────────────────────┘
```

---

## 🔗 主選單整合

### f1t_gui_main.py 修改

```python
class MainWindow(QMainWindow):
    def _init_menu_bar(self):
        # ... 既有選單
        
        # ✅ 新增: Ideal Lap Analysis 選單項目
        ideal_lap_action = QAction("🏁 Ideal Lap Analysis", self)
        ideal_lap_action.triggered.connect(self._prompt_ideal_lap_options)
        analysis_menu.addAction(ideal_lap_action)
    
    def _prompt_ideal_lap_options(self):
        """顯示理想圈分析選項對話框"""
        # 1. 取得賽事參數
        year, race, session, ok = self._show_race_parameter_dialog()
        if not ok:
            return
        
        # 2. 顯示分析類型選擇對話框
        from modules.gui.ideal_lap_analysis.ideal_lap_options_dialog import IdealLapAnalysisOptionsDialog
        dialog = IdealLapAnalysisOptionsDialog(self)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_types = dialog.get_selected_types()
        if not selected_types:
            QMessageBox.warning(self, "警告", "請至少選擇一種分析類型")
            return
        
        # 3. 根據選擇創建視窗
        self._create_ideal_lap_windows(selected_types, year, race, session)
    
    def _create_ideal_lap_windows(self, types, year, race, session):
        """創建理想圈分析視窗"""
        for analysis_type in types:
            if analysis_type == "ranking_table":
                self._create_ideal_lap_ranking_window(year, race, session)
            elif analysis_type == "sector_heatmap":
                self._create_ideal_lap_heatmap_window(year, race, session)
            elif analysis_type == "sector_comparison":
                self._create_ideal_lap_comparison_window(year, race, session)
    
    def _create_ideal_lap_ranking_window(self, year, race, session):
        """創建排名表格視窗"""
        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
        
        module = IdealLapRankingTableModule(
            parent=self,
            year=year,
            race=race,
            session=session
        )
        
        # 包裝進 MDI 子視窗
        sub_window = QMdiSubWindow()
        sub_window.setWidget(module.get_widget())
        sub_window.setWindowTitle(f"Ideal_Lap_Ranking_{year}_{race}_{session}")
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
    
    def _create_ideal_lap_heatmap_window(self, year, race, session):
        """創建熱力圖視窗"""
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_module import IdealLapSectorHeatmapModule
        
        module = IdealLapSectorHeatmapModule(
            parent=self,
            year=year,
            race=race,
            session=session
        )
        
        sub_window = QMdiSubWindow()
        sub_window.setWidget(module.get_widget())
        sub_window.setWindowTitle(f"Sector_Heatmap_{year}_{race}_{session}")
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
    
    def _create_ideal_lap_comparison_window(self, year, race, session):
        """創建比較圖視窗"""
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_module import IdealLapSectorComparisonModule
        
        module = IdealLapSectorComparisonModule(
            parent=self,
            year=year,
            race=race,
            session=session
        )
        
        sub_window = QMdiSubWindow()
        sub_window.setWidget(module.get_widget())
        sub_window.setWindowTitle(f"Sector_Comparison_{year}_{race}_{session}")
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
```

---

## 🔄 資料流程統一模式

### API-ONLY 模式整合

所有資料載入器遵循相同的 API-ONLY 政策：

```python
class IdealLap{SubModule}DataLoader(UniversalDataLoader):
    """資料載入器基本模式"""
    
    CLI_FUNCTION = 53  # 共用 Function 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    def __init__(self, year, race, session, parent=None):
        super().__init__(
            cli_function=self.CLI_FUNCTION,
            json_pattern=self.JSON_PATTERN,
            parent=parent
        )
        self.year = year
        self.race = race
        self.session = session
    
    def _validate_data_format(self, data):
        """驗證 JSON 結構"""
        required_keys = ["ranking", "summary", "sector_comparison"]
        return all(k in data.get("analysis_result", {}) for k in required_keys)
    
    def _transform_data_for_display(self, data):
        """轉換資料為子模組專用格式"""
        # 每個子模組實作自己的轉換邏輯
        pass
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        ⚠️ API-ONLY 模式: 禁止 CLI 調用
        """
        self._debug("⚠️ [API-ONLY] CLI 調用已禁用")
        return False
```

### 資料載入優先級

1. **API 服務**: `refactored_api.py` POST `/analyze` (function_id=53)
2. **本地 JSON**: 讀取 `json/ideal_lap_ranking_{year}_{race}_{session}.json`
3. **錯誤處理**: 提示使用者「資料不存在，請使用 API 獲取或手動執行 CLI」

---

## 🎨 子模組視覺化差異

### 1. 排名表格 (Ranking Table)
- **元件**: QTableWidget
- **展示**: 11 欄位表格 (排名、車手、車隊、理想圈、最快圈、時間差、分段標記...)
- **互動**: 點擊「詳情」按鈕 → 開啟該車手深度分析視窗
- **特色**: 車隊顏色背景、可排序、可篩選車隊

### 2. 分段熱力圖 (Sector Heatmap)
- **元件**: Seaborn Heatmap (matplotlib backend)
- **展示**: 3 行 (S1/S2/S3) × 20 列 (車手) 矩陣
- **顏色**: 綠-黃-紅梯度 (最快→最慢)
- **標記**: ★ 標註全場最快分段
- **互動**: 懸停顯示詳細資訊、點擊單元格打開車手分段詳情

### 3. 分段比較圖 (Sector Comparison)
- **元件**: Matplotlib 水平堆疊棒狀圖
- **展示**: 每位車手兩條棒狀 (理想圈 vs 最快圈)
- **顏色**: S1 藍色、S2 綠色、S3 橙色
- **標記**: ✓/❌ 標示是否在最快圈中達成最佳分段、顯示時間差
- **互動**: 點擊棒狀打開車手詳情

---

## ✅ 開發檢查清單

### Phase 1: 對話框與選單整合
- [ ] 實作 `IdealLapAnalysisOptionsDialog`
- [ ] 在 `f1t_gui_main.py` 新增選單項目
- [ ] 實作 `_prompt_ideal_lap_options()` 方法
- [ ] 實作 `_create_ideal_lap_windows()` 多視窗創建邏輯
- [ ] 測試對話框多選功能
- [ ] 測試同時開啟多個子模組視窗

### Phase 2: 排名表格模組
- [ ] 實作 `IdealLapRankingTableModule` (IAnalysisModule)
- [ ] 實作 `IdealLapRankingTableMDI` (UniversalAnalysisMDI)
- [ ] 實作 `IdealLapRankingTableDataLoader` (UniversalDataLoader)
- [ ] 實作 `IdealLapRankingTableWidget` (QTableWidget)
- [ ] 測試表格填充與排序
- [ ] 測試車隊顏色套用
- [ ] 測試「詳情」按鈕互動

### Phase 3: 分段熱力圖模組
- [ ] 實作 `IdealLapSectorHeatmapModule` (IAnalysisModule)
- [ ] 實作 `IdealLapSectorHeatmapMDI` (UniversalAnalysisMDI)
- [ ] 實作 `IdealLapSectorHeatmapDataLoader` (UniversalDataLoader)
- [ ] 實作 `IdealLapSectorHeatmapWidget` (Seaborn Heatmap)
- [ ] 測試熱力圖繪製與顏色梯度
- [ ] 測試 ★ 標記顯示
- [ ] 測試懸停提示功能

### Phase 4: 分段比較圖模組
- [ ] 實作 `IdealLapSectorComparisonModule` (IAnalysisModule)
- [ ] 實作 `IdealLapSectorComparisonMDI` (UniversalAnalysisMDI)
- [ ] 實作 `IdealLapSectorComparisonDataLoader` (UniversalDataLoader)
- [ ] 實作 `IdealLapSectorComparisonWidget` (Matplotlib 棒狀圖)
- [ ] 測試堆疊棒狀圖繪製
- [ ] 測試 ✓/❌ 標記與時間差顯示
- [ ] 測試點擊互動

### Phase 5: 整合測試
- [ ] 測試 API 資料載入
- [ ] 測試本地 JSON 備援機制
- [ ] 測試 API-ONLY 模式錯誤處理
- [ ] 測試三個子模組同時運行無衝突
- [ ] 測試 MDI 視窗管理 (最小化、關閉、重新開啟)
- [ ] 測試資料更新與重新整理
- [ ] 效能測試 (20 車手資料渲染速度)

### Phase 6: 文件與交付
- [ ] 更新 `README.md` 添加理想圈分析功能說明
- [ ] 撰寫使用者手冊 (如何選擇子模組、如何互動)
- [ ] 撰寫開發者文件 (架構說明、擴展指南)
- [ ] 建立單元測試檔案
- [ ] 建立整合測試案例
- [ ] 程式碼審查與最佳化

---

## 🚀 開發優先級建議

### 第一階段 (核心功能)
1. **對話框** → 先實作統一入口
2. **排名表格** → 最基礎的資料展示
3. **資料載入器共用邏輯** → 確保 API-ONLY 模式正常運作

### 第二階段 (視覺化擴展)
4. **分段熱力圖** → 視覺化分析
5. **分段比較圖** → 深度對比分析

### 第三階段 (整合與優化)
6. **整合測試** → 確保三模組協同工作
7. **效能優化** → 渲染速度優化
8. **文件與測試** → 完整交付

---

## 📝 參考檔案

- **RainAnalysisModule**: `modules/gui/rain_analysis/rain_analysis_module.py`
- **DetailedLapAnalysisOptionsDialog**: `modules/gui/driver_race/detailed_lap_analysis/detailed_lap_options_dialog.py`
- **UniversalAnalysisMDI**: `modules/gui/base/universal_analysis_mdi.py`
- **UniversalDataLoader**: `modules/gui/base/universal_data_loader_base.py`
- **UniversalChartWidget**: `modules/gui/base/universal_chart_widget.py`
- **IAnalysisModule**: `modules/gui/interfaces/analysis_module.py`

---

## ⚠️ 注意事項

1. **統一資料來源**: 三個子模組共用同一個 JSON 檔案，避免重複載入
2. **API-ONLY 強制**: 所有 `_generate_data_via_cli()` 必須返回 `False`
3. **車隊顏色一致性**: 使用 FastF1 官方色票，確保三個模組顏色一致
4. **中文字體**: 確保所有圖表支援中文顯示 (Microsoft JhengHei)
5. **MDI 視窗獨立性**: 每個子模組視窗可獨立關閉/最小化，不影響其他視窗
6. **記憶體管理**: 20 車手 x 多圈資料量較大，注意記憶體釋放
7. **錯誤容錯**: 處理部分車手資料缺失的情況 (例如只有 19 車手完賽)

---

**建立者**: GitHub Copilot  
**審查狀態**: 待審查  
**下一步**: 開始實作 `IdealLapAnalysisOptionsDialog`
