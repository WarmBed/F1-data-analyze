# F1T 全面重構計畫 (2026 Q2)

> 基於對整個程式碼庫（CLI + GUI + API + Core）的深度審閱而制定
> 建立日期：2026-04-04

---

## 0. 現狀總覽

### 專案規模

| 區域 | 檔案數 | 行數 | 說明 |
|------|--------|------|------|
| CLI core/ | 13 | 14,019 | 核心引擎 + **function_mapper.py (8,021 行)** |
| CLI analyzer/ | 80 | 55,241 | 52+ 個分析功能實現 |
| CLI prediction/ | 26 | 14,522 | ML 預測模組 |
| GUI modules/ | 368 | 201,002 | 前端分析模組 |
| Windows managers/ | 181 | 22,637 | 主視窗管理代理 |
| Windows widgets/ | 8 | 6,430 | 自訂 Qt 元件 |
| Windows workers/ | 3 | 513 | 背景工作執行緒 |
| Windows dialogs/ | 4 | 2,454 | 對話框 |
| API layer/ | 20 | 7,106 | FastAPI REST 服務 |
| Core infra/ | 15 | 8,442 | 日誌/i18n/設定/DB |
| **根目錄散落** | **141** | **~15,000+** | **check_/temp_/batch_ 等一次性腳本** |
| Tests/ | 710 | - | **大部分為診斷腳本而非 pytest** |
| Tools + Scripts/ | 94 | - | 開發工具 |
| **生產程式碼估計** | **~700+** | **~330,000+** | 不含測試 |

### 架構健康度評分

| 維度 | 分數 | 說明 |
|------|------|------|
| 根目錄整潔度 | 2/10 | 141 個 .py 散落根目錄 |
| 模組化程度 | 5/10 | GUI 通用架構良好，CLI 單點集中 |
| 程式碼重複度 | 3/10 | function_mapper ~40% 重複，GUI 模組 boilerplate 高 |
| 測試覆蓋率 | 2/10 | conftest.py 空白，710 個測試檔案中真正 pytest < 50 |
| 依賴管理 | 1/10 | **無 requirements.txt** |
| i18n 覆蓋率 | 49% | 368 個 GUI 檔案中 187 個未 import tr() |
| API 設計 | 7/10 | FastAPI 架構正確，中間層完善 |
| 文件化 | 5/10 | 37 篇 docs 但分散，根目錄 26 個 .md |

---

## 1. 嚴重問題清單 (Critical Issues)

### C1. God Class: function_mapper.py (8,021 行, 148 個 `_execute_*` 方法)

**問題描述：** 整個 CLI 後端的功能分派集中在一個檔案的一個類別中。148 個方法用幾乎相同的 try/except 模板包裝，約 40% 的程式碼是複製貼上的 boilerplate。新增功能意味著在 8000+ 行的檔案中再加一個方法。

**影響：**
- 無法獨立測試單一分析功能
- Git 合併衝突率極高（單檔案多人修改）
- 循環複雜度 ~450，IDE 效能下降
- 新開發者學習曲線極陡

**量化：**
- 148 個 `_execute_*` 方法
- 143 個主函數 + 17 個子函數
- ~40 個是 placeholder/stub (返回 `success: False`)
- 約 3,200 行是重複的 try/except + print + return 模板

### C2. 資料載入器分裂 (Data Loader Fragmentation)

**問題描述：** 存在三套平行的資料載入器，沒有繼承關係：
- `F1DataLoader` (舊版)
- `CompatibleF1DataLoader` (新版)
- `SimpleDataLoader` (base.py 備用)

同樣地，`F1AnalysisInstance` 和 `CompatibleF1AnalysisInstance` 是水平複製。

**影響：**
- Bug 修復需要同步多處
- 新開發者不知道該用哪個
- 函數映射器中有 fallback chain 做選擇，增加複雜性

### C3. 無依賴管理 (No requirements.txt)

