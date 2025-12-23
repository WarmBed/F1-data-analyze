# MDI 標題重複問題修正 - 測試報告

## 問題描述
用戶截圖顯示 All Drivers Straight Line Speed 模組的 MDI 標題重複顯示兩個 race：
```
標題顯示: "All Drivers Straight Line Speed - 2025 China R_2025_Australia_R"
預期標題: "All Drivers Straight Line Speed - 2025 China R"
```

## 根本原因

### 問題追蹤
1. **PopoutSubWindow.update_window_title()** (f1t_gui_main.py Line 2485-2522)
   - 使用 `self.local_year/race/session` 調用 `analysis_module.get_window_title()`
   - 當用戶切換 race 時，模組參數已更新，但 `local_*` 參數可能未同步
   - 導致標題生成時使用混合的新舊參數

2. **標題更新流程**
   ```
   用戶切換 race (Australia → China)
     ↓
   analysis_module.update_parameters(year='2025', race='China', session='R')
     → analysis_module.current_race = 'China' ✅
     → update_window_title() 被調用
     → parent_window 為 None，標題沒有更新 ❌
     ↓
   PopoutSubWindow.update_local_parameters(...) 被調用
     → self.local_race = 'Australia'（未同步） ❌
     → update_window_title() 被調用
     → 使用 local_race='Australia' 調用 analysis_module.get_window_title()
     → 生成錯誤標題
   ```

## 修正方案

### 1. PopoutSubWindow.update_window_title() 修正
**位置**: f1t_gui_main.py Line 2485-2522

**修正前**:
```python
def update_window_title(self):
    if self.analysis_module and hasattr(self.analysis_module, 'get_window_title'):
        new_title = self.analysis_module.get_window_title(
            year=str(self.local_year),      # ❌ 使用 PopoutSubWindow 的本地參數
            race=self.local_race,            # ❌ 可能未同步
            session=self.local_session       # ❌ 可能未同步
        )
```

**修正後**:
```python
def update_window_title(self):
    if self.analysis_module and hasattr(self.analysis_module, 'get_window_title'):
        # ✅ 優先從模組獲取當前參數（確保同步）
        if hasattr(self.analysis_module, 'current_year'):
            year = self.analysis_module.current_year      # ✅ 從模組獲取
            race = self.analysis_module.current_race      # ✅ 從模組獲取
            session = self.analysis_module.current_session # ✅ 從模組獲取
        else:
            year = str(self.local_year)
            race = self.local_race
            session = self.local_session
        
        new_title = self.analysis_module.get_window_title(year, race, session)
```

**效果**:
- 標題生成時優先使用 `analysis_module` 的當前參數
- 確保標題與模組狀態完全同步
- 避免新舊參數混用

### 2. universal_analysis_mdi_base.update_window_title() 增強
**位置**: modules/gui/base/universal_analysis_mdi_base.py Line 850-872

**修正**:
```python
def update_window_title(self) -> None:
    try:
        parent = getattr(self, 'parent_window', None)
        
        if parent and hasattr(parent, 'setWindowTitle'):
            new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
            
            # ✅ 添加調試輸出
            old_title = parent.windowTitle() if hasattr(parent, 'windowTitle') else "N/A"
            parent.setWindowTitle(new_title)  # ✅ 直接替換，不追加
            
            self._debug(f"🏷️ 視窗標題已更新")
            self._debug(f"   舊標題: {old_title}")
            self._debug(f"   新標題: {new_title}")
```

## 測試計劃

### 測試案例 1: 初次開啟模組
**步驟**:
1. 啟動 GUI
2. 主視窗參數：2025, Australia, R
3. 點擊功能樹 → "All Drivers Straight Line Speed"

**預期結果**:
- MDI 標題: `"All Drivers Straight Line Speed - 2025 Australia R"`
- ❌ 不應該是: `"... - 2025 Australia R_2025_Australia_R"`

### 測試案例 2: 切換 Race（核心測試）
**步驟**:
1. 開啟 All Drivers Straight Line Speed（Australia）
2. 主視窗切換 race → China
3. 觀察 MDI 標題變化

**預期結果**:
- 舊標題: `"All Drivers Straight Line Speed - 2025 Australia R"`
- 新標題: `"All Drivers Straight Line Speed - 2025 China R"`
- ❌ 不應該是: `"... - 2025 China R_2025_Australia_R"`

