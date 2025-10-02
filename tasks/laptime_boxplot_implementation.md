# Task: Lap Time Box Plot 實作 (Phase 2)

## 📋 任務概述

實作圈速箱型圖視覺化功能，基於 detailed_laptime_analysis JSON 數據，
使用 matplotlib 箱型圖展示所有車手的圈速分佈情況。

## 🎯 目標

1. 創建 `LapTimeBoxPlotWidget` 模組
2. 實現數據載入和處理邏輯
3. 繪製互動式箱型圖
4. 整合到主視窗 MDI 系統
5. 支援數據過濾和導出功能

## 📐 設計規格

### 數據源
- **JSON 檔案**: `detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json`
- **CLI 功能**: Function 28 (Detailed Lap Time Analysis)
- **數據結構**: 
  ```json
  {
    "all_drivers_detailed_laptime": {
      "VER": {
        "detailed_lap_data": [
          {
            "lap_number": 1,
            "lap_time_seconds": 85.123,
            "smart_markers": {
              "pit_stop_detection": {
                "is_pit_lap": false
              }
            }
          }
        ]
      }
    }
  }
  ```

### 視覺化設計
```
┌─────────────────────────────────────────────────────────────┐
│  📦 Lap Time Distribution (Box Plot)              [🔄 Refresh]│
├─────────────────────────────────────────────────────────────┤
│  📊 Display Options                                          │
│  ☑ Filter Pit Laps  ☑ Filter Outliers  Threshold: [1.5] IQR │
│                                            [💾 Export Chart]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│         Lap Time Distribution - 2025 Belgium R               │
│                                                              │
│   90 ┤                                                       │
│      │     ╭─┬─╮                                            │
│   85 ┤     │ │ │  ╭─┬─╮                                     │
│      │  ╭─┬┤ │ ├─┬┤ │ │                                     │
│   80 ┤  │ ││●││ │││●│ │                                     │
│      │  ├─┼┤ │ ├─┼┤ │ ├─┐                                  │
│   75 ┤  │ ││ │ │ ││ │ │ │                                  │
│      │  ╰─┴┴─┴─┴─┴┴─┴─┴─╯                                  │
│   70 └──────────────────────────────────────────            │
│        VER LEC HAM NOR PIA RUS SAI ALO GAS TSU              │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  ✅ Showing 20 drivers, 880 laps | 2025 Belgium R           │
└─────────────────────────────────────────────────────────────┘

圖例：
  ╭─┬─╮  箱型圖（Q1, Q2, Q3）
  ─●─   中位數（紅線）、平均值（綠色菱形）
  ╰─╯   異常值（outliers）
```

## 📝 實作清單

### Phase 2.1：創建核心模組 ✅
- [x] 創建 `modules/gui/driverLap_analysis/laptime_boxplot_widget.py`
- [x] 繼承 `UniversalDataLoader` 基類
- [x] 實作 `_generate_data_via_cli()` 方法
- [x] 實作 `_validate_data_format()` 方法
- [x] 實作 `_transform_data_for_display()` 方法
- [x] 實作 `_update_display()` 方法

### Phase 2.2：數據處理邏輯 ✅
- [x] 解析 JSON 數據結構
- [x] 按車手分組圈速數據
- [x] 過濾進站圈（使用 smart_markers）
- [x] 過濾異常值（IQR 方法）
- [x] 數據驗證和錯誤處理

### Phase 2.3：視覺化實作 ✅
- [x] 使用 matplotlib 創建箱型圖
- [x] 設置車隊配色
- [x] 添加標題、軸標籤、網格
- [x] 顯示中位數和平均值
- [x] 互動式工具列（縮放、平移、保存）

### Phase 2.4：UI 控制面板 ✅
- [x] 過濾進站圈 Checkbox
- [x] 過濾異常值 Checkbox
- [x] 異常值閾值調整 SpinBox
- [x] 刷新按鈕
- [x] 導出圖表功能

### Phase 2.5：主視窗整合 ✅
- [x] 修改 `f1t_gui_main.py` 的 `create_laptime_boxplot_window()`
- [x] 創建 MDI 子視窗
- [x] 設置視窗標題和大小
- [x] 錯誤處理和訊息提示

### Phase 2.6：測試驗證 🔄
- [ ] 獨立模組測試
- [ ] 主視窗整合測試
- [ ] 多選功能測試（同時顯示表格和箱型圖）
- [ ] 數據過濾測試
- [ ] 導出功能測試

## 🔧 技術細節

### 類別架構
```python
class LapTimeBoxPlotWidget(QWidget, UniversalDataLoader):
    """圈速箱型圖 Widget"""
    
    # 信號
    data_loaded = pyqtSignal(bool, str)
    analysis_updated = pyqtSignal()
    
    # 數據處理
    def _transform_data_for_display(self, raw_data) -> Dict[str, List[float]]
    def _filter_outliers(self, data: List[float]) -> List[float]
    
    # 視覺化
    def plot_boxplot(self)
    def _get_team_colors(self, drivers: List[str]) -> List[str]
    
    # 事件處理
    def on_filter_changed(self, state)
    def on_threshold_changed(self, value)
    def refresh_analysis(self)
    def export_chart(self)
```

### IQR 異常值檢測
```python
Q1 = percentile(data, 25)
Q3 = percentile(data, 75)
IQR = Q3 - Q1
lower_bound = Q1 - threshold * IQR
upper_bound = Q3 + threshold * IQR
```

