# 📊 深度分析：對話框與主視窗參數同步問題

**分析日期**: 2025-10-07  
**分析對象**: `LapAnalysisOptionsDialog` 與主視窗參數同步機制  
**問題**: 對話框預設值未從主視窗讀取，導致參數不一致

---

## 🔍 問題描述

### 用戶期望行為
```
主視窗設定:
- Driver 1: VER
- Lap 1: 13
- Driver 2: LEC  
- Lap 2: 25

用戶點擊「圈速分析」→ 彈出對話框
↓
對話框應該預設顯示:
- Driver 1: VER (已選中) ✅
- Lap 1: 13 ✅
- Driver 2: LEC (已選中) ✅
- Lap 2: 25 ✅

創建 MDI 視窗後，上方參數欄也應該同步為:
- Driver 1: VER
- Lap 1: 13
- Driver 2: LEC
- Lap 2: 25
```

### 實際行為
```
主視窗設定:
- Driver 1: VER
- Lap 1: 13
- Driver 2: LEC
- Lap 2: 25

用戶點擊「圈速分析」→ 彈出對話框
↓
對話框顯示預設值:
- Driver 1: (空或第一個車手) ❌
- Lap 1: 1 ❌
- Driver 2: None ❌
- Lap 2: 1 ❌

創建 MDI 視窗後，上方參數欄保持原值:
- Driver 1: VER (不變)
- Lap 1: 13 (不變)
- Driver 2: LEC (不變)
- Lap 2: 25 (不變)
```

---

## 🔎 根本原因分析

### 1. 對話框初始化流程

**檔案**: `f1t_gui_main.py` 第 564-814 行

#### 當前代碼（問題）
```python
class LapAnalysisOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... 樣式設定 ...
        self.init_ui()
        self.selected_charts = []
        # ❌ 沒有從父視窗讀取當前參數
```

#### init_ui() 方法中的預設值
```python
def init_ui(self):
    # Driver 1 預設值
    self.driver1_combo = QComboBox()  # ❌ 沒有設定預設選中項
    
    # Lap 1 預設值
    self.lap1_input = QLineEdit()
    self.lap1_input.setText("1")  # ❌ 硬編碼為 1
    
    # Driver 2 預設值
    self.driver2_combo = QComboBox()
    self.driver2_combo.addItem(tr("none_option", "None"), None)  # ❌ 預設為 None
    
    # Lap 2 預設值
    self.lap2_input = QLineEdit()
    self.lap2_input.setText("1")  # ❌ 硬編碼為 1
```

---

### 2. 主視窗調用流程

**檔案**: `f1t_gui_main.py` 第 10241-10328 行

#### 當前代碼
```python
def on_lap_analysis_clicked(self):
    """圈速分析 - 彈出選項對話框讓使用者選擇要顯示的遙測圖表和車手"""
    params = self.get_current_parameters()
    print(f"[分析] 圈速分析 - {params['year']} {params['race']} {params['session']}")
    
    try:
        # 彈出選項對話框
        dialog = LapAnalysisOptionsDialog(self)  # ❌ 沒有傳遞當前參數
        
        if dialog.exec_() == QDialog.Accepted:
            selected_charts = dialog.get_selected_charts()
            driver_info = dialog.get_selected_drivers()
            
            driver1 = driver_info['driver1']  # 從對話框獲取
            driver2 = driver_info['driver2']
            lap1_number = driver_info['lap1_number']
            lap2_number = driver_info['lap2_number']
            # ...
```

**問題**:
1. 創建對話框時沒有傳遞 `params`
2. 對話框無法知道主視窗當前的 driver/lap 選擇
3. 對話框使用硬編碼的預設值（Driver 1 空，Lap 1=1，Driver 2=None，Lap 2=1）

---

### 3. 主視窗參數控制器

**檔案**: `f1t_gui_main.py` 第 5650-5700 行

#### 主視窗的參數控制器
```python
# Lap Analysis 參數控制器
self.driver1_combo = QComboBox()  # 車手1選擇器
self.driver2_combo = QComboBox()  # 車手2選擇器
self.lap1_spinbox = QSpinBox()    # 圈數1選擇器
self.lap1_spinbox.setRange(1, 100)
self.lap1_spinbox.setValue(1)     # 預設 1
self.lap2_spinbox = QSpinBox()    # 圈數2選擇器
self.lap2_spinbox.setRange(1, 100)
self.lap2_spinbox.setValue(1)     # 預設 1
self.fastest_lap_checkbox = QCheckBox(tr("fastest_lap", "Fastest Lap"))
```

**這些控制器的值沒有被傳遞給對話框**

---

## 🔧 解決方案

### 方案 A: 對話框讀取主視窗參數（推薦）

#### 修改 1: 對話框初始化時讀取父視窗參數

**位置**: `f1t_gui_main.py` 第 567 行

