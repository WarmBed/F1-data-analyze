# Ideal Lap Ranking 參數更新流程

## 概述

Ideal Lap Ranking 模組已**完整實作參數更新機制**，可以隨主 GUI 的 Race/Year/Session 變更而自動更新並重新載入資料。

---

## 🔄 完整更新鏈

### 1️⃣ 主 GUI 事件觸發

**檔案**: `f1t_gui_main.py`  
**事件**: 使用者更改 Year/Race/Session 下拉選單

```python
# Line 3097-3140
def on_year_changed(self, year):
    """處理年份變更"""
    self.local_year = str(year)
    self.update_races_for_year(year)
    
    if self.sync_windows_checkbox.isChecked():
        self.sync_to_other_windows()
    else:
        self.update_current_window()  # → 觸發更新

def on_race_changed(self, race):
    """處理賽事變更"""
    self.local_race = race
    self._update_session_combo()
    
    if self.sync_windows_checkbox.isChecked():
        self.sync_to_other_windows()
    else:
        self.update_current_window()  # → 觸發更新

def on_session_changed(self, session):
    """處理賽段變更"""
    self.local_session = session
    
    if self.sync_windows_checkbox.isChecked():
        self.sync_to_other_windows()
    else:
        self.update_current_window()  # → 觸發更新
```

---

### 2️⃣ 視窗更新邏輯

**檔案**: `f1t_gui_main.py`  
**方法**: `update_current_window()` (Line 2254-2310)

```python
def update_current_window(self):
    """更新當前視窗 - 委託給模組處理"""
    if self.analysis_module:
        # 準備參數
        params = {
            'year': int(self.local_year),     # 轉換為 int
            'race': self.local_race,
            'session': self.local_session
        }
        
        # 更新標題
        self.update_window_title()
        
        # 🔑 調用模組的 update_parameters 方法
        success = self.analysis_module.update_parameters(**params)
        
        if success:
            print(f"[OK] [MODULE] {self.windowTitle()} 模組更新成功")
        else:
            print(f"[WARNING] [MODULE] {self.windowTitle()} 模組更新失敗")
        
        return success
```

---

### 3️⃣ 模組層更新

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_module.py`  
**方法**: `update_parameters()` (Line 185-218)

```python
def update_parameters(self, year: int, race: str, session: str, **kwargs) -> bool:
    """
    更新分析參數
    
    Args:
        year: 年份 (int)
        race: 賽事
        session: 賽段
        **kwargs: 額外參數
        
    Returns:
        bool: 更新是否成功
    """
    try:
        print(f"[RANKING_MODULE] 更新參數: {year} {race} {session}")
        
        # 更新模組本地參數
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        
        # 🔑 調用 MDI 核心的更新方法
        if self._ranking_core:
            return self._ranking_core.update_analysis_parameters(
                year=str(year),
                race=race,
                session=session
            )
        
        return False
        
    except Exception as e:
        print(f"❌ [RANKING_MODULE] 參數更新錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
```

---

### 4️⃣ MDI 核心更新

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`  
**方法**: `update_analysis_parameters()` (Line 522-555)

**修復前的問題**:
```python
# ❌ 舊版本：只調用 data_loader.load_data()
# 這個方法可能無法觸發 API 調用
if hasattr(self, 'data_loader') and self.data_loader:
    return self.data_loader.load_data(
        year=self.year,
        race=self.race,
        session=self.session
    )
```

**修復後的正確實作**:
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
        
        # 1. 更新 MDI 內部參數
        self.year = str(year)
        self.race = race
        self.session = session
        
        # 2. 同步更新 DataLoader 的參數
        if hasattr(self, 'data_loader') and self.data_loader:
            self.data_loader.year = str(year)
            self.data_loader.race = race
            self.data_loader.session = session
            print(f"[IDEAL_LAP_MDI] ✅ DataLoader 參數已同步")
        
        # 3. 🔑 重點：調用 load_initial_data() 觸發 API 請求
        # 這個方法會啟動 API Worker 並更新 UI
        print(f"[IDEAL_LAP_MDI] 🌐 觸發資料重新載入...")
        self.load_initial_data()
        
        # 異步載入，返回 True 表示啟動成功
        return True
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] 參數更新失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

---

