# Gap Evolution 修復總結 (2025-01)

## 問題回顧

### 問題 1: 預測曲線顯示直線而非二次曲線
**原因**: 使用線性衰退常數而非二次公式  
**修復**: 所有 5 個策略改用二次公式 `degradation = base * t + 0.5 * accel * t²`

### 問題 2: 虛線樣式不連續
**原因**: 多次 `drawLine()` 調用導致虛線斷裂  
**修復**: 改用 `QPainterPath` 繪製連續路徑

### 問題 3: AttributeError - _calculator 不存在
**原因**: Chase Strategy Widget 使用 `_strategy_calculator` 而非 `_calculator`  
**修復**: 統一命名並添加 `set_strategy_calculator()` 方法

### 問題 4: Workspace 載入時顯示直線
**原因**: `_strategy_calculator` 未在序列化過程中設置  
**修復**: `workspace_serializer.py` 調用 `set_strategy_calculator()` 並觸發重繪

### 問題 5: Delta 文字被曲線遮擋
**原因**: 文字位置計算錯誤  
**修復**: 移至較慢車手曲線上方 15px，並添加顏色編碼

### 問題 6: Gap Evo 預測值低於 Driver Strategy ⚠️ **關鍵修復**
**原因**: Gap Evo 使用 `min(lap_times)` (最快圈)，Driver Strategy 使用 5-25 百分位平均  
**修復**: 統一使用 5-25 百分位平均排除異常值

**修復前**:
```python
def _calculate_base_lap_time(self, lap_times_dict: dict) -> float:
    if not lap_times_dict:
        return 90.0
    return min(lap_times_dict.values())  # 最快圈 → 易受異常影響
```

**修復後**:
```python
def _calculate_base_lap_time(self, lap_times_dict: dict) -> float:
    if not lap_times_dict:
        return 90.0
    
    valid_times = [t for t in lap_times_dict.values() if t > 0]
    if not valid_times:
        return 90.0
    
    sorted_times = sorted(valid_times)
    n = len(sorted_times)
    
    if n > 5:
        # 5-25 百分位平均（與 Driver Strategy 一致）
        start_idx = max(1, n // 20)  # 5th percentile
        end_idx = max(2, n // 4)     # 25th percentile
        return sum(sorted_times[start_idx:end_idx]) / (end_idx - start_idx)
    
    return min(sorted_times)  # 圈數少時仍用最快圈
```

### 問題 7: 切換車手時 MDI 窗口變白屏 ⚠️ **CRITICAL 修復**
**原因**: `paintEvent()` 無異常處理，數據為空時崩潰  
**修復**: 添加 3 層防禦機制

#### 修復層級 1: paintEvent 異常捕獲
```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    try:
        # ... 繪製邏輯 ...
        
        # ✅ 數據為空時顯示等待訊息
        if not self.p1_lap_times and not self.p2_lap_times:
            self._draw_no_data_message(painter, chart_rect)
            painter.end()
            return
        
    except Exception as e:
        print(f"[ERROR] paintEvent 發生異常: {e}")
        traceback.print_exc()
        self._draw_error_message(painter, chart_rect)
    finally:
        painter.end()
```

#### 修復層級 2: 範圍計算防禦
```python
def _calculate_laptime_range(self):
    all_lap_times = []
    
    # ✅ 防禦性檢查
    if self.p1_lap_times:
        all_lap_times.extend([t for t in self.p1_lap_times.values() if t > 0])
    if self.p2_lap_times:
        all_lap_times.extend([t for t in self.p2_lap_times.values() if t > 0])
    
    try:
        _, future_p1_times, future_p2_times = self._calculate_future_lap_times()
        if future_p1_times:
            all_lap_times.extend([t for t in future_p1_times if t > 0])
        if future_p2_times:
            all_lap_times.extend([t for t in future_p2_times if t > 0])
    except Exception as e:
        print(f"[WARNING] Prediction failed: {e}")
        # 繼續使用真實數據
    
    if not all_lap_times:
        # 預設範圍
        self._laptime_min = 80.0
        self._laptime_max = 95.0
```