**問題描述：** 專案沒有任何標準的 Python 依賴宣告檔案 (`requirements.txt`、`pyproject.toml`、`setup.py` 皆不存在)。

**影響：**
- 新環境無法重現
- CI/CD 無法自動安裝
- PyInstaller 構建依賴手動追蹤

### C4. 根目錄嚴重汙染 (Root Directory Pollution)

**問題描述：** 141 個 .py 檔案散落在專案根目錄，包括：
- 26 個 `check_*.py`
- 22 個 `temp_*.py`
- 10 個 `batch_*.py`
- 9 個 `generate_*.py`
- 5 個 `verify_*.py`
- 3 個 `debug_*.py`
- 26 個散落的 .md 報告

**影響：**
- 新開發者無法辨識哪些是核心程式
- git status 永遠是一團亂
- IDE 檔案搜尋被大量不相關檔案淹沒

### C5. 測試基礎設施空洞 (Hollow Test Infrastructure)

**問題描述：**
- `conftest.py` 是空白檔案
- 710 個測試檔案中，絕大多數是獨立診斷腳本（手動執行的 `python test_xxx.py`），不是 pytest 格式
- 真正用 `def test_` + pytest fixture 的測試 < 50 個
- 沒有 CI 整合
- 許多測試是一次性的驗證腳本

**影響：**
- 重構時沒有安全網
- 回歸錯誤無法自動發現
- API 端點缺乏系統性測試

### C6. i18n 覆蓋率不足 (i18n Coverage Gap)

**問題描述：** 
- 368 個 GUI .py 檔案中有 187 個 (50.8%) 未 import `tr()`
- 翻譯字典全部硬編碼在 `gui_i18n.py` 的一個巨大 dict 中 (~2000+ 行)
- 無外部語言檔案 (json/yaml)
- 部分模組仍有直接的中文硬編碼字串

---

## 2. 中度問題清單 (Major Issues)

### M1. CLI Analyzer 模式不一致

**問題描述：** 80 個 analyzer 檔案使用了至少 3 種不同的開發模式：
- **函數式：** `def run_xxx(data_loader, show_detailed_output=True)` - 純函數
- **類別式：** `class XxxAnalyzer:` + `def analyze(self)` - OOP
- **混合式：** 頂層函數 + 內部類別 + data_loader 屬性

參數傳遞同樣不一致：
- 有些用 positional args (`year, race, session, driver`)
- 有些從 `**kwargs` 提取
- 有些從 `self.data_loader` 屬性讀取

### M2. 快取策略缺失 (Cache Strategy Missing)

**問題描述：**
- `CLI_modules/cli/cache/` 目錄完全空白
- 快取邏輯分散在各個 analyzer 中，用 pickle 序列化
- 無統一的快取失效策略
- 快取 key 有碰撞風險 (同一 race 不同 session 可能碰撞)
- API V2 的 `cache_service_v2.py` 與 CLI 快取系統脫節

### M3. Windows Manager 過度碎片化

**問題描述：** 181 個 manager 檔案，許多只有 30-80 行，只包含一個方法。例如：
- `mdi_windows_closer.py` - 可能只有一個 `close_all()` 方法
- `window_maximizer.py` - 可能只有一個 `maximize()` 方法
- `f1tv_auth_*.py` - 5 個独立檔案做同一功能

**影響：**
- 檔案探索成本高
- import 路徑冗長
- 部分 manager 功能重疊

### M4. GUI 模組 Boilerplate 過高

**問題描述：** 每個分析模組標準由 3 個檔案組成（DataLoader + MDI + ChartWidget），但這 3 個檔案中有大量重複的初始化、信號連接、錯誤處理程式碼。

**粗估：** 每個模組約有 30-50% 的程式碼是 boilerplate，乘以 30+ 個模組 = 大量重複。

### M5. Print 語句氾濫

