# F1T GUI 主視窗與 MDI 子視窗同步功能開發文件

## 概述

本文件詳細描述 F1T GUI 系統中主視窗與 MDI 子視窗之間的資料同步機制。當使用者在 MDI 子視窗啟用「視窗同步控制」功能時，主程式的年份、賽事、賽段參數變更將會自動同步到所有啟用同步功能的 MDI 子視窗。

## 目標

實現主視窗控制項（年份、賽事、賽段）與 MDI 子視窗之間的雙向同步機制，確保資料一致性並提升使用者體驗。

## 架構概述

### 現有架構
- **主視窗類別**: `StyleHMainWindow(QMainWindow)`
- **MDI 子視窗類別**: `PopoutSubWindow(QMdiSubWindow)`
- **MDI 區域**: `CustomMdiArea(QMdiArea)`

### 同步變數
- **核心變數**: `sync_windows_checkbox` (QCheckBox)
- **參數控制器**: 
  - `year_combo` (QComboBox)
  - `race_combo` (QComboBox) 
  - `session_combo` (QComboBox)

## 核心功能流程

### 1. 主視窗到 MDI 子視窗同步

```
使用者操作主視窗 → 參數變更事件 → 檢查MDI子視窗同步狀態 → 更新啟用同步的子視窗
```

#### 觸發條件
- 主視窗年份選擇器變更
- 主視窗賽事選擇器變更  
- 主視窗賽段選擇器變更

#### 同步邏輯
1. 主視窗檢測參數變更
2. 遍歷所有 MDI 子視窗
3. 檢查子視窗的 `sync_windows_checkbox.isChecked()` 狀態
4. 對啟用同步的子視窗執行參數更新
5. 觸發子視窗資料重新載入

### 2. MDI 子視窗內部同步

```
子視窗參數變更 → 檢查同步狀態 → 同步到其他子視窗 → 資料更新
```

#### 觸發條件  
- 子視窗內參數選擇器變更
- 同步勾選框狀態變更
- 重新分析按鈕點擊

#### 同步邏輯
1. 子視窗檢測自身參數變更
2. 檢查 `sync_windows_checkbox` 是否啟用
3. 如啟用，呼叫 `sync_to_other_windows()` 方法
4. 遍歷父MDI區域中的其他子視窗
5. 更新其他子視窗的參數設定

## 實現細節

### 主視窗實現需求

#### 1. 添加 MDI 區域引用
```python
class StyleHMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mdi_area = None  # 需要存儲 MDI 區域引用
```

#### 2. 主視窗參數控制器
```python
def create_main_control_panel(self):
    """創建主視窗控制面板"""
    # 年份選擇器
    self.main_year_combo = QComboBox()
    self.main_year_combo.currentTextChanged.connect(self.on_main_year_changed)
    
    # 賽事選擇器  
    self.main_race_combo = QComboBox()
    self.main_race_combo.currentTextChanged.connect(self.on_main_race_changed)
    
    # 賽段選擇器
    self.main_session_combo = QComboBox()
    self.main_session_combo.currentTextChanged.connect(self.on_main_session_changed)
```

#### 3. 主視窗同步方法
```python
def on_main_year_changed(self, year):
    """主視窗年份變更處理"""
    self.sync_to_mdi_subwindows('year', year)

def on_main_race_changed(self, race):
    """主視窗賽事變更處理"""
    self.sync_to_mdi_subwindows('race', race)

def on_main_session_changed(self, session):
    """主視窗賽段變更處理"""
    self.sync_to_mdi_subwindows('session', session)

def sync_to_mdi_subwindows(self, param_type, value):
    """同步參數到 MDI 子視窗"""
    if not self.mdi_area:
        return
        
    for subwindow in self.mdi_area.subWindowList():
        if hasattr(subwindow, 'sync_windows_checkbox') and \
           subwindow.sync_windows_checkbox.isChecked():
            # 更新子視窗參數
            if param_type == 'year' and hasattr(subwindow, 'year_combo'):
                subwindow.year_combo.setCurrentText(value)
            elif param_type == 'race' and hasattr(subwindow, 'race_combo'):
                subwindow.race_combo.setCurrentText(value)
            elif param_type == 'session' and hasattr(subwindow, 'session_combo'):
                subwindow.session_combo.setCurrentText(value)
            
            # 觸發子視窗資料更新
            if hasattr(subwindow, 'update_current_window'):
                subwindow.update_current_window()
```

