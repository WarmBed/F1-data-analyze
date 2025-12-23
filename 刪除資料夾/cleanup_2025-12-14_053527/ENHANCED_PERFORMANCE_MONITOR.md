# 增強版性能監控使用指南

## 🎯 新功能

現在性能監控會追蹤：

### 1. DataManager 主循環
- `DataManager._on_playback_tick` - 快照處理

### 2. 信號傳遞
- `Signal.snapshot_updated.emit` - 信號發送耗時

### 3. 所有模組更新
- `RankingTower._on_snapshot_updated`
- `TrackMap._on_snapshot_updated`
- `CircleMap._on_snapshot_updated`
- `PitWindow._on_snapshot_updated`
- ... 等所有開啟的模組

---

## 🚀 使用方式

### 步驟 1: 關閉現有監控視窗
如果已經打開監控視窗，請先關閉它

### 步驟 2: 重新打開
在 Python 控制台執行：
```python
from performance_monitor_widget import show_monitor
show_monitor()
```

或從選單：
```
Tools → Performance Monitor
```

### 步驟 3: 查看詳細統計
現在會看到類似：

```
🔍 函數執行耗時統計（前 15 名）:

  1. DataManager._on_playback_tick
     平均: 39.86ms | 最大: 49.80ms
     
  2. Signal.snapshot_updated.emit
     平均: 35.20ms | 最大: 45.60ms
     
  3. RankingTower._on_snapshot_updated
     平均: 12.50ms | 最大: 18.30ms
     🟢 性能尚可
     
  4. TrackMap._on_snapshot_updated
     平均: 8.20ms | 最大: 15.40ms
     ✅ 性能良好
     
  5. CircleMap._on_snapshot_updated
     平均: 7.80ms | 最大: 14.20ms
     ✅ 性能良好
```

---

## 📊 性能分析

### 理解數據

**DataManager._on_playback_tick (39.86ms)**
- 這是總耗時
- 包含了所有模組的更新時間

**Signal.snapshot_updated.emit (35.20ms)**
- 這是信號發送 + 所有接收者處理的時間
- 應該接近 DataManager 的耗時

**各模組 (5-15ms each)**
- 這是每個模組單獨的處理時間
- 加總應該接近 Signal.emit 的時間

### 找出瓶頸

1. **如果某個模組 >20ms** → 需要優化
2. **如果所有模組都 <10ms** → 瓶頸在 DataManager 本身
3. **如果 Signal.emit 很慢** → 開啟的模組太多

---

## 🎯 預期會看到什麼

### 典型分布（總計 40ms）

```
DataManager._on_playback_tick:    40.0ms (100%)
  └─ Signal.snapshot_updated.emit: 35.0ms (87.5%)
      ├─ RankingTower:             12.0ms (30%)
      ├─ TrackMap:                  8.0ms (20%)
      ├─ CircleMap:                 7.0ms (17.5%)
      ├─ PitWindow:                 4.0ms (10%)
      ├─ RaceControl:               2.0ms (5%)
      └─ Other modules:             2.0ms (5%)
```

### 如果發現問題

**情況 1: RankingTower >15ms**
- 原因：20×24 表格更新太頻繁
- 解決：已有 blockSignals 優化

**情況 2: TrackMap/CircleMap >15ms**
- 原因：Matplotlib 重繪太慢
- 解決：已實現跳幀渲染（30 FPS）

**情況 3: DataManager 本身 >5ms**
- 原因：預測計算或數據處理
- 解決：已移至背景執行緒

---

## ✅ 立即測試

在 Python 控制台執行：

```python
from performance_monitor_widget import show_monitor
show_monitor()
```

應該看到終端輸出：

```
[PERF_MONITOR] 開始注入性能監控...
✅ 檢測到賽事: 2025 Abu Dhabi Race
✅ 性能監控已注入
   - DataManager._on_playback_tick: 已包裝
   - snapshot_updated.emit: 已包裝

[PERF_MONITOR] 注入模組監控...
   ✅ 已注入: RankingTower
   ✅ 已注入: TrackMap
   ✅ 已注入: CircleMap
   ✅ 已注入: PitWindow
   ✅ 已監控 4 個模組

✅ 性能監控視窗已開啟
   - 監控模組數: 4
```

然後查看監控視窗的統計！