### 5️⃣ API 資料載入

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`  
**方法**: `load_initial_data()` (Line 385-438)

```python
def load_initial_data(self):
    """
    初始載入資料 - 優先使用 API
    
    流程:
    1. 清空舊資料
    2. 更新狀態為「載入中」
    3. 啟動 API Worker 異步請求
    4. Worker 完成後觸發 _on_api_success 或 _on_api_failure
    """
    try:
        print(f"[IDEAL_LAP_MDI] 🚀 開始載入資料: {self.year} {self.race} {self.session}")
        
        # 清空舊資料
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.clear_table()
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText("⏳ 正在從 API 載入資料...")
        
        # 準備 API 參數
        api_params = {
            "year": int(self.year),
            "race": self.race,
            "session": self.session,
            "force_refresh": False  # 可以改為 True 強制重新生成
        }
        
        # 啟動 API Worker
        print(f"[IDEAL_LAP_MDI] 🌐 啟動 API Worker...")
        self.api_worker = IdealLapRankingApiWorker(
            params=api_params,
            base_url="https://localhost:8000",
            timeout=60.0
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動執行緒
        self.api_worker.start()
        
        print(f"[IDEAL_LAP_MDI] ✅ API 請求已啟動")
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] 初始載入失敗: {e}")
        import traceback
        traceback.print_exc()
```

---

### 6️⃣ API Worker 執行

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`  
**類**: `IdealLapRankingApiWorker` (Line 33-105)

```python
def run(self):
    """執行 API 請求"""
    try:
        # 構建 API 端點
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        
        # 構建查詢參數
        query_params = {
            "function_id": 53,  # CLI Function 53 - Ideal Lap Ranking
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
        }
        
        print(f"[API_WORKER] 🌐 調用 API: {endpoint}")
        print(f"[API_WORKER] 📋 參數: {query_params}")
        
        # 發送 POST 請求
        response = requests.post(
            endpoint,
            params=query_params,
            timeout=self.timeout,
            headers={"Accept": "application/json"}
        )
        
        # 檢查 HTTP 狀態
        response.raise_for_status()
        
        # 解析 JSON 回應
        payload = response.json()
        
        # 發射成功信號
        self.success.emit(payload)
        
    except Exception as e:
        # 發射失敗信號
        self.failure.emit(str(e))
```

---

### 7️⃣ UI 更新

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`  
**方法**: `_on_api_success()` (Line 439-476)

```python
@pyqtSlot(dict)
def _on_api_success(self, payload: Dict[str, Any]):
    """API 請求成功 - 處理返回資料"""
    try:
        print(f"[IDEAL_LAP_MDI] ✅ API 調用成功")
        
        # 提取資料和元數據
        data = payload.get("data", {})
        meta = payload.get("metadata", {})
        
        # 驗證數據結構
        if not isinstance(data, dict):
            raise ValueError("API 返回的數據格式錯誤")
        
        if "analysis_result" not in data:
            raise ValueError("API 數據缺少 'analysis_result'")
        
        # 🔑 處理數據（觸發現有的 _on_data_loaded 處理邏輯）
        # 這會更新表格、統計摘要等所有 UI 元素
        self._on_data_loaded(data)
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.lbl_control_status.setText(f"✅ 已從 {source_label} 載入資料")
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] API 數據處理失敗: {e}")
        self._on_api_failure(str(e))
```

---

## 📊 完整流程圖

```
使用者操作
    ↓
主 GUI: on_year/race/session_changed()
    ↓
主 GUI: update_current_window()
    ↓
Module: update_parameters(year, race, session)
    ↓
MDI: update_analysis_parameters(year, race, session)
    ├─ 更新 self.year, race, session
    ├─ 同步 data_loader.year, race, session
    └─ 調用 load_initial_data()
           ↓
       清空舊表格 + 更新狀態為「載入中」
           ↓
       啟動 API Worker (異步執行緒)
           ↓
       POST /api/v2/analysis/execute?function_id=53
           ↓
       API 服務器 → CLI Function 53 → JSON 生成
           ↓
       API 返回資料
           ↓
       _on_api_success(payload)
           ↓
       _on_data_loaded(data)
           ├─ 更新表格資料
           ├─ 更新統計摘要
           └─ 更新狀態為「載入完成」
           ↓
       UI 完成更新 ✅
