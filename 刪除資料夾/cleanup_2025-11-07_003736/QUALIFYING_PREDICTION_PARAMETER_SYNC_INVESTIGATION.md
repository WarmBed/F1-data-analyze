# 🔍 Qualifying Prediction 參數同步機制深度調查報告

**日期**: 2025-11-05  
**模組**: `modules/gui/qualifying_prediction/`  
**調查重點**: Window Settings 參數同步機制與 API 重載流程

---

## 📋 調查背景

### 用戶觀察到的現象
1. **Mexico 2025**: 數據正常顯示（20 位車手預測）
2. **China 2025**: 視窗空白（無數據載入）
3. **Window Settings 對話框**: 可調整年份/賽事/賽段參數

### 用戶疑問
> 根據 MDI 通用模組，有一個設定可以調整分析參數（年份/賽事），對嗎？

**答案**: ✅ **是的！** MDI 通用架構提供完整的參數同步機制。

---

## 🏗️ 參數同步架構概覽

### 三層架構設計

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 主視窗（F1T GUI Main Window）                      │
│  - 全域參數控制（Year/Race/Session Combo）                    │
│  - 參數變更時廣播通知到所有 MDI 視窗                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Window Settings Dialog                            │
│  - [LINK] Checkbox: 接收主視窗同步 / 手動設定模式             │
│  - 參數選擇器：Year / Race / Session                         │
│  - OK 按鈕：應用設定並觸發數據重載                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 分析模組（Qualifying Prediction MDI）              │
│  - update_parameters(): 接收參數變更                          │
│  - update_analysis_parameters(): 更新內部狀態                │
│  - load_initial_data(): 觸發 API 重新載入                    │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Qualifying Prediction 已實現的同步機制

### 1. Window Settings Dialog（Layer 2）

#### 1.1 對話框組成
**檔案位置**: `f1t_gui_main.py:5436-5979`

```python
class WindowSettingsDialog(QDialog):
    """視窗設定對話框"""
    
    def __init__(self, parent_window):
        # [TOOL] 視窗分析設定
        # 組件:
        # 1. 同步控制區域
        #    - [LINK] Receive Main Window Sync (Year/Race/Session)
        #      ✅ 勾選：接收主視窗同步，參數選擇器禁用
        #      ❌ 取消：手動設定模式，參數選擇器啟用
        
        # 2. 分析參數區域
        #    - 年份選擇器：2020-2025
        #    - 賽事選擇器：動態載入賽季日曆
        #    - 賽段選擇器：FP1/FP2/FP3/SQ/Q/R
        
        # 3. 按鈕區域
        #    - OK：確認設定並應用
        #    - Cancel：取消變更
```

#### 1.2 同步模式 vs. 手動模式

| 模式 | [LINK] Checkbox 狀態 | 參數選擇器 | 行為 |
|------|---------------------|-----------|------|
| **同步接收** | ✅ 勾選 | 🔒 禁用（灰色） | 接收主視窗參數，不可手動編輯 |
| **手動設定** | ❌ 取消 | 🔓 啟用（可編輯） | 手動選擇參數，獨立於主視窗 |

**實現位置**: `f1t_gui_main.py:5545-5561`

```python
def on_sync_checkbox_toggled(self, checked):
    """處理同步勾選框狀態變化"""
    print(f"[DIALOG] 同步狀態變更: {'啟用' if checked else '停用'}")
    
    if checked:
        # 啟用同步 - 從主視窗同步參數
        print("[DIALOG] 從主視窗同步參數...")
        self.sync_params_from_main_window()
    
    # 更新分析參數的可編輯性
    self.update_analysis_params_editability()

def update_analysis_params_editability(self):
    """根據同步狀態更新分析參數的可編輯性"""
    is_sync_enabled = self.sync_windows_checkbox.isChecked()
    
    # 同步啟用時禁用手動編輯
    self.year_combo.setEnabled(not is_sync_enabled)
    self.race_combo.setEnabled(not is_sync_enabled)
    self.session_combo.setEnabled(not is_sync_enabled)
```

#### 1.3 OK 按鈕邏輯

**實現位置**: `f1t_gui_main.py:5879-5905`

```python
def accept_settings(self):
    """確認設定"""
    year = self.year_combo.currentText()
    race = self.get_selected_race_key()
    session = self.get_selected_session_code()
    sync_windows = self.sync_windows_checkbox.isChecked()
    
    # 保存同步狀態到父視窗
    self.parent_window.sync_enabled = sync_windows
    
    # 根據同步狀態決定行為
    if sync_windows:
        # 同步接收模式 - 僅更新當前視窗
        print(f"[REFRESH] 同步接收模式 - 僅更新當前視窗")
        self.update_current_window_only()
    else:
        # 手動設定模式 - 應用自定義參數
        print(f"[TOOL] 手動設定模式 - 應用自定義參數")
        self.apply_manual_settings(year, race, session)
    
    self.accept()
```

