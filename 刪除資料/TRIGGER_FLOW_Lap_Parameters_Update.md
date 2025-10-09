# 🔄 Lap Parameters Update 觸發流程完整分析

**日期**: 2025-10-07  
**問題**: 使用者在改變 driver、lap 或勾選 fastest lap 時的觸發機制  
**答案**: ✅ **是的，會直接自動觸發更新**

---

## 📊 觸發流程總覽

```
用戶操作
    │
    ├─ Driver1 下拉選單變更
    ├─ Driver2 下拉選單變更
    ├─ Lap1 數字調整
    ├─ Lap2 數字調整
    └─ Fastest Lap 勾選框切換
    │
    ▼
信號觸發 (currentTextChanged / valueChanged / toggled)
    │
    ▼
on_lap_parameters_changed() 🔑
    │
    ├─ 記錄所有參數值
    ├─ 調試輸出
    ├─ 啟動延遲計時器 (500ms)
    │
    ▼
update_all_lap_analysis() 🎯
    │
    ├─ 篩選遙測分析視窗
    ├─ 序列化更新所有模組
    └─ 顯示進度對話框
```

---

## 1. 信號連接配置

### 1.1 初始化時的信號綁定

**檔案**: `f1t_gui_main.py`  
**行數**: 5711-5715

```python
# 🔄 自動更新模式已啟用
# 控件變更時立即觸發更新
self.driver1_combo.currentTextChanged.connect(self.on_lap_parameters_changed)
self.driver2_combo.currentTextChanged.connect(self.on_lap_parameters_changed)
self.lap1_spinbox.valueChanged.connect(self.on_lap_parameters_changed)
self.lap2_spinbox.valueChanged.connect(self.on_lap_parameters_changed)
self.fastest_lap_checkbox.toggled.connect(self.on_lap_parameters_changed)
```

### 1.2 觸發條件

| 控件 | 信號類型 | 觸發時機 |
|------|---------|---------|
| `driver1_combo` | `currentTextChanged` | 下拉選單文字變更時 |
| `driver2_combo` | `currentTextChanged` | 下拉選單文字變更時 |
| `lap1_spinbox` | `valueChanged` | 數字調整時 |
| `lap2_spinbox` | `valueChanged` | 數字調整時 |
| `fastest_lap_checkbox` | `toggled` | 勾選狀態切換時 |

---

## 2. on_lap_parameters_changed() 處理器

### 2.1 完整代碼

**檔案**: `f1t_gui_main.py`  
**行數**: 6515-6554

```python
def on_lap_parameters_changed(self):
    """圈速參數變更時自動更新所有分析"""
    print("[LAP_CONTROL] 🔄 圈速參數已變更，準備自動更新...")
    
    # 🔍 詳細調試：記錄當前所有參數值
    try:
        driver1 = self.driver1_combo.currentText()
        driver2 = self.driver2_combo.currentText()
        lap1 = self.lap1_spinbox.value()
        lap2 = self.lap2_spinbox.value()
        is_fastest = self.fastest_lap_checkbox.isChecked()
        
        print(f"[LAP_CONTROL] 📊 當前參數值:")
        print(f"[LAP_CONTROL]   🏎️ 車手1: '{driver1}'")
        print(f"[LAP_CONTROL]   🏎️ 車手2: '{driver2}'")
        print(f"[LAP_CONTROL]   🏁 圈數1: {lap1}")
        print(f"[LAP_CONTROL]   🏁 圈數2: {lap2}")
        print(f"[LAP_CONTROL]   ⚡ 最速圈: {is_fastest}")
        
        # 🔍 檢查發送者控件
        sender = self.sender()
        if sender:
            sender_name = sender.objectName() or type(sender).__name__
            print(f"[LAP_CONTROL] 📤 觸發控件: {sender_name}")
            # 記錄觸發值...
        
    except Exception as e:
        print(f"[LAP_CONTROL] ❌ 參數調試時發生錯誤: {e}")
    
    # ⏱️ 延遲更新機制（防抖）
    if hasattr(self, '_lap_update_timer'):
        self._lap_update_timer.stop()
    
    self._lap_update_timer = QTimer()
    self._lap_update_timer.setSingleShot(True)
    self._lap_update_timer.timeout.connect(self.update_all_lap_analysis)
    self._lap_update_timer.start(500)  # 500毫秒延遲
```

### 2.2 關鍵特性

