# 速度模組記憶體洩漏測試指南 v3.3

## 🔍 **為什麼需要重新測試？**

### 重大發現：舊版程式碼正在執行！

查看 19:32 測試的日誌：
```
19:32:23 [ANALYSIS_MANAGER] Unregistered chart widget: SpeedAnalysisChartWidget  ← 舊版輸出
19:32:23 [SPEED_MDI] ✅ 已從分析模組管理器解除註冊
19:32:23 [SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件
```

**問題**：沒有看到新增的 `🔍` 診斷輸出！

**原因**：
1. Python 使用了緩存的 `.pyc` 檔案
2. 或 GUI 在修改前就已啟動

**已執行的修復**：
- ✅ 清理了 `lap_analysis` 目錄的 `__pycache__`
- ✅ 清理了 `linkage` 目錄的 `__pycache__`
- ✅ 確認新程式碼已正確保存

---

## 🎯 **測試目標**

驗證 `unregister_chart_widget()` 和 `unregister_module()` 是否真正從 list 中移除了引用。

### 關鍵問題

1. ❓ widget 是否在 list 中？
2. ❓ widget ID 是否匹配 list 中的 ID？
3. ❓ remove() 是否成功執行？
4. ❓ list 長度是否從 N 降為 N-1？

---

## 📋 **測試步驟**

### 1. 確保 GUI 已關閉

```powershell
# 強制關閉所有 Python 進程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
```

### 2. 啟動 GUI

```powershell
python f1t_gui_main.py
```

### 3. 執行測試操作

1. ✅ 開啟速度分析模組
2. ⏳ 等待 5 秒（確保完全載入）
3. ❌ 關閉速度分析模組
4. ⏳ 等待 5 秒（確保完全清理）

### 4. 檢查日誌

```powershell
# 搜尋新版診斷輸出（帶 🔍）
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "ANALYSIS_MANAGER.*🔍|LINKAGE_MANAGER.*🔍" | Select-Object -Last 20

# 檢查是否成功移除
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已從 list 移除|不在 list 中" | Select-Object -Last 10

# 檢查 GC 結果
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 5
```

---

## 🔍 **預期輸出對比**

### ✅ 新版輸出（v3.3）

```
[ANALYSIS_MANAGER] 🔍 unregister 前: list 長度 = 1
[ANALYSIS_MANAGER] 🔍 widget 在 list 中: True
[ANALYSIS_MANAGER] 🔍 widget ID: 2261568941536
[ANALYSIS_MANAGER] 🔍 list 中的 ID: [2261568941536]
[ANALYSIS_MANAGER] ✅ 已從 list 移除
[ANALYSIS_MANAGER] 🔍 unregister 後: list 長度 = 0
[ANALYSIS_MANAGER] Unregistered chart widget: SpeedAnalysisChartWidget

[LINKAGE_MANAGER] 🔍 unregister 前: list 長度 = 1
[LINKAGE_MANAGER] 🔍 module 在 list 中: True
[LINKAGE_MANAGER] 🔍 module ID: 2261568941536
[LINKAGE_MANAGER] 🔍 list 中的 ID: [2261568941536]
[LINKAGE_MANAGER] ✅ 已從 list 移除
[LINKAGE_MANAGER] 🔍 unregister 後: list 長度 = 0
```

### ❌ 舊版輸出（v3.2，已過時）

```
[ANALYSIS_MANAGER] Unregistered chart widget: SpeedAnalysisChartWidget
[SPEED_MDI] ✅ 已從分析模組管理器解除註冊
[SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件
```

---

## 🎯 **三種可能結果分析**

### 場景 A：List 成功移除 + GC 回收 > 0

```
[ANALYSIS_MANAGER] ✅ 已從 list 移除
[LINKAGE_MANAGER] ✅ 已從 list 移除
[SPEED_MDI] ✅ 已執行垃圾回收（回收 582 個物件）  ← 成功！
```

**結論**：✅ **問題解決！** list 成功釋放引用，GC 回收了洩漏的物件。

---

### 場景 B：List 成功移除 + GC 回收 0

