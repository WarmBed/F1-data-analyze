# 性能監控工具使用指南

## 🎯 問題分析

你遇到的 "QThread: Destroyed while thread is still running" 和 "未檢測到已載入的賽事" 是因為：

1. **跨進程隔離**：`realtime_monitor.py` 在獨立進程中無法訪問 GUI 的 DataManager 單例
2. **QApplication 衝突**：兩個進程各有自己的 QApplication 實例

## ✅ 解決方案

我已經創建了 **GUI 內嵌性能監控**，直接在 GUI 內部運行。

---

## 📊 使用方式

### 方法 1: 從 GUI 選單啟動（最簡單）

1. **啟動 GUI 並載入賽事**：
   ```powershell
   python f1t_gui_main.py
   ```

2. **載入 Abu Dhabi 2025 並開始播放**：
   - 打開 Live Timing Control
   - 選擇 2025 Abu Dhabi Race
   - 點擊 Load 按鈕
   - 點擊播放 ▶️

3. **打開性能監控**：
   - 選單：Tools → 📊 Performance Monitor
   - 會自動注入監控並顯示即時統計

---

### 方法 2: Python 控制台（進階用戶）

如果你想在運行時手動啟動監控：

```python
# 在 GUI 運行時，在 Python 控制台執行：
from performance_monitor_widget import show_monitor
show_monitor()
```

---

## 📈 監控視窗功能

監控視窗會顯示：

### 📊 快照處理統計
- 總快照數
- 平均耗時
- 最大/最小耗時
- 最近 10 次平均
- 估算 FPS

### 🔍 函數執行耗時（前 15 名）
每個函數顯示：
- 平均耗時
- 最大/最小耗時
- 最近 10 次平均
- 調用次數
- 慢更新率

### 性能狀態指示
- 🔴 嚴重阻塞 (>100ms)
- 🟡 輕微阻塞 (>50ms)
- 🟢 性能尚可 (>20ms)
- ✅ 性能良好 (<20ms)

### 控制按鈕
- **重置統計**：清除所有統計數據重新開始
- **暫停更新**：暫停視窗刷新（監控仍在進行）

---

## 🎯 完整性能分析方案

### 方案 A: GUI 內嵌監控（即時監控）

**適合場景**：
- ✅ 想看即時 FPS 和性能狀況
- ✅ 想知道哪個模組正在卡住
- ✅ 播放時即時監控

**使用方式**：
```
GUI 選單 → Tools → Performance Monitor
```

---

### 方案 B: 完整性能剖析（深度分析）

**適合場景**：
- ✅ 想要完整的函數調用統計
- ✅ 想生成 snakeviz 視覺化
- ✅ 想找出最根本的瓶頸

**使用方式**：
```powershell
python advanced_profiler.py
```

**特點**：
- 自動載入 Abu Dhabi 2025
- 播放 120 秒完整分析
- 生成 3 種報告
- 可用 snakeviz 視覺化

---

## 💡 建議的診斷流程

### 第一步：GUI 內嵌監控（現在就可以用）

1. 啟動 GUI: `python f1t_gui_main.py`
2. 載入 Abu Dhabi 2025 並播放
3. 選單：Tools → Performance Monitor
4. 觀察：
   - FPS 是否穩定在 20?
   - 哪些函數耗時最長?
   - 是否有慢更新警告?

### 第二步：完整剖析（如果需要更詳細）

```powershell
python advanced_profiler.py
```

查看：
- `live_timing_performance_report.txt`
- `snakeviz live_timing_performance.prof`

---

## 🚀 立即開始

**現在就試試 GUI 內嵌監控：**

1. 確保 GUI 正在運行並已載入賽事
2. 選單：Tools → 📊 Performance Monitor
3. 開始播放並觀察即時性能

**預期效果：**
- 每 2 秒更新一次統計
- 即時顯示 FPS 和耗時
- 自動標記慢函數
- 提供優化建議

---

## ⚠️ 故障排除

**如果顯示 "DataManager 尚未初始化"**：
- 確認 Live Timing Control 已打開
- 確認已點擊 Load 按鈕載入賽事

**如果顯示 "未載入賽事"**：
- 確認賽事已成功載入
- 確認有 "Loaded" 狀態顯示

**如果視窗無法打開**：
- 查看終端錯誤訊息
- 確認 `performance_monitor_widget.py` 存在