#### ✅ 自動防抖機制

```python
# 500ms 防抖延遲
# 用戶快速調整多個參數時，只會在最後一次變更後 500ms 觸發更新
self._lap_update_timer.start(500)
```

**效果**:
- 用戶快速點擊 lap1 從 1 → 2 → 3 → 4
- 不會觸發 4 次更新
- 只在最後一次變更後 500ms 觸發 **一次** 更新

#### 🔍 詳細調試輸出

每次參數變更時，控制台會輸出：
```
[LAP_CONTROL] 🔄 圈速參數已變更，準備自動更新...
[LAP_CONTROL] 📊 當前參數值:
[LAP_CONTROL]   🏎️ 車手1: 'VER'
[LAP_CONTROL]   🏎️ 車手2: 'LEC'
[LAP_CONTROL]   🏁 圈數1: 15
[LAP_CONTROL]   🏁 圈數2: 23
[LAP_CONTROL]   ⚡ 最速圈: False
[LAP_CONTROL] 📤 觸發控件: lap1_spinbox
[LAP_CONTROL] 📤 觸發值: 15
```

---

## 3. update_all_lap_analysis() 更新執行

### 3.1 執行流程

**檔案**: `f1t_gui_main.py`  
**行數**: 6269-6469

```python
def update_all_lap_analysis(self):
    """序列化更新所有遙測分析視窗（防止並發衝突）"""
    
    # 步驟1: 檢查活動視窗
    if len(self.lap_analysis_windows) == 0:
        QMessageBox.information(self, '更新', '沒有活動的圈速分析視窗')
        return
    
    # 步驟2: 定義遙測分析類型白名單
    telemetry_analysis_types = {
        'speed_analysis',  # 速度分析
        'brake',          # 煞車分析
        'throttle',       # 油門分析
        'gear',           # 檔位分析
        'rpm',            # RPM分析
        'acceleration',   # 加速度分析
        'speed_diff',     # 速度差分析
        'distancediff'    # 累積距離差分析
    }
    
    # 步驟3: 獲取當前參數
    driver1 = self.driver1_combo.currentText()
    driver2_data = self.driver2_combo.currentData()
    driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
    lap1 = self.lap1_spinbox.value()
    lap2 = self.lap2_spinbox.value()
    is_fastest = self.fastest_lap_checkbox.isChecked()
    
    year = self.year_combo.currentText()
    race_display = self.race_combo.currentText()
    session = self.session_combo.currentText()
    race = self._get_race_key_from_display(race_display)  # 清理日期後綴
    
    # 步驟4: 篩選需要更新的模組
    modules_to_update = []
    for analysis_module in list(self.lap_analysis_windows):
        analysis_type = getattr(analysis_module, '_analysis_type', 'unknown')
        
        if analysis_type in telemetry_analysis_types:
            modules_to_update.append((analysis_module, analysis_type))
    
    # 步驟5: 創建進度對話框
    progress = QProgressDialog(
        "準備更新...", 
        "取消", 
        0, 
        len(modules_to_update), 
        self
    )
    progress.setWindowModality(Qt.WindowModal)
    
    # 步驟6: 序列化更新每個模組
    updated_count = 0
    failed_count = 0
    
    for i, (analysis_module, analysis_type) in enumerate(modules_to_update, 1):
        if progress.wasCanceled():
            break
        
        # 更新進度
        window_title = analysis_module.get_window_title(year, race, session)
        progress.setLabelText(f"正在更新 {analysis_type} ({i}/{len(modules_to_update)})...\n{window_title}")
        progress.setValue(i)
        
        # 調用模組的更新方法
        if hasattr(analysis_module, 'update_lap_parameters'):
            success = analysis_module.update_lap_parameters(
                year=year,
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest=is_fastest
            )
            
            if success:
                updated_count += 1
            else:
                failed_count += 1
        
        # 防止並發衝突
        QApplication.processEvents()
        time.sleep(0.25)  # 250ms 延遲
    
    # 步驟7: 完成
    progress.setValue(len(modules_to_update))
    print(f"✅ 成功更新: {updated_count} 個模組")
    print(f"⚠️ 失敗: {failed_count} 個模組")
```

### 3.2 關鍵設計

#### 🎯 白名單過濾

只更新遙測相關的分析模組，跳過其他類型（如進站分析、事故分析等）

