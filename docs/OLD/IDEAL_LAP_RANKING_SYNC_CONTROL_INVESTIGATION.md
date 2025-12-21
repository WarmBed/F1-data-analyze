# 🔍 Ideal Lap Ranking Table 同步控制深度調查報告

> **調查日期**: 2025-10-20  
> **調查對象**: Ideal Lap Ranking Table 模組  
> **調查目的**: 確認同步控制行為是否符合使用者期望  
> **調查員**: GitHub Copilot AI Assistant

---

## 📋 使用者期望

### **期望行為**:
1. ✅ **取消勾選同步後**：MDI 視窗不會被主 GUI 的 year/race/session 更新
2. ✅ **MDI 自己更新參數時**：也不會同步主 GUI 的 year/race/session

---

## 🔬 調查方法

### **反幻覺編碼五原則執行**:
- ✅ 原則 1: 使用 `grep_search` 和 `read_file` 驗證所有方法
- ✅ 原則 2: 檢查 `modules/gui/` 資料夾既有實現
- ✅ 原則 3: 確認使用通用模組架構
- ✅ 原則 4: 檢查多國語言化
- ✅ 原則 5: 查看 log 確認執行結果

### **逐行代碼檢查範圍**:
1. `ideal_lap_ranking_table_module.py` (完整 442 行)
2. `ideal_lap_ranking_table_mdi.py` (Line 1-590, 關鍵方法)
3. `f1t_gui_main.py` PopoutSubWindow 同步機制 (Line 4387-4454)
4. `f1t_gui_main.py` 主視窗參數變更 (Line 3316-3383)
5. `f1t_gui_main.py` 參數廣播機制 (Line 9779-9879)
6. `f1t_gui_main.py` 批次更新機制 (Line 7303-7962)

---

## 📊 調查結果

### **✅ 期望 1: 取消勾選同步後，MDI 不會被主 GUI 更新**

#### **實現位置**: `f1t_gui_main.py:4387-4421`

```python
def receive_main_window_update_notification(self, param_type, value):
    """接收主視窗參數變更通知"""
    window_title = self.windowTitle()
    print(f"[ANNOUNCE] [NOTIFICATION] {window_title} 收到主視窗更新通知: {param_type}={value}")
    
    # 檢查同步狀態 - 支援多種同步狀態檢查方式
    sync_enabled = False
    
    # 方法1: 檢查 sync_windows_checkbox (用於有控制面板的子視窗)
    if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox:
        sync_enabled = self.sync_windows_checkbox.isChecked()
        print(f"[SEARCH] [NOTIFICATION] {window_title} 使用 checkbox 檢查同步狀態: {sync_enabled}")
    
    # 方法2: 檢查 sync_enabled 屬性 (用於 PopoutSubWindow 等)
    elif hasattr(self, 'sync_enabled'):
        sync_enabled = self.sync_enabled
        print(f"[SEARCH] [NOTIFICATION] {window_title} 使用屬性檢查同步狀態: {sync_enabled}")
    
    # 如果未啟用同步，直接返回 ← ✅ 關鍵保護！
    if not sync_enabled:
        print(f"🔴 [NOTIFICATION] {window_title} 同步已停用，忽略更新通知")
        return  # ← ✅ 直接返回，不更新！
    
    print(f"[GREEN] [NOTIFICATION] {window_title} 同步已啟用，處理參數更新")
    
    # [TOOL] 更新本地參數（同步模式）
    if param_type == 'year':
        self.local_year = value
    elif param_type == 'race':
        self.local_race = value
    elif param_type == 'session':
        self.local_session = value
    
    # [TOOL] 立即更新標題
    self.update_window_title()
    
    # 使用統一的方法更新視窗內容
    try:
        success = self.update_current_window()
        # ...
```

#### **行為驗證**:

| 步驟 | 代碼位置 | 行為 | 符合期望? |
|-----|---------|------|---------|
| 1. 主 GUI 參數變更 | Line 3316-3383 | `on_year_changed()` 觸發 | - |
| 2. 延遲廣播 | Line 3332 | `_schedule_parameter_broadcast()` 延遲 350ms | - |
| 3. 執行廣播 | Line 9779-9820 | `_broadcast_pending_parameters()` 調用 `on_race_parameters_changed()` | - |
| 4. 批次更新 | Line 7812-7868 | `on_race_parameters_changed()` 調用 `update_all_lap_analysis()` | - |
| 5. 發送通知 | Line 8648-8650 | `receive_main_window_update_notification()` 被調用 | - |
| 6. **檢查同步狀態** | Line 4394-4405 | `sync_enabled = self.sync_enabled` 檢查 | **✅** |
| 7. **如果未啟用同步** | Line 4407-4410 | `if not sync_enabled: return` **直接返回** | **✅ 符合期望！** |

#### **結論**:
✅ **完全符合期望**！當 `sync_enabled = False` 時，MDI 視窗會在 Line 4409 直接 `return`，**不會執行任何更新操作**。

---

### **✅ 期望 2: MDI 自己更新參數時，不會同步主 GUI**

#### **實現位置**: `ideal_lap_ranking_table_mdi.py:534-573`

```python
def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
    """
    更新分析參數並重新載入資料
    
    Args:
        year: 新的年份
        race: 新的賽事
        session: 新的賽段
        
    Returns:
        bool: 更新是否成功
    """
    try:
        print(f"[IDEAL_LAP_MDI] 🔄 更新參數: {year} {race} {session}")
        
        # 更新內部參數 ← ✅ 只更新本地參數！
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        self.year = str(year)
        self.race = race
        self.session = session
        
        # 同時更新 DataLoader 的參數 ← ✅ 只更新 DataLoader！
        if hasattr(self, 'data_manager') and self.data_manager:
            self.data_manager.year = str(year)
            self.data_manager.race = race
            self.data_manager.session = session
            print(f"[IDEAL_LAP_MDI] ✅ DataManager 參數已同步")
        elif hasattr(self, 'data_loader') and self.data_loader:
            self.data_loader.year = str(year)
            self.data_loader.race = race
            self.data_loader.session = session
            print(f"[IDEAL_LAP_MDI] ✅ DataLoader 參數已同步")
        
        # 🔑 重點：調用 load_initial_data() 觸發 API 請求
        # 這個方法會啟動 API Worker 並更新 UI
        print(f"[IDEAL_LAP_MDI] 🌐 觸發資料重新載入...")
        self.load_initial_data()  # ← ✅ 只重新載入數據，不向主 GUI 發送任何通知！
        
        # 異步載入，返回 True 表示啟動成功
        return True
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] 參數更新失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

#### **行為驗證**:

| 步驟 | 代碼位置 | 行為 | 符合期望? |
|-----|---------|------|---------|
| 1. MDI 更新參數 | `ideal_lap_ranking_table_mdi.py:534` | `update_analysis_parameters()` 被調用 | - |
| 2. 更新本地參數 | Line 547-553 | `self.current_year = str(year)` 等 | **✅** |
| 3. 更新 DataLoader | Line 556-564 | `self.data_loader.year = str(year)` 等 | **✅** |
| 4. 重新載入數據 | Line 569 | `self.load_initial_data()` 觸發 API | **✅** |
| 5. **是否通知主 GUI?** | 全方法檢查 | **沒有任何調用主 GUI 的代碼** | **✅ 符合期望！** |

#### **結論**:
✅ **完全符合期望**！`update_analysis_parameters()` 方法**只更新 MDI 內部參數**，**沒有任何代碼**會將參數變更同步回主 GUI。

---

### **❌ 潛在問題: WindowSettingsDialog 的 `apply_manual_settings`**

#### **問題位置**: `f1t_gui_main.py:5618-5631`

```python
def apply_manual_settings(self, year, race, session):
    """應用手動設定（獨立模式）"""
    window_title = self.parent_window.windowTitle()
    print(f"[TOOL] [SETTING] [{window_title}] 應用手動設定: {year} {race} {session}")
    
    try:
        # 更新當前視窗的內容（使用手動設定的參數）
        self.update_current_window_with_params(year, race, session)
        print(f"[OK] [SETTING] 手動設定應用完成")
    except Exception as e:
        print(f"[ERROR] [SETTING] 應用手動設定失敗: {e}")