**問題描述：** 整個專案使用 `print()` 輸出除錯資訊。雖然 `core/logger.py` 有 print patching 機制，但：
- function_mapper.py 中有 200+ 個 `print()` 呼叫
- 各 analyzer 也有大量 print 語句
- 混用 `print()` 和 `self._debug()` 和 `logger.info()`
- API 的 `analysis.py` 有 ~600 行 `print(f"[MERGE]...")` debug 輸出

### M6. Dead Code / Placeholder 功能

**問題描述：**
- function_mapper 中至少 18 個 placeholder 方法 (返回 `success: False`)
- 已棄用的 `/analyze` endpoint 仍有 ~60 行註解程式碼
- `CliAnalysisWorker` 的 `run()` 方法已禁用但保留了 ~60 行舊程式碼
- 部分 analyzer 標記為 "Deprecated" 但仍在使用 (Functions 11, 14, 22)

### M7. API CORS 和 Rate Limit 問題

**問題描述：**
- CORS 在 `cors.py` 和 `handlers.py` 中重複定義
- Rate limit 使用記憶體內 dict (`request_times`)，無清理機制，長時間運行會 memory leak
- 僅開發環境 origins (localhost:3000/8080/5173)，缺少生產域名

---

## 3. 輕度問題清單 (Minor Issues)

### m1. Magic Numbers 和 Magic Strings
- 函數 ID 硬編碼 (e.g., `if function_id in [25, 26]`)
- `lap == 99` 表示 "find fastest lap" 的魔術值
- `system_functions = {"18", "19", "20", "21", ...}` 硬編碼集合

### m2. 建構配置散亂
- 3 個 .spec 檔案 (`F1T_GUI.spec`, `F1T_GUI_clean.spec`, `F1T_GUI_fixed.spec`)
- 建構腳本 (`一鍵建構EXE.bat`, `build_exe_gui.py`)
- 無 CI/CD pipeline 定義

### m3. 文件分散
- 37 篇技術文件在 `docs/` 但無索引
- 26 篇 .md 報告散落在根目錄
- 部分文件已過時 (引用已移除的功能)

### m4. 版本管理
- 版本號在 `config/version.py` 中定義
- 但 API、GUI、CLI 的版本號可能不同步
- 無 changelog 格式規範

---

## 4. 重構計畫 - 分階段執行

### Phase 0: 基礎穩定 (Foundation Stabilization)

> 目標：建立安全網，不改變任何功能邏輯

#### P0.1 - 建立依賴管理
```
優先級: CRITICAL
風險: LOW
```

**任務：**
1. 從現有 `.venv` 匯出 `requirements.txt`
2. 建立 `requirements-dev.txt` (pytest, flake8, black 等)
3. 建立 `pyproject.toml` (長期目標)
4. 驗證 PyInstaller 構建仍然正常

**產出：**
- `requirements.txt`
- `requirements-dev.txt`

---

#### P0.2 - 根目錄大掃除
```
優先級: HIGH
風險: LOW
```

**任務：**
1. 建立目錄結構：
   ```
   scripts/
   ├── diagnostics/     ← 移入 check_*, temp_*, debug_*
   ├── batch/           ← 移入 batch_*
   ├── generators/      ← 移入 generate_*
   ├── validators/      ← 移入 validate_*, verify_*
   └── one-off/         ← 移入其他一次性腳本
   
   docs/
   ├── reports/         ← 移入根目錄 .md 報告
   ├── architecture/    ← 架構文件
   └── api/             ← API 文件
   ```
2. 更新 .gitignore 規則
3. 根目錄僅保留 5 個核心入口：
   - `f1t_gui_main.py` (GUI)
   - `f1_analysis_modular_main.py` (CLI)
   - `refactored_api.py` (API)  
   - `APIserver.py` (API 啟動)
   - `strategy_simulator_main.py` (模擬器)

**產出：**
- 根目錄從 141 個 .py 降為 < 10 個
- 所有腳本按功能分類到子目錄

---

#### P0.3 - 建立基礎測試框架
```
優先級: CRITICAL
風險: LOW
```

