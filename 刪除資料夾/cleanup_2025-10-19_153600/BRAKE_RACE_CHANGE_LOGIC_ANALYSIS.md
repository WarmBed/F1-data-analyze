# Brake Performance Race 更換邏輯逐行分析報告

**問題**: 使用者更換 race 時，Brake Performance 模組沒有更換數據  
**調查時間**: 2025-10-19  
**調查方法**: 逐行追蹤代碼執行流程

---

## 🔍 完整執行流程追蹤

### **階段 1: 使用者操作 - Race ComboBox 變更**

**觸發點**: `f1t_gui_main.py` 第 3281 行
```python
# 連接信號
self.race_combo.currentTextChanged.connect(self.on_race_changed)
```

**執行**: 使用者在下拉選單選擇新的 race → 觸發 `on_race_changed()` 方法

---

### **階段 2: Race 變更處理器**

**檔案**: `f1t_gui_main.py` 第 3334-3362 行

```python
def on_race_changed(self, race):
    """處理賽事變更"""
    # ✅ 步驟 1: 方法入口
    logger.info(f"🔵 [DEBUG]    on_race_changed 被調用: race={race}")
    print(f"🔵 [DEBUG]    on_race_changed 被調用: race={race}")
    
    # ✅ 步驟 2: 更新本地變數
    window_title = self.windowTitle()
    
    event = self.get_selected_event()
    if event:
        self.local_race = event.race_key
    else:
        canonical = self._display_to_race_key.get(race)
        if canonical:
            self.local_race = canonical
    
    # ✅ 步驟 3: 更新 session combo（因為不同 race 可能有不同的 session）
    self._update_session_combo()
    
    # ✅ 步驟 4: 同步視窗（如果啟用連動）
    if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
        self.sync_to_other_windows()
    else:
        self.update_current_window()
    
    # ✅ 步驟 5: 排程參數廣播（重點！）
    logger.info("🔵 [DEBUG]    on_race_changed - scheduling parameter broadcast")
    print("🔵 [DEBUG]    on_race_changed - scheduling parameter broadcast")
    self._schedule_parameter_broadcast("race_changed")
```

**關鍵發現 1**: `on_race_changed` 沒有直接更新模組，而是**排程一個延遲廣播**

---

### **階段 3: 參數廣播排程器（Debounce 機制）**

**檔案**: `f1t_gui_main.py` 第 9778-9808 行

```python
def _schedule_parameter_broadcast(self, reason: str) -> None:
    """Debounce rapid year/race/session changes before updating modules."""
    logger.info(f"[BROADCAST_DEBUG] _schedule_parameter_broadcast 被調用: reason={reason}")
    
    try:
        # ✅ 步驟 1: 獲取當前參數
        payload = {
            "reason": reason,
            "year": self.year_combo.currentText() if hasattr(self, "year_combo") else None,
            "race": self.get_selected_race_key() if hasattr(self, "get_selected_race_key") else None,
            "session": self.get_selected_session_code() if hasattr(self, "get_selected_session_code") else None,
        }
    except Exception as e:
        logger.error(f"[BROADCAST_DEBUG] 獲取參數時出錯: {e}")
        payload = {"reason": reason}
    
    # ✅ 步驟 2: 儲存待廣播的參數
    self._pending_parameter_payload = payload
    set_pending_update(reason, payload)
    
    logger.info(f"[BROADCAST_DEBUG] Pending payload: {payload}")
    
    # ✅ 步驟 3: 顯示狀態列提示
    try:
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage(tr("pending_analysis_update", "Queuing analysis refresh…"), 1500)
    except Exception:
        pass
    
    logger.info("[PARAMS] Queued parameter broadcast (%s): %s", reason, payload)
    
    # ✅ 步驟 4: 啟動 350ms 延遲計時器（防抖動）
    logger.info("[BROADCAST_DEBUG] 啟動 timer (350ms)")
    self._parameter_broadcast_timer.start()  # 350ms 後觸發 _broadcast_pending_parameters
```

**關鍵發現 2**: 使用 **350ms 延遲計時器**防止快速切換時重複更新（Debounce 機制）

**Timer 初始化位置**: `f1t_gui_main.py` 第 5868-5871 行
```python
self._parameter_broadcast_timer = QTimer(self)
self._parameter_broadcast_timer.setSingleShot(True)
self._parameter_broadcast_timer.setInterval(350)  # 350ms 延遲
self._parameter_broadcast_timer.timeout.connect(self._broadcast_pending_parameters)
```

---

### **階段 4: 執行參數廣播**

**檔案**: `f1t_gui_main.py` 第 9810-9829 行

