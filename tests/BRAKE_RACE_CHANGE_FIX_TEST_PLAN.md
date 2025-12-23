# Brake Performance Race 更換修復測試計劃

**修復時間**: 2025-10-19  
**修復內容**: 在 `_get_telemetry_analysis_windows()` 的 `all_analysis_types` 中添加 `'all_drivers_brake_performance'`  
**修復位置**: `f1t_gui_main.py` 第 7903 行

---

## ✅ 修復內容

### **修改檔案**: `f1t_gui_main.py`

**修改位置**: 第 7868-7910 行

**修改前**:
```python
all_analysis_types = {
    # 遙測分析類型
    'speed_analysis', 'speed', 'brake', 'throttle', 'steering',
    'gear', 'rpm', 'acceleration', 'speed_diff', 'Speeddiff',
    'distancediff', 'Distancediff', 'timediff', 'Timediff',
    'laptime', 'laptime_boxplot', 'throttle_boxplot',
    'throttle_line_chart_single_driver',
    # 賽事級分析類型
    'rain_weather', 'pitstop', 'accident', 'tire',
    'ideal_lap', 'ideal_lap_ranking', 'ideal_lap_sector_comparison',
    'ideal_lap_sector_heatmap', 'track_analysis',
    'all_drivers_straight_line_speed',  # 全車手直線速度分析
    # ❌ 缺少 'all_drivers_brake_performance'
}
```

**修改後**:
```python
all_analysis_types = {
    # 遙測分析類型
    'speed_analysis', 'speed', 'brake', 'throttle', 'steering',
    'gear', 'rpm', 'acceleration', 'speed_diff', 'Speeddiff',
    'distancediff', 'Distancediff', 'timediff', 'Timediff',
    'laptime', 'laptime_boxplot', 'throttle_boxplot',
    'throttle_line_chart_single_driver',
    # 賽事級分析類型
    'rain_weather', 'pitstop', 'accident', 'tire',
    'ideal_lap', 'ideal_lap_ranking', 'ideal_lap_sector_comparison',
    'ideal_lap_sector_heatmap', 'track_analysis',
    'all_drivers_straight_line_speed',  # 全車手直線速度分析
    'all_drivers_brake_performance',    # ✅ 全車手煞車性能分析 (F34)
}
```

---

## 🧪 測試計劃

### **測試環境**
- **應用程式**: F1T GUI (`f1t_gui_main.py`)
- **測試模組**: All Drivers Brake Performance
- **測試功能**: Race 更換後數據自動更新

### **前置條件**
1. 確保有多個 race 的數據 JSON 檔案（例如 China、Japan）
2. 或確保 API 可用（`https://localhost:8000`）

---

## 📋 測試案例

### **測試 1: Brake Performance Race 更換（基本功能）**

**步驟**:
1. ✅ 啟動 F1T GUI
2. ✅ 從選單開啟 "All Drivers Brake Performance" 模組
3. ✅ 確認初始數據已載入（例如 Japan R 2025）
4. ✅ 從頂部工具列更換 Race（例如從 Japan 改為 China）
5. ✅ 等待 350ms（debounce 延遲）
6. ✅ 觀察 Brake Performance 視窗是否自動更新數據

**預期結果**:
- ✅ 狀態列顯示 "正在自動更新 X 個分析視窗..."
- ✅ 控制台輸出：
  ```
  🔵 [DEBUG]    on_race_changed 被調用: race=China
  [BROADCAST_DEBUG] _schedule_parameter_broadcast 被調用: reason=race_changed
  [BROADCAST_DEBUG] 啟動 timer (350ms)
  [BROADCAST_DEBUG] _broadcast_pending_parameters 被調用
  [BROADCAST_DEBUG] 調用 on_race_parameters_changed()
  [RACE_CONTROL] 賽事參數已變更:
  [RACE_CONTROL]   年份: '2025'
  [RACE_CONTROL]   賽事: 'China'
  [RACE_CONTROL]   賽段: 'R'
  [DEBUG]    _get_telemetry_analysis_windows() - 開始搜尋視窗
  ✅ 找到 Tab 視窗 (widget): all_drivers_brake_performance
  [RACE_CONTROL] 發現 1 個需要更新的分析視窗
  🔵 [BATCH_UPDATE] 找到 1 個分析視窗
  [BRAKE_MODULE] 更新參數...
  [BRAKE_MODULE] 參數已更新: 2025 China R
  [BRAKE_MDI] 開始載入初始數據...
  [BRAKE_MDI] 資料載入完成信號
  ```