#### 修復層級 3: 用戶提示訊息
```python
def _draw_no_data_message(self, painter: QPainter, chart_rect: QRectF):
    """數據為空時顯示友好提示"""
    painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
    painter.setPen(QPen(QColor(COLOR_TEXT)))
    painter.drawText(center_x, center_y, "Waiting for lap time data...")
    painter.drawText(center_x, center_y + 20, "Switch drivers to load data")

def _draw_error_message(self, painter: QPainter, chart_rect):
    """異常時顯示錯誤訊息而非白屏"""
    painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
    painter.setPen(QPen(QColor('#FF6B6B')))
    painter.drawText(center_x, center_y, "Rendering Error - Check console")
```

---

## 測試檢查清單

### ✅ 預測曲線測試
- [ ] 策略 1-5 全部顯示二次曲線
- [ ] 虛線樣式連續不斷裂
- [ ] 預測值與 Driver Strategy 對齊（5-25 百分位基準）

### ✅ Workspace 測試
- [ ] 保存 Gap Evo 窗口
- [ ] 重新打開 workspace
- [ ] 預測曲線自動載入（不顯示直線）

### ✅ 穩定性測試 ⚠️ **CRITICAL**
- [ ] 切換車手無白屏
- [ ] 數據為空時顯示等待訊息
- [ ] 異常時顯示錯誤訊息而非崩潰
- [ ] Console 有完整錯誤堆棧（如果異常）

### ✅ 視覺測試
- [ ] Delta 文字位於較慢車手曲線上方
- [ ] Delta 顏色：紅色 (P2 slower) / 綠色 (P2 faster)
- [ ] 預測曲線不會異常偏低

---

## 關鍵代碼位置

### 檔案: `chase_strategy.py` (3195 lines)

**基準圈速計算** (Line 2530-2560):
- 改用 5-25 百分位平均
- 與 Driver Strategy 完全一致

**Paint 事件** (Line 1891-1945):
- Try-except 異常處理
- 數據為空檢查
- 錯誤訊息顯示

**範圍計算** (Line 1860-1895):
- 防禦性數據檢查
- 預測失敗容錯

**預測計算** (Line 2203-2484):
- 所有 5 個策略使用二次公式
- 無 fallback 機制

---

## 預期效果

### 修復前
- Gap Evo 預測曲線偏低 2-3 秒（異常最快圈影響）
- 切換車手時窗口白屏崩潰
- Workspace 載入時顯示直線

### 修復後
- Gap Evo 與 Driver Strategy 預測對齊（±0.5秒以內）
- 切換車手時顯示 "Waiting for lap time data..."
- Workspace 載入時正確顯示預測曲線
- 任何異常顯示錯誤訊息而非白屏

---

## 測試步驟

1. **啟動 GUI**:
   ```powershell
   python f1t_gui_main.py
   ```

2. **打開 Live Timing**:
   - 選擇 2025 Abu Dhabi Race
   - 開啟 Chase Strategy

3. **驗證預測曲線**:
   - 選擇 VER vs LEC
   - 確認 5 個策略全部顯示二次曲線
   - 檢查虛線連續性

4. **驗證基準對齊**:
   - 打開 Driver Strategy (同一賽事)
   - 比較 VER 的預測值
   - Gap Evo 與 Driver Strategy 應該在 ±0.5s 以內

5. **驗證白屏修復** ⚠️ **CRITICAL**:
   - 在 Chase Strategy 中切換車手 (VER → HAM → LEC)
   - 確認無白屏，顯示 "Waiting for lap time data..."
   - 等待數據載入後曲線正常顯示

6. **Workspace 測試**:
   - 保存當前 workspace
   - 關閉 GUI
   - 重新打開 GUI 並載入 workspace
   - 確認 Gap Evo 自動顯示預測曲線

7. **異常測試** (可選):
   - 修改代碼故意觸發異常
   - 確認顯示紅色錯誤訊息而非白屏
   - Console 有完整堆棧追蹤

---

## 相關檔案

- `modules/gui/live_timing/live_timing_modules/chase_strategy.py` (3195 lines)
- `modules/gui/live_timing/live_timing_modules/driver_strategy.py` (2789 lines)
- `core/workspace_serializer.py` (Lines 1216-1223)

---

## 修復日期
2025-01 (根據用戶時間)

## 修復狀態
✅ **已完成** - 等待用戶測試驗證