```python
def _broadcast_pending_parameters(self) -> None:
    """Execute the consolidated parameter update for all listening modules."""
    logger.info("[BROADCAST_DEBUG] _broadcast_pending_parameters 被調用")
    
    # ✅ 步驟 1: 取得待廣播的參數
    payload = self._pending_parameter_payload or {}
    self._pending_parameter_payload = None
    clear_pending_update()
    
    logger.info("[BROADCAST_DEBUG] 執行 payload: %s", payload)
    
    try:
        # ✅ 步驟 2: 調用參數變更處理器
        logger.info("[PARAMS] Executing parameter broadcast: %s", payload)
        logger.info("[BROADCAST_DEBUG] 調用 on_race_parameters_changed()")
        self.on_race_parameters_changed()  # 關鍵呼叫！
        logger.info("[BROADCAST_DEBUG] on_race_parameters_changed() 完成")
    except Exception as exc:
        logger.error("[BROADCAST_DEBUG] 錯誤: %s", exc)
        logger.error("Failed to broadcast parameter update: %s", exc)
        exc = None  # 立即釋放異常對象
```

**關鍵發現 3**: 350ms 後觸發 `on_race_parameters_changed()` 方法

---

### **階段 5: 賽事參數變更處理器**

**檔案**: `f1t_gui_main.py` 第 7812-7862 行

```python
def on_race_parameters_changed(self):
    """
    賽事參數變更處理器（年份、賽事、賽段）- 自動更新所有視窗
    
    功能：
    - 檢測 Year/Race/Session 組合參數的變更
    - 篩選需要更新的遙測分析視窗
    - **自動更新**所有視窗（不再詢問用戶）
    - 使用 update_all_lap_analysis() 執行批次更新
    """
    from PyQt5.QtWidgets import QMessageBox
    from core.gui_i18n import tr
    
    # ✅ 步驟 1: 獲取當前參數值
    current_year = self.year_combo.currentText()
    current_race = self.race_combo.currentText()
    current_session = self.session_combo.currentText()
    
    logger.info("[RACE_CONTROL] 賽事參數已變更:")
    logger.info("[RACE_CONTROL]   年份: '%s'", current_year)
    logger.info("[RACE_CONTROL]   賽事: '%s'", current_race)
    logger.info("[RACE_CONTROL]   賽段: '%s'", current_session)
    
    # ✅ 步驟 2: 檢查是否有需要更新的分析視窗
    analysis_windows = self._get_telemetry_analysis_windows()
    
    if len(analysis_windows) == 0:
        logger.info("[RACE_CONTROL] 沒有活動的分析視窗，無需更新")
        return
    
    logger.info("[RACE_CONTROL] 發現 %d 個需要更新的分析視窗", len(analysis_windows))
    
    # ✅ 步驟 3: 自動更新所有視窗（不再詢問用戶）
    try:
        self.statusBar().showMessage(
            tr("auto_updating_windows", "正在自動更新 {count} 個分析視窗...").format(count=len(analysis_windows)),
            2000  # 2 秒
        )
    except Exception:
        pass
    
    logger.info("[RACE_CONTROL] 開始自動更新所有視窗...")
    self.update_all_lap_analysis()  # 關鍵呼叫！
```

**關鍵發現 4**: 調用 `_get_telemetry_analysis_windows()` 獲取需要更新的視窗列表

---

### **階段 6: 獲取需要更新的分析視窗**

**檔案**: `f1t_gui_main.py` 第 7868-8050 行