---

### 2. UniversalAnalysisMDI 基類（Layer 3）

#### 2.1 參數更新方法

**檔案位置**: `modules/gui/base/universal_analysis_mdi_base.py:279-351`

```python
def update_parameters(self, year: int = None, race: str = None, 
                     session: str = None, **kwargs) -> bool:
    """更新參數 - 通用參數更新邏輯"""
    try:
        # 更新基本參數
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session
        
        # 發送參數更新信號
        params = {
            'year': self.current_year,
            'race': self.current_race,
            'session': self.current_session
        }
        self.parameters_updated.emit(params)
        
        # 更新視窗標題
        self.update_window_title()
        
        # 🔑 關鍵：觸發數據載入
        self._load_data_with_current_parameters()
        
        return True
        
    except Exception as e:
        self._error(f"參數更新失敗: {e}")
        return False
```

#### 2.2 接收主視窗通知

**檔案位置**: `modules/gui/base/universal_analysis_mdi_base.py:353-378`

```python
def receive_main_window_update_notification(self, param_type: str, value):
    """
    接收主視窗參數更新通知
    
    這個方法被主視窗的同步機制調用，用於響應主視窗參數變更
    
    Args:
        param_type: 參數類型 ('year', 'race', 'session')
        value: 新的參數值
    """
    try:
        self._debug(f"收到主視窗參數更新通知: {param_type} = {value}")
        
        # 根據參數類型更新對應參數
        if param_type == 'year':
            self.update_parameters(year=int(value))
        elif param_type == 'race':
            self.update_parameters(race=value)
        elif param_type == 'session':
            self.update_parameters(session=value)
        
    except Exception as e:
        self._error(f"處理主視窗參數更新通知失敗: {e}")
```

---

### 3. Qualifying Prediction 具體實現（Layer 3）

#### 3.1 覆寫 update_parameters()

**檔案位置**: `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py:557-595`

```python
def update_parameters(self, year: int = None, race: str = None, 
                     session: str = None, **kwargs) -> bool:
    """覆寫通用參數更新邏輯，確保觸發 API 載入"""
    try:
        target_year = year if year is not None else self.year
        target_race = race if race is not None else self.race
        # session 參數被忽略（排位賽預測固定使用 FP3）

        if not all([target_year, target_race]):
            print("❌ 參數更新失敗：缺少必要參數")
            return False

        normalized_year = str(target_year)
        normalized_race = target_race

        self.current_year = normalized_year
        self.current_race = normalized_race

        # 發送參數更新信號
        params_payload = {
            'year': self.current_year,
            'race': self.current_race
        }
        self.parameters_updated.emit(params_payload)
        
        # 更新視窗標題
        self.update_window_title()

        # 🔑 關鍵：調用專屬的參數更新方法
        return self.update_analysis_parameters(
            self.current_year,
            self.current_race
        )

    except Exception as exc:
        print(f"❌ update_parameters 失敗: {exc}")
        return False
```

#### 3.2 update_analysis_parameters() - API 重載觸發器

**檔案位置**: `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py:513-555`

```python
def update_analysis_parameters(self, year: str, race: str) -> bool:
    """
    更新分析參數並重新載入資料
    
    Args:
        year: 新的年份
        race: 新的賽事
        
    Returns:
        bool: 更新是否成功
    """
    try:
        print(f"[QUALIFYING_PRED_MDI] 🔄 更新參數: {year} {race}")
        
        # 更新內部參數
        self.current_year = str(year)
        self.current_race = race
        self.year = str(year)
        self.race = race
        
        # 同時更新 DataLoader 的參數
        if hasattr(self, 'data_manager') and self.data_manager:
            self.data_manager.year = str(year)
            self.data_manager.race = race
            print(f"[QUALIFYING_PRED_MDI] ✅ DataManager 參數已同步")
        
        # 🔑 重點：調用 load_initial_data() 觸發 API 請求
        # 這個方法會啟動 API Worker 並更新 UI
        print(f"[QUALIFYING_PRED_MDI] 🌐 觸發資料重新載入...")
        self.load_initial_data()
        
        # 異步載入，返回 True 表示啟動成功
        return True
        
    except Exception as e:
        print(f"❌ [QUALIFYING_PRED_MDI] 參數更新失敗: {e}")
        return False
```