```python
telemetry_analysis_types = {
    'speed_analysis',
    'brake',
    'throttle',
    # ... 等
}
```

#### ⏱️ 序列化更新 + 延遲

```python
# 每個模組更新完後延遲 250ms
time.sleep(0.25)

# 目的：
# 1. 防止並發數據載入衝突
# 2. 避免 API 服務器過載
# 3. 確保每個模組完全完成載入後再處理下一個
```

#### 📊 進度對話框

用戶可以看到實時更新進度：
```
正在更新 speed_analysis (1/3)...
速度分析_2025_Japan_R
```

#### 🔧 Driver2 特殊處理

```python
# 使用 currentData() 判斷是否為 "無"
# 支援多語言：中文 "無"、英文 "None"、日文 "なし"
driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
```

---

## 4. 模組級更新流程

### 4.1 Speed Analysis 為例

**檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py`  
**行數**: 482-540

```python
def _on_lap_numbers_changed(self, lap1: int, lap2: int):
    """處理圈數變更（從圖表組件觸發）"""
    print(f"[SPEED_MDI] ========== 圈數變更處理 ==========")
    print(f"[SPEED_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
    
    # 更新模組的圈數參數
    old_lap1, old_lap2 = self.lap1, self.lap2
    self.lap1 = lap1
    self.lap2 = lap2
    
    # 重新載入數據
    if self.data_manager:
        success = self.data_manager.load_speed_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            driver1=self.driver1,
            driver2=self.driver2,
            lap1=self.lap1,
            lap2=self.lap2
        )
```

### 4.2 數據載入鏈

```
SpeedAnalysisModule.update_lap_parameters()
    ↓
SpeedDataManager.load_speed_data()
    ↓
SpeedAnalysisDataLoader.load_speed_data()
    ↓
TelemetryDataLoader.load_telemetry_data()
    ↓
    ├─ API 模式: TelemetryApiWorker
    └─ 本地模式: _load_json_file()
    ↓
data_loaded 信號發送
    ↓
SpeedAnalysisModule._update_chart()
    ↓
SpeedAnalysisChartWidget.update_speed_data()
```

---

## 5. 實際觸發場景

### 場景1: 用戶選擇不同車手

```
用戶操作:
  Driver1: VER → LEC

觸發流程:
  1. driver1_combo.currentTextChanged 信號發出
  2. on_lap_parameters_changed() 被調用
  3. 啟動 500ms 計時器
  4. 500ms 後執行 update_all_lap_analysis()
  5. 所有開啟的遙測模組更新為 LEC 的數據

控制台輸出:
  [LAP_CONTROL] 🔄 圈速參數已變更，準備自動更新...
  [LAP_CONTROL] 📊 當前參數值:
  [LAP_CONTROL]   🏎️ 車手1: 'LEC'
  [LAP_CONTROL] 📤 觸發控件: driver1_combo
  [LAP_CONTROL] 🔄 開始序列化更新所有圈速分析視窗...
  [LAP_CONTROL] 找到 3 個遙測模組需要更新
  [SPEED_MDI] 重新載入數據...
```

### 場景2: 勾選 Fastest Lap

```
用戶操作:
  ☑️ Fastest Lap 勾選

觸發流程:
  1. fastest_lap_checkbox.toggled 信號發出
  2. _on_main_fastest_lap_changed() 自動設置 lap1=99, lap2=99
  3. on_lap_parameters_changed() 被調用
  4. 500ms 後更新所有模組
  5. 模組自動解析最速圈數據

控制台輸出:
  [LAP_CONTROL] 🏁 最速圈被勾選，自動設置圈數為99
  [LAP_CONTROL] 🏁 圈數1: 1 → 99
  [LAP_CONTROL] 🏁 圈數2: 1 → 99
  [LAP_CONTROL] 🔄 圈速參數已變更，準備自動更新...
  [LAP_CONTROL]   ⚡ 最速圈: True
  [SPEED_MDI] 🔄 解析 VER 的最速圈...
  [SPEED_MDI] ✅ 找到 VER 最速圈: 第15圈
```

### 場景3: 快速調整多個參數

```
用戶操作（1秒內完成）:
  Driver1: VER → LEC
  Lap1: 1 → 5
  Lap2: 1 → 10

觸發流程:
  1. driver1_combo 變更 → 啟動計時器
  2. 計時器尚未觸發，lap1 變更 → 重置計時器
  3. 計時器尚未觸發，lap2 變更 → 重置計時器
  4. 500ms 後只執行 **一次** 更新