### MDI 子視窗強化需求

#### 1. 雙向同步支援
```python
def set_analysis_parameters(self, params, skip_sync=False):
    """設置分析參數，支援跳過同步"""
    if hasattr(self, 'year_combo') and params:
        # 暫時斷開信號連接避免循環同步
        self.year_combo.blockSignals(True)
        self.race_combo.blockSignals(True)
        self.session_combo.blockSignals(True)
        
        # 更新參數
        self.year_combo.setCurrentText(params.get('year', '2025'))
        self.race_combo.setCurrentText(params.get('race', 'Japan'))
        self.session_combo.setCurrentText(params.get('session', 'R'))
        
        # 恢復信號連接
        self.year_combo.blockSignals(False)
        self.race_combo.blockSignals(False)
        self.session_combo.blockSignals(False)
        
        # 更新資料（如果不是跳過同步）
        if not skip_sync:
            self.update_current_window()
```

#### 2. 資料更新機制
```python
def update_current_window(self):
    """更新當前視窗的分析數據"""
    window_title = self.windowTitle()
    year = self.year_combo.currentText()
    race = self.race_combo.currentText()
    session = self.session_combo.currentText()
    
    print(f"🔄 [{window_title}] 更新視窗數據: {year} {race} {session}")
    
    # 資料載入邏輯
    self.load_race_data(year, race, session)
    
def load_race_data(self, year, race, session):
    """載入比賽資料 - 完整的JSON載入流程"""
    # Step 1: 載入JSON
    json_data = self.try_load_json(year, race, session)
    
    if json_data:
        # JSON存在，直接使用
        print(f"✅ 找到JSON檔案，直接載入資料")
        self.update_charts_and_analysis(json_data)
    else:
        # Step 2: 無JSON則進行CLI參數呼叫
        print(f"❌ 未找到JSON檔案，啟動CLI分析...")
        self.call_cli_analysis(year, race, session)
        
        # Step 3: 等待JSON產生
        self.wait_for_json_generation(year, race, session)

def try_load_json(self, year, race, session):
    """嘗試載入JSON檔案"""
    import glob
    import os
    
    # 構建JSON檔案搜尋模式
    json_patterns = [
        f"json/*{year}*{race}*{session}*.json",
        f"json_exports/*{year}*{race}*{session}*.json",
        f"cache/*{year}*{race}*{session}*.json"
    ]
    
    for pattern in json_patterns:
        json_files = glob.glob(pattern)
        if json_files:
            json_file = json_files[0]  # 取第一個符合的檔案
            print(f"📁 找到JSON檔案: {json_file}")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ JSON載入錯誤: {e}")
                continue
    
    return None

def call_cli_analysis(self, year, race, session):
    """呼叫CLI參數進行分析"""
    import subprocess
    import sys
    
    # 構建CLI命令
    cmd = [
        sys.executable,
        "f1_analysis_modular_main.py",
        "-f", "1",  # 強制模式
        "-y", str(year),
        "-r", race,
        "-s", session
    ]
    
    print(f"🚀 執行CLI命令: {' '.join(cmd)}")
    
    try:
        # 非阻塞式執行
        self.cli_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        print(f"⚡ CLI分析已啟動 (PID: {self.cli_process.pid})")
        
    except Exception as e:
        print(f"❌ CLI執行錯誤: {e}")

def wait_for_json_generation(self, year, race, session):
    """等待JSON產生"""
    from PyQt5.QtCore import QTimer
    
    # 設置JSON檢查計時器
    self.json_check_timer = QTimer()
    self.json_check_timer.timeout.connect(
        lambda: self.check_json_ready(year, race, session)
    )
    self.json_check_timer.start(2000)  # 每2秒檢查一次
    
    # 設置最大等待時間 (60秒)
    self.max_wait_timer = QTimer()
    self.max_wait_timer.setSingleShot(True)
    self.max_wait_timer.timeout.connect(self.on_json_wait_timeout)
    self.max_wait_timer.start(60000)  # 60秒超時
    
    print(f"⏳ 等待JSON檔案產生... (最多等待60秒)")

def check_json_ready(self, year, race, session):
    """檢查JSON是否已準備好"""
    # Step 4: 讀取JSON
    json_data = self.try_load_json(year, race, session)
    
    if json_data:
        # JSON已產生，停止計時器
        self.json_check_timer.stop()
        self.max_wait_timer.stop()
        
        print(f"✅ JSON檔案已產生，開始載入資料")
        self.update_charts_and_analysis(json_data)
    else:
        print(f"⏳ 繼續等待JSON檔案產生...")

def on_json_wait_timeout(self):
    """JSON等待超時處理"""
    self.json_check_timer.stop()
    print(f"⏰ JSON等待超時，可能分析失敗")
    
    # 可以在這裡添加錯誤處理邏輯
    # 例如：顯示錯誤訊息、重試機制等

def update_charts_and_analysis(self, json_data):
    """更新圖表和分析結果"""
    print(f"📊 開始更新圖表和分析結果...")
    
    try:
        # 更新遙測圖表
        if 'telemetry' in json_data:
            self.update_telemetry_chart(json_data['telemetry'])
            
        # 更新軌道地圖
        if 'track_data' in json_data:
            self.update_track_map(json_data['track_data'])
            
        # 更新分析數據
        if 'analysis_results' in json_data:
            self.update_analysis_data(json_data['analysis_results'])
            
        print(f"✅ 圖表和分析結果更新完成")
        
    except Exception as e:
        print(f"❌ 圖表更新錯誤: {e}")
        traceback.print_exc()
```