```python
class LapAnalysisOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 🆕 從父視窗讀取當前參數
        self.parent_window = parent
        self.current_params = {}
        
        if parent and hasattr(parent, 'get_current_parameters'):
            self.current_params = parent.get_current_parameters()
            
        if parent and hasattr(parent, 'driver1_combo'):
            self.current_params['driver1'] = parent.driver1_combo.currentText()
            self.current_params['driver2'] = parent.driver2_combo.currentText()
            self.current_params['lap1'] = parent.lap1_spinbox.value()
            self.current_params['lap2'] = parent.lap2_spinbox.value()
            self.current_params['is_fastest_lap'] = parent.fastest_lap_checkbox.isChecked()
        
        self.setWindowTitle(tr("telemetry_options_title"))
        # ... 其他初始化 ...
```

#### 修改 2: init_ui() 使用讀取的參數設定預設值

**位置**: `f1t_gui_main.py` 第 700-780 行

```python
def init_ui(self):
    # ... 前面的代碼 ...
    
    # 車手1 (必選)
    driver1_label = QLabel(tr("driver1_required"))
    self.driver1_combo = QComboBox()
    self.driver1_combo.setFixedWidth(100)
    driver_layout.addWidget(driver1_label, 0, 0)
    driver_layout.addWidget(self.driver1_combo, 0, 1)
    
    # 車手1圈數
    lap1_label = QLabel(tr("lap_number"))
    self.lap1_input = QLineEdit()
    
    # 🆕 使用父視窗的圈數作為預設值
    default_lap1 = self.current_params.get('lap1', 1)
    self.lap1_input.setText(str(default_lap1))
    
    self.lap1_input.setFixedWidth(50)
    self.lap1_input.setPlaceholderText(tr("lap", "Lap"))
    driver_layout.addWidget(lap1_label, 0, 2)
    driver_layout.addWidget(self.lap1_input, 0, 3)
    
    # 車手2 (選用)
    driver2_label = QLabel(tr("driver2_optional"))
    self.driver2_combo = QComboBox()
    self.driver2_combo.setFixedWidth(100)
    self.driver2_combo.addItem(tr("none_option", "None"), None)
    driver_layout.addWidget(driver2_label, 1, 0)
    driver_layout.addWidget(self.driver2_combo, 1, 1)
    
    # 車手2圈數
    lap2_label = QLabel(tr("lap_number"))
    self.lap2_input = QLineEdit()
    
    # 🆕 使用父視窗的圈數作為預設值
    default_lap2 = self.current_params.get('lap2', 1)
    self.lap2_input.setText(str(default_lap2))
    
    self.lap2_input.setFixedWidth(50)
    self.lap2_input.setPlaceholderText(tr("lap", "Lap"))
    driver_layout.addWidget(lap2_label, 1, 2)
    driver_layout.addWidget(self.lap2_input, 1, 3)
    
    # 最速圈勾選框
    self.fastest_lap_checkbox = QCheckBox(tr("fastest_lap_option", "Fastest Lap"))
    
    # 🆕 使用父視窗的最速圈設定作為預設值
    default_fastest_lap = self.current_params.get('is_fastest_lap', False)
    self.fastest_lap_checkbox.setChecked(default_fastest_lap)
    
    # ... 其他代碼 ...
```

#### 修改 3: _load_available_drivers() 中設定預設選中項

**位置**: `f1t_gui_main.py` 第 850-920 行

```python
def _load_available_drivers(self):
    """載入可用的車手列表 - 從進站分析JSON獲取"""
    try:
        # ... 前面的載入邏輯 ...
        
        # 填充車手1下拉選單
        self.driver1_combo.clear()
        for driver in drivers:
            self.driver1_combo.addItem(driver)
        
        # 🆕 設定預設選中的 Driver 1
        default_driver1 = self.current_params.get('driver1')
        if default_driver1:
            index = self.driver1_combo.findText(default_driver1)
            if index >= 0:
                self.driver1_combo.setCurrentIndex(index)
        
        # 填充車手2下拉選單
        self.driver2_combo.clear()
        self.driver2_combo.addItem(tr("none_option", "None"), None)
        for driver in drivers:
            self.driver2_combo.addItem(driver)
        
        # 🆕 設定預設選中的 Driver 2
        default_driver2 = self.current_params.get('driver2')
        if default_driver2 and default_driver2 != default_driver1:
            index = self.driver2_combo.findText(default_driver2)
            if index >= 0:
                self.driver2_combo.setCurrentIndex(index)
    except Exception as e:
        print(f"[ERROR] 載入車手列表失敗: {e}")
```

---

### 方案 B: 主視窗傳遞參數給對話框

#### 修改主視窗調用

**位置**: `f1t_gui_main.py` 第 10250 行

