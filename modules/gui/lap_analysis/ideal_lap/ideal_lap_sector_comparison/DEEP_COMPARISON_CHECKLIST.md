# 理想圈分段對比模組 vs 理想圈排名表 - 深度對比檢查清單
**Sector Comparison vs Ranking Table - Deep Comparison Checklist**

## 📋 對比檢查清單

### ✅ 已符合項目

| 檢查項目 | ranking_table | sector_comparison | 狀態 |
|---------|--------------|-------------------|------|
| **1. 基類繼承** | | | |
| └─ UniversalAnalysisMDI | ✅ | ✅ | ✅ 符合 |
| └─ AnalysisMDIConfig 註冊 | ✅ | ✅ | ✅ 符合 |
| └─ ensure_registered() 類別方法 | ✅ | ✅ | ✅ 符合 |
| **2. 數據管理** | | | |
| └─ create_data_manager() | ✅ | ✅ | ✅ 符合 |
| └─ create_chart_widget() | ✅ | ✅ | ✅ 符合 |
| └─ UniversalDataLoader 繼承 | ✅ | ✅ | ✅ 符合 |
| **3. 模組接口** | | | |
| └─ IAnalysisModule 實現 | ✅ | ✅ | ✅ 符合 |
| └─ load_data() | ✅ | ✅ | ✅ 符合 |
| └─ clear_data() | ✅ | ✅ | ✅ 符合 |
| └─ refresh_analysis() | ✅ | ✅ | ✅ 符合 |
| └─ export_data() | ✅ | ✅ | ✅ 符合 |
| **4. 參數管理** | | | |
| └─ year, race, session | ✅ | ✅ | ✅ 符合 |
| └─ initialize_module() | ✅ | ✅ | ✅ 符合 |
| └─ update_parameters() | ✅ | ✅ | ✅ 符合 |
| **5. API-ONLY 模式** | | | |
| └─ _generate_data_via_cli() 禁用 | ✅ | ✅ | ✅ 符合 |
| └─ API-ONLY 警告訊息 | ✅ | ✅ | ✅ 符合 |

---

### ❌ 缺失項目（critical）

| 檢查項目 | ranking_table | sector_comparison | 狀態 |
|---------|--------------|-------------------|------|
| **1. API Worker 執行緒** | | | |
| └─ IdealLapRankingApiWorker 類別 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ QThread 異步請求 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ progress, success, failure 信號 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| **2. API 整合方法** | | | |
| └─ load_initial_data() | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ _on_api_progress() | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ _on_api_success() | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ _on_api_failure() | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| **3. API 端點** | | | |
| └─ https://localhost:8000 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ POST /api/v2/analysis/execute | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| └─ function_id=53 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |
| **4. 數據處理流程** | | | |
| └─ API → 驗證 → 轉換 → 顯示 | ✅ 完整 | ⚠️ **不完整** | 🟡 需要完善 |
| └─ 錯誤處理和回退機制 | ✅ 有 | ❌ **缺少** | 🔴 需要補充 |

---

### 🔍 詳細對比分析

#### 1. API Worker 實現

**ranking_table 有，sector_comparison 缺少**:

```python
# ranking_table 有完整的 API Worker
class IdealLapRankingApiWorker(QThread):
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, params, base_url="https://localhost:8000", timeout=60.0):
        # ...
    
    def run(self):
        # 執行 API 請求
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params = {
            "function_id": 53,
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
        }
        response = requests.post(endpoint, params=query_params, timeout=self.timeout)
        # ...
```

**sector_comparison 缺少**: ❌ 完全沒有 API Worker 類別

---

#### 2. load_initial_data() 方法

**ranking_table**:
```python
def load_initial_data(self):
    """載入初始資料 - 強制使用 API"""
    # 創建 API Worker
    self.api_worker = IdealLapRankingApiWorker(
        params={"year": self.year, "race": self.race, "session": self.session},
        base_url="https://localhost:8000",
        timeout=60.0
    )
    # 連接信號
    self.api_worker.progress.connect(self._on_api_progress)
    self.api_worker.success.connect(self._on_api_success)
    self.api_worker.failure.connect(self._on_api_failure)
    # 啟動
    self.api_worker.start()
```

