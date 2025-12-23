# Workspace 載入後 Race 變更響應測試報告

## 🎯 測試目標
驗證從 workspace 載入的模組能否正確響應主視窗的 race 變更信號。

## 📋 測試前提

### 問題描述
- **現象**：從 workspace 載入的模組（假設有 5 個分頁），在其中一個分頁更換 race 時，其他分頁不會更新
- **對比**：手動開啟的模組則會正常更新

### 根本原因分析
1. **遙測分析模組**：已正確註冊到 `lap_analysis_windows`，通過 `on_lap_analysis_window_opened()` 方法
2. **賽事級分析模組**（rain, pitstop, accident, tire, ideal_lap, track 等）：
   - 從 workspace 載入時**未被註冊到任何追蹤列表**
   - `_get_telemetry_analysis_windows()` 會從 Tab 中查找模組
   - **關鍵問題**：這些模組缺少 `analysis_type` 屬性，導致無法被檢測到

## 🔧 修復方案

### 修改位置
**檔案**：`core/workspace_serializer.py`  
**方法**：`_rebuild_mdi_window()`

### 修改內容
在註冊遙測分析視窗之前，為**所有分析模組**統一設置 `analysis_type` 屬性：

```python
# 步驟 12: 為所有分析模組設置 analysis_type 屬性
# ✅ 關鍵修復：確保所有模組都能被 _get_telemetry_analysis_windows() 檢測到
print(f"[WORKSPACE] 🏷️ 為模組設置 analysis_type 屬性: {window_type}")

# 設置 analysis_type 到模組
if not hasattr(analysis_module, 'analysis_type'):
    analysis_module.analysis_type = window_type
    print(f"[WORKSPACE] ✅ 已設置 analysis_module.analysis_type = '{window_type}'")
else:
    print(f"[WORKSPACE] ℹ️  模組已有 analysis_type = '{analysis_module.analysis_type}'")

# 步驟 13: 註冊遙測分析視窗（如果是遙測模組）
# ... 原有的遙測註冊邏輯
```

### 為什麼這個修復有效？

1. **`_get_telemetry_analysis_windows()` 的檢測邏輯**：
   ```python
   # 在 f1t_gui_main.py 的 _get_telemetry_analysis_windows() 中
   # 會檢查所有 tab 的 widget 是否有 analysis_type 屬性
   if hasattr(widget, 'analysis_type'):
       analysis_type_value = widget.analysis_type
       if analysis_type_value in all_analysis_types:
           analysis_windows.append(widget)  # ✅ 添加到更新列表
   ```

2. **修復後的流程**：
   ```
   Workspace 載入 → _rebuild_mdi_window()
   ↓
   創建分析模組 (analysis_module)
   ↓
   設置 analysis_module.analysis_type = window_type  ← ✅ 新增步驟
   ↓
   添加到 MDI 區域
   ↓
   註冊遙測模組（如果是遙測類型）
   ↓
   Race 變更時 → _get_telemetry_analysis_windows()
   ↓
   檢測到 analysis_type 屬性 → 添加到更新列表  ← ✅ 現在能檢測到了
   ↓
   調用 update_parameters() 更新模組  ← ✅ 所有模組都會更新
   ```

## 🧪 測試步驟

### 步驟 1: 準備測試環境
1. ✅ 確保修改已應用到 `core/workspace_serializer.py`
2. ✅ 確保語法正確（已通過 `python -m py_compile` 驗證）

### 步驟 2: 創建測試 Workspace
1. 啟動 F1T GUI：
   ```powershell
   python f1t_gui_main.py
   ```

2. 手動開啟多個不同類型的分析模組（至少包含）：
   - ✅ Rain Analysis (賽事級)
   - ✅ Pitstop Analysis (賽事級)
   - ✅ Speed Analysis (遙測級)
   - ✅ Brake Analysis (遙測級)
   - ✅ Ideal Lap Ranking (賽事級)

3. 確認所有模組都能響應 Race 變更：
   - 在任一分頁更換 Race
   - 觀察其他分頁是否自動更新

4. 保存 Workspace：
   - File → Save Workspace
   - 命名為 "Test_Race_Change_Response"

### 步驟 3: 測試 Workspace 載入
1. 關閉 GUI

2. 重新啟動 GUI：
   ```powershell
   python f1t_gui_main.py
   ```

3. 載入 Workspace：
   - File → Load Workspace
   - 選擇 "Test_Race_Change_Response"

4. 等待所有模組載入完成

### 步驟 4: 驗證 Race 變更響應

#### 測試 4.1: 檢查 analysis_type 屬性
在任一模組的 Python REPL 或調試器中檢查：
```python
# 在 _get_telemetry_analysis_windows() 添加調試輸出
# 觀察 console 是否顯示：
# [WORKSPACE] ✅ 已設置 analysis_module.analysis_type = 'rain_weather'
# [WORKSPACE] ✅ 已設置 analysis_module.analysis_type = 'pitstop'
# ... 等
```

#### 測試 4.2: 實際變更 Race
1. 切換到分頁 1（例如 Rain Analysis）
2. 在主視窗的 Race 下拉選單中選擇不同的 Race（例如從 "Japan" 改為 "Australia"）
3. 觀察：
   - ✅ 分頁 1 的 Rain Analysis 是否更新？
   - ✅ 切換到分頁 2（例如 Pitstop Analysis），內容是否自動更新？
   - ✅ 切換到分頁 3（例如 Speed Analysis），內容是否自動更新？
   - ✅ 切換到分頁 4（例如 Brake Analysis），內容是否自動更新？
   - ✅ 切換到分頁 5（例如 Ideal Lap Ranking），內容是否自動更新？

