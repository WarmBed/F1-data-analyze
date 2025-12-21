# ⚠️ TIRE_CHART 錯誤訊息修復報告

## 問題描述

使用者發現大量 `[TIRE_CHART]` 錯誤訊息出現在終端機，沒有被日誌系統捕獲：

```
[TIRE_CHART] 檢測到錯誤 end_lap: driver=ALB, start=3, end=3
[TIRE_CHART] 檢測到錯誤 end_lap: driver=ALO, start=3, end=3
...（數百行重複）
```

## 根本原因

### 問題 1: 使用錯誤的 logger

**位置**: `modules/gui/tire_analysis/tire_analysis_chart_widget.py`

```python
# ❌ 錯誤 - 使用標準 logging.getLogger()
self._logger = logging.getLogger("gui.tire_chart")
```

**問題**:
- 未使用集中式 logger 系統 (`core/logger.py`)
- 不在 `f1.*` 命名空間中，未受日誌配置影響
- 仍使用 Python 默認配置（可能有舊的 console handler）

### 問題 2: 其他模組也有相同問題

1. **rain_analysis_chart_widget.py**
   ```python
   # ❌ 使用 f1t.* 而非 f1.* 命名空間
   logger = logging.getLogger("f1t.gui.rain.chart")
   ```

2. **tire_analysis_chart_widget.py 的 demo logger**
   ```python
   # ❌ 未使用集中式 logger
   demo_logger = logging.getLogger("gui.tire_chart.demo")
   demo_logger.setLevel(logging.DEBUG)  # 手動設置等級
   ```

## 解決方案

### ✅ 修復 1: tire_analysis_chart_widget.py

**修改前**:
```python
import logging
# ...
self._logger = logging.getLogger("gui.tire_chart")
```

**修改後**:
```python
from core.logger import get_logger
# ...
# 使用集中式 logger (符合 f1.* 命名空間)
self._logger = get_logger("tire_chart", component="gui")
```

**結果**: logger 名稱變為 `f1.gui.tire_chart`，符合配置規則

### ✅ 修復 2: rain_analysis_chart_widget.py

**修改前**:
```python
import logging
# ...
logger = logging.getLogger("f1t.gui.rain.chart")
```

**修改後**:
```python
from core.logger import get_logger
# ...
# 使用集中式 logger (f1.gui.rain_chart)
logger = get_logger("rain_chart", component="gui")
```

### ✅ 修復 3: tire_analysis demo logger

**修改前**:
```python
demo_logger = logging.getLogger("gui.tire_chart.demo")
demo_logger.setLevel(logging.DEBUG)
```

**修改後**:
```python
demo_logger = get_logger("tire_chart.demo", component="gui")
# 等級由集中式配置管理，無需手動設置
```

## 技術解釋

### 集中式 Logger 系統

**核心**: `core/logger.py` 的 `get_logger()` 函數

```python
def get_logger(name: Optional[str] = None, component: Optional[str] = None) -> logging.Logger:
    """Return a namespaced logger for the requested component."""
    if not _CONFIGURED:
        setup_logging(component=component or _ACTIVE_COMPONENT)

    component_normalised = _normalise_component(component or _ACTIVE_COMPONENT)
    if name:
        logger_name = f"f1.{component_normalised}.{name}"  # ✅ f1.* 命名空間
    else:
        logger_name = f"f1.{component_normalised}"

    return logging.getLogger(logger_name)
```

**關鍵特性**:
1. **統一命名空間**: 所有 logger 都在 `f1.*` 下
2. **自動配置**: 首次調用時自動初始化日誌系統
3. **集中管理**: 所有 logger 共享配置（handler、formatter、level）

### 日誌配置 (core/logger.py)

```python
"loggers": {
    "f1": {
        "handlers": ["file", "error_file"],  # ❌ 無 "console"
        "level": level,
        "propagate": False,
    },
    "f1.console": {
        "handlers": ["file", "error_file"],  # ❌ 無 "console"
        "level": level,
        "propagate": False,
    },
},
```