```python
def _get_telemetry_analysis_windows(self):
    """
    獲取所有需要更新的分析視窗（包含遙測類型和賽事級類型）
    
    Returns:
        list: 分析視窗列表
    """
    logger.info("[DEBUG]    _get_telemetry_analysis_windows() - 開始搜尋視窗")
    
    # ✅ 步驟 1: 定義所有支援的分析類型
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
        'all_drivers_straight_line_speed',  # ✅ 全車手直線速度分析
        # ⚠️ 關鍵問題: 缺少 'all_drivers_brake_performance'！
    }
    
    analysis_windows = []
    seen_ids = set()
    
    # ✅ 步驟 2: 檢查 MDI 視窗（遙測分析）
    logger.info("[DEBUG]    檢查 lap_analysis_windows: %d 個", len(self.lap_analysis_windows))
    
    for window in self.lap_analysis_windows:
        if hasattr(window, 'analysis_type') and window.analysis_type in all_analysis_types:
            window_id = id(window)
            if window_id not in seen_ids:
                analysis_windows.append(window)
                seen_ids.add(window_id)
                logger.info(f"  ✅ 找到 MDI 視窗: {window.analysis_type} (id={window_id})")
                print(f"  ✅ 找到 MDI 視窗: {window.analysis_type} (id={window_id})")
    
    # ✅ 步驟 3: 檢查 Tab 視窗（賽事級分析）
    logger.info(f"🔵 [DEBUG]    檢查 tab_widget: {self.tab_widget.count()} 個標籤")
    print(f"🔵 [DEBUG]    檢查 tab_widget: {self.tab_widget.count()} 個標籤")
    
    for i in range(self.tab_widget.count()):
        widget = self.tab_widget.widget(i)
        tab_text = self.tab_widget.tabText(i)
        
        # ⏭️ 跳過 Welcome Tab 和 Home Tab
        if not widget or widget.objectName() in ["welcome_tab", "home_tab"]:
            continue
        
        # 🔍 檢查 widget 本身是否是分析模組
        if hasattr(widget, 'analysis_type'):
            analysis_type_value = widget.analysis_type
            
            if analysis_type_value in all_analysis_types:
                candidate_id = id(widget)
                if candidate_id not in seen_ids:
                    analysis_windows.append(widget)
                    seen_ids.add(candidate_id)
                    logger.info(f"  ✅ 找到 Tab 視窗 (widget): {analysis_type_value}")
                    print(f"  ✅ 找到 Tab 視窗 (widget): {analysis_type_value}")
        
        # 🔍 如果是 CustomMdiArea，檢查其子視窗
        if type(widget).__name__ == 'CustomMdiArea':
            logger.info(f"     發現 CustomMdiArea，檢查子視窗...")
            
            sub_windows = widget.subWindowList()
            logger.info(f"     子視窗數量: {len(sub_windows)}")
            
            for sub_win in sub_windows:
                # ... 檢查子視窗的 analysis_module ...
                # ... 這裡會檢查 analysis_type 是否在 all_analysis_types 中 ...
                pass
    
    return analysis_windows
```

**🔴 關鍵問題發現**: `all_analysis_types` 集合中**缺少 `'all_drivers_brake_performance'`**！

**對比**:
- ✅ 包含: `'all_drivers_straight_line_speed'`（第 7851 行）
- ❌ 缺少: `'all_drivers_brake_performance'`

**結果**: Brake Performance 模組不會被加入 `analysis_windows` 列表，因此不會被更新！

---

### **階段 7: 批次更新所有視窗**

**檔案**: `f1t_gui_main.py` 第 7303-7500 行

```python
def update_all_lap_analysis(self):
    """序列化更新所有遙測分析視窗（防止並發衝突）"""
    logger.info("🟢 [DEBUG]    ========== update_all_lap_analysis 開始 ==========")
    print("🟢 [DEBUG]    ========== update_all_lap_analysis 開始 ==========")
    
    # ✅ 步驟 1: 定義應該被更新的分析類型（又定義一次！）
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
        'all_drivers_straight_line_speed',  # ✅ 全車手直線速度分析
        'all_drivers_brake_performance',    # ✅ 全車手煞車性能分析 (F34) - 這裡有！
    }
    
    # ✅ 步驟 2: 獲取當前基本設置
    year = self.year_combo.currentText()
    race_display = self.race_combo.currentText()
    session = self.session_combo.currentText()
    
    race = self._get_race_key_from_display(race_display)
    
    # ✅ 步驟 3: 使用 _get_telemetry_analysis_windows() 獲取所有分析視窗
    all_analysis_windows = self._get_telemetry_analysis_windows()
    total_analysis_windows = len(all_analysis_windows)
    logger.info(f"🔵 [BATCH_UPDATE] 找到 {total_analysis_windows} 個分析視窗")
    print(f"🔵 [BATCH_UPDATE] 找到 {total_analysis_windows} 個分析視窗")
    
    if total_analysis_windows == 0:
        logger.warning("[LAP_CONTROL] [DEBUG]   沒有符合條件的分析視窗")
        print("[LAP_CONTROL] [DEBUG]   ⚠️ 沒有符合條件的分析視窗")
        QMessageBox.information(self, tr('update'), tr('update_progress_no_windows'))
        return
    
    # ✅ 步驟 4: 遍歷所有視窗，調用 update_parameters
    # ... (省略更新邏輯，因為 Brake Performance 根本不在列表中) ...
```

**🔴 關鍵問題確認**: 
1. `update_all_lap_analysis()` 中的 `all_analysis_types` **有** `'all_drivers_brake_performance'`（第 7352 行）
2. 但是！`_get_telemetry_analysis_windows()` 中的 `all_analysis_types` **沒有** `'all_drivers_brake_performance'`（缺少！）
3. 因為 `update_all_lap_analysis()` 調用 `_get_telemetry_analysis_windows()` 獲取視窗列表
4. Brake Performance 不在列表中 → 不會被更新

---

## 🔥 根本原因分析

### **問題 1: `all_analysis_types` 定義重複且不一致**

**位置 A**: `_get_telemetry_analysis_windows()` 第 7874-7901 行
```python
all_analysis_types = {
    # ... 28 種類型 ...
    'all_drivers_straight_line_speed',  # ✅ 有
    # ❌ 沒有 'all_drivers_brake_performance'
}
```

