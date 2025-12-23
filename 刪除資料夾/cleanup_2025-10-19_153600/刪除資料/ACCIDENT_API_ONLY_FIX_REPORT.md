# 事故分析模組 API-ONLY 模式修復報告

**修復日期**: 2025-10-11  
**模組**: `modules/gui/accident_analysis/accident_data_manager.py`  
**問題來源**: 錯誤日誌 `f1_gui_2025-10-11.log` 第 541-557 行

---

## 📋 問題摘要

### 問題 1: Qt 導入錯誤
```
ERROR | [ERROR] [ACCIDENT_API] 啟動 API 請求失敗: name 'Qt' is not defined
```

**根本原因**: `PyQt5.QtCore` 導入語句缺少 `Qt` 類別

### 問題 2: 違反 API-ONLY 政策
```
INFO | [ACCIDENT_API DEBUG] 啟動本地 JSON/CLI 後備流程
INFO | [ACCIDENT_API DEBUG] ✅ 找到現有
```

**根本原因**: API 請求失敗後自動回退到本地 JSON，違反 API-ONLY 強制政策

---

## ✅ 修復內容

### 修復 1: 添加 Qt 導入

**檔案**: `accident_data_manager.py` 第 14 行

```python
# 修復前
from PyQt5.QtCore import QObject, QThread, pyqtSignal

# 修復後
from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal
```

**影響範圍**: 第 307 行的 `Qt.QueuedConnection` 調用

---

### 修復 2: 啟用 API-ONLY 政策

#### 2.1 修改預設後備政策

**檔案**: `accident_data_manager.py` 第 579-599 行

```python
def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
    """
    ⚠️ API-ONLY 模式: 預設禁用本地 JSON 後備
    
    根據 API-ONLY 政策，GUI 模組必須強制使用 API 獲取數據。
    只有明確設置環境變數才允許本地 JSON 後備（僅用於開發/調試）。
    """
    env_value = os.getenv("F1T_ALLOW_ACCIDENT_JSON_FALLBACK")
    if env_value is not None:
        normalized = str(env_value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True, f"環境變數 F1T_ALLOW_ACCIDENT_JSON_FALLBACK={env_value}"
        return False, f"環境變數 F1T_ALLOW_ACCIDENT_JSON_FALLBACK={env_value}"
    # ⚠️ API-ONLY 模式: 預設禁用本地 JSON 後備
    return False, "API-ONLY 模式（預設政策）"
```

**變更**:
- ❌ 移除: `return True, "預設允許本地 JSON 後備"`
- ✅ 新增: `return False, "API-ONLY 模式（預設政策）"`

#### 2.2 修改 API 請求啟動失敗處理

**檔案**: `accident_data_manager.py` 第 275-287 行

```python
# 修復前
try:
    self._start_api_request()
    return True
except Exception as exc:
    self._is_loading = False
    self._error(f"啟動 API 請求失敗: {exc}")
    self.status_changed.emit("API 載入啟動失敗，嘗試使用本地資料")
    self._fallback_to_local(str(exc))  # ❌ 無條件回退
    return False

# 修復後
try:
    self._start_api_request()
    return True
except Exception as exc:
    self._is_loading = False
    self._error(f"啟動 API 請求失敗: {exc}")
    if self._allow_local_fallback:  # ✅ 檢查政策
        self.status_changed.emit("API 載入啟動失敗，嘗試使用本地資料")
        self._fallback_to_local(str(exc))
        return True
    else:
        self.status_changed.emit("API 載入啟動失敗且未啟用本地 JSON 後備")
        self.error_occurred.emit(f"API 請求失敗: {exc}")
        return False
```

#### 2.3 修改 API 錯誤回調處理

**檔案**: `accident_data_manager.py` 第 344-352 行

```python
# 修復前
def _on_api_error(self, message: str) -> None:
    self._error(f"API 請求失敗: {message}")
    self._is_loading = False
    self.status_changed.emit("API 請求失敗，改用本地資料")
    self._fallback_to_local(message)  # ❌ 無條件回退

# 修復後
def _on_api_error(self, message: str) -> None:
    self._error(f"API 請求失敗: {message}")
    self._is_loading = False
    if self._allow_local_fallback:  # ✅ 檢查政策
        self.status_changed.emit("API 請求失敗，改用本地資料")
        self._fallback_to_local(message)
    else:
        self.status_changed.emit("API 請求失敗且未啟用本地 JSON 後備")
        self.error_occurred.emit(f"API 請求失敗: {message}")
```

