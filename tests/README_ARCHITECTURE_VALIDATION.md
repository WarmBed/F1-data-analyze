# F1T 系統架構驗證測試

## 概述

本目錄包含 F1T 專案的系統架構驗證測試套件，用於確保系統符合「反幻覺編碼五原則」及所有關鍵開發準則。

## 測試文件

### 主要測試套件
- **test_system_architecture_validation.py** - 完整的架構驗證測試套件
  - 17 個測試用例
  - 6 個測試類別
  - 涵蓋架構、API-ONLY 模式、基礎類別、國際化、文檔等方面

### 驗證報告
- **SYSTEM_ARCHITECTURE_VALIDATION_REPORT.md** - 詳細的驗證報告
  - 測試結果總結
  - 關鍵發現
  - 改進建議
  - 後續行動計畫

## 快速開始

### 執行完整驗證測試

```bash
# 在專案根目錄執行
python tests/test_system_architecture_validation.py
```

### 執行特定測試類別

```bash
# 執行 API-ONLY 模式測試
python -m unittest tests.test_system_architecture_validation.TestAPIOnlyMode

# 執行通用基礎類別測試
python -m unittest tests.test_system_architecture_validation.TestUniversalBaseClasses

# 執行文檔完整性測試
python -m unittest tests.test_system_architecture_validation.TestDocumentation
```

### 使用 pytest 執行（如已安裝）

```bash
pytest tests/test_system_architecture_validation.py -v
```

## 測試類別說明

### 1. TestSystemArchitecture
**目的**: 驗證系統核心架構完整性

**測試項目**:
- 核心目錄結構存在
- 關鍵檔案存在
- Core logger 系統可導入

### 2. TestAPIOnlyMode
**目的**: 驗證 API-ONLY 模式正確實施

**測試項目**:
- UniversalDataLoader 包含 API-ONLY 註解
- CliAnalysisWorker 已被禁用
- refactored_api.py 存在且包含 FastAPI

### 3. TestUniversalBaseClasses
**目的**: 驗證通用基礎類別架構

**測試項目**:
- UniversalDataLoader 類別存在
- UniversalChartWidget 類別存在
- UniversalDataLoader 包含必要的信號

### 4. TestInternationalization
**目的**: 驗證國際化支援

**測試項目**:
- 模組使用 tr() 函數
- 無 emoji 原則已記錄

### 5. TestDocumentation
**目的**: 驗證文檔完整性

**測試項目**:
- copilot-instructions.md 存在
- 五大原則已記錄
- API-ONLY 模式已記錄
- tasks/ 目錄存在且包含任務追蹤文件

### 6. TestCLIFunctionMapper
**目的**: 驗證 CLI 功能映射器

**測試項目**:
- function_mapper.py 存在
- F1AnalysisFunctionMapper 類別存在

## 測試結果解讀

### 成功輸出範例

```
======================================================================
F1T 系統架構驗證測試
測試反幻覺編碼五原則和系統完整性
======================================================================

test_core_directories_exist ... ok
test_core_logger_import ... ok
test_key_files_exist ... ok
...

----------------------------------------------------------------------
Ran 17 tests in 0.027s

OK

======================================================================
✅ 所有測試通過！系統架構符合開發原則。
======================================================================
```

### 失敗輸出處理

如果測試失敗，會顯示詳細的錯誤訊息：

```
FAIL: test_universal_data_loader_exists
----------------------------------------------------------------------
AssertionError: Required file missing: modules/gui/base/universal_data_loader_base.py
```

**處理步驟**:
1. 檢查錯誤訊息中指出的缺失檔案或目錄
2. 確認是否因為專案結構變更導致
3. 更新測試用例以反映新的專案結構
4. 或修復專案結構以符合原有設計

## 持續整合

### 在 CI/CD 中使用

**GitHub Actions 範例**:

```yaml
name: Architecture Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Run Architecture Validation
      run: python tests/test_system_architecture_validation.py
```

### 在開發流程中使用

建議在以下時機執行驗證測試：

1. **每次提交前** - 確保變更不破壞架構
2. **Pull Request 前** - 驗證符合開發原則
3. **定期審查** - 每週或每月執行一次完整驗證
4. **重大重構後** - 確認架構完整性

## 擴展測試套件

### 添加新的測試用例

```python
class TestNewFeature(unittest.TestCase):
    """新功能驗證測試"""
    
    def test_new_feature_exists(self):
        """測試：新功能存在"""
        feature_file = PROJECT_ROOT / 'path/to/new_feature.py'
        self.assertTrue(feature_file.exists())
```

### 添加到測試套件

在 `run_validation_suite()` 函數中添加：

```python
def run_validation_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # ... 現有測試類別 ...
    suite.addTests(loader.loadTestsFromTestCase(TestNewFeature))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()
```

## 故障排除

### 常見問題

#### 1. 導入錯誤 (ModuleNotFoundError)

**問題**: 測試無法導入專案模組

**解決方案**:
```bash
# 確保在專案根目錄執行
cd /path/to/F1-data-analyze
python tests/test_system_architecture_validation.py
```

#### 2. 路徑錯誤

**問題**: 測試找不到檔案或目錄

**解決方案**:
- 確認專案結構沒有變更
- 檢查 PROJECT_ROOT 變數設置正確
- 更新測試中的路徑以反映新結構

#### 3. 依賴套件缺失

**問題**: 部分測試因缺少依賴而失敗

**解決方案**:
```bash
# 安裝開發依賴
pip install -r requirements.txt  # 如有此檔案
```

**注意**: 架構驗證測試設計為不依賴 PyQt5 等 GUI 套件，應該可以在純 Python 環境中執行。

## 維護指南

### 定期審查清單

- [ ] 每月執行一次完整驗證測試
- [ ] 檢查是否有新的架構組件需要添加測試
- [ ] 更新 SYSTEM_ARCHITECTURE_VALIDATION_REPORT.md
- [ ] 審查改進建議並實施

### 測試更新觸發條件

以下情況應該更新驗證測試：

1. **添加新的基礎類別** - 添加對應的測試用例
2. **修改架構原則** - 更新相關測試和文檔
3. **重構目錄結構** - 更新目錄和檔案檢查
4. **新增開發規範** - 添加驗證測試

## 相關資源

- **開發指南**: `.github/copilot-instructions.md`
- **任務追蹤**: `tasks/` 目錄
- **API 文檔**: `api/` 目錄
- **GUI 模組**: `modules/gui/` 目錄
- **CLI 模組**: `CLI_modules/cli/` 目錄

## 貢獻

如果您發現測試套件可以改進的地方：

1. 在 `tasks/` 目錄創建新的任務文檔
2. 描述需要添加的測試用例
3. 提交 Pull Request
4. 確保所有測試通過

## 授權

本測試套件屬於 F1T 專案的一部分，遵循專案的授權條款。

---

**最後更新**: 2026-01-05  
**維護者**: F1T Development Team
