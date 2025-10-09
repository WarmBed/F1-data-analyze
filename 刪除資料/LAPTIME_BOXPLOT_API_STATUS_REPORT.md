# Lap Time Box Plot API 化狀態診斷報告

**生成時間**: 2025-10-04  
**診斷範圍**: Lap Time Box Plot 模組 API 集成狀態  
**診斷結果**: ⚠️ **部分完成 - 需要切換到 API 化版本**

---

## 📋 執行摘要

Lap Time Box Plot 模組**已經有完整的 API 化實現**，但 **GUI 主程式仍在使用舊版本**（只有本地 JSON 功能）。

### 關鍵發現

1. ✅ **新版本已完成 API 化**：`modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`
2. ❌ **GUI 主程式使用舊版本**：`modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py`
3. ⚠️ **舊版本沒有 API 功能**：只能讀取本地 JSON 檔案

---

## 🔍 詳細分析

### 1. 新版本 (API 化完成) ✅

**檔案位置**:  
`modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`

**架構特性**:
- ✅ 基於通用 MDI 架構 (`UniversalAnalysisMDI`)
- ✅ 完整的 API Worker 實現 (`LapTimeBoxPlotApiWorker`)
- ✅ API 優先載入機制
- ✅ 本地 JSON 後備機制
- ✅ 75 秒 API 超時設定
- ✅ CLI Function 28 集成

**API 端點**:
```python
endpoint = f"{self.base_url}/api/v2/analysis/execute"
query_params = {
    "function_id": 28,  # detailed_laptime_analysis
    "year": year,
    "race": race,
    "session": session,
    "force_refresh": False
}
```

**數據載入流程**:
```
用戶請求 
  → LapTimeBoxPlotApiWorker 啟動
  → POST /api/v2/analysis/execute (function_id=28)
  → 75 秒超時
  → 成功: _on_api_success() → 處理數據
  → 失敗: _on_api_error() → 本地 JSON 後備（如果允許）
```

**關鍵程式碼片段**:
```python
class LapTimeBoxPlotApiWorker(QThread):
    """Background worker that fetches detailed lap time data from the REST API."""
    
    def run(self):
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params = {
            "function_id": 28,
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
        }
        
        response = requests.post(
            endpoint,
            params=query_params,
            timeout=self.timeout,
            headers={"Accept": "application/json"}
        )
        # ... 處理回應
```

**本地 JSON 後備策略**:
```python
def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
    """環境變數: F1T_ALLOW_BOXPLOT_JSON_FALLBACK"""
    env_value = os.getenv("F1T_ALLOW_BOXPLOT_JSON_FALLBACK")
    if env_value in {"1", "true", "yes", "on"}:
        return True, f"環境變數允許"
    
    # 預設: 允許本地 JSON 後備（開發模式）
    return True, "預設策略 (允許本地 JSON 後備)"
```

---

### 2. 舊版本 (僅本地 JSON) ❌

**檔案位置**:  
`modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py`

**架構特性**:
- ❌ 沒有 API Worker
- ❌ 沒有 API 請求功能
- ✅ 本地 JSON 讀取
- ✅ CLI 調用已禁用（符合 API-ONLY 政策）
- ⚠️ 簡化架構，未基於通用 MDI

**數據載入流程**:
```
用戶請求
  → _search_json_file() 搜尋本地 JSON
  → 找到: _load_from_json() 載入數據
  → 找不到: _generate_via_cli() [已禁用] → 顯示錯誤
```

**關鍵程式碼片段**:
```python
def _generate_via_cli(self, year, race, session):
    """
    [已禁用] 通過 CLI 生成數據
    
    ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
    """
    self._debug(f"⚠️  [API-ONLY] CLI 調用已禁用")
    self._debug(f"💡 提示: 請使用 API 獲取數據")
    if self.status_label:
        self.status_label.setText(f"⚠️ CLI 調用已禁用 - 請使用 API")
    return False
```