**任務：**
1. 建立 `conftest.py` 基礎配置 (fixtures, marks)
2. 建立 `tests/conftest.py` 共用 fixtures
3. 標準化測試目錄結構：
   ```
   tests/
   ├── conftest.py          ← pytest 配置
   ├── unit/
   │   ├── cli/             ← CLI 單元測試
   │   ├── gui/             ← GUI 單元測試
   │   └── api/             ← API 單元測試
   ├── integration/
   │   ├── api/             ← API 整合測試
   │   └── e2e/             ← 端到端測試
   ├── manual/              ← 手動測試 (保留)
   └── legacy/              ← 移入舊的診斷腳本 (710 個)
   ```
4. 為 API 端點寫 smoke test (5-10 個基礎測試)
5. 為 function_mapper 寫 regression test (至少覆蓋 10 個核心功能)
6. 配置 `pytest.ini` 或 `pyproject.toml [tool.pytest]` 設定

**產出：**
- 可執行的 `pytest tests/unit/ -v` 命令
- 至少 30 個真正的 pytest 測試
- CI-ready 的測試基礎設施

---

### Phase 1: CLI 引擎重構 (CLI Engine Refactoring)

> 目標：拆解 God Class，建立可擴展的分析器註冊系統

#### P1.1 - Analyzer Registry 系統
```
優先級: CRITICAL
風險: HIGH (核心重構)
前置: P0.3 (需要測試保護)
```

**現狀：**
```python
# function_mapper.py - 8,021 行 God Class
class F1AnalysisFunctionMapper:
    function_mapping = {
        1: self._execute_rain_intensity_analysis,
        2: self._execute_track_path_analysis,
        ...  # 143 個條目
    }
    
    def _execute_rain_intensity_analysis(self, **kwargs):
        try:
            print(f"[START] Rain analysis...")
            # 5-20 行實際邏輯
            return {"success": True, ...}
        except Exception as e:
            return {"success": False, "message": str(e)}
    # ... 重複 148 次
```

**目標架構：**
```python
# CLI_modules/cli/core/analyzer_registry.py - NEW
class AnalyzerRegistry:
    """分析功能註冊系統 - 替代 God Class"""
    _analyzers: Dict[int, Type[BaseAnalyzer]] = {}
    
    @classmethod
    def register(cls, function_id: int, name: str = "", category: str = ""):
        """裝飾器：註冊分析功能"""
        def decorator(analyzer_cls):
            cls._analyzers[function_id] = AnalyzerEntry(
                function_id=function_id,
                name=name,
                category=category,
                analyzer_class=analyzer_cls
            )
            return analyzer_cls
        return decorator
    
    @classmethod
    def execute(cls, function_id: int, **kwargs) -> dict:
        """執行指定功能"""
        entry = cls._analyzers.get(function_id)
        if not entry:
            return {"success": False, "message": f"Unknown function: {function_id}"}
        analyzer = entry.analyzer_class(**kwargs)
        return analyzer.execute()

# CLI_modules/cli/core/base_analyzer.py - NEW
class BaseAnalyzer(ABC):
    """所有分析功能的基類"""
    
    def __init__(self, data_loader, **kwargs):
        self.data_loader = data_loader
        self.year = kwargs.get('year')
        self.race = kwargs.get('race')
        self.session = kwargs.get('session')
    
    @abstractmethod
    def execute(self) -> dict:
        """執行分析，返回標準結果"""
        pass
    
    def _standard_result(self, success: bool, data=None, message="", **extra):
        """統一結果格式"""
        return {
            "success": success,
            "data": data,
            "message": message,
            "function_id": str(self.function_id),
            "cache_used": extra.get("cache_used", False),
            **extra
        }

# CLI_modules/cli/analyzer/weather/rain_analyzer.py - 改造
@AnalyzerRegistry.register(function_id=1, name="Rain Intensity", category="weather")
class RainIntensityAnalyzer(BaseAnalyzer):
    def execute(self) -> dict:
        # 直接實現，不需要 try/except boilerplate（由 Registry 統一處理）
        session_info = self._get_session_info()
        rain_data = self._analyze_rain_intensity()
        return self._standard_result(True, data=rain_data)
```