**sector_comparison**: ❌ 沒有 `load_initial_data()` 方法

---

#### 3. API 回調處理

**ranking_table 有完整的回調**:
```python
@pyqtSlot(int)
def _on_api_progress(self, progress: int):
    """API 請求進度更新"""
    self.lbl_control_status.setText(f"API 載入中... {progress}%")

@pyqtSlot(dict)
def _on_api_success(self, result: Dict[str, Any]):
    """API 請求成功"""
    data = result.get("data", {})
    # 驗證和處理數據
    # 調用 chart_widget 顯示
    self.chart_widget.populate_table(analysis_result)

@pyqtSlot(str)
def _on_api_failure(self, error_msg: str):
    """API 請求失敗"""
    # 回退到本地 JSON 或顯示錯誤
```

**sector_comparison**: ❌ 完全沒有這些回調方法

---

#### 4. 參數初始化方式

**ranking_table**:
```python
def __init__(self, parent=None):  # ✅ 不接受 year/race/session
    super().__init__(analysis_type="ideal_lap_ranking", parent=parent)
    self.year = None  # 延遲初始化
    self.race = None
    self.session = None

def initialize_module(self, parent_widget=None, **kwargs):
    # 從 current_year, current_race, current_session 屬性獲取
    self.year = str(self.current_year)
    self.race = self.current_race
    self.session = self.current_session
```

**sector_comparison**:
```python
def __init__(self, year: str = None, race: str = None, session: str = None, parent=None):
    # ⚠️ 直接接受參數，與 ranking_table 不一致
    self.year = str(year) if year else None
    self.race = race
    self.session = session
```

**問題**: 參數設置方式不一致，可能導致 UniversalAnalysisMDI 基類無法正確設置參數

---

## 🔧 需要修復的問題總結

### Critical（必須修復）

1. ❌ **添加 API Worker 類別** - `IdealLapSectorComparisonApiWorker`
2. ❌ **添加 load_initial_data() 方法** - 主要載入入口
3. ❌ **添加 API 回調方法** - `_on_api_progress`, `_on_api_success`, `_on_api_failure`
4. ❌ **使用公開 API 網域** - `https://localhost:8000`
5. ❌ **修正 __init__ 參數** - 改為延遲初始化，從基類屬性獲取

### High（強烈建議）

6. ⚠️ **添加狀態標籤** - `lbl_control_status` 顯示載入狀態
7. ⚠️ **添加重新載入按鈕** - `btn_reload` 手動刷新
8. ⚠️ **錯誤處理** - API 失敗時的回退機制

### Medium（建議）

9. 💡 **統一日誌前綴** - `[SECTOR_COMPARISON_MDI]` vs `[IDEAL_LAP_MDI]`
10. 💡 **統一狀態管理** - `_is_data_loaded`, `_current_data`

---

## 📊 修復優先級

### 第一階段（立即執行）- 30 分鐘

1. 創建 `IdealLapSectorComparisonApiWorker` 類別（複製 + 修改）
2. 添加 `load_initial_data()` 方法
3. 添加 API 回調方法
4. 修正 `__init__` 參數設置

### 第二階段（隨後） - 15 分鐘

5. 添加控制面板狀態標籤
6. 添加重新載入按鈕
7. 完善錯誤處理

---

## ✅ 修復後驗證清單

- [ ] API Worker 可以正確發送請求
- [ ] load_initial_data() 可以啟動 API 請求
- [ ] API 成功時資料正確顯示在圖表
- [ ] API 失敗時顯示錯誤訊息
- [ ] 重新載入按鈕可以刷新資料
- [ ] 參數更新後可以重新載入
- [ ] 與 ranking_table 模式完全一致

---

**報告生成時間**: 2025-10-09  
**對比基準**: ideal_lap_ranking_table (v1.0.0)  
**檢查模組**: ideal_lap_sector_comparison (v1.0.0)  
**總體符合度**: 約 60%（缺少關鍵的 API 整合）