```

---

## ✅ 驗證清單

### 已實作功能
- [x] **主 GUI 事件綁定**: Year/Race/Session 下拉選單變更事件
- [x] **視窗更新邏輯**: `update_current_window()` 調用模組的 `update_parameters()`
- [x] **模組層更新**: `IdealLapRankingTableModule.update_parameters()`
- [x] **MDI 層更新**: `IdealLapRankingTableMDI.update_analysis_parameters()`
- [x] **參數同步**: MDI 和 DataLoader 參數同步更新
- [x] **資料重新載入**: 調用 `load_initial_data()` 觸發 API 請求
- [x] **API Worker**: 異步執行 HTTP 請求
- [x] **UI 更新**: 清空舊資料 + 載入新資料 + 更新狀態

### 關鍵修復 (2025-10-09)
- [x] **修復 MDI 的 `update_analysis_parameters()`**:
  - 從：調用 `data_loader.load_data()` (不會觸發 API)
  - 改為：調用 `load_initial_data()` (正確觸發 API Worker)
  - 新增：DataLoader 參數同步更新

---

## 🧪 測試建議

### 手動測試步驟
1. 啟動 GUI: `python f1t_gui_main.py`
2. 打開 Ideal Lap Ranking 模組 (使用預設參數，例如 2025 Japan R)
3. 驗證初始資料載入成功
4. 更改主 GUI 的 Year 下拉選單 (例如從 2025 → 2024)
5. **預期行為**: 表格清空 → 狀態變為「載入中」→ API 請求 → 表格更新為新資料
6. 更改 Race 下拉選單 (例如從 Japan → Italy)
7. **預期行為**: 同步驟 5
8. 更改 Session 下拉選單 (例如從 R → Q)
9. **預期行為**: 同步驟 5

### 控制台輸出檢查
```
[IDEAL_LAP_MDI] 🔄 更新參數: 2024 Italy Q
[IDEAL_LAP_MDI] ✅ DataLoader 參數已同步
[IDEAL_LAP_MDI] 🌐 觸發資料重新載入...
[IDEAL_LAP_MDI] 🚀 開始載入資料: 2024 Italy Q
[IDEAL_LAP_MDI] 🌐 啟動 API Worker...
[API_WORKER] 🌐 調用 API: https://localhost:8000/api/v2/analysis/execute
[API_WORKER] 📋 參數: {'function_id': 53, 'year': 2024, 'race': 'Italy', 'session': 'Q'}
[IDEAL_LAP_MDI] ✅ API 調用成功
[IDEAL_LAP_MDI] 資料載入完成，開始處理...
[IDEAL_LAP_MDI] ✅ 表格已更新 (20 位車手)
```

### 異常情況測試
1. **API 服務器離線**: 
   - 預期: 自動切換到本地 JSON 備援
   - 狀態: 「⚠️ 從本地檔案載入（API 失敗）」

2. **本地 JSON 也不存在**: 
   - 預期: 顯示錯誤對話框
   - 訊息: 「API 調用失敗，本地檔案也找不到，請檢查網路連接或手動執行 CLI 生成資料」

3. **網路超時**: 
   - 預期: 60 秒後超時，切換到本地 JSON

---

## 📝 開發筆記

### 為什麼要調用 `load_initial_data()` 而不是 `data_loader.load_data()`?

1. **`load_initial_data()`**:
   - 🌐 啟動 **API Worker** 執行緒
   - 🧹 清空舊表格資料
   - 📊 更新 UI 狀態（載入中 → 完成）
   - 🔄 完整的異步載入流程

2. **`data_loader.load_data()`** (舊方法):
   - 📂 只讀取本地 JSON 檔案
   - ❌ **不會**調用 API
   - ❌ **不會**更新 UI 狀態
   - ⚠️ 無法獲取最新資料

### DataLoader 的角色

在 Ideal Lap Ranking 的架構中，`DataLoader` 主要負責：
- ✅ 驗證資料格式 (`_validate_data_format`)
- ✅ 轉換資料為顯示格式 (`_transform_data_for_display`)
- ✅ 建立檔案搜尋模式 (`_build_filename_patterns`)
- ❌ **不負責** API 調用（由 API Worker 處理）

---

## 🎯 結論

**Ideal Lap Ranking 模組已完整實作參數更新機制** ✅

使用者更改主 GUI 的 Year/Race/Session 時：
1. 模組會自動接收更新通知
2. 清空舊資料
3. 調用 API 獲取新資料
4. 更新表格和統計摘要

**無需任何手動操作，完全自動化！** 🎉

---

**文檔版本**: v1.0.0  
**建立日期**: 2025-10-09  
**最後更新**: 2025-10-09  
**作者**: F1T Team