**執行步驟：**
1. 建立 `BaseAnalyzer` ABC 和 `AnalyzerRegistry`
2. 為 Registry 加入統一的 try/except、快取檢查、日誌記錄 (decorator)
3. 逐步遷移：先遷移 5 個最簡單的功能作為驗證
4. 每遷移一組功能，跑回歸測試
5. function_mapper.py 做 thin wrapper 轉發到 Registry（保持向後相容）
6. 最終：function_mapper.py 只剩下 Registry 呼叫

**分組遷移計畫：**

| 批次 | 功能範圍 | 數量 | 難度 | 說明 |
|------|---------|------|------|------|
| Batch 1 | F1-F5 | 5 | 低 | 基礎分析（降雨/賽道/進站） |
| Batch 2 | F6-F15 | 10 | 中 | 遙測分析（需要 driver 參數） |
| Batch 3 | F16-F30 | 15 | 中 | 進階分析 |
| Batch 4 | F31-F54 | 24 | 中 | 擴展功能 |
| Batch 5 | F55-F91 | 37 | 高 | ML 預測 + 超車分析 |
| Batch 6 | F92-F143 | 52 | 中 | 專業功能 |
| 清理 | Placeholders | ~40 | 低 | 移除或正式標記為未實現 |

---

#### P1.2 - 統一資料載入器
```
優先級: HIGH
風險: MEDIUM
前置: P1.1 開始後
```

**任務：**
1. 以 `CompatibleF1DataLoader` 為唯一正式版本
2. 將 `F1DataLoader` 做 thin wrapper 轉發 (deprecation warning)
3. 移除 `SimpleDataLoader`
4. 統一 `F1AnalysisInstance` 和 `CompatibleF1AnalysisInstance` 為一個
5. `BaseAnalyzer` 只接受統一的 data_loader

**產出：**
- 從 3 個 data loader 降為 1 個
- 從 2 個 analysis instance 降為 1 個

---

#### P1.3 - 統一快取層
```
優先級: MEDIUM
風險: LOW
前置: P1.1
```

**任務：**
1. 在 `CLI_modules/cli/cache/` 建立 `cache_manager.py`
2. 定義統一快取介面：
   ```python
   class CacheManager:
       def get(self, cache_key: str) -> Optional[dict]
       def set(self, cache_key: str, data: dict, ttl: int = 3600)
       def invalidate(self, pattern: str)
       def generate_key(self, function_id, **params) -> str
   ```
3. 整合 API 的 `cache_service_v2.py` 和 CLI 的 pickle 快取
4. 加入快取失效策略（TTL + 手動清除）
5. 在 `BaseAnalyzer` 中提供 `@cached` 裝飾器

---

#### P1.4 - 清理 Dead Code
```
優先級: MEDIUM
風險: LOW
```

**任務：**
1. 移除 function_mapper 中所有 placeholder 方法 (約 40 個)
2. 清理已禁用的 CLI worker 程式碼
3. 移除 API 的 deprecated `/analyze` endpoint 中的註解程式碼
4. 對標記 "Deprecated" 的功能 (F11, F14, F22) 做正式處理

---

### Phase 2: GUI 架構精煉 (GUI Architecture Refinement)

> 目標：減少 boilerplate，提昇 i18n 覆蓋率，強化模組一致性

#### P2.1 - i18n 達到 100% 覆蓋
```
優先級: HIGH
風險: LOW
前置: 無
```

**現狀：**
- 187 / 368 個 GUI .py 檔案未 import `tr()` (50.8%)
- 翻譯字典在 `gui_i18n.py` 單一巨大 dict 中

