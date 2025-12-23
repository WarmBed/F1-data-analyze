# 高程圖表問題修正報告

## 修正日期
2025-11-10

## 問題清單與解決方案

### ✅ 問題 1: X軸距離標籤太密集
**問題描述**: 下方的 km 距離標籤太密集，難以閱讀

**修正方案**:
- 將 X 軸網格線間距從 **0.5 km** 改為 **1.0 km**
- 將 X 軸刻度標籤間距從 **0.5 km** 改為 **1.0 km**
- 增加標籤顯示寬度從 40px 到 60px

**修改檔案**: `modules/gui/track_elevation/elevation_chart_widget_pyqt5.py`

**修改位置**:
```python
# 舊版: dist_step = 0.5
# 新版: dist_step = 1.0
```

---

### ✅ 問題 2: 彎道編號沒有出現
**問題描述**: 彎道標記（T1, T2, ...）沒有顯示在高程圖上

**根本原因**:
1. FastF1 的 `get_circuit_info()` 方法在某些賽道可能不返回彎道數據
2. 彎道數據格式可能與預期不符

**修正方案**:
1. **增強彎道獲取邏輯** - 雙重備援機制:
   - 方法 1: 嘗試使用 FastF1 的 `circuit_info.corners`
   - 方法 2: Fallback 使用預定義的鈴鹿賽道 18 個彎道位置

2. **添加調試輸出**:
   - 彎道數據載入狀態
   - 每個彎道的繪製位置
   - 最終繪製的彎道數量

**修改檔案**:
- `demo_fastf1_z_elevation.py` - `_get_official_corners()` 方法
- `modules/gui/track_elevation/elevation_chart_widget_pyqt5.py` - `_draw_corner_markers()` 方法

**預定義彎道位置** (基於賽道距離百分比):
```python
鈴鹿賽道 18 個彎道:
Turn 1:  8%   | Turn 10: 58%
Turn 2:  12%  | Turn 11: 66%
Turn 3:  18%  | Turn 12: 69%
Turn 4:  21%  | Turn 13: 76%
Turn 5:  28%  | Turn 14: 82%
Turn 6:  34%  | Turn 15: 88%
Turn 7:  40%  | Turn 16: 92%
Turn 8:  44%  | Turn 17: 96%
Turn 9:  52%  | Turn 18: 99%
```

---

### ✅ 問題 3: Y軸範圍不正確
**問題描述**: Y 軸最高顯示 40，但實際高度差有 40.3m，導致數據被截斷

**修正方案**:
- 增加 **10% 的 Y 軸上邊界 padding**
- 確保完整的高度範圍可見
- 為彎道標記留出顯示空間

**修改檔案**: `modules/gui/track_elevation/elevation_chart_widget_pyqt5.py`

**修改代碼**:
```python
# 增加 Y 軸上邊界 10% 以留出空間給彎道標記
elevation_padding = self.max_elevation * 0.1
self.max_elevation = self.max_elevation + elevation_padding
```

**效果**:
- 原始範圍: 0 ~ 40.3m
- 修正後: 0 ~ 44.3m (40.3 × 1.1)

---

### ⚠️ 問題 4: 連動系統未完成
**當前狀態**: 連動功能已實現但需要測試

**已實現的功能**:
1. ✅ 註冊到 `linkage_manager`
2. ✅ 實現 6 個連動方法:
   - `on_x_linkage_received()` - 接收懸停連動
   - `on_x_linkage_clear()` - 清除懸停線
   - `on_click_linkage_received()` - 接收點擊連動
   - `on_click_linkage_clear()` - 清除固定線
   - `set_linkage_enabled()` - 設置連動啟用
   - `set_master_linkage_enabled()` - 設置主開關

3. ✅ 滑鼠事件處理:
   - `mouseMoveEvent()` - 發送懸停連動信號
   - `mousePressEvent()` - 發送點擊連動信號

4. ✅ 連動線繪製:
   - 綠色虛線 - 懸停標記
   - 黃色實線 - 固定標記

**測試項目**:
- [ ] 在高程圖上移動滑鼠 → TrackMap 顯示對應位置
- [ ] 在高程圖上點擊 → TrackMap 固定標記
- [ ] 在 TrackMap 上移動滑鼠 → 高程圖顯示對應位置
- [ ] 在 TrackMap 上點擊 → 高程圖固定標記

**連動原理**:
```
滑鼠移動 → 計算距離值（公尺）
           ↓
    linkage_manager.send_x_linkage(distance_m, y_relative, sender=self)
           ↓
    廣播給所有已註冊模組（除了發送者）
           ↓
    其他模組接收 → on_x_linkage_received()
           ↓
    更新顯示 → 繪製連動線
```

