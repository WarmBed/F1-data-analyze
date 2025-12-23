# F1T GUI 性能分析完整指南

## 🎯 概述

本指南提供完整的 F1T GUI 性能分析流程，特別針對 **Live timing 模組大量開啟** 時的性能瓶頸分析。

## 📦 工具安裝

### 1. 必要工具

```powershell
# 安裝 snakeviz（用於視覺化 cProfile 結果）
pip install snakeviz

# 安裝 py-spy（低開銷的即時性能採樣）
pip install py-spy

# 安裝 matplotlib（用於生成對比圖表）
pip install matplotlib
```

### 2. 驗證安裝

```powershell
# 驗證 snakeviz
python -m snakeviz --version

# 驗證 py-spy
py-spy --version

# 驗證 matplotlib
python -c "import matplotlib; print(matplotlib.__version__)"
```

## 🔧 可用工具

### 工具 1: `profile_gui.py` - cProfile 深度分析

**特點：**
- 精確的函數級別分析
- 自動啟動 SnakeViz 視覺化
- 生成詳細的文字報告
- 支援三種分析模式

**使用場景：**
- 需要精確的函數調用統計
- 分析啟動速度
- 找出具體的性能瓶頸函數

**模式說明：**

#### 模式 1: 啟動速度分析
```powershell
python tools/profile_gui.py --mode startup
```
- 分析 GUI 初始化過程
- 識別啟動階段的慢函數
- 輸出：`.prof` + `.txt` + SnakeViz 火焰圖

#### 模式 2: 運行時分析
```powershell
python tools/profile_gui.py --mode runtime --duration 30
```
- 分析 30 秒的運行時性能
- 需要手動操作 GUI（打開選單、分析模組等）
- 適合分析用戶交互場景

#### 模式 3: Live timing 壓力測試
```powershell
python tools/profile_gui.py --mode live --windows 8
```
- 自動開啟 8 個 Live timing 視窗
- 專門分析多視窗場景的性能
- **推薦用於 Live timing 性能分析**

---

### 工具 2: `profile_gui_pyspy.py` - py-spy 即時監控

**特點：**
- 極低開銷（< 1% CPU）
- 無需修改代碼
- 生成火焰圖和 speedscope 格式
- 可附加到正在運行的進程

**使用場景：**
- 需要即時監控性能
- 長時間運行的性能分析
- 對比優化前後的性能

**模式說明：**

#### 模式 1: 記錄並生成火焰圖
```powershell
# SVG 格式（瀏覽器查看）
python tools/profile_gui_pyspy.py --mode record --duration 60

# speedscope 格式（上傳 speedscope.app）
python tools/profile_gui_pyspy.py --mode record --duration 60 --format speedscope
```

#### 模式 2: 即時監控（類似 top）
```powershell
python tools/profile_gui_pyspy.py --mode top
```
- 即時顯示函數 CPU 使用率
- 按 Ctrl+C 停止

#### 模式 3: Live timing 壓力測試
```powershell
python tools/profile_gui_pyspy.py --mode live --windows 10 --duration 45
```
- 自動開啟 10 個 Live timing 視窗
- 記錄 45 秒的性能數據

---

### 工具 3: `compare_performance.py` - 性能對比分析

**特點：**
- 對比多個性能分析結果
- 生成視覺化對比圖表
- HTML 互動式報告
- 識別性能變化趨勢

**使用場景：**
- 對比不同數量視窗的性能影響
- 對比優化前後的效果
- 生成性能報告

**使用範例：**

```powershell
# 步驟 1: 生成多個性能檔案（不同視窗數量）
python tools/profile_gui.py --mode live --windows 2
python tools/profile_gui.py --mode live --windows 5
python tools/profile_gui.py --mode live --windows 10

# 步驟 2: 對比分析
python tools/compare_performance.py `
    --files reports/profiling/gui_live_timing_stress_20251210_143022.prof `
            reports/profiling/gui_live_timing_stress_20251210_143145.prof `
            reports/profiling/gui_live_timing_stress_20251210_143308.prof `
    --labels "2個視窗" "5個視窗" "10個視窗"
```