**任務：**
1. 掃描所有 GUI 檔案，列出未使用 `tr()` 的位置
2. 逐模組加入 `tr()` 包裹
3. 將翻譯字典遷移到外部 JSON 檔案：
   ```
   core/i18n/
   ├── zh.json    ← 繁體中文
   ├── en.json    ← 英文
   └── ja.json    ← 日文
   ```
4. `gui_i18n.py` 改為從 JSON 載入翻譯
5. 建立翻譯 coverage 檢查工具

**產出：**
- i18n 覆蓋率 50% → 100%
- 翻譯維護成本大幅降低

---

#### P2.2 - GUI 模組 Boilerplate 精簡
```
優先級: MEDIUM
風險: MEDIUM
前置: P0.3 (測試保護)
```

**任務：**
1. 分析 30+ 個模組的共同 boilerplate 程式碼
2. 在 `UniversalDataLoader` 基類中擴展：
   - 自動 JSON 搜尋 + 載入（已有，確認一致性）
   - 自動錯誤信號發送
   - 自動 progress tracking
3. 在 `UniversalAnalysisMDI` 基類中擴展：
   - 標準化 `_on_data_loaded()` → chart update 流程
   - 標準化 parameter update 信號處理
   - 標準化視窗標題 i18n 更新
4. 建立 Module Generator 腳本：
   ```powershell
   python scripts/create_analysis_module.py --name "new_analysis" --category "race"
   # 自動生成 data_loader.py + mdi.py + chart_widget.py 骨架
   ```

---

#### P2.3 - Windows Manager 合併
```
優先級: LOW
風險: MEDIUM
前置: P0.3
```

**任務：**
1. 審查 181 個 manager 檔案的功能
2. 合併功能重疊的 manager：
   - 5 個 `f1tv_auth_*.py` → 1 個 `f1tv_auth_manager.py`
   - MDI 相關 (closer/visibility/finder) → 1 個 `mdi_operations.py`
   - Window 狀態 (maximizer/restorer/cascader) → 1 個 `window_layout.py`
3. 目標：181 個 → ~60-80 個有意義的 manager 檔案

---

### Phase 3: API 和基礎設施 (API & Infrastructure)

> 目標：生產化 API，建立 CI/CD

#### P3.1 - API 修復
```
優先級: MEDIUM
風險: LOW
```

**任務：**
1. 修復 CORS 重複定義 (cors.py vs handlers.py)
2. 修復 Rate Limit memory leak (加入定時清理 / 改用 sliding window)
3. 加入生產域名到 CORS allowed origins
4. 移除 `analysis.py` 中 ~600 行的 debug print
5. 清理 deprecated `/analyze` endpoint 的註解程式碼

---

#### P3.2 - 日誌系統標準化
```
優先級: MEDIUM
風險: LOW
```

**任務：**
1. 全面使用 `logging` 替代 `print()`
2. 定義日誌等級標準：
   - `DEBUG`: 資料結構、變數值
   - `INFO`: 功能執行開始/結束、快取命中
   - `WARNING`: 資料品質問題、效能降低
   - `ERROR`: 可恢復的錯誤
   - `CRITICAL`: 系統無法運作
3. function_mapper.py 的 200+ 個 print 改為 logger
4. analyzer 中的 print 改為 logger

---

#### P3.3 - CI/CD Pipeline
```
優先級: LOW
風險: LOW
前置: P0.1, P0.3
```

**任務：**
1. 建立 `.github/workflows/test.yml` (GitHub Actions)
2. 配置 lint (flake8/ruff) + format check (black)
3. 配置 pytest 自動執行
4. 配置 PyInstaller 構建驗證
5. 建立 PR template 和 branch protection

---

### Phase 4: 長期演進 (Long-term Evolution)

> 目標：為持續成長做好準備

#### P4.1 - Plugin 架構
```
優先級: LOW
前置: P1.1 (AnalyzerRegistry)
```

將 `@AnalyzerRegistry.register()` 擴展為可插拔系統：
- 自動掃描 `CLI_modules/cli/analyzer/**/` 目錄
- 每個 analyzer 自我註冊
- 第三方可新增 analyzer 而不需修改核心

