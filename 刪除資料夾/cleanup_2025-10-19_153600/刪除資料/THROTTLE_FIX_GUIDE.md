# Throttle Line Chart 快速修復指令

## 狀況總結

所有代碼已完成，但因繼承架構需求，需要實現兩個抽象方法才能運行。

## 問題核心

`ThrottleLineChartMDI` 繼承自 `UniversalAnalysisMDI`，必須實現:
- `create_data_manager()` - 創建數據管理器
- `create_chart_widget()` - 創建圖表組件

## 快速修復方案

### 修改 `throttle_line_chart_mdi.py`

在類中添加這兩個方法:

```python
def create_data_manager(self):
    """創建數據管理器（必須實現的抽象方法）"""
    self._loader = ThrottleLineChartDataLoader(parent=self)
    
    # 連接數據載入器的信號
    self._loader.data_loaded.connect(self._on_data_loaded)
    self._loader.load_error.connect(self._on_data_error)
    
    return self._loader

def create_chart_widget(self):
    """創建圖表組件（必須實現的抽象方法）"""
    # 創建 splitter 容器
    self._main_splitter = QSplitter(Qt.Vertical)
    
    # 創建兩個圖表
    self._throttle_chart = ThrottleDurationChartWidget()
    self._lap_time_chart = LapTimeChartWidget()
    
    # 添加到 splitter
    self._main_splitter.addWidget(self._throttle_chart)
    self._main_splitter.addWidget(self._lap_time_chart)
    
    # 設置初始比例
    self._main_splitter.setSizes([450, 450])
    
    # 連接同步信號
    self._connect_sync_signals()
    
    return self._main_splitter
```

### 同時添加信號處理方法

```python
def _on_data_loaded(self, data: Dict):
    """數據載入完成處理"""
    self._debug("數據載入完成")
    # 更新圖表
    if self._throttle_chart and self._lap_time_chart:
        laps_df = self._loader.get_laps_dataframe()
        if laps_df is not None:
            self._throttle_chart.plot_data(laps_df, self._loader.get_stint_ranges())
            self._lap_time_chart.plot_data(laps_df, self._loader.get_stint_ranges())

def _on_data_error(self, error_msg: str):
    """數據載入錯誤處理"""
    self._error(f"數據載入失敗: {error_msg}")
    QMessageBox.warning(self, "載入錯誤", f"無法載入數據:\n{error_msg}")
```

## 測試步驟

1. 修改完成後執行:
   ```powershell
   python test_throttle_imports.py
   ```

2. 如果通過，啟動 GUI:
   ```powershell
   python f1t_gui_main.py
   ```

3. 測試功能:
   - 選擇賽事 (2025 Australia R)
   - 點擊「油門分析」→「Throttle Line Chart」
   - 選擇車手
   - 點擊「載入數據並顯示圖表」

## 預期結果

✅ 應該看到兩個同步的圖表窗口:
- 上方: 全油門秒數折線圖
- 下方: 圈速折線圖

兩個窗口應該:
- 同步縮放/平移
- 同步 hover 高亮
- 顯示詳細 tooltip
- 支援導出功能

## 如果仍有問題

檢查 `_init_ui()` 方法是否與基類衝突:
- 基類會自動調用 `create_chart_widget()`
- 不需要在 `_init_ui()` 中手動創建圖表
- 只保留控制組件（車手選擇下拉框等）

## 備選方案

如果架構整合太複雜，可以:
1. 將 `ThrottleLineChartMDI` 改為繼承 `QWidget` 而非 `UniversalAnalysisMDI`
2. 自行實現所有邏輯
3. 失去基類的自動化功能，但完全自主控制

祝調試順利！🚀