**位置 B**: `update_all_lap_analysis()` 第 7324-7352 行
```python
all_analysis_types = {
    # ... 29 種類型 ...
    'all_drivers_straight_line_speed',  # ✅ 有
    'all_drivers_brake_performance',    # ✅ 有（第 7352 行）
}
```

**問題**: 兩個方法各自定義了 `all_analysis_types`，但內容不一致！

---

### **問題 2: 視窗搜索依賴第一個定義**

**執行順序**:
```
on_race_parameters_changed()
  ↓
_get_telemetry_analysis_windows()  # 使用位置 A 的定義（沒有 Brake）
  ↓
return analysis_windows  # Brake Performance 不在列表中
  ↓
update_all_lap_analysis()  # 雖然位置 B 有定義，但已經太晚了
  ↓
遍歷 analysis_windows 更新  # Brake Performance 不在列表中 → 不會更新
```

---

## ✅ 解決方案

### **修復方法**: 在 `_get_telemetry_analysis_windows()` 的 `all_analysis_types` 中添加 `'all_drivers_brake_performance'`

**修改位置**: `f1t_gui_main.py` 第 7874-7901 行

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
    'all_drivers_straight_line_speed',  # ✅ 全車手直線速度分析
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
    'all_drivers_straight_line_speed',     # ✅ 全車手直線速度分析
    'all_drivers_brake_performance',       # ✅ 全車手煞車性能分析 (F34) - 新增！
}
```

---

## 🎯 修復驗證流程

修復後，執行流程應該變為：

```
使用者選擇新 race
  ↓
on_race_changed() 觸發
  ↓
_schedule_parameter_broadcast("race_changed")
  ↓ 350ms 延遲
_broadcast_pending_parameters()
  ↓
on_race_parameters_changed()
  ↓
_get_telemetry_analysis_windows()
  ↓ 
檢查 all_analysis_types（✅ 包含 'all_drivers_brake_performance'）
  ↓
找到 Brake Performance 模組（✅ 加入 analysis_windows 列表）
  ↓
update_all_lap_analysis()
  ↓
遍歷 analysis_windows
  ↓
調用 Brake Performance Module.update_parameters(year, race, session)
  ↓
MDI.load_initial_data()
  ↓
Loader.load_data()
  ↓
數據成功更新！✅
```

---

## 📊 對比分析

| 特性 | Speed Module | Brake Module |
|------|--------------|--------------|
| **在 `update_all_lap_analysis()` 定義中** | ✅ 有 (`'all_drivers_straight_line_speed'`) | ✅ 有 (`'all_drivers_brake_performance'`) |
| **在 `_get_telemetry_analysis_windows()` 定義中** | ✅ 有 | ❌ **沒有**（根本原因） |
| **Race 更換時是否被檢測到** | ✅ 是 | ❌ 否 |
| **Race 更換時是否被更新** | ✅ 是 | ❌ 否 |

---

## 🔍 額外發現

### **問題 3: 代碼重複**

**重複定義**: `all_analysis_types` 在至少 2 個地方定義：
1. `_get_telemetry_analysis_windows()` 第 7874 行
2. `update_all_lap_analysis()` 第 7324 行

**改進建議**: 提取為全局常量或類別屬性

```python
# 在 F1TelemetryStationGUI 類別開頭定義
ALL_SUPPORTED_ANALYSIS_TYPES = {
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
    'all_drivers_straight_line_speed',
    'all_drivers_brake_performance',
}

def _get_telemetry_analysis_windows(self):
    all_analysis_types = self.ALL_SUPPORTED_ANALYSIS_TYPES  # 使用統一定義
    # ...

def update_all_lap_analysis(self):
    all_analysis_types = self.ALL_SUPPORTED_ANALYSIS_TYPES  # 使用統一定義
    # ...
```

---

## 📝 總結

### **問題根源**:
`_get_telemetry_analysis_windows()` 方法中的 `all_analysis_types` 集合缺少 `'all_drivers_brake_performance'`，導致 Brake Performance 模組在 race 更換時不被檢測到，因此不會觸發數據更新。

### **修復方案**:
在 `f1t_gui_main.py` 第 7900 行附近，於 `all_analysis_types` 集合中添加 `'all_drivers_brake_performance'`。

### **優化建議**:
1. 提取 `all_analysis_types` 為全局常量，避免重複定義
2. 添加單元測試，確保所有已註冊模組都在列表中
3. 使用動態註冊機制，自動維護支援的分析類型列表

---

**報告完成時間**: 2025-10-19  
**問題類型**: 配置遺漏（Missing Configuration）  
**嚴重程度**: 高（影響核心功能）  
**修復難度**: 低（單行修改）  
**測試建議**: 手動測試 race 更換後 Brake Performance 是否正確更新數據