## 資料同步流程圖

```
[主視窗] 
    ↓ 參數變更
[檢查MDI子視窗]
    ↓ 遍歷子視窗
[檢查同步狀態]
    ↓ sync_windows_checkbox.isChecked()
[更新參數設定]
    ↓ setCurrentText()
[子視窗資料載入流程]
    ↓
┌─────────────────────────────────────┐
│ 1. 載入JSON                         │
│    ↓ try_load_json()               │
│ 2. 檢查JSON是否存在                 │
│    ↓ 是/否                         │
│ 3a. [是] 直接使用JSON               │
│     ↓ update_charts_and_analysis()│
│ 3b. [否] 進行CLI參數呼叫            │
│     ↓ call_cli_analysis()         │
│ 4. 等待JSON產生                    │
│    ↓ wait_for_json_generation()   │
│ 5. 定期檢查JSON狀態                │
│    ↓ check_json_ready() (每2秒)   │
│ 6. 讀取新產生的JSON                │
│    ↓ try_load_json()              │
│ 7. 更新視覺化                      │
│    ↓ update_charts_and_analysis() │
└─────────────────────────────────────┘
[完成同步]
```

### 詳細流程說明

#### 階段1: JSON檢查
- 搜尋 `json/`, `json_exports/`, `cache/` 目錄
- 使用模式匹配：`*{year}*{race}*{session}*.json`
- 如找到JSON檔案，直接載入並跳到階段7

#### 階段2: CLI分析觸發
- 執行 `f1_analysis_modular_main.py`
- 參數：`-f 1 -y {year} -r {race} -s {session}`
- 非阻塞式執行，取得程序PID

#### 階段3: 智慧等待機制  
- 每2秒檢查一次JSON檔案
- 最大等待時間60秒
- 支援超時處理和錯誤回復

#### 階段4: 資料更新
- 載入JSON資料
- 更新遙測圖表
- 更新軌道地圖  
- 更新分析結果

## 事件處理機制

### 1. 防止循環同步
- 使用 `blockSignals()` 方法暫時停用信號
- 添加 `skip_sync` 參數控制同步行為
- 實現同步狀態追蹤機制