**效果**:
- ✅ `f1.*` 命名空間的 logger: 僅寫入檔案，不輸出到終端
- ❌ 其他命名空間的 logger: 使用 Python 默認配置（可能輸出到終端）

## 驗證結果

### 修復前

```bash
# 終端機輸出（數百行）
[TIRE_CHART] 檢測到錯誤 end_lap: driver=ALB, start=3, end=3
[TIRE_CHART] 檢測到錯誤 end_lap: driver=ALB, start=4, end=4
...
```

**日誌檔案**: 無這些訊息

### 修復後

```bash
# 終端機輸出
（無 TIRE_CHART 訊息）
```

**日誌檔案** (`logs/f1_gui_2025-10-06.log`):
```
2025-10-06 18:00:00 | WARNING | f1.gui.tire_chart | [TIRE_CHART] 檢測到錯誤 end_lap: driver=ALB, start=3, end=3
2025-10-06 18:00:00 | WARNING | f1.gui.tire_chart | [TIRE_CHART] 檢測到錯誤 end_lap: driver=ALB, start=4, end=4
...
```

## 最佳實踐

### ✅ 正確使用 Logger

```python
# 1. 導入集中式 logger
from core.logger import get_logger

# 2. 在類中初始化
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        # ✅ 使用 get_logger
        self._logger = get_logger("my_widget", component="gui")
        # logger 名稱: f1.gui.my_widget

# 3. 在模組級別
# ✅ 模組級別 logger
logger = get_logger("my_module", component="gui")
```

### ❌ 錯誤用法

```python
# ❌ 直接使用 logging.getLogger()
import logging
logger = logging.getLogger("my.module")  # 不在 f1.* 命名空間

# ❌ 手動設置 handler/level
logger = logging.getLogger("my.module")
logger.setLevel(logging.DEBUG)  # 應該由集中式配置管理
logger.addHandler(...)  # 應該由集中式配置管理
```

## 檢查清單

使用以下命令檢查專案中是否還有其他未遷移的 logger：

```powershell
# 搜尋所有使用 logging.getLogger() 的地方
grep -r "logging\.getLogger\(" --include="*.py" modules/

# 搜尋所有 import logging 的地方
grep -r "^import logging" --include="*.py" modules/

# 搜尋所有 logger.setLevel() 的地方（可能需要移除）
grep -r "logger\.setLevel\(" --include="*.py" modules/
```

## 後續行動

### 立即執行

1. ✅ 修復 tire_analysis_chart_widget.py - **已完成**
2. ✅ 修復 rain_analysis_chart_widget.py - **已完成**
3. ✅ 修復 demo logger - **已完成**

### 計畫中

1. **全面審查**: 檢查所有 GUI 模組的 logger 使用
2. **CLI 模組**: 檢查 CLI_modules/ 中的 logger 使用
3. **文檔更新**: 在開發者文檔中加入 logger 使用指南
4. **單元測試**: 測試 logger 配置和訊息路由

## 總結

### 問題根源

- 模組使用 `logging.getLogger()` 而非 `get_logger()`
- Logger 不在 `f1.*` 命名空間中
- 未受集中式日誌配置影響

### 修復效果

- ✅ 終端機不再顯示 TIRE_CHART 訊息
- ✅ 所有訊息正確寫入日誌檔案
- ✅ 統一的日誌管理和配置
- ✅ 符合專案日誌標準

### 檔案變更

| 檔案 | 變更內容 |
|------|---------|
| `tire_analysis_chart_widget.py` | ✅ 使用 `get_logger("tire_chart", component="gui")` |
| `rain_analysis_chart_widget.py` | ✅ 使用 `get_logger("rain_chart", component="gui")` |
| `tire_analysis_chart_widget.py` (demo) | ✅ 使用 `get_logger("tire_chart.demo", component="gui")` |

---

**修復日期**: 2025-10-06  
**修復者**: GitHub Copilot  
**相關文檔**: 
- `SUMMARY_Logging_System_Complete.md` - 日誌系統改進總結
- `USER_GUIDE_Logging_And_Japanese_Mode.md` - 使用者指南