#### 3.3 load_initial_data() - API Worker 啟動

**檔案位置**: `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py:413-447`

```python
def load_initial_data(self):
    """
    載入初始資料 - 強制使用 API
    
    優先級：
    1. API 調用 (https://api.f1telemetrystationpro.org)
    2. 備援: 本地 JSON 檔案（API 失敗時）
    """
    print("[QUALIFYING_PRED_MDI] 🚀 開始載入初始資料...")
    print(f"[QUALIFYING_PRED_MDI] 📋 參數: {self.year} {self.race}")
    
    # 更新狀態
    if hasattr(self, 'lbl_control_status'):
        self.lbl_control_status.setText(
            tr("loading_from_api", "正在從 API 載入資料...")
        )
    
    # 創建 API Worker
    api_params = {
        "year": self.year,
        "race": self.race,
        "force_refresh": False  # 可選：強制刷新
    }
    
    print("[QUALIFYING_PRED_MDI] 🌐 創建 API Worker...")
    self.api_worker = QualifyingPredictionApiWorker(
        params=api_params,
        base_url="https://api.f1telemetrystationpro.org",
        timeout=60.0
    )
    
    # 連接信號
    self.api_worker.progress.connect(self._on_api_progress)
    self.api_worker.success.connect(self._on_api_success)
    self.api_worker.failure.connect(self._on_api_failure)
    
    # 啟動 API 請求
    print("[QUALIFYING_PRED_MDI] ▶️  啟動 API 請求...")
    self.api_worker.start()
```

---

## 🔄 完整參數同步流程

### 流程 1: 主視窗同步模式（[LINK] Checkbox ✅ 勾選）

```
用戶操作主視窗 Year Combo
    ↓
主視窗廣播參數變更通知
    ↓
Qualifying Prediction MDI.receive_main_window_update_notification()
    ↓
MDI.update_parameters(year=2025)
    ↓
MDI.update_analysis_parameters(year="2025", race="China")
    ↓
MDI.load_initial_data()
    ↓
創建 QualifyingPredictionApiWorker
    ↓
API 請求: POST /api/v2/analysis/execute?function_id=74&year=2025&race=China
    ↓
成功: _on_api_success() → _on_data_loaded() → 更新表格
失敗: _on_api_failure() → 顯示錯誤訊息
```

### 流程 2: 手動設定模式（[LINK] Checkbox ❌ 取消）

```
用戶點擊 Window Settings 按鈕
    ↓
打開 WindowSettingsDialog
    ↓
用戶取消勾選 [LINK] Checkbox
    ↓
參數選擇器變為可編輯（Year/Race/Session）
    ↓
用戶選擇: 2025 China R
    ↓
點擊 OK 按鈕
    ↓
WindowSettingsDialog.accept_settings()
    ↓
調用 apply_manual_settings(year="2025", race="China", session="R")
    ↓
調用 update_current_window_with_params()
    ↓
PopoutSubWindow.update_local_parameters(year, race, session)
    ↓
分析模組.update_parameters(year=2025, race="China", session="R")
    ↓
（後續流程與流程 1 相同）
```

---

## 🐛 China 2025 空白視窗問題調查

### 可能原因 1: API 沒有 China 2025 數據

**驗證命令**:
```powershell
# 測試 CLI 是否能生成 China 2025 數據
python f1_analysis_modular_main.py -f 74 -y 2025 -r China
```

**預期結果**:
- ✅ 成功：生成 `json/qualifying_prediction_2025_China.json`
- ❌ 失敗：找不到 China 2025 FP3 數據或模型

### 可能原因 2: 模型檔案不存在

**檢查路徑**:
```
models/track_specific_v3.8/China.pkl
```

**驗證方法**:
```powershell
Test-Path "models\track_specific_v3.8\China.pkl"
```

### 可能原因 3: FP3 數據不可用

**說明**: F74 需要 FP3 數據作為預測特徵

**驗證流程**:
1. 檢查 China 2025 是否有 FP3 會話
2. 檢查 FastF1 是否能載入 FP3 數據

---

## 📝 Window Settings 使用指南

### 功能 1: 同步接收模式（推薦）

**適用場景**: 希望視窗跟隨主視窗參數自動更新

**操作步驟**:
1. 點擊視窗工具列的 **⚙️ Settings** 按鈕
2. 確保 **[LINK] Receive Main Window Sync** 勾選 ✅
3. 點擊 **OK**
4. 之後主視窗的年份/賽事/賽段變更會自動同步

**視覺標識**:
- 參數選擇器顯示為灰色（禁用狀態）
- 視窗標題跟隨主視窗變化