## 📊 分析流程範例

### 場景 1: 分析 Live timing 大量開啟的性能瓶頸

#### 步驟 1: 收集基準數據
```powershell
# 測試不同數量的視窗
python tools/profile_gui.py --mode live --windows 1
python tools/profile_gui.py --mode live --windows 3
python tools/profile_gui.py --mode live --windows 5
python tools/profile_gui.py --mode live --windows 8
python tools/profile_gui.py --mode live --windows 10
```

#### 步驟 2: 查看個別結果
- SnakeViz 會自動在瀏覽器中開啟
- 檢查 `reports/profiling/*.txt` 文字報告
- 找出最慢的前 20 個函數

#### 步驟 3: 對比分析
```powershell
python tools/compare_performance.py `
    --files reports/profiling/gui_live_timing_stress_*.prof `
    --labels "1視窗" "3視窗" "5視窗" "8視窗" "10視窗"
```

#### 步驟 4: 分析結果
- 查看 `comparison_report_*.txt` 文字報告
- 查看 `comparison_charts_*.png` 圖表
- 查看 `comparison_report_*.html` 互動式報告

---

### 場景 2: 使用 py-spy 進行低開銷長時間監控

```powershell
# 記錄 2 分鐘的運行數據
python tools/profile_gui_pyspy.py --mode record --duration 120

# 或使用 speedscope 格式（可上傳 speedscope.app 查看）
python tools/profile_gui_pyspy.py --mode record --duration 120 --format speedscope
```

---

### 場景 3: 對比優化前後的性能

```powershell
# 優化前
python tools/profile_gui.py --mode live --windows 10
# 保存結果: gui_live_timing_stress_before.prof

# 進行優化（修改代碼）

# 優化後
python tools/profile_gui.py --mode live --windows 10
# 保存結果: gui_live_timing_stress_after.prof

# 對比分析
python tools/compare_performance.py `
    --files gui_live_timing_stress_before.prof gui_live_timing_stress_after.prof `
    --labels "優化前" "優化後"
```

## 🔍 如何閱讀性能分析結果