效果:
  ✅ 只發送一次 API 請求
  ✅ 避免 3 次重複載入
  ✅ 提升性能和用戶體驗
```

---

## 6. 防抖機制詳解

### 6.1 為什麼需要防抖？

```
❌ 沒有防抖的情況:
  用戶調整 Lap1: 1 → 2 → 3 → 4 → 5
  觸發次數: 4 次
  API 請求: 4 次
  等待時間: 4 × 2秒 = 8秒
  用戶體驗: 😤 等太久！

✅ 有防抖的情況:
  用戶調整 Lap1: 1 → 2 → 3 → 4 → 5
  觸發次數: 1 次（最後一次變更後 500ms）
  API 請求: 1 次
  等待時間: 1 × 2秒 = 2秒
  用戶體驗: 😊 快速響應！
```

### 6.2 實現細節

```python
# 每次參數變更時
if hasattr(self, '_lap_update_timer'):
    self._lap_update_timer.stop()  # 停止之前的計時器

# 創建新的單次計時器
self._lap_update_timer = QTimer()
self._lap_update_timer.setSingleShot(True)  # 單次觸發
self._lap_update_timer.timeout.connect(self.update_all_lap_analysis)
self._lap_update_timer.start(500)  # 500ms 延遲
```

### 6.3 時序圖

```
時間軸 (毫秒)
│
0ms    │ 用戶改變 driver1 → 啟動計時器 A (500ms)
       │
100ms  │ 用戶改變 lap1 → 停止 A，啟動計時器 B (500ms)
       │
300ms  │ 用戶改變 lap2 → 停止 B，啟動計時器 C (500ms)
       │
800ms  │ ✅ 計時器 C 觸發 → 執行更新（只此一次）
       │
```

---

## 7. 最佳實踐與注意事項

### ✅ 優點

1. **自動化**: 用戶無需手動點擊「更新」按鈕
2. **防抖**: 避免重複請求，提升性能
3. **序列化**: 防止並發衝突
4. **進度顯示**: 用戶可見實時進度
5. **錯誤容忍**: 單個模組失敗不影響其他模組
6. **多語言支援**: Driver2 "無" 選項正確處理

### ⚠️ 注意事項

1. **延遲感知**: 500ms 防抖 + 更新時間，用戶可能需等待 1-3 秒
2. **並發限制**: 每個模組間隔 250ms，大量視窗時會較慢
3. **API 負載**: 同時開啟多個模組時，會連續發送多個 API 請求
4. **用戶可取消**: 進度對話框提供取消按鈕

### 💡 建議

```python
# 如果用戶覺得 500ms 太快/太慢，可調整：
self._lap_update_timer.start(500)  # 當前設置

# 更快響應（但可能增加重複請求）:
self._lap_update_timer.start(300)

# 更穩定（但用戶需等更久）:
self._lap_update_timer.start(1000)
```

---

## 8. 總結

### 🎯 問題答案

**Q: 使用者在改變 driver、lap 或勾選 fastest lap 時會直接觸發更新嗎？**

**A: ✅ 是的！完整流程如下：**

```
用戶操作（任何參數變更）
    ↓ (立即)
信號觸發
    ↓ (立即)
on_lap_parameters_changed()
    ↓ (500ms 防抖延遲)
update_all_lap_analysis()
    ↓ (序列化，每個模組 250ms 間隔)
所有遙測模組更新完成
```

### 📊 關鍵特性

- ✅ **自動觸發**: 無需手動操作
- ✅ **智能防抖**: 500ms 延遲避免重複
- ✅ **序列化更新**: 防止並發衝突
- ✅ **進度可見**: 實時顯示更新狀態
- ✅ **可取消**: 用戶可中斷更新

### 🔧 核心代碼位置

| 功能 | 檔案 | 行數 |
|------|------|------|
| 信號連接 | f1t_gui_main.py | 5711-5715 |
| 防抖處理器 | f1t_gui_main.py | 6515-6554 |
| 序列化更新 | f1t_gui_main.py | 6269-6469 |
| 模組更新 | speed_analysis_mdi.py | 482-540 |
| 數據載入 | telemetry_data_loader_base.py | 150-450 |

---

**文件版本**: 1.0.0  
**最後更新**: 2025-10-07  
**維護者**: F1T Team

