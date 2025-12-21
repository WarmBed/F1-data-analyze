# All Drivers Straight Line Speed - 修正報告

## 問題 1：棒狀圖寬度覆蓋問題 ⚠️

### 問題描述
從截圖看到視覺化欄位的條形圖有覆蓋/超出單元格邊界的問題。

### 原因分析
在 `AccelerationBarDelegate.paint()` 方法中（第 84 行）：

```python
total_width = option.rect.width() - 20  # 固定邊距
speed_max_pos = total_width * relative_ratio
```

問題：
1. `speed_max_pos` 使用相對時間比例計算，但沒有限制最大寬度
2. 當 `relative_ratio` 接近 1.0 時，條形圖會接近 `total_width`
3. 加上右側的時間文字標籤（`text_x = base_x + speed_max_pos + 15`），總寬度會超出單元格

### 修正方案
1. **保留文字空間**：從 `total_width` 中預留文字區域（約 80px）
2. **動態寬度計算**：確保條形圖 + 文字標籤不超出單元格

```python
# 修正前
total_width = option.rect.width() - 20
speed_max_pos = total_width * relative_ratio

# 修正後
text_label_width = 80  # 預留文字區域
available_width = option.rect.width() - 20 - text_label_width
speed_max_pos = available_width * relative_ratio
```

---

## 問題 2：API 調用確認 ✅

### 調查結果
**✅ 已確認：All Drivers Straight Line Speed 模組已在調用 API**

### API 調用路徑
```
User Action
    ↓
AllDriversStraightLineSpeedMDI.initialize_module()
    ↓
StraightLineSpeedDataLoader.load_data()
    ↓
檢查本地 JSON 檔案
    ↓ (找不到)
StraightLineSpeedDataLoader._fetch_via_api_and_cache()
    ↓
requests.post(
    "{base_url}/api/v2/analysis/execute",
    params={"function_id": 48, "year": ..., "race": ..., "session": ...}
)
    ↓
API 返回 JSON
    ↓
_write_payload_to_cache() 寫入 json/ 目錄
    ↓
_process_data() 處理數據
    ↓
更新表格顯示
```

### 與 ideal_lap_sector_comparison 對比

| 特性 | straight_line_speed | ideal_lap_sector_comparison |
|------|---------------------|----------------------------|
| **API 調用** | ✅ 是 | ✅ 是 |
| **API 端點** | `/api/v2/analysis/execute` | `/api/v2/analysis/execute` |
| **Function ID** | 48 | 53 |
| **異步執行緒** | ❌ 同步（阻塞式） | ✅ `QThread` 異步 |
| **進度信號** | ✅ `load_progress.emit()` | ✅ `progress.emit()` |
| **數據緩存** | ✅ 寫入 `json/` | ✅ 可能有緩存 |

### 架構差異

#### straight_line_speed（當前實現）
```python
# 同步調用（在主執行緒中阻塞）
def load_data(self, **kwargs) -> bool:
    existing = self._find_data_file(**kwargs)
    if not existing:
        if not self._fetch_via_api_and_cache(**kwargs):  # 同步阻塞
            return False
    return super().load_data(**kwargs)
```

#### ideal_lap_sector_comparison（異步實現）
```python
# 異步調用（使用 QThread）
class IdealLapSectorComparisonApiWorker(QThread):
    def run(self):
        response = requests.post(endpoint, params=params)  # 在背景執行緒
        self.success.emit(result)  # 完成後發送信號
```

### 結論
1. ✅ **straight_line_speed 已在調用 API**
2. ⚠️ **架構差異**：使用同步調用，可能在 API 請求時阻塞 GUI
3. ✅ **功能正常**：API 端點、參數、數據處理都正確
4. 💡 **優化建議**：未來可考慮改為異步執行緒（參考 ideal_lap_sector_comparison）

---

## 修正計劃

### 立即修正（Priority 1）
- [x] 問題 1：修正棒狀圖寬度計算，防止覆蓋

### 已確認正常（無需修正）
- [x] 問題 2：API 調用已確認正常運作

### 未來優化（Priority 2）
- [ ] 考慮將 API 調用改為異步執行緒（參考 ideal_lap_sector_comparison）
- [ ] 增強錯誤處理和重試機制
- [ ] 優化進度反饋體驗

---

**修正完成時間**: 2025-10-14
**測試狀態**: 待測試
**修正檔案**: `all_drivers_straight_line_speed_table_widget.py`