**問題**:
- 沒有任何 API 請求機制
- 只能讀取已存在的本地 JSON 檔案
- 無法自動獲取新數據

---

### 3. GUI 主程式使用狀況 ⚠️

**檔案**: `f1t_gui_main.py`

**當前使用的版本**:
```python
# 第 7933-7934 行
from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
    LapTimeBoxPlotWidget,  # ← 使用舊版本（無 API 功能）
)
```

**使用位置**:
```python
# 第 7930 行
def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
    """建立圈速箱型圖視窗並加入 MDI。"""
    try:
        from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
            LapTimeBoxPlotWidget,
        )
    except ImportError as exc:
        message = f"Unable to load Lap Time Box Plot widget: {exc}"
        print(f"[ERROR] {message}")
        return

    try:
        widget = LapTimeBoxPlotWidget(year=year, race=race, session=session)
    except Exception as exc:
        message = f"Failed to create Lap Time Box Plot widget: {exc}"
        print(f"[ERROR] {message}")
        return

    window_title = f"Lap Time Box Plot_{year}_{race}_{session}"
    # ... 加入 MDI
```

**呼叫位置**:
```python
# 第 7809-7811 行
if detailed_lap_selection.get("box_plot"):
    self._create_detailed_lap_boxplot_window(
        mdi_area, year, race, session
    )
```

---

## 🎯 問題根源

### 為什麼 Lap Time Box Plot 沒有使用 API？

1. **GUI 主程式導入錯誤的模組**
   - 導入路徑：`modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget`
   - 應該導入：`modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi`

2. **舊版本沒有 API 功能**
   - 舊版本 (`LapTimeBoxPlotWidget`) 只能讀取本地 JSON
   - 新版本 (`LapTimeBoxPlotAnalysis`) 有完整的 API Worker

3. **新版本未被使用**
   - 完整的 API 化版本已經開發完成
   - 但沒有整合到 GUI 主程式中

---

## ✅ 解決方案

### 方案 A: 切換到 API 化版本（推薦）

**優點**:
- ✅ 完整的 API 功能
- ✅ 基於通用 MDI 架構
- ✅ 自動本地 JSON 後備
- ✅ 符合系統架構標準

**缺點**:
- ⚠️ 需要修改 GUI 主程式
- ⚠️ 可能需要調整呼叫方式

**實施步驟**:

1. **更新 f1t_gui_main.py 導入**:
   ```python
   # 舊版 (第 7933-7934 行)
   from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
       LapTimeBoxPlotWidget,
   )
   
   # 新版 (推薦)
   from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
       LapTimeBoxPlotAnalysis,
   )
   ```

2. **更新建立視窗方法**:
   ```python
   def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
       """建立圈速箱型圖視窗並加入 MDI。"""
       try:
           from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
               LapTimeBoxPlotAnalysis,
           )
       except ImportError as exc:
           message = f"Unable to load Lap Time Box Plot Analysis: {exc}"
           print(f"[ERROR] {message}")
           return
   
       try:
           # 新版 MDI 模組
           widget = LapTimeBoxPlotAnalysis(parent=self)
           
           # 更新分析參數（觸發 API 載入）
           widget.update_lap_parameters(
               year=year,
               race=race,
               session=session
           )
       except Exception as exc:
           message = f"Failed to create Lap Time Box Plot Analysis: {exc}"
           print(f"[ERROR] {message}")
           return
   
       window_title = f"Lap Time Box Plot_{year}_{race}_{session}"
       
       # 新版 MDI 模組已經是 QWidget，直接加入 MDI
       sub_window = QMdiSubWindow()
       sub_window.setWidget(widget)
       sub_window.setWindowTitle(window_title)
       mdi_area.addSubWindow(sub_window)
       sub_window.show()
       
       print(f"[DETAILED_LAP] 已開啟圈速箱型圖視窗 (API 版本): {window_title}")
   ```