### 測試案例 3: 多次切換 Race
**步驟**:
1. 開啟模組（Australia）
2. 切換到 China
3. 切換到 Japan
4. 切換回 Australia

**預期結果**:
- 每次切換後，MDI 標題應該只顯示最新的 race
- ❌ 不應該累積舊 race 名稱

### 測試案例 4: 同時開啟多個模組
**步驟**:
1. 開啟 All Drivers Straight Line Speed（Australia）
2. 開啟 All Drivers Brake Performance（Australia）
3. 主視窗切換到 China
4. 檢查兩個模組的標題

**預期結果**:
- Speed 標題: `"All Drivers Straight Line Speed - 2025 China R"`
- Brake 標題: `"All Drivers Brake Performance - 2025 China R"`
- ❌ 兩個模組都不應該有重複的 race 名稱

## 調試輸出範例

### 正常流程（修正後）
```
[TITLE] [MODULE] 使用模組標題: All Drivers Straight Line Speed - 2025 China R
[TITLE] [MODULE] 參數: 2025 China R
[LABEL] [TITLE] 標題已更新: All Drivers Straight Line Speed - 2025 China R
```

### 異常流程（修正前）
```
[TITLE] [MODULE] 使用模組標題: All Drivers Straight Line Speed - 2025 China R
[LABEL] [TITLE] 標題已更新: All Drivers Straight Line Speed - 2025 China R_2025_Australia_R
                                                                           ^^^^^^^^^^^^^^^^^^
                                                                           舊標題殘留
```

## 影響範圍

### 修正的模組
- ✅ All Drivers Straight Line Speed（F48）
- ✅ All Drivers Brake Performance（F34）
- ✅ 所有繼承 UniversalAnalysisMDI 的新架構模組

### 不受影響的模組
- ⚪ 賽道分析（舊架構，IAnalysisModule）
- ⚪ 其他舊版模組

## 驗證清單

開發者測試清單：
- [ ] Test Case 1: 初次開啟模組（標題正確）
- [ ] Test Case 2: 切換 Race（標題更新正確）
- [ ] Test Case 3: 多次切換 Race（標題不累積）
- [ ] Test Case 4: 多個模組同時開啟（標題互不干擾）
- [ ] 檢查控制台輸出（調試信息正確）
- [ ] 檢查是否有 AttributeError 或 TypeError

用戶驗收清單：
- [ ] 視覺確認：MDI 標題只顯示最新的 race
- [ ] 功能確認：切換 race 後數據正確載入
- [ ] 性能確認：標題更新無明顯延遲

## 回歸測試

確保以下功能未受影響：
- [ ] 模組數據載入功能
- [ ] 圖表繪製功能
- [ ] 參數同步功能
- [ ] MDI 子視窗關閉功能
- [ ] 舊架構模組（賽道分析）

## 已知限制

1. **PopoutSubWindow.local_* 參數可能仍未同步**
   - 但不影響標題生成（優先使用 analysis_module 參數）
   - 未來可能需要統一參數同步機制

2. **parent_window 未設置時標題不更新**
   - 在 PopoutSubWindow 構造函數初始同步時會發生
   - 但最終標題會在 PopoutSubWindow.update_window_title() 被正確設置

## 相關文件

- 原始需求：用戶截圖和描述
- 相關代碼：
  - `f1t_gui_main.py` Line 2485-2522 (PopoutSubWindow.update_window_title)
  - `universal_analysis_mdi_base.py` Line 850-872 (update_window_title)
  - `universal_analysis_mdi_base.py` Line 355-375 (get_window_title)

## 結論

✅ **修正完成**，核心改動：
1. `PopoutSubWindow.update_window_title()` 優先從 `analysis_module` 獲取參數
2. 增強調試輸出以便追蹤標題變化

🧪 **建議測試**：
- 啟動 GUI → 開啟 All Drivers Straight Line Speed → 切換 race → 驗證標題正確

📋 **後續優化**（可選）：
- 統一 `PopoutSubWindow.local_*` 和 `analysis_module.current_*` 的同步機制
- 考慮移除 `local_*` 參數，完全依賴 `analysis_module` 的狀態