```

#### **追蹤 `update_current_window_with_params`**: Line 5633-5663

```python
def update_current_window_with_params(self, year, race, session):
    """使用指定參數更新當前視窗"""
    window_title = self.parent_window.windowTitle()
    print(f"[REFRESH] [SETTING] [{window_title}] 使用參數更新視窗: {year} {race} {session}")
    
    try:
        # [TOOL] 新方法：直接更新子視窗的本地參數
        if hasattr(self.parent_window, 'update_local_parameters'):
            # 更新本地參數（這會自動更新標題）
            self.parent_window.update_local_parameters(year, race, session)
            
            # 調用視窗更新 ← ✅ 只更新視窗本身！
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                
            print(f"[OK] [SETTING] 參數更新完成（新方法）: {year} {race} {session}")
            return
        # ...
```

#### **追蹤 `update_current_window`**: `f1t_gui_main.py:2664-2734` (PopoutSubWindow)

```python
def update_current_window(self):
    """更新當前視窗 - 委託給模組處理"""
    print(f"[UPDATE_DEBUG] ========== 視窗更新請求 ==========")
    print(f"[UPDATE_DEBUG] 視窗標題: {self.windowTitle()}")
    print(f"[UPDATE_DEBUG] 是否有 analysis_module: {self.analysis_module is not None}")
    
    if self.analysis_module:
        print(f"[UPDATE_DEBUG] 🎯 使用新版模組更新邏輯")
        # 如果有模組，委託給模組處理
        try:
            params = {}
            if self.sync_enabled and self._parameter_provider:
                # 同步模式：使用主視窗參數
                params = {
                    'year': int(self._parameter_provider.get_current_year()),
                    'race': self._parameter_provider.get_current_race(),
                    'session': self._parameter_provider.get_current_session()
                }
                # 更新本地參數
                self.local_year = str(params['year'])
                self.local_race = params['race'] 
                self.local_session = params['session']
            else:
                # 非同步模式：使用本地參數 ← ✅ 使用本地參數！
                params = {
                    'year': int(self.local_year),
                    'race': self.local_race,
                    'session': self.local_session
                }
            
            # 更新標題
            self.update_window_title()
            
            print(f"[REFRESH] [{self.windowTitle()}] 更新視窗數據: {params['year']} {params['race']} {params['session']}")
            
            # [TOOL] 重新載入模組而不是委託更新
            success = self.analysis_module.update_parameters(**params)  # ← ✅ 調用模組的 update_parameters！
            if success:
                print(f"[OK] [MODULE] {self.windowTitle()} 模組更新成功")
            else:
                print(f"[WARNING] [MODULE] {self.windowTitle()} 模組更新失敗")
            return success
            
        except Exception as e:
            print(f"[ERROR] [MODULE] {self.windowTitle()} 更新異常: {e}")
            return False