### 2. 錯誤處理
```python
def safe_sync_to_subwindows(self, param_type, value):
    """安全的同步方法，包含錯誤處理"""
    try:
        self.sync_to_mdi_subwindows(param_type, value)
    except Exception as e:
        print(f"❌ 同步錯誤: {e}")
        traceback.print_exc()

def handle_cli_analysis_error(self, year, race, session, error):
    """處理CLI分析錯誤"""
    error_msg = f"CLI分析失敗: {year} {race} {session} - {error}"
    print(f"❌ {error_msg}")
    
    # 可選的錯誤處理策略：
    # 1. 重試機制
    # 2. 使用預設資料
    # 3. 顯示錯誤提示給使用者
    self.show_error_message(error_msg)

def handle_json_timeout(self, year, race, session):
    """處理JSON載入超時"""
    timeout_msg = f"資料載入超時: {year} {race} {session}"
    print(f"⏰ {timeout_msg}")
    
    # 超時處理選項：
    # 1. 延長等待時間
    # 2. 重新觸發CLI分析
    # 3. 使用快取資料
    self.show_timeout_options(year, race, session)
```

### 3. 效能優化
- 批量更新機制
- 延遲載入策略  
- 只更新可見的子視窗
- **智慧快取機制**: 避免重複CLI呼叫
- **並行處理**: 多個子視窗可同時載入資料
- **進度追蹤**: 顯示CLI分析和JSON生成進度

## 使用者體驗設計

### 1. 視覺回饋
- 同步進行時顯示載入指示器
- **CLI分析進度**: 顯示「正在分析...」狀態
- **JSON等待進度**: 顯示倒計時和檢查次數
- 完成同步後顯示確認訊息
- 錯誤發生時顯示警告訊息
- **分階段狀態**: JSON搜尋 → CLI執行 → 等待生成 → 載入完成

### 2. 互動設計
- 同步勾選框狀態即時生效
- 支援選擇性同步特定參數
- 提供同步歷史記錄

## 測試策略

### 1. 單元測試
- 測試參數同步邏輯
- 測試資料載入機制
- 測試錯誤處理功能

### 2. 整合測試
- 測試主視窗與子視窗互動
- 測試多子視窗同步場景
- **測試JSON載入流程**: 存在/不存在兩種情況
- **測試CLI觸發機制**: 參數正確性和執行狀態
- **測試等待和超時機制**: 各種時間長度的分析任務
- 測試邊界條件和異常情況

### 3. 使用者測試
- 測試同步功能的直觀性
- 測試效能表現
- 測試穩定性和可靠性

## 實現優先順序

### Phase 1: 基礎架構
1. 主視窗添加控制面板
2. 實現基本同步邏輯
3. **實現JSON檢查機制**
4. **實現CLI呼叫功能**
5. 添加錯誤處理機制

### Phase 2: 功能完善
1. 實現雙向同步
2. **實現智慧等待機制**
3. **添加進度顯示和狀態追蹤**
4. 添加效能優化
5. 完善使用者體驗

### Phase 3: 高級功能
1. **智慧快取和重試機制**
2. 同步歷史記錄
3. 選擇性同步選項
4. 進階視覺化回饋

## 技術風險與緩解策略

### 風險識別
1. **循環同步風險**: 可能造成無限循環
2. **效能風險**: 大量子視窗同時更新
3. **資料一致性風險**: 同步過程中的資料不一致
4. **CLI執行風險**: CLI程序失敗或卡死
5. **JSON等待風險**: 長時間等待造成界面凍結
6. **檔案系統風險**: JSON檔案損壞或權限問題

### 緩解策略
1. 實現同步鎖定機制
2. 採用批量更新和延遲載入
3. 添加資料驗證和回滾機制
4. **CLI程序監控**: 設置執行超時和程序終止機制
5. **非阻塞等待**: 使用QTimer避免界面凍結
6. **檔案驗證**: JSON載入前驗證檔案完整性

## 結論

此同步功能將大幅提升 F1T GUI 系統的使用者體驗，實現主視窗與 MDI 子視窗間的無縫資料同步。通過分階段實現和充分測試，確保功能的穩定性和可靠性。

---

**文件版本**: 1.0  
**創建日期**: 2025年8月28日  
**最後更新**: 2025年8月28日  
**作者**: F1T Development Team
