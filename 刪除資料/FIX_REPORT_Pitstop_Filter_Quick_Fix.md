# ✅ 快速修復：過濾 Pitstop 模組避免誤入 lap_analysis 追蹤

**修復日期**: 2025-10-06  
**修復類型**: 防禦性過濾  
**影響範圍**: `f1t_gui_main.py` - `check_and_show_lap_controls_if_needed` 方法

---

## 🔧 修復內容

### 修改位置
**檔案**: `f1t_gui_main.py`  
**方法**: `check_and_show_lap_controls_if_needed`  
**行數**: ~5840

### 修改前
```python
lap_analysis_windows_found = []
for sub_window in current_mdi_area.subWindowList():
    if not sub_window.isVisible():
        continue

    window_title = sub_window.windowTitle()
    widget = sub_window.widget()
    # 直接檢查模組類型...
```

### 修改後
```python
lap_analysis_windows_found = []
for sub_window in current_mdi_area.subWindowList():
    if not sub_window.isVisible():
        continue

    window_title = sub_window.windowTitle()
    
    # ✅ 修復：過濾進站分析視窗，避免誤認為 lap_analysis 模組
    if any(keyword in window_title for keyword in ["進站分析", "Pitstop", "ピットストップ"]):
        print(f"[LAP_CONTROL] ⏭️  跳過非遙測模組 (Pitstop): {window_title}")
        continue
    
    widget = sub_window.widget()
    # 繼續檢查模組類型...
```

---

## 🎯 修復邏輯

### 問題分析
`check_and_show_lap_controls_if_needed` 方法會掃描所有 MDI 子視窗，尋找遙測分析模組以顯示車手/圈數控件。

**潛在問題**：
- Pitstop 進站分析視窗也可能被誤認為 lap_analysis 模組
- 當 Pitstop 視窗被添加到 `lap_analysis_windows` 追蹤列表後
- 後續的參數更新可能觸發意外行為

### 修復策略
**防禦性過濾**：
- 在檢查模組類型之前，先通過視窗標題過濾
- 明確排除 Pitstop 進站分析視窗
- 支援多語言：中文、英文、日文

### 過濾關鍵字
- "進站分析" (繁體中文)
- "Pitstop" (英文)
- "ピットストップ" (日文)

---

## ✅ 預期效果

### 修復前行為
1. 用戶開啟 RPM 分析視窗
2. 同時開啟 Pitstop 進站分析視窗
3. 切換主視窗賽事/車手
4. 💥 **問題**: Pitstop 視窗可能被誤認為 lap_analysis 模組
5. 💥 **結果**: 意外的視窗創建或參數更新

### 修復後行為
1. 用戶開啟 RPM 分析視窗
2. 同時開啟 Pitstop 進站分析視窗
3. 切換主視窗賽事/車手
4. ✅ **修復**: Pitstop 視窗被正確過濾，不進入追蹤列表
5. ✅ **結果**: 只有 RPM 視窗更新，Pitstop 保持獨立

---

## 🧪 測試計劃

### 測試 1: 單獨 RPM 視窗
```
步驟：
1. 開啟 RPM 分析視窗
2. 切換主視窗賽事
3. 檢查日誌輸出

預期日誌：
[LAP_CONTROL] 🔍 檢查是否需要顯示遙測分析控件...
[LAP_CONTROL] 🎯 發現遙測分析視窗: RPM Analysis - ...
(不應該有 Pitstop 相關輸出)
```

### 測試 2: RPM + Pitstop 混合
```
步驟：
1. 開啟 RPM 分析視窗
2. 開啟 Pitstop 進站分析視窗
3. 切換主視窗賽事
4. 檢查日誌輸出

預期日誌：
[LAP_CONTROL] 🔍 檢查是否需要顯示遙測分析控件...
[LAP_CONTROL] ⏭️  跳過非遙測模組 (Pitstop): 進站分析 - 2025 Japan R
[LAP_CONTROL] 🎯 發現遙測分析視窗: RPM Analysis - ...
```

