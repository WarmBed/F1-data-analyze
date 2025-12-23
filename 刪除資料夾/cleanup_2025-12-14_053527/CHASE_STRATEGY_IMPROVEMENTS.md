# Chase Strategy 改進完成摘要

## ✅ 已完成的改進

### 1. **移除策略 5 詳情區域**
- ❌ 移除 `detail_widget` 及其相關的 3 個子標籤
- ❌ 移除 `scenario1_label`, `scenario2_label`, `scenario3_label`
- ❌ 移除 `_toggle_detail_widget()` 方法
- ✅ 表格下方空白區域已清除，只保留策略 5 主行

### 2. **表格寬度自動調整**
- ✅ 最後一欄 "Advantage" 現在會根據視窗寬度自動調整
- ✅ `setStretchLastSection(True)` 已啟用
- ✅ 移除固定寬度 `setColumnWidth(4, 100)`
- ✅ 不會蓋住按鈕（Refresh 按鈕已隱藏）

### 3. **隱藏 Refresh 按鈕**
- ✅ `refresh_btn.hide()` 已添加
- ✅ 按鈕功能仍保留，只是視覺上隱藏
- ✅ 自動刷新機制運作正常（車手選擇改變時觸發）

### 4. **右鍵選單顯示 Gap 曲線圖**
#### 4.1 右鍵選單
- ✅ 舊的 `_show_table_context_menu` 已替換為 `_show_strategy_chart_menu`
- ✅ 點擊任何策略行即可顯示 "Show Gap Evolution Chart"

#### 4.2 Gap 曲線圖功能
- ✅ 為每個策略生成 Gap 演變曲線
- ✅ 顯示 4 條曲線：
  - **綠色實線 (o--)**: P2 當前實際 Gap (過去數據)
  - **藍色實線 (o--)**: P1 當前實際 Gap (過去數據，始終為 0)
  - **黃色虛線 (--)**: P2 預估未來 Gap
  - **橙色虛線 (--)**: P1 預估未來 Gap
- ✅ 標記：
  - **紅色虛線**: 當前圈數
  - **綠色虛線**: 追上圈數（如有）

#### 4.3 不同策略的曲線邏輯
1. **策略 1 (繼續當前輪胎)**:
   - P2 Gap 逐漸縮小（-0.1s/圈）
   - P1 保持領先（Gap = 0）

2. **策略 2 (立即進站 Undercut)**:
   - 進站時 Gap 擴大 +20s
   - 之後快速縮小（-0.3s/圈）

3. **策略 3 (等待安全車)**:
   - 假設 5 圈後 SC 出現
   - SC 前緩慢縮小（-0.05s/圈）
   - SC 後 Gap 降至 5s，再快速縮小（-0.2s/圈）

4. **策略 4 (主動模擬)**:
   - 根據使用者設定的進站圈數
   - 進站前緩慢縮小
   - 進站後先擴大再快速縮小

5. **策略 5 (P1 先進站)**:
   - **P1 曲線變化**: 進站後暫時落後（-20s），再逐漸追回
   - **P2 曲線變化**: 保持領先，緩慢增加 Gap

## 📊 新增數據結構

```python
# ChaseStrategyWidget 新增變數
self._current_results: List[StrategyResult] = []  # 當前策略計算結果
self._current_lap: int = 0                         # 當前圈數
self._current_gap: float = 0.0                     # 當前 Gap
self._p1_tla: str = ""                             # P1 車手代碼
self._p2_tla: str = ""                             # P2 車手代碼
```

## 🎨 視覺效果

### 圖表樣式
- **背景色**: #1a1a1a (深色主題)
- **軸線顏色**: #444444
- **文字顏色**: #E0E0E0
- **網格**: 半透明 (#444444, alpha=0.2)
- **圖例**: 深色背景 (#2a2a2a)

### 曲線顏色
- P2 實際: `#00FF00` (綠色)
- P1 實際: `#3671C6` (藍色)
- P2 預估: `#FFCC00` (黃色)
- P1 預估: `#FF8000` (橙色)
- 當前圈標記: `#FF3333` (紅色)
- 追上圈標記: `#00FF00` (綠色)

## 🔧 技術細節

### 導入的新套件
```python
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
```

### 中文字體設定
```python
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

### 新增方法
1. `_show_strategy_chart_menu(pos)`: 右鍵選單處理
2. `_show_gap_chart(strategy)`: 彈出圖表對話框
3. `_plot_gap_evolution(ax, strategy)`: 繪製曲線邏輯

## ✅ 測試驗證結果

```
✅ 模組導入正常
✅ 繪圖方法已添加 (_show_strategy_chart_menu, _show_gap_chart, _plot_gap_evolution)
✅ 變數結構完整 (_current_results, _current_lap, _current_gap, _p1_tla, _p2_tla)
✅ matplotlib 環境就緒
```

## 📝 使用方式

1. **啟動 Live Timing**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Chase Strategy**
   - Live Timing → Chase Strategy

3. **查看 Gap 曲線**
   - 在策略表格的任一行上**右鍵點擊**
   - 選擇 "Show Gap Evolution Chart"
   - 查看該策略的 Gap 演變預估

## 🎯 改進對照

### Before (改進前)
- ❌ 策略 5 有龐大的詳情區域（3 個子標籤）
- ❌ Refresh 按鈕佔用空間
- ❌ Advantage 欄位固定寬度，視窗縮放時可能蓋住按鈕
- ❌ 無法視覺化 Gap 變化趨勢

### After (改進後)
- ✅ 表格簡潔，只顯示 5 個策略行
- ✅ Refresh 按鈕隱藏，自動刷新
- ✅ Advantage 欄位自動調整寬度
- ✅ 右鍵可查看每個策略的 Gap 曲線圖（4 條曲線 + 標記）

## 🚀 後續可能改進

1. **歷史數據整合**: 使用真實的過去 Gap 數據（而非線性假設）
2. **更精確的預估**: 根據輪胎衰退率、賽道特性調整預估參數
3. **可調整參數**: 讓使用者調整進站損失時間、Gap 縮小速率等
4. **多策略比較**: 在同一圖表中顯示多個策略的 Gap 曲線
5. **導出功能**: 將圖表保存為 PNG/PDF 檔案

---

**完成時間**: 2025-12-08  
**版本**: Chase Strategy v2.0 (Gap Chart Edition)