- ✅ Brake Performance 表格顯示 China 的數據（硬編碼終點 4775m）

**失敗時檢查**:
- ❌ 如果沒有更新：檢查 `_get_telemetry_analysis_windows()` 是否找到 Brake Performance
- ❌ 如果找不到：確認修改已保存（第 7903 行應有 `'all_drivers_brake_performance'`）

---

### **測試 2: 同時開啟 Speed + Brake（對比測試）**

**步驟**:
1. ✅ 啟動 F1T GUI
2. ✅ 開啟 "All Drivers Straight Line Speed" 模組
3. ✅ 開啟 "All Drivers Brake Performance" 模組
4. ✅ 確認兩個模組都顯示 Japan R 2025 數據
5. ✅ 更換 Race 為 China
6. ✅ 觀察兩個模組是否都自動更新

**預期結果**:
- ✅ 狀態列顯示 "正在自動更新 2 個分析視窗..."
- ✅ Speed 模組更新為 China 數據
- ✅ Brake 模組更新為 China 數據
- ✅ 控制台輸出顯示找到 2 個視窗：
  ```
  ✅ 找到 Tab 視窗 (widget): all_drivers_straight_line_speed
  ✅ 找到 Tab 視窗 (widget): all_drivers_brake_performance
  [RACE_CONTROL] 發現 2 個需要更新的分析視窗
  ```

---

### **測試 3: Session 更換測試**

**步驟**:
1. ✅ 啟動 F1T GUI
2. ✅ 開啟 "All Drivers Brake Performance" 模組（Japan R 2025）
3. ✅ 更換 Session 為 "Q"（排位賽）
4. ✅ 觀察 Brake Performance 是否自動更新

**預期結果**:
- ✅ Brake Performance 自動載入 Japan Q 2025 數據
- ✅ 控制台輸出：
  ```
  🔵 [DEBUG]    on_session_changed 被調用: session=Q
  [BRAKE_MODULE] 參數已更新: 2025 Japan Q
  ```

---

### **測試 4: Year 更換測試**

**步驟**:
1. ✅ 啟動 F1T GUI
2. ✅ 開啟 "All Drivers Brake Performance" 模組（2025 Japan R）
3. ✅ 更換 Year 為 "2024"
4. ✅ 觀察 Brake Performance 是否自動更新

**預期結果**:
- ✅ Brake Performance 自動載入 2024 Japan R 數據
- ✅ 控制台輸出：
  ```
  🔵 [DEBUG]    on_year_changed 被調用: year=2024
  [BRAKE_MODULE] 參數已更新: 2024 Japan R
  ```

---

### **測試 5: 快速切換 Race（Debounce 測試）**

**步驟**:
1. ✅ 啟動 F1T GUI
2. ✅ 開啟 "All Drivers Brake Performance" 模組
3. ✅ 快速切換 Race：Japan → China → Japan → China（間隔 < 350ms）
4. ✅ 停止切換，等待 350ms
5. ✅ 觀察最終是否只觸發一次更新

**預期結果**:
- ✅ Debounce 機制生效，只有最後一次 Race 觸發更新
- ✅ 控制台輸出顯示只有一次 `_broadcast_pending_parameters` 調用
- ✅ 最終顯示的數據是最後選擇的 Race（China）

---

### **測試 6: API 失敗容錯測試**

**步驟**:
1. ✅ 關閉 API 服務器（或斷網）
2. ✅ 啟動 F1T GUI
3. ✅ 開啟 "All Drivers Brake Performance" 模組
4. ✅ 刪除本地 JSON 緩存（如果存在）
5. ✅ 更換 Race
6. ✅ 觀察錯誤處理

**預期結果**:
- ✅ 不彈出 API 失敗警告框（API-ONLY 模式修正）
- ✅ 控制台輸出：
  ```
  [BRAKE_LOADER] API 載入失敗: ...
  💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接
  ```
- ✅ Brake Performance 表格保持舊數據或顯示空白（不崩潰）

---

## 🔍 調試檢查點

### **日誌追蹤關鍵訊息**

