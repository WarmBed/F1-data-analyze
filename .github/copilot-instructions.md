# F1T 賽車數據分析 - AI 編程助手指導文件

## ⚠️ 重要系統政策更新 (2025-10-03)

**🔒 API-ONLY 模式現已啟用**

系統現在禁止 GUI 直接呼叫 CLI 進程。所有 GUI 模組必須:
- ✅ 通過 REST API (`refactored_api.py`) 獲取數據
- ✅ 讀取已存在的本地 JSON 檔案
- ❌ **禁止**自動啟動 CLI 進程或執行緒
- ❌ **禁止**使用 `subprocess` 執行 CLI 命令

詳見 [API-ONLY 模式政策](#4-api-only-模式政策--重要更新-2025-10-03)

---

## 🏎️ 專案概述

F1T 是一個專業的 Formula 1 遙測分析系統，採用**雙重架構**設計：
- **GUI 應用程式** (`f1t_gui_main.py`) - 基於 PyQt5 的分析工作站
- **CLI 模組化系統** (`f1_analysis_modular_main.py`) - 52+ 個分析功能

系統使用 **FastF1** 和 **OpenF1 API** 處理 F1 賽事數據，具備自動緩存和 JSON 導出功能。

## 🎯 核心開發原則

### � **最高優先級開發準則** (2025-10-11 更新)

#### 0. **反幻覺編碼五原則（最高優先）** ⚠️ 新增
**原則 0：在每次聊天時先宣告下方五個原則 不可節省token**
- 請每次執行任何項目時，都宣告下面四個原則
- 不懂就問
- 確認需求才實作
- 

**原則 1：禁止幻覺編碼 - 必須先驗證再編寫**
- ❌ **絕對禁止**憑想像或假設編寫任何代碼
- ✅ **強制要求**：編寫任何代碼前必須用 `grep_search` 或 `read_file` 驗證相關實現
- ✅ **強制要求**：調用任何方法前必須確認該方法在目標類別中確實存在
- 🎯 **執行標準**：看到實際代碼才能動手，絕不憑空想像

**原則 2：模組資料夾優先 - 複用現有功能**
- ✅ **開發新功能前**：必須先檢查 `modules/gui/` 資料夾是否已有類似實現
- ✅ **搜索範圍**：
  - `modules/gui/` - 所有 GUI 模組
  - `modules/gui/base/` - 通用基礎類別
  - `CLI_modules/cli/analyzer/` - CLI 分析實現
- ✅ **發現既有功能時**：必須複用或繼承，禁止重複開發
- 🎯 **執行標準**：先用 `file_search` 和 `semantic_search` 確認無重複功能

**原則 3：通用模組優先 - 統一架構模式**
- ✅ **必須使用**：`UniversalDataLoader` 作為所有分析模組的基礎類別
- ✅ **必須使用**：`UniversalChartWidget` 進行數據視覺化
- ✅ **必須使用**：`CustomMdiArea` 管理 MDI 子視窗
- ✅ **參考實現**：以 `rain_analysis` 為標準範本（最完整的通用架構實現）
- 🎯 **執行標準**：任何新模組必須遵循 Rain Analysis 的架構模式

**原則 4 : 模組多國語言化**
- ✅ **必須使用**：`tr()` 函數包裹所有用戶可見字串
不可以有emoji

**原則 5 : print的輸出會被logger導出到log，如有調用print請查看log**

**三原則執行檢查清單**：
```markdown
開始開發前必須完成：
- [ ] ✅ 用 semantic_search 搜索相關功能是否已存在
- [ ] ✅ 用 file_search 檢查 modules/gui/ 是否有類似模組
- [ ] ✅ 用 grep_search 驗證要調用的方法確實存在
- [ ] ✅ 閱讀 rain_analysis 的實現作為參考範本
- [ ] ✅ 確認使用 UniversalDataLoader 和 UniversalChartWidget
- [ ] ❌ 沒有任何假設性編碼或憑空想像的方法調用
```

---

### �🚨 **絕對禁止的開發行為** (2025-10-10 更新)

#### 1. **假設性編程（零容忍）** ⚠️ 已整合至原則 0
- ❌ **禁止假設方法存在**：不得假設任何方法、屬性或類別存在
- ❌ **禁止創造性命名**：不得自行創造方法名稱（如 `update_chart()`）
- ✅ **必須驗證後調用**：每次調用方法前必須用 `grep_search` 或 `read_file` 驗證
- ✅ **完全複製參考**：必須完全複製參考實現的方法調用模式

**錯誤範例**：
```python
# ❌ 錯誤：假設 update_chart() 存在
self.chart_widget.update_chart(data)  # 沒有驗證，直接調用
```

**正確範例**：
```python
# ✅ 正確步驟 1: 用 grep_search 搜索 Widget 的方法
# 發現實際方法是 draw_comparison_bars()

# ✅ 正確步驟 2: 閱讀參考實現的調用方式
# ranking_table 調用 _on_data_loaded() → populate_table()

# ✅ 正確步驟 3: 完全複製調用模式
self._on_data_loaded(api_data)  # 調用實際存在的方法
```

#### 2. **跳過測試（零容忍）** ⚠️ 新增
- ❌ **禁止未測試就交付**：任何代碼必須通過測試才能交付用戶
- ❌ **禁止假設能運行**：不得假設代碼邏輯正確就能運行
- ✅ **三階段測試**：必須執行 Import → 方法驗證 → 功能測試
- ✅ **測試通過才交付**：所有測試通過才能向用戶交付代碼

**強制測試流程**：
```markdown
階段 1: 模組創建後（5 分鐘內）
- [ ] Import 測試通過
- [ ] Widget 方法列表驗證
- [ ] MDI 初始化測試通過
- [ ] 所有引用的方法已確認存在

階段 2: GUI 整合後（10 分鐘內）
- [ ] GUI 啟動無錯誤
- [ ] 選單項目顯示正確
- [ ] 點擊無 AttributeError
- [ ] 點擊無 TypeError

階段 3: 功能測試（15 分鐘內）
- [ ] API 調用成功
- [ ] 圖表正常繪製
- [ ] 錯誤處理正確觸發
- [ ] 無任何未處理異常
```

#### 3. **基類誤用（零容忍）** ⚠️ 新增
- ❌ **禁止假設基類類型**：不得假設 MDI 是 QWidget
- ❌ **禁止自創錯誤處理**：不得直接用 `QMessageBox(self, ...)`
- ✅ **檢查繼承鏈**：必須檢查基類的實際類型
- ✅ **使用基類方法**：必須使用基類提供的 `_show_error()` 等方法

**錯誤範例**：
```python
# ❌ 錯誤：假設 self 是 QWidget
QMessageBox.warning(self, "標題", "訊息")  # TypeError!
```

**正確範例**：
```python
# ✅ 正確步驟 1: 檢查 ranking_table 的錯誤處理
# 發現使用 _show_error() 方法

# ✅ 正確步驟 2: 實現 _show_error() 方法
def _show_error(self, title: str, message: str):
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)

# ✅ 正確步驟 3: 使用基類方法
self._show_error("標題", "訊息")
```

### GUI 模組開發政策
- **統一架構**：任何新的 GUI 分析模組必須以 Rain Analysis 為範例，遵循 `UniversalAnalysisMDI` + `UniversalDataLoader` 的通用架構，保持資料載入器與 MDI 管理分層一致。
- **變更前任務追蹤**：在修改或新增模組前，先於 `tasks/` 目錄建立對應的 `task.md` 描述目標、清單與測試計畫，更新進度直至完成。
- **單項驗證**：每項任務完成後必須執行針對該變更的單項測試或手動驗證，確認無誤才能合併或交付。
- **公開 API 網域強制**：所有 GUI 模組的 HTTP 請求必須指向 `https://localhost:8000`，禁止自動回退至 `localhost`、內網或未經核准的網域。
- **回應篇幅**：在撰寫說明或回覆時，不需節省字數或 token；以完整、細緻的內容回覆使用者需求。

### 1. **禁用模擬數據政策**
- **僅使用真實數據**：所有分析必須使用來自 FastF1/OpenF1 API 的真實 F1 賽事數據
- **禁止模擬**：絕不使用生成、模擬或偽造的遙測數據
- **緩存管理**：API 不可用時可使用緩存的真實數據，但絕不模擬回應

### 2. **PowerShell 命令標準**
- **Windows 環境**：統一使用 PowerShell 命令，絕不使用 CMD
- **腳本執行**：所有批次檔案和自動化使用 PowerShell 語法
- **終端整合**：VS Code 任務配置為 PowerShell 環境
- **Python 指令執行**：`python -c ...`、`python script.py` 等命令必須在 PowerShell 終端直接執行，切勿在 Python REPL 中再次輸入 `python` 觸發 SyntaxError

### 3. **不需要節省token**
- **完整回覆**：在回答問題或撰寫說明時，不需節省字數或 token
- **詳盡內容**：提供完整、細緻的資訊以滿足使用者需求
- **無字數限制**：不設字數上限，確保資訊充分    

### 4. **API-ONLY 模式政策** ⚠️ 重要更新 (2025-10-03)
- **禁止 GUI 呼叫 CLI**：GUI 模組絕不允許直接啟動 CLI 進程或執行緒
- **僅允許 API 獲取數據**：GUI 只能通過 REST API (`refactored_api.py`) 獲取分析數據
- **本地 JSON 讀取**：允許讀取已存在的 JSON 檔案，但不可自動生成
- **手動 CLI 執行**：開發時需要新數據，必須手動在終端執行 CLI 命令
- **對外 API 網域**：正式服務統一使用 `https://localhost:8000`

**禁止的模式**：
```python
# ❌ 禁止：啟動 CLI 進程
self.cli_worker = CliAnalysisWorker(year, race, session, force_mode)
self.cli_worker.start()

# ❌ 禁止：subprocess 執行 CLI
subprocess.run(["python", "f1_analysis_modular_main.py", "-f", "1"])

# ❌ 禁止：自動生成數據
if not data_file:
    self._start_data_generation(**kwargs)  # 不允許!
```

**正確的模式**：
```python
# ✅ 正確：通過 API 獲取數據
self.api_client.get_analysis_data(year, race, session, function_id)

# ✅ 正確：讀取已存在的 JSON
data = self._load_json_data(json_file_path)

# ✅ 正確：提示用戶手動執行
self.load_error.emit("找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據")
```

**手動 CLI 執行範例**：
```powershell
# 正確：PowerShell 語法
python f1_analysis_modular_main.py -f 12 -y 2025 -r Japan -s R

# 避免：CMD 風格命令
```

## 📊 核心架構

### 功能映射系統
系統的核心是 `CLI_modules/cli/core/function_mapper.py`，提供 **52 個標準化分析功能** (1-52)：
- 功能 1-10：基礎分析（降雨、賽道、進站、事故）
- 功能 11-23：進階遙測和車手比較
- 功能 24-35：專業賽事分析
- 功能 36-52：擴展功能和實驗性功能

**CLI 使用範例：**
```powershell
python f1_analysis_modular_main.py -f 13 -y 2025 -r Japan -s R -d VER -d2 LEC
```

### 數據流模式
**⚠️ API-ONLY 模式 (2025-10-03 更新)**

系統現在採用嚴格的 API-ONLY 架構:

1. **API 優先**：所有動態數據獲取必須通過 `refactored_api.py` REST API
2. **本地 JSON 讀取**：允許讀取 `json/` 目錄中已存在的檔案
3. **禁止 CLI 調用**：GUI 不得自動啟動 CLI 進程或執行緒
4. **手動生成**：開發時需要新數據，必須手動執行 CLI 命令生成 JSON

**數據流向**：
```
用戶操作 → GUI 模組 → API 請求 → refactored_api.py → CLI 後端 → 返回 JSON
                    ↓
                本地 JSON 緩存 (僅讀取，不自動生成)
```

### 模組結構
```
CLI_modules/cli/         # 後端分析引擎
modules/gui/            # 前端 GUI 組件  
├── lap_analysis/       # 遙測分析模組
├── tire_analysis/      # 輪胎策略分析
├── rain_analysis/      # 天氣分析
└── base/              # 通用數據載入器
```

## 🔧 開發模式

### GUI 數據載入架構 (API-ONLY)
**⚠️ 重要變更 (2025-10-03)**: GUI 模組已禁用所有 CLI 直接調用

GUI 模組現在採用 **API-ONLY 模式**:
```python
# ✅ 正確模式：API 優先 + 本地 JSON 讀取
json_files = self._search_json_files(**params)
if json_files:
    # 讀取已存在的本地 JSON
    return self._load_json_data(json_files[0])
else:
    # 不再自動啟動 CLI！改為提示錯誤
    self.load_error.emit("找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據")
    return False
```

**已禁用的模式** (不可再使用):
```python
# ❌ 禁止：自動 CLI 生成 (已移除)
if not json_files:
    self._generate_data_via_cli(**params)  # 此方法現在固定返回 False
```

### 通用數據載入器
所有 GUI 分析模組繼承自 `UniversalDataLoader`:
```python
class YourAnalysisLoader(UniversalDataLoader):
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取數據")
        return False
        
    def _validate_data_format(self, raw_data):
        # 驗證 JSON 結構
        pass
        
    def _transform_data_for_display(self, raw_data):
        # 將數據轉換為 GUI 格式
        pass
```

### CLI 功能開發
添加新分析功能時：
1. 在 `F1AnalysisFunctionMapper` 的 `function_mapping` 字典中添加
2. 實現 `_execute_your_function()` 方法
3. 導出結構化 JSON 以匹配 GUI 期望
4. 在 `show_help()` 中更新幫助文檔

## 🚀 建置和測試工作流

### 快速啟動命令
```powershell
# GUI 模式（主要介面）
python f1t_gui_main.py

# CLI 分析（後端處理）  
python f1_analysis_modular_main.py -f 1 -y 2025 -r Japan -s R

# API 服務器模式
python APIserver.py

# 執行所有測試
python -m pytest tests/ -v --tb=short
```

### 可用的 VS Code 任務
- `🎯 執行 F1T GUI 主程式` - 啟動主要 GUI
- `🔄 重啟 F1T GUI` - 強制重啟 GUI
- `🧪 執行所有測試` - 執行測試套件
- `🧹 清理緩存檔案` - 清理緩存檔案

## 💡 關鍵整合點

### 數據源優先級 (API-ONLY 模式)
**⚠️ 2025-10-03 更新**: GUI 不再自動調用 CLI

1. **API 服務**：`refactored_api.py` REST API (主要數據來源)
2. **本地 JSON**：`json/` 目錄中已存在的分析結果 (只讀)
3. **FastF1 緩存**：`f1_analysis_cache/` 中的 HTTP 緩存
4. **手動 CLI**：開發者手動執行 CLI 生成 JSON

**GUI 數據獲取流程**:
```
GUI 請求 → 檢查本地 JSON → 存在: 讀取檔案
                          ↓
                          不存在: ❌ 禁止啟動 CLI
                                 ✅ 通過 API 獲取
                                 ✅ 提示用戶手動執行
```

### 會話參數
所有功能使用標準化的賽事識別：
- **年份**：2024, 2025（主要支援的賽季）
- **賽事**：國家名稱（例如："Japan"、"Italy"、"Australia"）
- **會話**："R"（正賽）、"Q"（排位賽）、"FP1/2/3"（練習賽）
- **車手代碼**：3 字母格式（"VER"、"LEC"、"HAM"）

### 檔案命名約定
```
# JSON 導出
{analysis_type}_{year}_{race}_{session}_{driver}_{timestamp}.json

# 緩存檔案  
f1_data_{year}_{race}_{session}.pkl

# 遙測比較
comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{n}.json
```

## 🎯 GUI 模組開發

### MDI 視窗模式
GUI 使用**多文檔介面**與 `CustomMdiArea`：
```python
# 創建分析視窗
analysis_window = YourAnalysisModule(year, race, session)
sub_window = QMdiSubWindow()
sub_window.setWidget(analysis_window)
self.mdi_area.addSubWindow(sub_window)
```

### 圖表整合
使用 `UniversalChartWidget` 進行一致的數據視覺化：
- 自動主題管理
- 內建導出功能  
- 遙測數據繪圖優化

### 背景處理 (已禁用)
**⚠️ API-ONLY 模式**: GUI 不再使用 CLI 背景執行緒

**已禁用的模式**:
```python
# ❌ 不再使用此模式
self.cli_worker = CliAnalysisWorker(year, race, session, force_mode)
self.cli_worker.analysis_completed.connect(self._on_analysis_complete)
self.cli_worker.start()
```

**正確的模式**:
```python
# ✅ 使用 API 異步請求
self.api_worker = ApiRequestWorker(url, params)
self.api_worker.data_received.connect(self._on_data_received)
self.api_worker.start()
```

## ⚠️ 常見陷阱

- **禁用模擬數據**：絕不使用模擬或偽造的 F1 數據 - 始終使用真實的 FastF1/OpenF1 API
- **僅用 PowerShell**：所有終端命令使用 PowerShell 語法，避免 CMD
- **API-ONLY 模式**：GUI 絕不自動啟動 CLI 進程，只允許通過 API 或讀取本地 JSON 獲取數據
- **編碼處理**：subprocess 調用中文文字輸出時始終使用 UTF-8
- **緩存管理**：檢查 `cache/` 和 `f1_analysis_cache/` 兩個目錄  
- **功能 ID**：使用整數映射（1-52），不使用小數（避免 "6.1"，使用 force_mode=6）
- **JSON 結構**：CLI 輸出必須符合 GUI 期望的數據格式
- **會話密鑰**：OpenF1 API 需要在賽事分析前查找 session_key
- **開發模式**：為開發環境保留本地 JSON 工作流程

## 🌐 API 系統與架構現代化

### FastAPI REST 服務器
系統包含一個生產就緒的 FastAPI 服務器（`APIserver.py`），通過 REST 端點公開 CLI 功能：

```python
# 啟動 API 服務器
python APIserver.py
# 可在以下位置訪問（本地開發）：http://localhost:8000
# 正式對外服務網址：https://localhost:8000
```

**主要 API 端點：**
- `POST /analyze` - 執行分析功能
- `GET /modules` - 列出可用的分析模組 
- `GET /supported-functions` - 獲取功能 ID（1-52）
- `GET /health` - 健康檢查端點
- `GET /docs` - 自動生成的 API 文檔

### API 優先開發模式
**⚠️ API-ONLY 模式 (2025-10-03 更新)**: GUI 現在強制使用 API-ONLY 模式

**開發模式（手動 CLI + 本地 JSON）：**
```python
# 步驟 1: 手動在終端執行 CLI 生成 JSON 檔案
# PowerShell:
python f1_analysis_modular_main.py -f 12 -y 2025 -r Japan -s R
# → 輸出到 json/ 目錄

# 步驟 2: GUI 讀取本地 JSON 檔案
json_files = self._search_json_files(**params)
if json_files:
    return self._load_json_data(json_files[0])
else:
    # ❌ 不再自動啟動 CLI
    self.load_error.emit("找不到數據檔案，請使用 API 或手動執行 CLI")
```

**生產模式（API 整合）：**
```python
# 當前：基於 API 的數據載入  
async def _fetch_analysis_via_api(self, **params):
    response = await self.api_client.post("/analyze", json={
        "function_id": self.cli_function,
        "year": params["year"],
        "race": params["race"], 
        "session": params["session"]
    })
    return response.json()["data"]
```

**已禁用的模式**:
```python
# ❌ 不再支援自動模式切換
if DEVELOPMENT_MODE:
    if not data:
        self._generate_data_via_cli(**params)  # 此方法已禁用
```

### 請求/響應模型
```python
# 分析請求結構
{
    "function_id": "12",
    "year": 2025,
    "race": "Japan", 
    "session": "R",
    "driver1": "VER",
    "driver2": "LEC"
}

# 標準化 API 響應
{
    "success": true,
    "message": "分析完成",
    "data": { /* 分析結果 */ },
    "timestamp": "2025-09-15T10:30:00",
    "execution_time": "2.5秒"
}
```

## 🌍 國際化 (i18n) 框架

### 當前語言支援
系統在多個模組中具有**部分雙語支援**（英文/中文）：

```python
# 範例：事故分析中的事件翻譯
def _translate_event_to_chinese(self, message):
    message_upper = message.upper()
    if 'TRACK LIMIT' in message_upper:
        return '賽道邊界違規'
    elif 'PENALTY' in message_upper:
        return '處罰'
    # ... 更多翻譯
```

### 計劃的 i18n 架構
**目標實現：**具有語言檔案的集中式翻譯系統：

```python
# 建議結構
locales/
├── en.json          # 英文翻譯
├── zh-TW.json       # 繁體中文  
├── zh-CN.json       # 簡體中文
└── ja.json          # 日文（未來）

# 使用模式
from core.i18n import translate as _
message = _("TRACK_LIMIT_VIOLATION", locale="zh-TW")
```

### 翻譯整合點
1. **GUI 標籤**：所有 PyQt5 小工具文字
2. **分析結果**：數據表格標題和描述  
3. **API 響應**：錯誤訊息和狀態文字
4. **CLI 輸出**：終端進度和結果訊息
5. **圖表圖例**：Matplotlib 圖形標籤和標題

### CJK 字體管理
多個模組中已實現中文字體支援：
```python
# matplotlib 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

## 🔍 調試

### 啟用調試輸出
```python
# GUI 模組
self._debug_enabled = True  # 在 UniversalDataLoader 子類中

# CLI 模組  
show_detailed_output = True  # 在功能映射器調用中
```

### 常見調試位置
- GUI：`modules/gui/{analysis_type}/` - 檢查數據載入器調試輸出
- CLI：`CLI_modules/cli/analyzer/` - 個別分析實現
- 緩存：`f1_analysis_cache/fastf1_http_cache.sqlite` - FastF1 HTTP 緩存
- 日誌：終端輸出，包含 `[DEBUG]`、`[ERROR]`、`[SUCCESS]` 前綴
- API：`logs/f1_api.log` - FastAPI 服務器日誌，包含請求/響應追蹤