### cProfile 輸出解讀

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
100     0.500    0.005    2.000    0.020   module.py:42(slow_function)
```

- **ncalls**: 調用次數
- **tottime**: 總時間（不含子函數）
- **percall**: 平均時間/調用（tottime/ncalls）
- **cumtime**: 累計時間（含子函數）⭐ **最重要的指標**
- **percall**: 平均累計時間/調用

**優化策略：**
1. 優先優化 **cumtime 最大** 的函數
2. 如果 **ncalls 很大**，考慮減少調用次數
3. 如果 **tottime 很大**，優化函數內部邏輯

---

### SnakeViz 火焰圖解讀

火焰圖（Flamegraph）說明：
- **X 軸（寬度）**: 函數佔用的 CPU 時間比例
- **Y 軸（高度）**: 調用棧深度（底部是根函數）
- **顏色**: 隨機，無特殊意義
- **可點擊**: 點擊任何區塊可放大查看

**分析技巧：**
1. 找出最寬的區塊（佔用時間最多）
2. 查看調用棧深度（是否有過度遞迴）
3. 關注 Live timing 相關的函數

---

### py-spy 火焰圖解讀

與 SnakeViz 類似，但：
- 採樣頻率更低（每秒 100 次）
- 開銷更小（適合生產環境）
- 可以附加到正在運行的進程

**Speedscope 格式：**
- 上傳到 https://www.speedscope.app/
- 提供時間軸視圖（Timeline）
- 可以看到性能隨時間的變化

## 🎯 常見性能瓶頸

### 1. PyQt5 事件循環
**症狀**: `QApplication.exec_()` 佔用大量時間  
**原因**: 大量事件處理、重繪、信號槽  
**優化**:
- 減少不必要的 `update()` 調用
- 使用 `QTimer.singleShot()` 延遲更新
- 批次處理多個更新

### 2. Matplotlib 繪圖
**症狀**: `plt.plot()`, `plt.draw()` 很慢  
**原因**: Matplotlib 渲染開銷大  
**優化**:
- 使用 `blit` 模式（局部更新）
- 減少繪圖點數（數據抽樣）
- 使用 `FigureCanvasQTAgg` 的緩存

### 3. 數據載入
**症狀**: `json.load()`, `pickle.load()` 很慢  
**原因**: 檔案 I/O、反序列化  
**優化**:
- 使用異步載入（QThread）
- 實現數據緩存
- 壓縮 JSON 檔案（使用 gzip）

### 4. Live timing 更新
**症狀**: 大量 `update_*()` 函數調用  
**原因**: 頻繁的 UI 更新  
**優化**:
- 限制更新頻率（debounce）
- 只更新可見的視窗
- 使用虛擬化列表（QListView）

## 📈 性能優化檢查清單

### 啟動階段
- [ ] 延遲載入非必要模組
- [ ] 使用 `import` 而非 `from ... import *`
- [ ] 減少全局變數初始化
- [ ] 延遲創建 GUI 組件

### 運行階段
- [ ] 限制 UI 更新頻率（< 30 FPS）
- [ ] 使用異步操作（QThread, asyncio）
- [ ] 實現數據緩存
- [ ] 減少不必要的重繪

### Live timing 模組
- [ ] 只更新可見視窗
- [ ] 實現虛擬化列表
- [ ] 批次處理多個更新
- [ ] 使用高效的數據結構（dict, set）

### 記憶體管理
- [ ] 及時釋放不用的對象
- [ ] 避免循環引用
- [ ] 使用 `weakref`
- [ ] 實現對象池

## 🛠️ 進階技巧

### 1. 生成性能基準報告

```powershell
# 創建基準測試腳本
$tests = @(
    @{windows=1; label="1視窗"},
    @{windows=2; label="2視窗"},
    @{windows=4; label="4視窗"},
    @{windows=6; label="6視窗"},
    @{windows=8; label="8視窗"},
    @{windows=10; label="10視窗"}
)

foreach ($test in $tests) {
    Write-Host "測試: $($test.label)"
    python tools/profile_gui.py --mode live --windows $($test.windows)
    Start-Sleep -Seconds 5
}

# 對比所有結果
python tools/compare_performance.py `
    --files (Get-ChildItem reports/profiling/gui_live_timing_stress_*.prof | Select-Object -Last 6).FullName `
    --labels "1視窗" "2視窗" "4視窗" "6視窗" "8視窗" "10視窗"
```

### 2. 持續性能監控

```powershell
# 在後台運行 py-spy top
Start-Process python -ArgumentList "tools/profile_gui_pyspy.py --mode top" -NoNewWindow
```

### 3. 整合到 CI/CD

```yaml
# .github/workflows/performance.yml
name: Performance Benchmarks

on:
  push:
    branches: [ main ]

jobs:
  benchmark:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run performance tests
        run: |
          python tools/profile_gui.py --mode startup
          python tools/profile_gui.py --mode live --windows 5
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-reports
          path: reports/profiling/
```

## 📚 參考資源

- [cProfile 官方文檔](https://docs.python.org/3/library/profile.html)
- [SnakeViz 使用指南](https://jiffyclub.github.io/snakeviz/)
- [py-spy GitHub](https://github.com/benfred/py-spy)
- [Speedscope 火焰圖查看器](https://www.speedscope.app/)
- [Python 性能優化指南](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)

## 🤝 貢獻

如果你發現新的性能瓶頸或優化方案，請：
1. 使用這些工具進行分析
2. 記錄優化前後的性能數據
3. 提交 Pull Request 並附上對比報告

## 📝 更新日誌

- **2025-12-10**: 初版發布
  - 添加 `profile_gui.py` (cProfile)
  - 添加 `profile_gui_pyspy.py` (py-spy)
  - 添加 `compare_performance.py` (對比分析)
