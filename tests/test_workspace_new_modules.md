# 🎯 Workspace 新增模組測試指南

## ✅ 已添加的模組

本次更新在 `_create_module_instance` 方法中添加了以下三個模組：

### 1. **Pitstop Analysis** (進站分析)
- **analysis_type**: `pitstop`
- **類別**: `PitstopAnalysisModule`
- **導入路徑**: `modules.gui.pitstop_analysis.pitstop_analysis_mdi`
- **參數**: 無參數構造 `()`，參數通過屬性設定
- **用途**: F1 車手最快進站時間排行榜

### 2. **Accident Analysis** (事故分析)
- **analysis_type**: `accident`
- **類別**: `AccidentAnalysisModule`
- **導入路徑**: `modules.gui.accident_analysis.accident_analysis_mdi`
- **參數**: 無參數構造 `()`，參數通過屬性設定
- **用途**: F1 事故統計分析和視覺化

### 3. **Telemetry Analysis** (遙測分析)
- **analysis_type**: `telemetry`
- **類別**: `TelemetryAnalysisModule`
- **導入路徑**: `modules.gui.telemetry_analysis_mdi`
- **參數**: 無參數構造 `()`，參數通過屬性設定
- **用途**: F1 單場比賽車手性能儀表板

---

## 🧪 測試步驟

### 階段 1: 測試 Pitstop Analysis

1. **打開模組**:
   - 從左側樹狀選單打開 **Pitstop Analysis**
   - 確認視窗正常顯示進站時間排行榜

2. **保存 Workspace**:
   ```
   Workspace 名稱: test_pitstop_2025_usa_r
   ```

3. **關閉視窗並載入**:
   - 關閉 Pitstop Analysis MDI 視窗
   - 點擊 **Load Workspace**
   - 選擇 `test_pitstop_2025_usa_r`

4. **預期結果**:
   - ✅ Pitstop Analysis 視窗成功重新打開
   - ✅ 顯示相同的賽事參數（Year/Race/Session）
   - ✅ 日誌顯示：`[WORKSPACE] ✅ Pitstop Analysis 模組已創建`

---

### 階段 2: 測試 Accident Analysis

1. **打開模組**:
   - 從左側樹狀選單打開 **Accident Analysis**
   - 確認視窗正常顯示事故統計

2. **保存 Workspace**:
   ```
   Workspace 名稱: test_accident_2025_usa_r
   ```

3. **關閉視窗並載入**:
   - 關閉 Accident Analysis MDI 視窗
   - 點擊 **Load Workspace**
   - 選擇 `test_accident_2025_usa_r`

4. **預期結果**:
   - ✅ Accident Analysis 視窗成功重新打開
   - ✅ 顯示相同的賽事參數
   - ✅ 日誌顯示：`[WORKSPACE] ✅ Accident Analysis 模組已創建`

---

### 階段 3: 測試 Telemetry Analysis

1. **打開模組**:
   - 從左側樹狀選單打開 **Telemetry Analysis**
   - 確認視窗正常顯示遙測數據

2. **保存 Workspace**:
   ```
   Workspace 名稱: test_telemetry_2025_usa_r
   ```

3. **關閉視窗並載入**:
   - 關閉 Telemetry Analysis MDI 視窗
   - 點擊 **Load Workspace**
   - 選擇 `test_telemetry_2025_usa_r`

4. **預期結果**:
   - ✅ Telemetry Analysis 視窗成功重新打開
   - ✅ 顯示相同的賽事參數
   - ✅ 日誌顯示：`[WORKSPACE] ✅ Telemetry Analysis 模組已創建`

---

### 階段 4: 混合測試（所有模組）

1. **同時打開多個模組**:
   - Rain Analysis
   - Pitstop Analysis
   - Accident Analysis
   - Telemetry Analysis

2. **保存 Workspace**:
   ```
   Workspace 名稱: test_all_modules_2025_usa_r
   ```

3. **關閉所有視窗並載入**:
   - 關閉所有 MDI 視窗
   - 點擊 **Load Workspace**
   - 選擇 `test_all_modules_2025_usa_r`

4. **預期結果**:
   - ✅ 所有 4 個視窗成功重新打開
   - ✅ 每個視窗顯示正確的內容
   - ✅ 日誌顯示所有模組成功創建

---

## 🔍 日誌驗證命令

測試後執行以下命令檢查日誌：

```powershell
# 檢查最新的 Workspace 操作
Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String "WORKSPACE"

# 檢查特定模組創建
Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String "Pitstop|Accident|Telemetry"

# 檢查錯誤
Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String "ERROR|Exception|Traceback"
```