### 功能 2: 手動設定模式（獨立分析）

**適用場景**: 希望視窗顯示不同賽事的數據（獨立於主視窗）

**操作步驟**:
1. 點擊視窗工具列的 **⚙️ Settings** 按鈕
2. **取消勾選** **[LINK] Receive Main Window Sync** ❌
3. 參數選擇器變為可編輯（黑色文字）
4. 選擇目標年份/賽事/賽段（例如：2024 Japan Q）
5. 點擊 **OK**
6. 視窗將重新載入選定的數據

**視覺標識**:
- 參數選擇器顯示為黑色（啟用狀態）
- 視窗標題固定為選定的參數

---

## ✅ Qualifying Prediction 參數同步狀態檢查

### 已實現的功能

| 功能 | 狀態 | 實現位置 |
|------|------|----------|
| **update_parameters()** | ✅ 已實現 | `qualifying_prediction_mdi.py:557-595` |
| **update_analysis_parameters()** | ✅ 已實現 | `qualifying_prediction_mdi.py:513-555` |
| **receive_main_window_update_notification()** | ✅ 繼承自基類 | `universal_analysis_mdi_base.py:353-378` |
| **load_initial_data() API 觸發** | ✅ 已實現 | `qualifying_prediction_mdi.py:413-447` |
| **API Worker 異步請求** | ✅ 已實現 | `qualifying_prediction_mdi.py:25-129` |
| **Window Settings 對話框** | ✅ 通用實現 | `f1t_gui_main.py:5436-5979` |
| **同步模式切換** | ✅ 通用實現 | `f1t_gui_main.py:5545-5561` |
| **手動設定應用** | ✅ 通用實現 | `f1t_gui_main.py:5919-5967` |

### 驗證測試清單

- [ ] **測試 1**: 主視窗同步模式
  - 打開 Qualifying Prediction (Mexico 2025)
  - 確保 [LINK] Checkbox 勾選 ✅
  - 主視窗切換到 Japan 2024
  - 驗證 Qualifying Prediction 視窗自動重載 Japan 2024 數據

- [ ] **測試 2**: 手動設定模式
  - 打開 Window Settings
  - 取消勾選 [LINK] Checkbox ❌
  - 手動選擇 2024 Austria Q
  - 點擊 OK
  - 驗證視窗顯示 Austria 2024 數據

- [ ] **測試 3**: China 2025 數據可用性
  - CLI 執行: `python f1_analysis_modular_main.py -f 74 -y 2025 -r China`
  - 檢查 JSON 是否生成
  - 檢查模型檔案是否存在

---

## 🎯 後續調查建議

### 立即執行

1. **驗證 China 2025 數據**:
   ```powershell
   # 檢查模型檔案
   Test-Path "models\track_specific_v3.8\China.pkl"
   
   # 嘗試生成 China 2025 預測
   python f1_analysis_modular_main.py -f 74 -y 2025 -r China
   ```

2. **測試參數同步**:
   - 打開 Mexico 2025（已有數據）
   - 使用 Window Settings 切換到不同賽事
   - 觀察 API 請求日誌

3. **檢查 API 日誌**:
   ```powershell
   # 查看 nssm_monitor_gui 終端的 API 日誌
   # 搜尋 "[REQUEST] POST /api/v2/analysis/execute"
   # 確認 function_id=74 是否正確調用
   ```

### 可能的問題排查

**如果 China 2025 仍然空白**:

1. **檢查 API 回應**:
   - 觀察終端輸出的 `[API_WORKER]` 日誌
   - 確認是否返回 `success: true`

2. **檢查 JSON 結構**:
   ```powershell
   Get-Content "json\qualifying_prediction_2025_China.json" | ConvertFrom-Json | Select-Object -Property metadata, predictions
   ```

3. **檢查錯誤處理**:
   - 觀察是否觸發 `_on_api_failure()`
   - 檢查狀態標籤是否顯示錯誤訊息

---

## 📚 相關文件

- `modules/gui/base/universal_analysis_mdi_base.py` - MDI 基類實現
- `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py` - Qualifying Prediction MDI
- `f1t_gui_main.py:5436-5979` - Window Settings Dialog
- `docs/MDI_WINDOW_SETTINGS_DIALOG_GUIDE.md` - Window Settings 完整指南
- `BUGFIX_QUALIFYING_PREDICTION_FUNCTION_ID.md` - 功能 ID 修正報告

---

**調查完成時間**: 2025-11-05 19:15 UTC+8  
**結論**: ✅ Qualifying Prediction 已完整實現參數同步機制