執行測試時，應在控制台看到以下日誌序列：

```
步驟 1: Race 更換觸發
🔵 [DEBUG]    on_race_changed 被調用: race=China

步驟 2: 排程參數廣播
[BROADCAST_DEBUG] _schedule_parameter_broadcast 被調用: reason=race_changed
[BROADCAST_DEBUG] Pending payload: {'reason': 'race_changed', 'year': '2025', 'race': 'China', 'session': 'R'}
[BROADCAST_DEBUG] 啟動 timer (350ms)

步驟 3: 執行參數廣播（350ms 後）
[BROADCAST_DEBUG] _broadcast_pending_parameters 被調用
[BROADCAST_DEBUG] 執行 payload: {'reason': 'race_changed', 'year': '2025', 'race': 'China', 'session': 'R'}
[BROADCAST_DEBUG] 調用 on_race_parameters_changed()

步驟 4: 搜尋需要更新的視窗
[DEBUG]    _get_telemetry_analysis_windows() - 開始搜尋視窗
🔵 [DEBUG]    檢查 tab_widget: X 個標籤
✅ 找到 Tab 視窗 (widget): all_drivers_brake_performance  ← 關鍵！

步驟 5: 批次更新視窗
[RACE_CONTROL] 發現 1 個需要更新的分析視窗
🔵 [BATCH_UPDATE] 找到 1 個分析視窗
🟢 [DEBUG]    ========== update_all_lap_analysis 開始 ==========

步驟 6: 更新 Brake Module
[BRAKE_MODULE] 更新參數...
[BRAKE_MODULE] 參數已更新: 2025 China R
[BRAKE_MDI] 開始載入初始數據...
[BRAKE_MDI] 收到資料載入完成信號
[BRAKE_MDI] 資料處理完成
```

### **關鍵驗證點**

**✅ 修復成功標誌**:
```
✅ 找到 Tab 視窗 (widget): all_drivers_brake_performance
```

**❌ 修復失敗標誌**:
```
[RACE_CONTROL] 沒有活動的分析視窗，無需更新
# 或者
[RACE_CONTROL] 發現 0 個需要更新的分析視窗
```

---

## 📊 測試結果記錄表

| 測試案例 | 預期結果 | 實際結果 | 狀態 | 備註 |
|---------|---------|---------|------|------|
| 測試 1: Brake Race 更換 | 自動更新為 China 數據 | | ⏳ 待測試 | |
| 測試 2: Speed + Brake 同時更新 | 兩個模組都更新 | | ⏳ 待測試 | |
| 測試 3: Session 更換 | 自動更新為 Q 數據 | | ⏳ 待測試 | |
| 測試 4: Year 更換 | 自動更新為 2024 數據 | | ⏳ 待測試 | |
| 測試 5: 快速切換（Debounce） | 只觸發一次更新 | | ⏳ 待測試 | |
| 測試 6: API 失敗容錯 | 不彈窗，顯示日誌 | | ⏳ 待測試 | |

---

## 🐛 已知問題與限制

### **問題 1: 代碼重複**
- `all_analysis_types` 在兩個地方定義（`_get_telemetry_analysis_windows` 和 `update_all_lap_analysis`）
- 未來可能再次不一致
- **建議**: 提取為全局常量

### **問題 2: 硬編碼類型列表**
- 新增模組時需要手動添加到列表中
- 容易遺漏
- **建議**: 實現動態註冊機制

---

## ✅ 完成標準

測試通過條件：
1. ✅ 測試 1-6 全部通過
2. ✅ 控制台日誌包含關鍵驗證點
3. ✅ Brake Performance 表格正確顯示新 Race 的數據
4. ✅ 無異常或錯誤彈窗（除非 API 失敗，且只記錄日誌）

---

## 📝 回歸測試

修復後，確保以下功能不受影響：

1. ✅ Speed Module 仍然正常更新
2. ✅ 其他分析模組（Rain, Pitstop, Tire）正常更新
3. ✅ 遙測分析模組（Speed, Brake, Throttle）正常更新
4. ✅ MDI 視窗和 Tab 視窗都能被正確檢測

---

**測試計劃完成時間**: 2025-10-19  
**預計測試時間**: 15-20 分鐘  
**下一步**: 執行測試並記錄結果
