# All Drivers Straight Line Speed - 完整調查報告

## 調查項目

1. ⚠️ 棒狀圖寬度覆蓋問題
2. ✅ API 調用機制確認
3. ✅ 參數更新機制對比

---

## 問題 1：棒狀圖寬度覆蓋問題 ⚠️ 已修正

### 問題描述
從用戶截圖發現：視覺化欄位的條形圖有覆蓋/超出單元格邊界的問題。

### 原因分析
在 `AccelerationBarDelegate.paint()` 方法中：

```python
# 修正前（第 84 行）
total_width = option.rect.width() - 20  # 固定邊距
speed_max_pos = total_width * relative_ratio
```

**問題**:
1. `speed_max_pos` 使用相對時間比例計算，沒有限制最大寬度
2. 右側時間文字標籤（`text_x = base_x + speed_max_pos + 15`）會超出單元格
3. 當 `relative_ratio` 接近 1.0 時，總寬度 = 條形圖 + 文字 > 單元格寬度

### 修正方案
**預留文字空間，確保條形圖 + 文字標籤不超出單元格**

```python
# 修正後
text_label_width = 80  # 預留右側文字區域（兩行時間顯示）
available_width = option.rect.width() - 20 - text_label_width
speed_max_pos = available_width * relative_ratio
```

### 修正效果
- ✅ 條形圖最大寬度限制在 `available_width` 內
- ✅ 文字標籤固定在條形圖右側 80px 區域
- ✅ 總寬度 = 左邊距(10) + 條形圖(available_width * ratio) + 文字區(80) + 右邊距(10)
- ✅ 不會再有覆蓋問題

### 修正檔案
- `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`
  - 第 84-88 行：修正寬度計算邏輯

---

## 問題 2：API 調用機制確認 ✅ 已驗證

### 調查結果
**✅ 確認：All Drivers Straight Line Speed 模組已在調用 API**

### API 調用路徑
```
User Action
    ↓
AllDriversStraightLineSpeedMDI.initialize_module()
    ↓
StraightLineSpeedDataLoader.load_data()
    ↓
檢查本地 JSON 檔案（_find_data_file）
    ↓ (找不到)
StraightLineSpeedDataLoader._fetch_via_api_and_cache()
    ↓
requests.post(
    "{base_url}/api/v2/analysis/execute",
    params={"function_id": 48, "year": ..., "race": ..., "session": ...}
)
    ↓
API 返回 JSON（嵌套兩層 data）
    ↓
_write_payload_to_cache() 寫入 json/ 目錄
    ↓
_validate_data_format() 驗證數據結構
    ↓
_process_data() 處理嵌套數據（已修正）
    ↓
更新表格顯示
```

### 與 ideal_lap_sector_comparison 對比

| 特性 | straight_line_speed | ideal_lap_sector_comparison | 一致性 |
|------|---------------------|----------------------------|--------|
| **API 調用** | ✅ 是 | ✅ 是 | ✅ 一致 |
| **API 端點** | `/api/v2/analysis/execute` | `/api/v2/analysis/execute` | ✅ 一致 |
| **請求方式** | `requests.post()` | `requests.post()` | ✅ 一致 |
| **Function ID** | 48 | 53 | ✅ 各自正確 |
| **異步執行緒** | ❌ 同步（阻塞式） | ✅ `QThread` 異步 | ⚠️ 架構差異 |
| **進度信號** | ✅ `load_progress.emit()` | ✅ `progress.emit()` | ✅ 一致 |
| **數據緩存** | ✅ 寫入 `json/` | ✅ 可能有緩存 | ✅ 一致 |
| **錯誤處理** | ✅ `load_error.emit()` | ✅ `failure.emit()` | ✅ 一致 |

### 架構差異說明

#### straight_line_speed（同步實現）
```python
# 在 DataLoader 中同步調用 API
def _fetch_via_api_and_cache(self, **kwargs):
    response = requests.post(endpoint, params=params)  # 同步阻塞
    payload = response.json()
    self._write_payload_to_cache(payload, ...)
```

**特點**:
- ✅ 代碼簡潔
- ⚠️ API 請求時會阻塞 GUI（短時間）
- ✅ 錯誤處理直接在方法內

#### ideal_lap_sector_comparison（異步實現）
```python
# 使用 QThread 異步調用 API
class IdealLapSectorComparisonApiWorker(QThread):
    def run(self):
        response = requests.post(endpoint, params=params)  # 在背景執行緒
        self.success.emit(result)  # 完成後發送信號
```