```

#### **最終追蹤**: `ideal_lap_ranking_table_module.py:237-264`

```python
def update_parameters(self, year: int, race: str, session: str, **kwargs) -> bool:
    """
    更新分析參數
    
    Args:
        year: 年份
        race: 賽事
        session: 賽段
        **kwargs: 額外參數
        
    Returns:
        bool: 更新是否成功
    """
    try:
        print(f"[RANKING_MODULE] 更新參數: {year} {race} {session}")
        
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        
        if self._ranking_core:
            return self._ranking_core.update_analysis_parameters(
                year=str(year),
                race=race,
                session=session
            )  # ← ✅ 最終調用 update_analysis_parameters！
        
        return False
        
    except Exception as e:
        print(f"❌ [RANKING_MODULE] 參數更新錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
```

#### **完整調用鏈**:

```
WindowSettingsDialog.accept_settings()
  → WindowSettingsDialog.apply_manual_settings(year, race, session)
    → WindowSettingsDialog.update_current_window_with_params(year, race, session)
      → PopoutSubWindow.update_local_parameters(year, race, session)
        (更新 self.local_year, self.local_race, self.local_session)
      → PopoutSubWindow.update_current_window()
        → IdealLapRankingTableModule.update_parameters(year, race, session)
          → IdealLapRankingTableMDI.update_analysis_parameters(year, race, session)
            → IdealLapRankingTableMDI.load_initial_data()
              (觸發 API 請求，更新數據)
```

#### **行為驗證**:

| 步驟 | 方法 | 是否修改主 GUI? | 符合期望? |
|-----|------|---------------|---------|
| 1. Settings Dialog 確認 | `accept_settings()` | ❌ 否 | ✅ |
| 2. 應用手動設定 | `apply_manual_settings()` | ❌ 否 | ✅ |
| 3. 更新本地參數 | `update_local_parameters()` | ❌ 否 | ✅ |
| 4. 更新視窗內容 | `update_current_window()` | ❌ 否 | ✅ |
| 5. 模組參數更新 | `update_parameters()` | ❌ 否 | ✅ |
| 6. MDI 參數更新 | `update_analysis_parameters()` | ❌ 否 | ✅ |
| 7. 重新載入數據 | `load_initial_data()` | ❌ 否 | ✅ |

#### **結論**:
✅ **完全符合期望**！整個調用鏈**沒有任何代碼**會將 MDI 的參數變更同步回主 GUI。

---

## 🎯 總結

### **最終結論**:

| 期望 | 驗證結果 | 實現方式 |
|-----|---------|---------|
| **期望 1**: 取消勾選同步後，MDI 不會被主 GUI 更新 | ✅ **完全符合** | Line 4407-4410: `if not sync_enabled: return` |
| **期望 2**: MDI 自己更新參數時，不會同步主 GUI | ✅ **完全符合** | 整個更新鏈無任何代碼向主 GUI 發送通知 |

### **行為矩陣**:

```
┌─────────────────────┬────────────────┬────────────────┐
│                     │ 同步模式啟用   │ 同步模式停用   │
│                     │ (sync_enabled) │ (sync_disabled)│
├─────────────────────┼────────────────┼────────────────┤
│ 主 GUI → MDI        │ ✅ 會更新      │ ❌ 不會更新    │
│ (參數廣播)          │ (接收通知)     │ (直接 return) │
├─────────────────────┼────────────────┼────────────────┤
│ MDI → 主 GUI        │ ❌ 不會更新    │ ❌ 不會更新    │
│ (參數同步)          │ (無反向通知)   │ (無反向通知)   │
├─────────────────────┼────────────────┼────────────────┤
│ MDI → MDI 自己      │ ✅ 會更新      │ ✅ 會更新      │
│ (本地更新)          │ (調用 API)     │ (調用 API)     │
└─────────────────────┴────────────────┴────────────────┘
```

---

## 📝 關鍵代碼位置

### **1. 同步狀態檢查**
- **檔案**: `f1t_gui_main.py`
- **位置**: Line 4387-4421
- **方法**: `PopoutSubWindow.receive_main_window_update_notification()`
- **關鍵邏輯**: Line 4407-4410
  ```python
  if not sync_enabled:
      print(f"🔴 [NOTIFICATION] {window_title} 同步已停用，忽略更新通知")
      return  # ← ✅ 直接返回，不執行任何更新
  ```

### **2. MDI 參數更新**
- **檔案**: `ideal_lap_ranking_table_mdi.py`
- **位置**: Line 534-573
- **方法**: `update_analysis_parameters()`
- **關鍵邏輯**: 
  - Line 547-553: 更新本地參數
  - Line 556-564: 更新 DataLoader 參數
  - Line 569: 觸發 API 重新載入
  - **無任何代碼向主 GUI 發送通知**

### **3. Settings Dialog 手動更新**
- **檔案**: `f1t_gui_main.py`
- **位置**: Line 5584-5663
- **調用鏈**: 
  ```
  accept_settings() 
    → apply_manual_settings() 
      → update_current_window_with_params()
        → PopoutSubWindow.update_local_parameters()
          → PopoutSubWindow.update_current_window()
            → Module.update_parameters()
              → MDI.update_analysis_parameters()
  ```
- **關鍵邏輯**: **整個調用鏈無任何代碼向主 GUI 發送通知**

---

## 🧪 測試建議

### **測試場景 1: 驗證同步模式停用**

**步驟**:
1. 開啟 Ideal Lap Ranking Table MDI 視窗
2. 點擊標題欄 ⚙ 按鈕開啟 Settings Dialog
3. **取消勾選** "Receive Main Window Sync"
4. 點擊 OK
5. 在主 GUI 變更 Year/Race/Session
6. 觀察 MDI 視窗是否更新

**期望結果**:
- ❌ MDI 視窗 **不應該** 更新
- ✅ Log 應該顯示: `🔴 [NOTIFICATION] ... 同步已停用，忽略更新通知`

### **測試場景 2: 驗證 MDI 獨立更新**

**步驟**:
1. 開啟 Ideal Lap Ranking Table MDI 視窗（同步模式停用）
2. 點擊標題欄 ⚙ 按鈕開啟 Settings Dialog
3. 變更 Year 為 2024, Race 為 Japan, Session 為 Q
4. 點擊 OK
5. 檢查主 GUI 的 Year/Race/Session 參數

**期望結果**:
- ✅ MDI 視窗應該更新為 2024 Japan Q
- ❌ 主 GUI 參數 **不應該** 變更
- ✅ Log 應該顯示: `[IDEAL_LAP_MDI] 🔄 更新參數: 2024 Japan Q`

### **測試場景 3: 驗證多視窗獨立性**

**步驟**:
1. 開啟 2 個 Ideal Lap Ranking Table MDI 視窗
2. 視窗 A: 2025 Singapore R (同步模式停用)
3. 視窗 B: 2024 Japan Q (同步模式停用)
4. 在主 GUI 變更參數為 2023 Italy R
5. 分別開啟視窗 A 和 B 的 Settings

**期望結果**:
- ✅ 視窗 A 仍然顯示 2025 Singapore R
- ✅ 視窗 B 仍然顯示 2024 Japan Q
- ❌ 兩個視窗 **都不應該** 更新為 2023 Italy R

---

## 🔗 相關文件

- [MDI 視窗設定深度解析](./MDI_WINDOW_SETTINGS_DEEP_DIVE.md)
- [Window Settings Dialog 指南](./MDI_WINDOW_SETTINGS_DIALOG_GUIDE.md)
- [開發原則](../.github/copilot-instructions.md)

---

## 📅 調查日誌

### 2025-10-20 深度調查
- ✅ 完整檢查 `ideal_lap_ranking_table_module.py` (442 行)
- ✅ 完整檢查 `ideal_lap_ranking_table_mdi.py` (Line 1-590)
- ✅ 逐行驗證 `PopoutSubWindow.receive_main_window_update_notification()`
- ✅ 逐行驗證 `WindowSettingsDialog.apply_manual_settings()` 調用鏈
- ✅ 確認無任何代碼向主 GUI 發送反向通知
- ✅ **結論**: 完全符合使用者期望

---

**調查完成** | 如有問題，請參考 `.github/copilot-instructions.md`