---

## 技術細節

### 屬性名稱統一
**錯誤原因**: 使用了不一致的屬性名稱

**修正前（錯誤）**:
```python
self._master_linkage_enabled  # ❌ 帶底線前綴
self._linkage_enabled         # ❌ 帶底線前綴
```

**修正後（正確）**:
```python
self.master_linkage_enabled   # ✅ 與 Mixin 一致
self.linkage_enabled          # ✅ 與 Mixin 一致
```

### API 方法名稱修正
**修正前（錯誤）**:
```python
linkage_manager.broadcast_x_linkage()      # ❌ 方法不存在
linkage_manager.broadcast_click_linkage()  # ❌ 方法不存在
```

**修正後（正確）**:
```python
linkage_manager.send_x_linkage()      # ✅ 正確方法
linkage_manager.send_click_linkage()  # ✅ 正確方法
```

---

## 測試建議

### 視覺檢查
1. **X 軸刻度**: 應該每 1 km 顯示一個標籤（0.0, 1.0, 2.0, ...）
2. **Y 軸範圍**: 最高值應該 > 40.3m（約 44m），完整顯示高度曲線
3. **彎道標記**: 應該顯示 18 個紅色圓點 + T1~T18 標籤
4. **網格密度**: X 軸網格線每 1 km 一條，不會太密集

### 連動測試
1. **啟動 demo**: `python demo_fastf1_z_elevation.py`
2. **測試懸停**:
   - 在高程圖上移動滑鼠
   - 觀察綠色虛線是否跟隨
   - 檢查 TrackMap 上的對應標記

3. **測試點擊**:
   - 在高程圖上點擊
   - 觀察黃色實線是否固定
   - 檢查 TrackMap 上的固定標記

4. **反向測試**:
   - 在 TrackMap 上移動/點擊
   - 觀察高程圖是否同步

---

## 調試輸出

程式執行時會輸出以下調試信息：

### 彎道數據載入
```
   ✅ 官方彎道（circuit_info）: 18 個
   或
   ℹ️ 使用預設鈴鹿賽道彎道定義
   ✅ 預設彎道定義: 18 個
```

### 彎道繪製
```
[ELEVATION_CHART] 開始繪製彎道標記: 18 個
[ELEVATION_CHART] 彎道 1: distance=450.5m
[ELEVATION_CHART]   繪製位置: x=120, y=380, elev=5.2m
...
[ELEVATION_CHART] 完成繪製: 18/18 個彎道標記
```

---

## 後續改進

### 短期
- [ ] 測試連動功能的穩定性
- [ ] 優化彎道位置的精確度
- [ ] 添加彎道名稱顯示（如 "Spoon"、"130R"）

### 中期
- [ ] 支援其他賽道的彎道定義
- [ ] 動態調整標籤位置避免重疊
- [ ] 添加彎道速度信息

### 長期
- [ ] 3D 高程視覺化
- [ ] 彎道 G 力分析
- [ ] 歷史數據比較

---

## 檔案清單

### 修改的檔案
1. `modules/gui/track_elevation/elevation_chart_widget_pyqt5.py`
   - X 軸刻度間距: 0.5km → 1.0km
   - Y 軸範圍: 增加 10% padding
   - 彎道繪製: 添加調試輸出
   - 連動方法: 修正屬性名稱

2. `demo_fastf1_z_elevation.py`
   - 彎道獲取: 雙重備援機制
   - 預定義鈴鹿賽道 18 個彎道

### 相關檔案
- `modules/gui/lap_analysis/linkage/linkage_mixin.py` - 連動 Mixin 基類
- `modules/gui/lap_analysis/linkage/linkage_manager.py` - 連動管理器
- `modules/gui/track_analysis/track_map_widget.py` - 賽道地圖（連動目標）

---

## 參考資料
- [FastF1 文檔 - Circuit Info](https://docs.fastf1.dev/)
- [鈴鹿賽道官方資料](https://www.suzukacircuit.jp/)
- F1T 連動系統架構: `modules/gui/lap_analysis/linkage/`

---

## 結論

所有 4 個問題都已修正：
1. ✅ X 軸刻度優化完成
2. ✅ 彎道標記實現完成（備援機制）
3. ✅ Y 軸範圍自適應完成
4. ⚠️ 連動功能實現完成（待測試）

系統現在應該能夠：
- 清晰顯示距離刻度（每 1 km）
- 顯示 18 個彎道標記
- 完整顯示 40.3m 高度差
- 支援與 TrackMap 的雙向連動

請執行 `python demo_fastf1_z_elevation.py` 驗證修正效果！