#### 測試 4.3: 檢查 Console 日誌
觀察 console 輸出，應該看到：
```
[RACE_CONTROL] 賽事參數已變更:
[RACE_CONTROL]   年份: '2025'
[RACE_CONTROL]   賽事: 'Australia'
[RACE_CONTROL]   賽段: 'R'
[RACE_CONTROL] 發現 5 個需要更新的分析視窗  ← ✅ 應該檢測到所有模組
  ✅ 找到 Tab 視窗 (widget): rain_weather
  ✅ 找到 Tab 視窗 (widget): pitstop
  ✅ 找到 MDI 視窗: speed (id=...)
  ✅ 找到 MDI 視窗: brake (id=...)
  ✅ 找到 Tab 視窗 (widget): ideal_lap_ranking
[RACE_CONTROL] 開始自動更新所有視窗...
```

## ✅ 預期結果

### 修復前（問題狀態）
- ❌ 從 workspace 載入的賽事級分析模組（rain, pitstop, accident 等）**不響應** race 變更
- ✅ 從 workspace 載入的遙測級分析模組（speed, brake 等）**能響應** race 變更
- ✅ 手動開啟的所有模組**都能響應** race 變更

### 修復後（期望狀態）
- ✅ 從 workspace 載入的**所有模組**（賽事級 + 遙測級）**都能響應** race 變更
- ✅ 手動開啟的所有模組**都能響應** race 變更
- ✅ 所有模組的行為完全一致，無論載入方式

## 🔍 故障排除

### 如果測試失敗

#### 問題 1: 仍然無法響應 Race 變更
**檢查步驟**：
1. 確認 `analysis_type` 是否正確設置：
   ```python
   # 在 _rebuild_mdi_window() 中添加調試輸出
   print(f"[DEBUG] analysis_module type: {type(analysis_module)}")
   print(f"[DEBUG] hasattr analysis_type: {hasattr(analysis_module, 'analysis_type')}")
   print(f"[DEBUG] analysis_type value: {getattr(analysis_module, 'analysis_type', None)}")
   ```

2. 確認 `_get_telemetry_analysis_windows()` 是否檢測到：
   ```python
   # 在 _get_telemetry_analysis_windows() 中檢查
   print(f"[DEBUG] Checking widget: {widget}")
   print(f"[DEBUG] Has analysis_type: {hasattr(widget, 'analysis_type')}")
   print(f"[DEBUG] analysis_type value: {getattr(widget, 'analysis_type', None)}")
   ```

#### 問題 2: 只有部分模組響應
**檢查步驟**：
1. 確認 `all_analysis_types` 集合是否包含該模組類型
2. 確認 `window_type` 與 `all_analysis_types` 中的字串完全匹配（大小寫敏感）

#### 問題 3: Console 沒有輸出調試信息
**檢查步驟**：
1. 確認是否真的觸發了 race 變更事件
2. 確認 `on_race_parameters_changed()` 是否被調用
3. 檢查 `_get_telemetry_analysis_windows()` 的返回值

## 📊 測試記錄模板

```markdown
### 測試執行記錄

**測試日期**：2025-10-XX  
**測試人員**：[Your Name]  
**F1T 版本**：[Version]

#### 測試結果

| 模組類型 | 載入方式 | Race 變更響應 | 備註 |
|---------|---------|-------------|------|
| Rain Analysis | Workspace 載入 | ✅ 成功 / ❌ 失敗 | |
| Pitstop Analysis | Workspace 載入 | ✅ 成功 / ❌ 失敗 | |
| Speed Analysis | Workspace 載入 | ✅ 成功 / ❌ 失敗 | |
| Brake Analysis | Workspace 載入 | ✅ 成功 / ❌ 失敗 | |
| Ideal Lap Ranking | Workspace 載入 | ✅ 成功 / ❌ 失敗 | |

#### Console 日誌摘錄

```
[貼上相關的 console 輸出]
```

#### 問題 / 觀察

[記錄測試過程中發現的任何問題或異常行為]
```

## 🎓 技術總結

### 關鍵學習點

1. **模組追蹤機制**：
   - 遙測模組：通過 `lap_analysis_windows` 集合追蹤
   - 賽事級模組：通過 Tab widget 的 `analysis_type` 屬性檢測

2. **信號連接的重要性**：
   - 手動開啟：自動設置所有必要的屬性和信號連接
   - Workspace 載入：必須手動複製相同的初始化邏輯

3. **調試技巧**：
   - 使用 `hasattr()` 檢查屬性是否存在
   - 使用 `type()` 和 `id()` 追蹤對象實例
   - 在關鍵路徑添加調試輸出

### 未來改進建議

1. **統一註冊機制**：
   - 考慮創建統一的 `register_analysis_module()` 方法
   - 無論手動開啟還是 workspace 載入，都使用相同的註冊流程

2. **自動化測試**：
   - 創建單元測試驗證 workspace 載入的模組屬性
   - 創建整合測試驗證 race 變更響應

3. **文檔完善**：
   - 在模組開發指南中明確說明必須設置 `analysis_type` 屬性
   - 提供模組註冊的標準流程文檔

---

**修復版本**：2025-10-25  
**修復作者**：GitHub Copilot  
**關聯問題**：Workspace 載入模組無法響應 race 變更