#### 2.4 修改 API 成功回調錯誤處理

**檔案**: `accident_data_manager.py` 第 318-342 行

```python
# 修復前
except Exception as exc:
    self._error(f"處理 API 數據失敗: {exc}")
    self._is_loading = False
    self.status_changed.emit("API 資料錯誤，改用本地資料")
    self._fallback_to_local(str(exc))  # ❌ 無條件回退

# 修復後
except Exception as exc:
    self._error(f"處理 API 數據失敗: {exc}")
    self._is_loading = False
    if self._allow_local_fallback:  # ✅ 檢查政策
        self.status_changed.emit("API 資料錯誤，改用本地資料")
        self._fallback_to_local(str(exc))
    else:
        self.status_changed.emit("API 資料錯誤且未啟用本地 JSON 後備")
        self.error_occurred.emit(f"API 數據處理失敗: {exc}")
```

---

## 🎯 修復驗證

### 驗證 1: Qt 導入正確
```python
from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager, Qt
# ✅ 成功導入，無 NameError
```

### 驗證 2: API-ONLY 政策啟用
```python
manager = AccidentDataManager()
assert manager._allow_local_fallback == False
assert "API-ONLY" in manager._fallback_policy_reason
# ✅ 預設禁用本地 JSON 後備
```

### 驗證 3: 錯誤處理正確
```python
manager._on_api_error("測試錯誤")
# ✅ 發出 error_occurred 信號
# ❌ 不會自動載入本地 JSON
```

---

## 📊 影響範圍

### 變更的檔案
- ✅ `modules/gui/accident_analysis/accident_data_manager.py` (4 處修改)

### 變更的方法
1. ✅ `_resolve_local_fallback_policy()` - 修改預設返回值
2. ✅ `_request_analysis()` - 添加後備政策檢查
3. ✅ `_on_api_error()` - 添加後備政策檢查
4. ✅ `_on_api_success()` - 添加後備政策檢查

### 不受影響的功能
- ✅ API 正常流程（成功獲取數據）
- ✅ 環境變數覆蓋功能（`F1T_ALLOW_ACCIDENT_JSON_FALLBACK=1`）
- ✅ 數據處理和信號發送邏輯

---

## 🔧 開發者指南

### 如何啟用本地 JSON 後備（僅開發用）

**方式 1: PowerShell 臨時環境變數**
```powershell
$env:F1T_ALLOW_ACCIDENT_JSON_FALLBACK = "1"
python f1t_gui_main.py
```

**方式 2: 永久環境變數**
```powershell
[System.Environment]::SetEnvironmentVariable(
    "F1T_ALLOW_ACCIDENT_JSON_FALLBACK", 
    "1", 
    [System.EnvironmentVariableTarget]::User
)
```

**方式 3: 在代碼中設置（不推薦）**
```python
import os
os.environ['F1T_ALLOW_ACCIDENT_JSON_FALLBACK'] = '1'
```

---

## ✅ 合規性確認

### 符合 API-ONLY 政策 ✅
- ✅ GUI 模組預設只能通過 API 獲取數據
- ✅ 禁止自動啟動 CLI 進程或執行緒
- ✅ 禁止自動回退到本地 JSON
- ✅ 只允許通過環境變數明確啟用後備（開發用）

### 符合開發準則 ✅
- ✅ 遵循 `UniversalDataLoader` 架構
- ✅ 使用 `pyqtSignal` 進行異步通信
- ✅ 正確處理錯誤和異常
- ✅ 提供詳細的調試日誌

---

## 📝 後續建議

### 短期
1. ✅ 測試 GUI 啟動無 `Qt` 錯誤
2. ✅ 驗證 API 失敗時不會自動載入 JSON
3. ⚠️  通知用戶更新錯誤處理邏輯

### 中期
1. 🔄 統一所有 GUI 模組的 API-ONLY 政策
2. 🔄 添加單元測試覆蓋錯誤處理路徑
3. 🔄 改進 API 錯誤訊息的用戶友好性

### 長期
1. 📋 移除所有本地 JSON 後備代碼（純 API 架構）
2. 📋 實現 API 重試機制和斷線恢復
3. 📋 添加 API 請求快取層減少網路依賴

---

## 🎉 修復完成

**狀態**: ✅ 完全修復  
**測試**: ✅ 已驗證  
**部署**: 🚀 可立即部署  

**修復人員**: GitHub Copilot  
**審查狀態**: 待用戶確認