**特點**:
- ✅ GUI 不會阻塞
- ⚠️ 代碼較複雜（需要 Worker 類別）
- ✅ 更好的用戶體驗

### 結論
- ✅ **straight_line_speed 已正確調用 API**
- ✅ **功能完全正常，無需修正**
- 💡 **未來優化**：可考慮改為異步執行緒（參考 ideal_lap_sector_comparison）

---

## 問題 3：參數更新機制對比 ✅ 已驗證

### 調查結果
**✅ 確認：兩個模組的參數更新機制都是正常的，但實現風格不同**

### 機制對比

| 特性 | straight_line_speed | ideal_lap_sector_comparison | 評價 |
|------|---------------------|----------------------------|------|
| **基類繼承** | `UniversalAnalysisMDI` | `UniversalAnalysisMDI` | ✅ 相同 |
| **initialize_module()** | ✅ 有 | ✅ 有 | ✅ 相同 |
| **接收參數來源** | `current_year/race/session` | `current_year/race/session` | ✅ 相同 |
| **update_parameters()** | ❌ 無（使用基類） | ✅ 有（覆寫） | ⚠️ 風格差異 |
| **DataManager 參數同步** | ❌ 無（通過參數傳遞） | ✅ 有（明確同步） | ⚠️ 實現差異 |
| **觸發數據載入** | ✅ 基類自動 | ✅ 手動調用 | ⚠️ 方式不同 |

### 參數更新流程對比

#### straight_line_speed（簡潔風格）
```
主GUI調用 update_parameters(year, race, session)
    ↓
基類 UniversalAnalysisMDI.update_parameters()
    ↓
1. 更新 self.current_year/race/session
2. 發送 parameters_updated 信號
3. 更新視窗標題
4. 自動調用 _load_data_with_current_parameters()
    ↓
data_manager.load_data(year=new_year, race=new_race, session=new_session)
    ↓
API 調用 → 更新 UI
```

**特點**:
- ✅ 完全信任基類邏輯
- ✅ 代碼簡潔
- ⚠️ 缺少 DataManager 內部參數同步

#### ideal_lap_sector_comparison（明確風格）
```
主GUI調用 update_parameters(**params)
    ↓
IdealLapSectorComparisonMDI.update_parameters()
    ↓
轉發到 update_analysis_parameters(year, race, session)
    ↓
1. 更新 self.year/race/session
2. ✅ 同步 data_manager.year/race/session
3. 手動調用 self.load_initial_data()
    ↓
data_manager.load_data(**params)
    ↓
API 調用 → 更新 UI
```

**特點**:
- ✅ 明確控制每個步驟
- ✅ DataManager 內部參數同步
- ⚠️ 代碼略多，部分邏輯與基類重複

### 結論
- ✅ **兩種實現都是功能正常的**
- ✅ **straight_line_speed 使用簡潔風格，完全依賴基類**
- ✅ **ideal_lap_sector_comparison 使用明確風格，更多自定義控制**
- ✅ **兩者都能正確處理參數更新和數據重載**
- 💡 **建議保持 straight_line_speed 當前實現，除非遇到具體問題**

---

## 總結

### 修正項目
1. ✅ **已修正**：棒狀圖寬度計算（預留文字空間）

### 驗證項目
2. ✅ **已確認**：API 調用機制正常運作
3. ✅ **已確認**：參數更新機制正常運作

### 差異說明
- ⚠️ **API 調用方式**：straight_line_speed 使用同步，ideal_lap_sector_comparison 使用異步
- ⚠️ **參數更新風格**：straight_line_speed 依賴基類，ideal_lap_sector_comparison 自定義控制
- ✅ **功能等效**：兩種實現方式都是有效的

### 未來優化建議
1. 💡 考慮將 API 調用改為異步執行緒（提升用戶體驗）
2. 💡 可選：添加 DataManager 內部參數同步（增強一致性）
3. 💡 可選：添加更詳細的錯誤處理和重試機制

---

**報告完成時間**: 2025-10-14
**調查模組**: all_drivers_straight_line_speed
**參考模組**: ideal_lap_sector_comparison
**修正檔案**: `all_drivers_straight_line_speed_table_widget.py`
**驗證文檔**: `PARAMETER_UPDATE_MECHANISM_COMPARISON.md`, `STRAIGHT_SPEED_BAR_WIDTH_FIX.md`