### 測試 3: 多模組混合
```
步驟：
1. 開啟 RPM + Speed + Gear 分析視窗
2. 開啟 Pitstop 進站分析視窗
3. 切換主視窗賽事
4. 檢查日誌輸出

預期結果：
- 3 個遙測分析視窗正常更新
- Pitstop 視窗被正確過濾
- 不應該有額外的視窗創建
```

---

## 📊 修復驗證

### 靜態檢查
```powershell
# 確認修改已應用
Select-String -Path "f1t_gui_main.py" -Pattern "跳過非遙測模組.*Pitstop" -Context 2,2
```

**預期輸出**:
```
  window_title = sub_window.windowTitle()
  
> # ✅ 修復：過濾進站分析視窗，避免誤認為 lap_analysis 模組
> if any(keyword in window_title for keyword in ["進站分析", "Pitstop", "ピットストップ"]):
>     print(f"[LAP_CONTROL] ⏭️  跳過非遙測模組 (Pitstop): {window_title}")
      continue
  
  widget = sub_window.widget()
```

### 動態測試
```powershell
# 1. 重新打包 EXE（如果需要）
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller F1T_GUI.spec --clean

# 2. 執行 GUI
python f1t_gui_main.py
# 或
.\dist\F1T_GUI\F1T_GUI.exe

# 3. 執行測試計劃 1-3

# 4. 檢查日誌
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "跳過非遙測模組|Pitstop" -Context 1,1 | Select-Object -Last 20
```

---

## 🚨 已知限制

### 限制 1: 依賴視窗標題
- **問題**: 如果 Pitstop 視窗標題不包含關鍵字，過濾會失敗
- **解決方案**: 後續可改為檢查模組類型 (`isinstance(module, PitstopAnalysisModule)`)

### 限制 2: 硬編碼關鍵字
- **問題**: 添加新語言時需要修改程式碼
- **解決方案**: 後續可改為從翻譯檔案讀取關鍵字列表

### 限制 3: 只修復追蹤列表問題
- **問題**: 如果 Pitstop 自動創建是其他原因導致，此修復無效
- **解決方案**: 需要更深入的診斷（見 `DIAGNOSIS_RPM_Auto_Pitstop_Issue.md`）

---

## 🔄 後續改進

### 短期 (本週內)
- [ ] 用戶測試確認問題是否解決
- [ ] 如未解決，執行完整診斷步驟
- [ ] 添加單元測試驗證過濾邏輯

### 中期 (本月內)
- [ ] 重構車手列表載入邏輯，不依賴 Pitstop JSON
- [ ] 實現基於模組類型的過濾 (更可靠)
- [ ] 添加模組創建白名單機制

### 長期 (下個版本)
- [ ] 統一模組追蹤機制
- [ ] 實現模組註冊表 (Registry Pattern)
- [ ] 自動化測試 GUI 視窗創建行為

---

## 📝 補充說明

### 為什麼選擇此修復方案？

1. **快速見效**: 只修改幾行程式碼，立即可測試
2. **低風險**: 只是添加過濾，不改變現有邏輯
3. **易於驗證**: 從日誌即可看到過濾效果
4. **不影響其他模組**: 只排除 Pitstop，不影響其他功能

### 如果問題仍未解決？

請提供以下信息：
1. **日誌輸出**: `dist\logs\f1_gui_*.log` 中包含 "Pitstop" 的所有行
2. **重現步驟**: 詳細的操作步驟（見診斷報告）
3. **視窗標題**: 自動出現的 Pitstop 視窗的完整標題
4. **觸發時機**: 切換賽事？切換車手？其他？

這將幫助我們進行更深入的診斷。

---

**修復工程師**: GitHub Copilot  
**報告日期**: 2025-10-06  
**修復類型**: 快速防禦性修復  
**狀態**: ✅ 已應用，等待測試驗證
