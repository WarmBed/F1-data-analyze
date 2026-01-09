# Monte Carlo 位置分析 - 輪胎策略配置增強

## 更新日期
2026-01-07

## 更新內容

### 新增功能
在 **策略排名** 標籤的 **Monte Carlo 位置分析** 表格中新增兩列：

1. **Stops（進站次數）**：顯示每個策略的進站次數
2. **Tire Strategy（輪胎策略）**：顯示輪胎配置序列（例如：S→M→H）

### 表格列配置

更新後的 Monte Carlo 位置分析表格包含 10 列：

| 列號 | 列名 | 寬度 | 說明 |
|------|------|------|------|
| 0 | Strategy | 自動 | 策略名稱 |
| 1 | **Stops** | 60px | **進站次數** |
| 2 | **Tire Strategy** | 自動 | **輪胎配置（例如：S→M→H）** |
| 3 | Win% | 80px | 勝率百分比 |
| 4 | Mean Time | 120px | 平均完賽時間 |
| 5 | Std Dev | 80px | 時間標準差 |
| 6 | No SC | 70px | 無 SC 情況獲勝次數 |
| 7 | With SC | 70px | 有 SC 情況獲勝次數 |
| 8 | Pos. Gain | 90px | 預期位置提升 |
| 9 | Risk | 90px | 風險評估 |

### 技術實現

#### 修改檔案
- `strategy_simulator/gui/results_tabs/strategy_comparison.py`

#### 主要變更

1. **表格結構更新**
```python
self.mc_table.setColumnCount(10)  # 從 8 增加到 10
```

2. **列標題更新**
```python
self.mc_table.setHorizontalHeaderLabels([
    tr("STRATEGY", "Strategy"),
    tr("STOPS", "Stops"),              # 新增
    tr("TIRE_STRATEGY", "Tire Strategy"),  # 新增
    tr("WIN_PCT", "Win%"), 
    # ... 其他列
])
```

3. **數據填充邏輯**
```python
# 從結果中獲取輪胎策略配置
tire_notation = ""
num_stops = 0
if self._results:
    matching_result = next((r for r in self._results if r.strategy_name == name), None)
    if matching_result:
        tire_notation = matching_result.get_stint_notation()  # "S→M→H"
        num_stops = matching_result.num_stops  # 2
```

4. **列寬度優化**
```python
mc_header.setSectionResizeMode(0, QHeaderView.Stretch)  # Strategy
mc_header.setSectionResizeMode(1, QHeaderView.Fixed)    # Stops
mc_header.setSectionResizeMode(2, QHeaderView.Stretch)  # Tire Strategy
# ... 其他固定寬度列
```

### 視覺效果

#### 輪胎策略標記範例
- **2 停策略**：`S→M→H`（軟胎 → 中性胎 → 硬胎）
- **2 停策略**：`M→M→H`（中性胎 → 中性胎 → 硬胎）
- **1 停策略**：`M→H`（中性胎 → 硬胎）

#### 字體樣式
- **策略名稱**：Arial, 10pt, Bold
- **輪胎策略**：Consolas, 10pt, Bold（等寬字體，方便對齊）

### Tooltip 提示

新列的 Tooltip：
- **Stops**：Number of pit stops（進站次數）
- **Tire Strategy**：Tire compound sequence (e.g., S→M→H)（輪胎配置序列）

### 測試驗證

#### 測試檔案
- `test_mc_logic.py` - 非 GUI 邏輯測試
- `test_mc_tire_strategy.py` - GUI 視覺測試

#### 測試結果
```
✅ 輪胎標記生成正確（例如：S→M→H）
✅ 進站次數計算正確
✅ Monte Carlo 數據結構完整
✅ 結果與 MC 數據可正確整合
```

### 使用方式

1. 執行模擬器並進行策略分析
2. 啟用 Monte Carlo 模擬
3. 切換到 **策略排名** 標籤
4. 查看 **Monte Carlo 位置分析** 表格
5. 新的 **Stops** 和 **Tire Strategy** 列將自動顯示

### 優點

1. **一目了然**：直接在 Monte Carlo 結果中看到輪胎策略配置
2. **快速比較**：無需切換標籤即可比較不同策略的輪胎選擇
3. **完整資訊**：結合勝率、時間、風險與輪胎配置的完整視圖
4. **視覺清晰**：使用等寬字體和箭頭符號，配置一目了然

### 未來改進建議

1. **顏色編碼**：為不同輪胎配置添加背景顏色
   - 軟胎：紅色背景
   - 中性胎：黃色背景
   - 硬胎：白色背景

2. **進站時機**：添加進站圈數顯示（例如：L15, L35）

3. **輪胎年限**：如果有輪胎衰減數據，可顯示預計輪胎壽命

4. **互動功能**：點擊輪胎策略列可跳轉到詳細的 stint 分析

### 相關文件
- `strategy_simulator/core/lap_simulator.py` - StrategySimulationResult 類別
- `strategy_simulator/core/monte_carlo.py` - MonteCarloSummary 類別
- `strategy_simulator/gui/results_tabs/strategy_comparison.py` - 策略比較標籤

### 開發者備註
- 確保 `self._results` 在 `update_monte_carlo()` 被調用前已設置
- 輪胎標記使用 `get_stint_notation()` 方法生成
- 進站次數通過 `num_stops` 屬性獲取（= len(stints) - 1）