```
[ANALYSIS_MANAGER] ✅ 已從 list 移除
[ANALYSIS_MANAGER] 🔍 unregister 後: list 長度 = 0
[LINKAGE_MANAGER] ✅ 已從 list 移除
[LINKAGE_MANAGER] 🔍 unregister 後: list 長度 = 0
[SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）  ← 仍然失敗
```

**結論**：❌ **還有其他隱藏引用！**

**下一步診斷**：
1. 檢查 `dict` 引用（模組的 `__dict__`）
2. 檢查 `QWidget` 父容器引用
3. 檢查 `builtin_function_or_method` 引用
4. 使用 `gc.get_referrers()` 追蹤剩餘的引用來源

---

### 場景 C：Widget 不在 List 中

```
[ANALYSIS_MANAGER] 🔍 widget 在 list 中: False
[ANALYSIS_MANAGER] ⚠️ widget 不在 list 中，無法移除
[ANALYSIS_MANAGER] 🔍 widget ID: 2261568941536
[ANALYSIS_MANAGER] 🔍 list 中的 ID: [2261568999999]  ← ID 不匹配！
```

**結論**：❌ **Register 和 Unregister 的物件不一致！**

**可能原因**：
1. Register 時註冊的是 `widget_A`
2. Unregister 時傳入的是 `widget_B`
3. 兩者 ID 不同，`in` 檢查失敗

**下一步診斷**：
1. 檢查 `register_chart_widget()` 的調用點
2. 檢查 `unregister_chart_widget()` 傳入的參數
3. 確認是否有物件替換或重新創建的情況

---

## 📊 **測試後需要提供的資訊**

請在測試後提供以下日誌搜尋結果：

### 1. 完整的 unregister 診斷輸出

```powershell
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "🔍" | Select-Object -Last 30
```

### 2. GC 回收結果

```powershell
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 5
```

### 3. 完整的清理流程

```powershell
$timestamp = (Get-Date).ToString("HH:mm")
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "$timestamp.*\[(CRITICAL|SPEED_MDI|ANALYSIS_MANAGER|LINKAGE_MANAGER)\]" | Select-Object -Last 50
```

---

## 🔧 **如果看不到新版輸出**

### 檢查清單

1. ✅ 確認 GUI 已關閉
   ```powershell
   Get-Process python -ErrorAction SilentlyContinue
   ```
   應該沒有輸出

2. ✅ 確認緩存已清理
   ```powershell
   Get-ChildItem -Path "modules\gui\lap_analysis" -Include "__pycache__" -Recurse
   ```
   應該沒有輸出

3. ✅ 確認程式碼已保存
   ```powershell
   Select-String -Path "modules\gui\lap_analysis\analysis_module_manager.py" -Pattern "🔍 unregister"
   ```
   應該有 2 個匹配

4. ✅ 重新啟動 GUI
   ```powershell
   python f1t_gui_main.py
   ```

---

## 📝 **總結**

### 為什麼需要重新測試？

因為 19:32 的測試使用的是**舊版程式碼**（沒有 `🔍` 診斷輸出），無法看到：

1. ❓ widget 是否在 list 中
2. ❓ widget ID 是否匹配
3. ❓ list 長度變化
4. ❓ remove() 是否成功

### 新版測試的價值

新版診斷代碼會告訴我們：

- 如果 **list 成功移除 + GC 仍為 0**
  → 說明還有其他引用（dict, QWidget, builtin_function_or_method）
  
- 如果 **widget 不在 list 中**
  → 說明 register/unregister 的物件不一致
  
- 如果 **ID 不匹配**
  → 說明有物件替換或重新創建的問題

### 差異總結

| 測試版本 | 輸出內容 | 診斷能力 |
|---------|---------|---------|
| v3.2 (19:32) | `Unregistered chart widget` | ❌ 無法診斷 |
| v3.3 (現在) | `🔍 widget 在 list 中: True/False` | ✅ 可以診斷 |

---

**創建時間**：2025-10-15 19:55
**版本**：v3.3 測試指南
**狀態**：等待重新測試