```python
def on_lap_analysis_clicked(self):
    """圈速分析 - 彈出選項對話框讓使用者選擇要顯示的遙測圖表和車手"""
    params = self.get_current_parameters()
    
    try:
        # 🆕 傳遞當前參數給對話框
        current_selection = {
            'driver1': self.driver1_combo.currentText(),
            'driver2': self.driver2_combo.currentText(),
            'lap1': self.lap1_spinbox.value(),
            'lap2': self.lap2_spinbox.value(),
            'is_fastest_lap': self.fastest_lap_checkbox.isChecked()
        }
        
        dialog = LapAnalysisOptionsDialog(self, initial_params=current_selection)
        # ... 其他代碼 ...
```

#### 修改對話框接收參數

```python
class LapAnalysisOptionsDialog(QDialog):
    def __init__(self, parent=None, initial_params=None):
        super().__init__(parent)
        
        self.current_params = initial_params or {}
        # ... 其他初始化 ...
```

---

## 📋 實施步驟

### Step 1: 修改對話框 __init__
- [ ] 從父視窗讀取當前參數
- [ ] 存儲到 `self.current_params`

### Step 2: 修改 init_ui()
- [ ] Lap 1 預設值使用 `self.current_params.get('lap1', 1)`
- [ ] Lap 2 預設值使用 `self.current_params.get('lap2', 1)`
- [ ] Fastest Lap 預設值使用 `self.current_params.get('is_fastest_lap', False)`

### Step 3: 修改 _load_available_drivers()
- [ ] Driver 1 自動選中 `self.current_params.get('driver1')`
- [ ] Driver 2 自動選中 `self.current_params.get('driver2')`

### Step 4: 測試驗證
- [ ] 主視窗設定 VER/13/LEC/25
- [ ] 打開對話框，確認預設值正確
- [ ] 點擊 OK，確認 MDI 視窗載入正確數據
- [ ] 檢查上方參數欄是否仍保持原值

---

## ✅ 預期效果

### 修改前
```
主視窗: VER/13/LEC/25
  ↓
對話框: (空)/1/(None)/1  ❌ 不一致
  ↓
用戶必須重新輸入 VER/13/LEC/25 ❌ 重複操作
```

### 修改後
```
主視窗: VER/13/LEC/25
  ↓
對話框: VER/13/LEC/25  ✅ 自動同步
  ↓
用戶可以直接點擊 OK 或微調參數 ✅ 便利
```

---

## 🎯 額外改進建議

### 1. 雙向同步（可選）

如果用戶在對話框中修改了參數，是否要同步回主視窗？

```python
def on_lap_analysis_clicked(self):
    # ... 前面的代碼 ...
    
    if dialog.exec_() == QDialog.Accepted:
        driver_info = dialog.get_selected_drivers()
        
        # 🆕 將對話框的選擇同步回主視窗
        self.driver1_combo.setCurrentText(driver_info['driver1'])
        self.lap1_spinbox.setValue(driver_info['lap1_number'])
        
        if driver_info['driver2']:
            self.driver2_combo.setCurrentText(driver_info['driver2'])
            self.lap2_spinbox.setValue(driver_info['lap2_number'])
        
        self.fastest_lap_checkbox.setChecked(driver_info['is_fastest_lap'])
```

**優點**: 保持一致性  
**缺點**: 用戶可能不希望主視窗參數被改變

---

### 2. 記住上次選擇（可選）

使用 QSettings 保存用戶最後的選擇：

```python
class LapAnalysisOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 從設定檔讀取上次的選擇
        settings = QSettings("F1T", "LapAnalysis")
        self.last_driver1 = settings.value("last_driver1", "")
        self.last_driver2 = settings.value("last_driver2", "")
        self.last_lap1 = int(settings.value("last_lap1", 1))
        self.last_lap2 = int(settings.value("last_lap2", 1))
        # ...
    
    def accept(self):
        # 保存用戶選擇
        settings = QSettings("F1T", "LapAnalysis")
        settings.setValue("last_driver1", self.driver1_combo.currentText())
        settings.setValue("last_driver2", self.driver2_combo.currentText())
        settings.setValue("last_lap1", self.lap1_input.text())
        settings.setValue("last_lap2", self.lap2_input.text())
        super().accept()
```

---

## 📝 總結

### 當前問題
- ❌ 對話框預設值與主視窗參數不同步
- ❌ 用戶需要重新輸入已經設定過的參數
- ❌ 造成操作不便和困惑

### 推薦方案
✅ **方案 A**: 對話框從父視窗讀取當前參數作為預設值

### 實施難度
⭐⭐☆☆☆ (中等) - 需要修改 3 個方法，約 30 行代碼

### 優先級
🔥🔥🔥 **高** - 直接影響用戶體驗

---

**分析完成時間**: 2025-10-07  
**下一步**: 需要用戶確認是否實施方案 A
