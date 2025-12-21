# Ideal Lap Analysis Module

## 📂 模組結構

```
ideal_lap_analysis/
├── __init__.py                          # 主模組入口
├── ideal_lap_options_dialog.py         # 統一選項對話框（待實作）
│
├── ideal_lap_ranking_table/             # 📊 排名表格模組
│   ├── __init__.py
│   ├── ideal_lap_ranking_table_module.py       # IAnalysisModule 實作
│   ├── ideal_lap_ranking_table_mdi.py          # UniversalAnalysisMDI 子類
│   ├── ideal_lap_ranking_table_data_loader.py  # UniversalDataLoader 子類
│   └── ideal_lap_ranking_table_widget.py       # QTableWidget 元件
│
├── ideal_lap_sector_heatmap/            # 🔥 分段熱力圖模組
│   ├── __init__.py
│   ├── ideal_lap_sector_heatmap_module.py      # IAnalysisModule 實作
│   ├── ideal_lap_sector_heatmap_mdi.py         # UniversalAnalysisMDI 子類
│   ├── ideal_lap_sector_heatmap_data_loader.py # UniversalDataLoader 子類
│   └── ideal_lap_sector_heatmap_widget.py      # Seaborn Heatmap 元件
│
└── ideal_lap_sector_comparison/         # 📈 分段比較圖模組
    ├── __init__.py
    ├── ideal_lap_sector_comparison_module.py      # IAnalysisModule 實作
    ├── ideal_lap_sector_comparison_mdi.py         # UniversalAnalysisMDI 子類
    ├── ideal_lap_sector_comparison_data_loader.py # UniversalDataLoader 子類
    └── ideal_lap_sector_comparison_widget.py      # Matplotlib 棒狀圖元件
```

## 🎯 模組說明

### 1. Ranking Table (排名表格)
- **功能**: 顯示所有車手的理想圈排名、車手最速圈、差異與全場最速實際圈
- **視覺化**: QTableWidget 可排序表格
- **關鍵欄位**: 排名、車手、車隊、車手最速圈、理想圈、差異、全場最速實際圈、與全場最速差距、分段標記

### 2. Sector Heatmap (分段熱力圖)
- **功能**: 視覺化各車手在 S1/S2/S3 的最佳表現
- **視覺化**: Seaborn Heatmap (3 行 x 20 列矩陣)
- **特色**: 綠-黃-紅梯度、★ 標記全場最快分段

### 3. Sector Comparison (分段比較圖)
- **功能**: 理想圈 vs 最快圈的分段詳細對比
- **視覺化**: Matplotlib 水平堆疊棒狀圖
- **特色**: S1/S2/S3 顏色區分、✓/❌ 標記、時間差顯示

## 📊 共享資料來源

所有模組共用 CLI Function 53 的 JSON 輸出：
```
json/ideal_lap_ranking_{year}_{race}_{session}.json
```

## 🏗️ 架構模式

所有模組遵循通用模組四層架構：
1. **IAnalysisModule** - 介面層
2. **UniversalAnalysisMDI** - MDI 視窗層
3. **UniversalDataLoader** - 資料載入層 (CLI_FUNCTION=53)
4. **UniversalChartWidget** - 視覺化層

## 🚀 開發順序

### Phase 1: 核心基礎 ✅ 完成
- [x] 創建資料夾結構
- [x] 創建 `__init__.py` 檔案
- [x] 實作 `IdealLapAnalysisOptionsDialog` (統一對話框) ✅
- [x] 主 GUI 樹狀圖整合 ✅
- [ ] 實作 `IdealLapRankingTableModule` 系列 (排名表格) ⏳ 下一步

### Phase 2: 排名表格模組 (優先實作)
- [ ] `ideal_lap_ranking_table_module.py` - IAnalysisModule 介面實作
- [ ] `ideal_lap_ranking_table_mdi.py` - UniversalAnalysisMDI 子類
- [ ] `ideal_lap_ranking_table_data_loader.py` - UniversalDataLoader (CLI Function 53)
- [ ] `ideal_lap_ranking_table_widget.py` - QTableWidget 10 欄位表格

### Phase 2: 視覺化擴展
- [ ] 實作 `IdealLapSectorHeatmapModule` 系列 (熱力圖)
- [ ] 實作 `IdealLapSectorComparisonModule` 系列 (比較圖)

### Phase 3: 整合測試
- [ ] 主選單整合
- [ ] 測試三個模組同時運行
- [ ] API-ONLY 模式驗證

## 📝 參考文件

- 架構總覽: `docs/develop task/GUI Develop task/IdealLap_UniversalArchitecture_Overview.md`
- 排名表格: `docs/develop task/GUI Develop task/IdealLap_RankingTable_AllDrivers_開發文件.md`
- 分段熱力圖: `docs/develop task/GUI Develop task/IdealLap_SectorHeatmap_AllDrivers_開發文件.md`
- 分段比較圖: `docs/develop task/GUI Develop task/IdealLap_SectorComparison_AllDrivers_開發文件.md`

## ⚠️ 注意事項

- **API-ONLY 模式**: 所有 DataLoader 禁止 CLI 調用
- **車隊顏色一致性**: 使用 FastF1 官方色票
- **中文字體支援**: 確保所有圖表支援中文顯示
- **共享 JSON**: 三個模組讀取同一個 JSON 檔案，避免重複載入