#### P4.2 - 測試生態完善
```
前置: P0.3
```

- 建立 GUI 測試框架 (pytest-qt)
- API 測試改用 `httpx.AsyncClient`
- 目標：所有核心功能 > 80% 覆蓋率

#### P4.3 - 效能監控
- APM 整合 (Prometheus metrics export)
- GUI 啟動時間 profiling
- 記憶體用量追蹤 dashboard

---

## 5. 執行優先順序矩陣

```
影響 ↑
      │
HIGH  │  P0.1(依賴)    P1.1(Registry)
      │  P0.3(測試)    P1.2(DataLoader)
      │  P2.1(i18n)    
      │
MED   │  P0.2(清理)    P1.3(快取)
      │  P3.2(日誌)    P2.2(Boilerplate)
      │  P3.1(API)     P1.4(Dead Code)
      │
LOW   │  P2.3(Manager) P3.3(CI/CD)
      │  m1-m4         P4.1-P4.3
      │
      └────────────────────────────────→ 風險
           LOW         MEDIUM       HIGH
```

### 建議執行順序

```
Week 1-2:  P0.1 → P0.2 → P0.3 (基礎穩定，零風險)
Week 3-4:  P2.1 (i18n 覆蓋率，可平行)
Week 3-6:  P1.1 Batch 1-2 (Registry 試點)
Week 5-6:  P1.2 + P1.4 (DataLoader 統一 + Dead Code)
Week 7-8:  P1.1 Batch 3-4 (Registry 持續遷移)
Week 8-9:  P3.1 + P3.2 (API 修復 + 日誌標準化)
Week 9-12: P1.1 Batch 5-6 (Registry 完成)
Week 10+:  P1.3, P2.2, P2.3, P3.3 (依需求優先級)
```

---

## 6. 風險評估

| 風險 | 概率 | 影響 | 緩解策略 |
|------|------|------|---------|
| P1.1 Registry 遷移破壞現有功能 | 高 | 高 | 保留 function_mapper 做 thin wrapper，漸進式遷移 |
| 根目錄清理破壞其他腳本的相對路徑引用 | 中 | 低 | 在舊位置留 import redirect |
| i18n 批量修改引入顯示錯誤 | 中 | 低 | 逐模組修改+手動驗證 |
| 測試框架選擇不當浪費時間 | 低 | 中 | 直接用 pytest，不引入額外框架 |
| DataLoader 統一破壞特定功能 | 中 | 高 | 先寫對應測試，確認行為一致後再移除舊版 |

---

## 7. 重構原則

1. **漸進式遷移**：絕不做大爆炸重構。每次改動都要保持系統可運行。
2. **測試先行**：重構前先為目標區域寫測試，確認行為不變。
3. **向後相容**：舊介面保留 deprecation wrapper，給下游足夠遷移時間。
4. **One Pull = One Concern**：每個 PR 只做一件事，方便 code review 和 rollback。
5. **驗證驅動**：每完成一個階段，跑 GUI 啟動測試 + API smoke test + CLI 功能測試。

---

## 附錄 A: 程式碼度量快照 (2026-04-04)

```
function_mapper.py:     8,021 行 | 148 個 _execute_ 方法 | 394 KB
f1t_gui_main.py:        2,527 行 | 300+ 個代理方法
refactored_api.py:        109 行 | (路由已分散到 api/routers/)
GUI 模組:               368 檔案 | 201,002 行
CLI 分析器:               80 檔案 |  55,241 行
Windows managers:        181 檔案 |  22,637 行
API 層:                   20 檔案 |   7,106 行
核心基礎設施:             15 檔案 |   8,442 行
根目錄散落腳本:          141 檔案
測試檔案:                710 檔案 | (< 50 個是 pytest 格式)
i18n 未覆蓋 GUI:         187 / 368 (50.8%)
依賴管理檔案:             0 個 (無 requirements.txt)
```