---

## 📊 預期日誌輸出

成功載入時應看到：

```
[WORKSPACE] 🔄 開始反序列化 Workspace...
[WORKSPACE] 🔨 重建分頁: 'Tab 1' (4 個視窗)
[WORKSPACE] ✅ 已創建分頁: 'Tab 1' (index=1)

[WORKSPACE] 🔨 重建視窗: '🌧️ Rain Analysis_2025_United States_R' (type=rain_weather)
[WORKSPACE] 🔧 創建模組: type=rain_weather, params={'year': '2025', 'race': 'United States', 'session': 'R'}
[WORKSPACE] ✅ Rain Analysis 模組已創建 (type=rain_weather)
[WORKSPACE] ✅ 視窗已重建: '🌧️ Rain Analysis_2025_United States_R'

[WORKSPACE] 🔨 重建視窗: '⛽ Pitstop Analysis_2025_United States_R' (type=pitstop)
[WORKSPACE] 🔧 創建模組: type=pitstop, params={'year': '2025', 'race': 'United States', 'session': 'R'}
[WORKSPACE] ✅ Pitstop Analysis 模組已創建
[WORKSPACE] ✅ 視窗已重建: '⛽ Pitstop Analysis_2025_United States_R'

[WORKSPACE] 🔨 重建視窗: '🚨 Accident Analysis_2025_United States_R' (type=accident)
[WORKSPACE] 🔧 創建模組: type=accident, params={'year': '2025', 'race': 'United States', 'session': 'R'}
[WORKSPACE] ✅ Accident Analysis 模組已創建
[WORKSPACE] ✅ 視窗已重建: '🚨 Accident Analysis_2025_United States_R'

[WORKSPACE] 🔨 重建視窗: '🚗 Telemetry Analysis_2025_United States_R' (type=telemetry)
[WORKSPACE] 🔧 創建模組: type=telemetry, params={'year': '2025', 'race': 'United States', 'session': 'R'}
[WORKSPACE] ✅ Telemetry Analysis 模組已創建
[WORKSPACE] ✅ 視窗已重建: '🚗 Telemetry Analysis_2025_United States_R'

[WORKSPACE] ✅ 已設定活動分頁: index=1
[WORKSPACE] ✅ Workspace 反序列化完成！
```

---

## 🐛 故障排除

### 問題 1: 模組未正確打開
**症狀**: Load 後視窗沒有出現

**檢查步驟**:
1. 查看日誌是否有 "不支援的視窗類型" 錯誤
2. 確認模組的 `analysis_type` 是否與 `_create_module_instance` 中的匹配
3. 執行：
   ```powershell
   Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 50 | Select-String "不支援"
   ```

### 問題 2: 參數未正確設定
**症狀**: 視窗打開但顯示錯誤的賽事

**檢查步驟**:
1. 確認序列化時參數是否正確保存到資料庫
2. 檢查反序列化時參數是否正確提取
3. 執行：
   ```powershell
   python -c "import sqlite3; conn=sqlite3.connect('workspaces/f1t_workspaces.db'); c=conn.cursor(); c.execute('SELECT window_type, parameters FROM mdi_windows ORDER BY id DESC LIMIT 5'); [print(row) for row in c.fetchall()]"
   ```

### 問題 3: 模組導入失敗
**症狀**: 日誌顯示 ImportError 或 ModuleNotFoundError

**解決方案**:
1. 確認模組檔案路徑正確
2. 檢查類別名稱拼寫
3. 確認模組已正確安裝

---

## 📝 測試報告模板

測試完成後請報告：

```
測試時間：[時間]

✅ Pitstop Analysis:
- 打開: [成功/失敗]
- 保存: [成功/失敗]
- 載入: [成功/失敗]
- 備註: [任何觀察]

✅ Accident Analysis:
- 打開: [成功/失敗]
- 保存: [成功/失敗]
- 載入: [成功/失敗]
- 備註: [任何觀察]

✅ Telemetry Analysis:
- 打開: [成功/失敗]
- 保存: [成功/失敗]
- 載入: [成功/失敗]
- 備註: [任何觀察]

✅ 混合測試:
- 所有模組同時載入: [成功/失敗]
- 備註: [任何觀察]

日誌片段：
[貼上相關日誌]

問題描述（如有）：
[描述問題]
```

---

## 🎯 下一步

測試通過後，可以繼續添加更多模組：
- Driver Standings
- Constructor Standings
- Season Progress
- Lap Box Plot
- 等等...

參考文檔：`docs/WORKSPACE_MODULE_MAPPING.md`