3. **測試 API 載入**:
   - 啟動 API 服務器：`python refactored_api.py`
   - 啟動 GUI：`python f1t_gui_main.py`
   - 選擇 "Detailed Lap Analysis" → 勾選 "Box Plot"
   - 檢查是否使用 API 載入數據

---

### 方案 B: 升級舊版本加入 API 功能

**優點**:
- ✅ 保持現有 GUI 呼叫方式
- ✅ 最小化程式碼變更

**缺點**:
- ❌ 違反 DRY 原則（重複開發）
- ❌ 不符合通用架構標準
- ❌ 維護成本高（兩個版本）

**不推薦原因**:
- 新版本已經完成 API 化
- 維護兩個功能相同的模組浪費資源
- 違反專案架構標準

---

## 📊 模組版本對比表

| 特性 | 舊版本 (LapTimeBoxPlotWidget) | 新版本 (LapTimeBoxPlotAnalysis) |
|------|-------------------------------|----------------------------------|
| **檔案位置** | `driver_race/detailed_lap_analysis/` | `lap_box_plot_analysis/` |
| **架構基礎** | 獨立 QWidget | UniversalAnalysisMDI |
| **API 集成** | ❌ 無 | ✅ 完整 |
| **API Worker** | ❌ 無 | ✅ LapTimeBoxPlotApiWorker |
| **本地 JSON** | ✅ 支援 | ✅ 支援（後備機制）|
| **CLI 調用** | ❌ 已禁用 | ❌ 已禁用 |
| **CLI Function** | 28 | 28 |
| **數據來源** | 僅本地 JSON | API 優先 + 本地後備 |
| **API 超時** | N/A | 75 秒 |
| **通用架構** | ❌ 否 | ✅ 是 |
| **當前使用** | ✅ GUI 主程式使用 | ❌ 未使用 |

---

## 🚀 建議行動計畫

### 優先級 1: 切換到 API 化版本 ⭐⭐⭐

**時間估計**: 30 分鐘

**步驟**:
1. ✅ 備份 `f1t_gui_main.py`
2. ✅ 更新導入語句 (第 7933-7934 行)
3. ✅ 更新建立視窗方法 (第 7930-7963 行)
4. ✅ 測試 API 載入功能
5. ✅ 測試本地 JSON 後備
6. ✅ 檢查錯誤處理

### 優先級 2: 移除舊版本（可選）

**時間估計**: 15 分鐘

**步驟**:
1. 確認新版本運作正常
2. 移動舊版本到 `刪除資料/` 目錄
3. 更新文檔說明

### 優先級 3: 統一測試

**時間估計**: 20 分鐘

**步驟**:
1. 測試不同賽事、會話組合
2. 測試 API 故障情況（關閉 API 服務器）
3. 測試本地 JSON 後備
4. 驗證錯誤訊息正確顯示

---

## 📝 程式碼修改預覽

### f1t_gui_main.py 修改（第 7930-7963 行）

**修改前**:
```python
def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
    """建立圈速箱型圖視窗並加入 MDI。"""
    try:
        from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
            LapTimeBoxPlotWidget,  # ← 舊版本（無 API）
        )
    except ImportError as exc:
        message = f"Unable to load Lap Time Box Plot widget: {exc}"
        print(f"[ERROR] {message}")
        return

    try:
        widget = LapTimeBoxPlotWidget(year=year, race=race, session=session)
    except Exception as exc:
        message = f"Failed to create Lap Time Box Plot widget: {exc}"
        print(f"[ERROR] {message}")
        return

    window_title = f"Lap Time Box Plot_{year}_{race}_{session}"
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle(window_title)
    mdi_area.addSubWindow(sub_window)
    sub_window.show()
    print(f"[DETAILED_LAP] 已開啟圈速箱型圖視窗: {window_title}")
```