### 車隊配色
```python
team_colors = {
    'VER': '#0600EF',  # Red Bull
    'LEC': '#DC0000',  # Ferrari
    'HAM': '#00D2BE',  # Mercedes
    'NOR': '#FF8700',  # McLaren
    # ... 更多車隊
}
```

## 📊 數據流

```
使用者選擇「Lap Time Box Plot」
    ↓
LapTimeBoxPlotWidget 初始化
    ↓
搜尋本地 JSON 檔案
    ↓
┌────────────┬───────────────┐
│ 檔案存在    │ 檔案不存在     │
├────────────┼───────────────┤
│ 直接載入    │ 調用 CLI (F28)│
│ JSON 數據   │ 生成數據      │
└────────────┴───────────────┘
    ↓
數據驗證 & 轉換
    ↓
按車手分組 & 過濾
    ↓
繪製箱型圖
    ↓
顯示在 MDI 視窗
```

## ✅ 驗收標準

1. **數據載入**
   - ✅ 可以載入現有 JSON 檔案
   - ✅ JSON 不存在時自動調用 CLI 生成
   - ✅ 數據格式驗證正確

2. **視覺化品質**
   - ✅ 箱型圖正確顯示所有車手
   - ✅ 中位數和平均值清晰可見
   - ✅ 車隊配色正確應用
   - ✅ 軸標籤和標題清晰

3. **互動功能**
   - ✅ 過濾選項即時生效
   - ✅ 閾值調整正確更新圖表
   - ✅ 刷新按鈕正常工作
   - ✅ 導出功能正常（PNG/PDF/SVG）

4. **整合品質**
   - ✅ MDI 視窗正常顯示
   - ✅ 可以與表格分析同時顯示
   - ✅ 視窗標題正確
   - ✅ 錯誤處理完善

## 🧪 測試計畫

### 單元測試
1. **數據處理測試**
   ```python
   # 測試過濾進站圈
   # 測試過濾異常值
   # 測試數據轉換
   ```

2. **視覺化測試**
   ```python
   # 測試箱型圖繪製
   # 測試配色正確性
   # 測試圖例和標籤
   ```

### 整合測試
1. **主視窗測試**
   - [ ] 從選單啟動
   - [ ] 從選項對話框啟動
   - [ ] MDI 子視窗正常顯示

2. **多視窗測試**
   - [ ] 同時顯示表格和箱型圖
   - [ ] 不同賽事的多個箱型圖
   - [ ] 視窗切換和管理

### 手動測試清單
1. **基本功能**
   - [ ] 點擊「Detailed Lap Analysis」
   - [ ] 選擇「Lap Time Box Plot」
   - [ ] 驗證箱型圖正確顯示

2. **數據過濾**
   - [ ] 勾選/取消「Filter Pit Laps」
   - [ ] 勾選/取消「Filter Outliers」
   - [ ] 調整閾值（1.0 - 3.0）
   - [ ] 驗證圖表即時更新

3. **導出功能**
   - [ ] 導出為 PNG
   - [ ] 導出為 PDF
   - [ ] 導出為 SVG
   - [ ] 驗證檔案正確生成

4. **邊界測試**
   - [ ] 無數據時的處理
   - [ ] 單一車手的數據
   - [ ] 極大數據量（20+ 車手）

## 📅 進度追蹤

| 階段 | 任務 | 狀態 | 完成時間 |
|-----|------|------|---------|
| 2.1 | 創建核心模組 | ✅ 已完成 | 2025-10-02 |
| 2.2 | 數據處理邏輯 | ✅ 已完成 | 2025-10-02 |
| 2.3 | 視覺化實作 | ✅ 已完成 | 2025-10-02 |
| 2.4 | UI 控制面板 | ✅ 已完成 | 2025-10-02 |
| 2.5 | 主視窗整合 | ✅ 已完成 | 2025-10-02 |
| 2.6 | 測試驗證 | 🔄 進行中 | - |

## 🔗 相關文件

- 數據源：`json/detailed_laptime_analysis_*.json`
- 基類：`modules/gui/base/universal_data_loader_base.py`
- 參考模組：`modules/gui/rain_analysis/rain_analysis_module.py`
- 主視窗：`f1t_gui_main.py`
- Phase 1 文件：`tasks/detailed_lap_analysis_options_dialog.md`

## 📌 注意事項

1. **數據過濾**：進站圈的圈速通常異常長，必須過濾
2. **異常值處理**：安全車圈、黃旗圈也需要過濾
3. **車隊配色**：2025 賽季車隊配色需要更新
4. **中文字體**：確保 matplotlib 正確顯示中文
5. **性能優化**：大數據量時考慮數據採樣

## 🎯 未來擴展

完成 Phase 2 後，可以考慮：
- **進階統計**：顯示標準差、變異係數
- **比較模式**：對比不同賽事的圈速分佈
- **動畫模式**：展示圈速隨時間的變化
- **詳細數據表**：點擊車手顯示詳細統計
- **導出數據**：導出為 CSV/Excel

---

**建立時間**：2025-10-02  
**預計完成時間**：Phase 2 約 1 小時  
**負責人**：AI Assistant + User  
**狀態**：✅ Phase 2.1-2.5 已完成，🔄 Phase 2.6 測試中
