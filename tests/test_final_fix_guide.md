# 🎯 最終測試指南：rain_weather 完整修復驗證

## 🔧 修復內容
已在 `core/workspace_serializer.py` 的 `_create_module_instance` 方法中添加 `rain_weather` 類型支援。

**修改位置：第 646 行**
```python
# 修改前：
if window_type == "rain_analysis":

# 修改後：
if window_type in ("rain_analysis", "rain_weather"):
```

## ✅ 代碼驗證結果
```
✅ rain_weather 在條件中: True
✅ rain_analysis 在條件中: True  
✅ 使用 in 運算符: True
✅ 導入 RainAnalysisModuleAdapter: True
```

---

## 🧪 手動測試步驟（GUI 環境）

### 步驟 1: 啟動 GUI
```powershell
python f1t_gui_main.py
```

### 步驟 2: 打開 Rain Analysis
1. 從左側樹狀選單找到 **Rain Analysis**
2. 點擊打開（建議使用已有數據的賽事，例如 2025 USA R）
3. 等待視窗完全載入並顯示圖表

### 步驟 3: 保存 Workspace
1. 點擊主視窗的 **Save Workspace** 按鈕
2. 輸入測試名稱：`test_rain_weather_fix`
3. 確認保存成功

### 步驟 4: 關閉視窗
1. 關閉 Rain Analysis MDI 視窗（點擊 X）
2. 確認 MDI 區域為空

### 步驟 5: 載入 Workspace
1. 點擊主視窗的 **Load Workspace** 按鈕
2. 選擇剛才保存的 `test_rain_weather_fix`
3. 等待視窗重建

---

## 🎯 預期結果

### ✅ 成功標誌：
1. **視窗出現**：Rain Analysis 視窗成功重新打開
2. **參數正確**：視窗標題顯示正確的 Year/Race/Session
3. **圖表顯示**：視窗中的圖表正確顯示（如有緩存數據）
4. **日誌正確**：查看 `logs/f1_gui_2025-10-21.log` 應顯示：
   ```
   [WORKSPACE] 🔨 重建視窗: type=rain_weather
   [WORKSPACE] 🔧 創建模組: type=rain_weather, params={'year': '2025', ...}
   [WORKSPACE] ✅ Rain Analysis 模組已創建 (type=rain_weather)
   [WORKSPACE] ✅ Rain Analysis 視窗重建成功
   ```

### ❌ 失敗標誌：
1. 視窗沒有出現
2. 日誌顯示 "⚠️ 不支援的視窗類型: rain_weather"
3. 任何異常或錯誤訊息

---

## 📋 測試檢查清單

- [ ] GUI 啟動成功
- [ ] Rain Analysis 打開並正常顯示
- [ ] Save Workspace 成功（無錯誤）
- [ ] 關閉 MDI 視窗（MDI 區域為空）
- [ ] Load Workspace 執行
- [ ] Rain Analysis 視窗重新出現
- [ ] 視窗參數正確（Year/Race/Session）
- [ ] 日誌顯示 "✅ Rain Analysis 模組已創建 (type=rain_weather)"

---

## 🐛 故障排除

### 如果視窗仍未出現：
1. 查看日誌文件最後 100 行：
   ```powershell
   Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String "WORKSPACE"
   ```

2. 檢查資料庫內容：
   ```powershell
   python -c "import sqlite3; conn=sqlite3.connect('workspaces/f1t_workspaces.db'); c=conn.cursor(); c.execute('SELECT window_type, parameters FROM mdi_windows WHERE workspace_id=(SELECT id FROM workspaces ORDER BY created_at DESC LIMIT 1)'); print(c.fetchall())"
   ```

3. 檢查是否有其他錯誤：
   ```powershell
   Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 50 | Select-String "ERROR|Exception|Traceback"
   ```

---

## 🔍 修復歷史

### 第一階段：序列化修復（已完成）
- **問題**：所有視窗保存為 "unknown" 類型
- **原因**：`subwindow.widget()` 返回 UI 容器而非實際模組
- **解決**：修改 `_serialize_mdi_window` 檢查 `subwindow.analysis_module`
- **結果**：✅ 正確保存為 "rain_weather" 類型

### 第二階段：反序列化修復（本次完成）
- **問題**：載入時報錯 "不支援的視窗類型: rain_weather"
- **原因**：`_create_module_instance` 只支援 "rain_analysis"
- **解決**：修改條件為 `in ("rain_analysis", "rain_weather")`
- **結果**：✅ 代碼驗證通過，等待 GUI 測試

---

## 📊 測試報告模板

請在測試後報告結果：

```
測試時間：[時間]
測試結果：[成功/失敗]

詳細記錄：
- GUI 啟動：[✅/❌]
- Save Workspace：[✅/❌]
- Load Workspace：[✅/❌]
- 視窗重建：[✅/❌]
- 參數正確：[✅/❌]

日誌片段：
[貼上相關日誌]

問題描述（如失敗）：
[描述問題]
```