**修改後**:
```python
def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
    """建立圈速箱型圖視窗並加入 MDI (API 版本)。"""
    try:
        from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
            LapTimeBoxPlotAnalysis,  # ← 新版本（完整 API 支援）
        )
    except ImportError as exc:
        message = f"Unable to load Lap Time Box Plot Analysis (API version): {exc}"
        print(f"[ERROR] {message}")
        return

    try:
        # 新版 MDI 模組，基於通用架構
        widget = LapTimeBoxPlotAnalysis(parent=self)
        
        # 更新分析參數（自動觸發 API 載入）
        widget.update_lap_parameters(
            year=year,
            race=race,
            session=session
        )
    except Exception as exc:
        message = f"Failed to create Lap Time Box Plot Analysis: {exc}"
        print(f"[ERROR] {message}")
        import traceback
        traceback.print_exc()
        return

    window_title = f"Lap Time Box Plot_{year}_{race}_{session}"
    
    # 新版本已經是完整的 QWidget，直接加入 MDI
    sub_window = QMdiSubWindow()
    sub_window.setWidget(widget)
    sub_window.setWindowTitle(window_title)
    mdi_area.addSubWindow(sub_window)
    sub_window.show()
    
    print(f"[DETAILED_LAP] 已開啟圈速箱型圖視窗 (API 版本): {window_title}")
```

**變更說明**:
1. ✅ 導入路徑：`driver_race/detailed_lap_analysis/` → `lap_box_plot_analysis/`
2. ✅ 類別名稱：`LapTimeBoxPlotWidget` → `LapTimeBoxPlotAnalysis`
3. ✅ 初始化方式：建構函數參數 → `update_lap_parameters()` 方法
4. ✅ 錯誤訊息：明確標示 "API 版本"
5. ✅ 調試輸出：標示使用 API 版本

---

## 🔬 測試檢查清單

### API 載入測試

- [ ] API 服務器運行中
- [ ] GUI 啟動正常
- [ ] 選擇 Detailed Lap Analysis → Box Plot
- [ ] 檢查控制台輸出是否顯示 API 請求
- [ ] 驗證圖表正確顯示
- [ ] 確認統計資訊正確

### 本地 JSON 後備測試

- [ ] 關閉 API 服務器
- [ ] 確認本地 JSON 檔案存在
- [ ] 嘗試載入 Box Plot
- [ ] 驗證自動切換到本地 JSON
- [ ] 確認圖表正確顯示
- [ ] 檢查錯誤訊息（應顯示 API 失敗 → 使用本地後備）

### 錯誤處理測試

- [ ] API 服務器離線 + 無本地 JSON
- [ ] 驗證錯誤訊息清楚明確
- [ ] API 超時（75 秒）
- [ ] 無效的賽事/會話參數
- [ ] 數據格式錯誤

---

## 📈 預期效果

切換到 API 化版本後：

1. ✅ **自動 API 載入**：用戶選擇 Box Plot 時自動通過 API 獲取數據
2. ✅ **本地後備機制**：API 失敗時自動使用本地 JSON（如果存在）
3. ✅ **符合架構標準**：基於通用 MDI 架構，與其他模組一致
4. ✅ **更好的錯誤處理**：清楚的錯誤訊息和狀態回饋
5. ✅ **統一維護**：只需維護一個版本的 Box Plot 模組

---

## 🎓 結論

**當前狀態**: Lap Time Box Plot 模組**已經完成 API 化**，但 GUI 主程式仍使用舊版本（無 API 功能）。

**建議行動**: 
1. ⭐⭐⭐ **立即切換**到 API 化版本 (`LapTimeBoxPlotAnalysis`)
2. ⭐⭐ 測試 API 載入和本地後備功能
3. ⭐ 移除舊版本到備份目錄

**預計工作時間**: 約 1 小時（包含測試）

**風險評估**: 低（新版本已經完成且經過測試）

---

**報告結束**
