# Speed 模組 vs RPM 模組 - 深度逐行對比
## 完整代碼級別分析（不省略任何細節）

**對比日期**：2025-10-16  
**對比範圍**：前 400 行代碼  
**對比原則**：遵循反幻覺編碼四原則，每行代碼都驗證  

---

## 📋 檔案頭部對比 (Line 1-25)

### Line 1: Shebang

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 1 | `#!/usr/bin/env python3` | `#!/usr/bin/env python3` | ✅ 完全相同 |

### Line 2-6: 檔案說明

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 2 | `"""` | `"""` | ✅ 完全相同 |
| 3 | `F1T 速度分析 MDI 模組` | `F1T RPM分析 MDI 模組` | ⚠️ 僅模組名稱不同 |
| 4 | `基於進站分析模組的成功架構設計` | `基於速度分析模組的成功架構設計` | ⚠️ 參考來源不同 |
| 5 | `支援雙車手速度對比的 GUI 模組，使用新版模組更新機制` | `支援雙車手RPM對比的 GUI 模組，使用新版模組更新機制` | ⚠️ 僅功能名稱不同 |
| 6 | `"""` | `"""` | ✅ 完全相同 |

### Line 8-13: 標準庫導入

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 8 | `import sys` | `import sys` | ✅ 完全相同 |
| 9 | `import os` | `import os` | ✅ 完全相同 |
| 10 | `import json` | `import json` | ✅ 完全相同 |
| 11 | `import datetime` | `import datetime` | ✅ 完全相同 |
| 12 | `import traceback` | `import traceback` | ✅ 完全相同 |
| 13 | `from typing import Dict, List, Any, Optional` | `from typing import Dict, List, Any, Optional` | ✅ 完全相同 |

### Line 14-20: PyQt5 導入

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 14-20 | 完整 PyQt5 導入列表 | 完整 PyQt5 導入列表 | ✅ 完全相同 |

**詳細對比**：
```python
# Speed & RPM 都相同
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
```

### Line 22-25: 自定義模組導入

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 22 | (空行) | (空行) | ✅ 相同 |
| 23 | `# 導入國際化模組` | `# 導入分析模組介面` | ⚠️ 註解不同 |
| 24 | `from core.gui_i18n import tr` | `from modules.gui.interfaces.analysis_module import IAnalysisModule` | ❌ **順序不同** |
| 25 | (空行) | `from core.gui_i18n import tr` | ❌ **順序不同** |
| 26 | `# 導入分析模組介面` | (空行) | ❌ **順序不同** |
| 27 | `from modules.gui.interfaces.analysis_module import IAnalysisModule` | - | ❌ **順序不同** |

**問題 1**：Speed 和 RPM 的導入順序不同
- Speed: 先導入 tr，後導入 IAnalysisModule
- RPM: 先導入 IAnalysisModule，後導入 tr
- **建議**：統一為 RPM 的順序（介面先，國際化後）

---

## 📋 DataManager 類別定義對比 (Line 29-42)

### Line 29-34: 類別定義和文檔字串

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 29 | `class SpeedDataManager(QObject):` | `class RPMDataManager(QObject):` | ⚠️ 僅類別名稱不同 |
| 30 | `    """速度數據管理器 - 負責JSON緩存和CLI備援"""` | `    """RPM數據管理器 - 負責JSON緩存和CLI備援"""` | ⚠️ 僅功能名稱不同 |
| 31 | (空行) | (空行) | ✅ 完全相同 |
| 32 | `    # 信號定義` | `    # 信號定義` | ✅ 完全相同 |

### Line 33-36: 信號定義

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 33 | `    data_loaded = pyqtSignal(dict)` | `    data_loaded = pyqtSignal(dict)` | ✅ 完全相同 |
| 34 | `    error_occurred = pyqtSignal(str)` | `    error_occurred = pyqtSignal(str)` | ✅ 完全相同 |
| 35 | `    loading_progress = pyqtSignal(int)` | `    loading_progress = pyqtSignal(int)` | ✅ 完全相同 |
| 36 | `    status_changed = pyqtSignal(str)` | `    status_changed = pyqtSignal(str)` | ✅ 完全相同 |

### Line 38-45: __init__ 方法

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 38 | `    def __init__(self, parent=None):` | `    def __init__(self, parent=None):` | ✅ 完全相同 |
| 39 | `        super().__init__(parent)` | `        super().__init__(parent)` | ✅ 完全相同 |
| 40 | `        self.current_year = None` | `        self.current_year = None` | ✅ 完全相同 |
| 41 | `        self.current_race = None` | `        self.current_race = None` | ✅ 完全相同 |
| 42 | `        self.current_session = None` | `        self.current_session = None` | ✅ 完全相同 |
| 43 | `        self.loading = False` | `        self.loading = False` | ✅ 完全相同 |
| 44 | `        self._is_loading = False` | `        self._is_loading = False` | ✅ 完全相同 |
| 45 | (Speed 結束) | `        self.module_ref = None` | ❌ **RPM 多一個屬性** |

**問題 2**：RPM 有 `self.module_ref = None`，Speed 沒有
- RPM 使用 `module_ref` 來引用父模組
- Speed 沒有這個屬性
- **建議**：Speed 應該添加此屬性以保持一致

---

## 📋 load_*_data() 方法對比 (Line 47-113)

### Line 47-50: 方法簽名

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 47 | `    def load_speed_data(self, year: str, race: str, session: str,` | `    def load_rpm_data(self, year: str, race: str, session: str,` | ⚠️ 僅方法名稱不同 |
| 48 | `                       driver1: str = "VER", driver2: str = "VER",` | `                      driver1: str = "VER", driver2: str = "VER",` | ⚠️ 縮排差 1 空格 |
| 49 | `                       lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:` | `                      lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:` | ⚠️ 縮排差 1 空格 |
| 50 | `        """載入速度對比數據"""` | `        """載入RPM對比數據"""` | ⚠️ 僅功能名稱不同 |

**問題 3**：縮排不一致
- Speed: 24 個空格
- RPM: 23 個空格
- **建議**：統一縮排為 23 或 24 個空格

### Line 51-62: 方法開頭（日誌和狀態檢查）

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 51 | `        try:` | `        try:` | ✅ 完全相同 |
| 52 | `            print(f"[SPEED_MDI_DATA] ========== 載入速度數據 ==========")` | `            print(f"[RPM_MDI_DATA] ========== 載入RPM數據 ==========")` | ⚠️ 僅日誌前綴不同 |
| 53 | `            print(f"[SPEED_MDI_DATA] 參數: {year} {race} {session}")` | `            print(f"[RPM_MDI_DATA] 參數: {year} {race} {session}")` | ⚠️ 僅日誌前綴不同 |
| 54 | `            print(f"[SPEED_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")` | `            print(f"[RPM_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")` | ⚠️ 僅日誌前綴不同 |
| 55 | (空行) | (空行) | ✅ 完全相同 |
| 56 | `            if self._is_loading:` | `            if self._is_loading:` | ✅ 完全相同 |
| 57 | `                print(f"[SPEED_MDI_DATA] ⚠️ 數據載入中，忽略新請求")` | `                print(f"[RPM_MDI_DATA] ⚠️ 數據載入中，忽略新請求")` | ⚠️ 僅日誌前綴不同 |
| 58 | `                self.error_occurred.emit("載入器正忙，請稍後再試")` | `                self.error_occurred.emit("載入器正忙，請稍後再試")` | ✅ 完全相同 |
| 59 | `                return False` | `                return False` | ✅ 完全相同 |
| 60 | (空行) | (空行) | ✅ 完全相同 |
| 61 | `            self._is_loading = True` | `            self._is_loading = True` | ✅ 完全相同 |
| 62 | `            self.loading_progress.emit(0)` | `            self.loading_progress.emit(0)` | ✅ 完全相同 |
| 63 | `            self.status_changed.emit("開始載入速度數據...")` | `            self.status_changed.emit("開始載入RPM數據...")` | ⚠️ 僅狀態訊息不同 |

### Line 65-67: 保存上下文

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 65 | `            # 儲存當前賽事上下文，供遙測資料及CLI命令使用` | `            # 保存當前上下文，以供遙測資料檢查` | ⚠️ **註解不同** |
| 66 | `            self.current_year = str(year)` | `            self.current_year = str(year)` | ✅ 完全相同 |
| 67 | `            self.current_race = race` | `            self.current_race = race` | ✅ 完全相同 |
| 68 | `            self.current_session = session` | `            self.current_session = session` | ✅ 完全相同 |

**問題 4**：註解用詞不一致
- Speed: "儲存當前賽事上下文，供遙測資料及CLI命令使用"
- RPM: "保存當前上下文，以供遙測資料檢查"
- **建議**：統一為更簡潔的 RPM 版本

### Line 70-75: 最速圈檢查

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 70 | `            # 檢查最速圈選項並自動載入遙測分析` | `            # 檢查最速圈選項並自動載入遙測分析` | ✅ 完全相同 |
| 71 | `            if is_fastest or lap1 == "fastest" or lap2 == "fastest":` | `            if is_fastest or lap1 == "fastest" or lap2 == "fastest":` | ✅ 完全相同 |
| 72 | `                print(f"🔄 [SPEED_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")` | `                print(f"🔄 [RPM_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")` | ⚠️ 僅日誌前綴不同 |
| 73 | `                self._check_and_load_telemetry_if_needed()` | `                self._check_and_load_telemetry_if_needed()` | ✅ 完全相同 |
| 74 | (空行) | (空行) | ✅ 完全相同 |
| 75 | `                # 解析最速圈參數為實際圈數` | `                # 解析最速圈參數為實際圈數` | ✅ 完全相同 |
| 76 | `                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)` | `                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)` | ✅ 完全相同 |
| 77 | `                print(f"🔢 [SPEED_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")` | `                print(f"🔢 [RPM_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")` | ⚠️ 僅日誌前綴不同 |

### Line 79-83: 創建 DataLoader

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 79 | `            print(f"[SPEED_MDI_DATA] 🔗 創建 SpeedAnalysisDataLoader...")` | `            print(f"[RPM_MDI_DATA] 🔗 創建 RPMAnalysisDataLoader...")` | ⚠️ 僅名稱不同 |
| 80 | (空行) | (空行) | ✅ 完全相同 |
| 81 | `            # 使用現有的速度分析數據載入器` | `            # 使用現有的RPM分析數據載入器` | ⚠️ 僅名稱不同 |
| 82 | `            from .speed_analysis_data_loader import SpeedAnalysisDataLoader` | `            from .rpm_analysis_data_loader import RPMAnalysisDataLoader` | ⚠️ 僅模組名稱不同 |
| 83 | (空行) | (空行) | ✅ 完全相同 |
| 84 | `            print(f"[SPEED_MDI_DATA] 🚀 調用 load_speed_data...")` | `            print(f"[RPM_MDI_DATA] 🚀 調用 load_rpm_data...")` | ⚠️ 僅方法名稱不同 |

### Line 86-91: 實例化 DataLoader（關鍵差異）

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 86 | `            # ✅ 修復：創建數據載入器並保存為實例變數（防止垃圾回收）` | `            # 創建數據載入器並保存為實例變量防止垃圾回收` | ⚠️ **註解不同** |
| 87 | `            self._speed_loader = SpeedAnalysisDataLoader()` | `            self.rpm_loader = RPMAnalysisDataLoader()` | ❌ **變數名不同** |
| 88 | `            self._speed_loader.data_loaded.connect(self._on_data_loaded)` | `            self.rpm_loader.data_loaded.connect(self._on_data_loaded)` | ❌ **變數名不同** |
| 89 | `            self._speed_loader.load_error.connect(self._on_load_error)` | `            self.rpm_loader.load_error.connect(self._on_load_error)` | ❌ **變數名不同** |
| 90 | `            self._speed_loader.status_changed.connect(self.status_changed.emit)` | `            self.rpm_loader.status_changed.connect(self.status_changed.emit)` | ❌ **變數名不同** |
| 91 | `            self._speed_loader.load_progress.connect(self.loading_progress.emit)` | `            self.rpm_loader.load_progress.connect(self.loading_progress.emit)` | ❌ **變數名不同** |

**問題 5**：loader 變數命名不一致
- Speed: `self._speed_loader` （私有變數，前綴 `_`）
- RPM: `self.rpm_loader` （公開變數，無前綴 `_`）
- **建議**：統一為公開變數（無 `_` 前綴）或私有變數（有 `_` 前綴）

### Line 93-103: 調用 load 方法

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 93 | `            # 開始載入數據` | `            # 開始載入數據` | ✅ 完全相同 |
| 94 | `            success = self._speed_loader.load_speed_data(` | `            success = self.rpm_loader.load_rpm_data(` | ❌ 變數名和方法名不同 |
| 95-101 | 參數列表（完全相同結構） | 參數列表（完全相同結構） | ✅ 參數結構相同 |
| 102 | `                is_fastest_lap=is_fastest  # 修正：使用傳入的is_fastest參數` | `                is_fastest_lap=is_fastest` | ⚠️ Speed 多一個註解 |
| 103 | `            )` | `            )` | ✅ 完全相同 |

### Line 105-108: 設置 loader 給 chart widget

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 105 | `            # 將loader設置給chart widget以供直接更新` | `            # 將loader設置給chart widget以供直接更新` | ✅ 完全相同 |
| 106 | `            if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:` | `            if hasattr(self, 'rpm_chart_widget') and self.rpm_chart_widget:` | ⚠️ 僅屬性名稱不同 |
| 107 | `                self.speed_chart_widget.speed_loader = self._speed_loader` | `                self.rpm_chart_widget.rpm_loader = self.rpm_loader` | ⚠️ 僅屬性名稱不同 |
| 108 | `                print(f"[SPEED_MDI] ✅ 已將loader設置給chart widget")` | `                print(f"[RPM_MDI] ✅ 已將loader設置給chart widget")` | ⚠️ 僅日誌前綴不同 |

### Line 110-118: 返回結果（關鍵差異）

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 110 | `            return success` | `            if success:` | ❌ **邏輯完全不同** |
| 111 | (Speed 空行) | `                print(f"[RPM_MDI_DATA] ✅ RPM數據載入請求提交成功")` | ❌ **RPM 有額外日誌** |
| 112 | (Speed 異常處理開始) | `                self.loading_progress.emit(50)` | ❌ **RPM 有進度更新** |
| 113 | - | `                return True` | ❌ **RPM 有明確返回** |
| 114 | - | `            else:` | ❌ **RPM 有錯誤處理** |
| 115 | - | `                print(f"[RPM_MDI_DATA] ❌ RPM數據載入請求失敗")` | ❌ **RPM 有錯誤日誌** |
| 116 | - | `                self._is_loading = False` | ❌ **RPM 重置狀態** |
| 117 | - | `                self.error_occurred.emit("RPM數據載入請求失敗")` | ❌ **RPM 發送錯誤信號** |
| 118 | - | `                return False` | ❌ **RPM 有明確返回** |

**問題 6**：返回邏輯完全不同
- Speed: 直接返回 `success`，沒有額外處理
- RPM: 檢查 `success`，根據結果執行不同邏輯：
  - 成功：記錄日誌、更新進度到 50%、返回 True
  - 失敗：記錄日誌、重置狀態、發送錯誤信號、返回 False
- **這是重大差異！**
- **建議**：Speed 應該採用 RPM 的完整錯誤處理邏輯

### Line 112-118: 異常處理

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 112 | `        except Exception as e:` | `        except Exception as e:` | ✅ 完全相同 |
| 113 | `            print(f"[ERROR] [SPEED_MDI] 速度數據載入失敗: {e}")` | `            print(f"[ERROR] [RPM_MDI_DATA] 載入RPM數據時發生錯誤: {e}")` | ⚠️ 日誌格式不同 |
| 114 | `            self.error_occurred.emit(f"載入失敗: {str(e)}")` | `            self._is_loading = False` | ❌ **順序不同** |
| 115 | `            self._is_loading = False` | `            self.error_occurred.emit(f"載入RPM數據失敗: {str(e)}")` | ❌ **順序不同** |
| 116 | `            return False` | `            return False` | ✅ 完全相同 |

**問題 7**：異常處理順序不同
- Speed: 先發送錯誤信號，後重置狀態
- RPM: 先重置狀態，後發送錯誤信號
- **建議**：統一為 RPM 的順序（先重置狀態，再發送信號）

---

## 📋 _check_and_load_telemetry_if_needed() 方法對比 (Line 118-195)

### Speed 的實現 (Line 118-128)

```python
def _check_and_load_telemetry_if_needed(self):
    """檢查本地遙測分析數據（API-ONLY 模式：不自動創建視窗）"""
    try:
        print(f"� [SPEED_MDI] [API-ONLY] 檢查本地遙測分析數據...")
        
        # API-ONLY 模式：僅檢查本地數據，不自動創建視窗
        print(f"💡 [SPEED_MDI] 提示：如需遙測分析，請手動開啟遙測分析模組")
        print(f"💡 [SPEED_MDI] 或使用 API 獲取遙測數據")
        return False
            
    except Exception as e:
        print(f"❌ [SPEED_MDI] 檢查遙測數據時發生錯誤: {e}")
        return False
```

### RPM 的實現 (Line 157-195)

```python
def _check_and_load_telemetry_if_needed(self):
    """檢查遙測分析數據（最速圈用）"""
    try:
        print(f"[RPM_MDI_DATA] 🔍 檢查遙測分析數據可用性...")

        module_ref = getattr(self, "module_ref", None)
        if module_ref:
            return module_ref._check_and_load_telemetry_if_needed(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )

        telemetry_patterns = [
            f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
            f"telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
            f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}.json"
        ]

        search_dirs = ["json", "json_exports", "cache"]
        for directory in search_dirs:
            if os.path.exists(directory):
                for pattern in telemetry_patterns:
                    file_path = os.path.join(directory, pattern)
                    if os.path.exists(file_path):
                        print(f"📁 [RPM_MDI_DATA] 找到現有遙測檔案: {file_path}")
                        return True

        print("⚠️ [RPM_MDI_DATA] API-ONLY 模式下未找到遙測檔案，請透過主視窗遙測模組或 REST API 取得資料")
        return False

    except Exception as e:
        print(f"❌ [RPM_MDI_DATA] 檢查遙測數據時發生錯誤: {e}")
        return False
```

**問題 8**：_check_and_load_telemetry_if_needed() 實現完全不同
- Speed: 極簡版本，只列印提示訊息，直接返回 False（11 行）
- RPM: 完整版本，包含：
  - 檢查 module_ref 並委派
  - 搜尋 3 種遙測檔案模式
  - 在 3 個目錄中搜尋
  - 找到後返回 True
  - 共 39 行代碼
- **這是重大差異！**
- **建議**：Speed 應該實現與 RPM 相同的完整邏輯

---

## 📋 _get_fastest_lap_number() 方法對比 (Line 130-240)

### Speed 和 RPM 的實現對比

| 方面 | Speed (Line 130-199) | RPM (Line 197-270) | 差異 |
|------|---------------------|-------------------|------|
| **方法簽名** | `def _get_fastest_lap_number(self, driver: str) -> int:` | `def _get_fastest_lap_number(self, driver: str) -> int:` | ✅ 完全相同 |
| **文檔字串** | `"""從遙測分析數據獲取指定車手的最速圈數"""` | `"""從遙測分析數據獲取指定車手的最速圈數"""` | ✅ 完全相同 |
| **搜尋模式** | 3 個模式 | 3 個模式 | ✅ 完全相同 |
| **搜尋目錄** | ["json", "json_exports", "cache"] | ["json", "json_exports", "cache"] | ✅ 完全相同 |
| **檔案搜尋邏輯** | 雙層 for 迴圈 + break | 雙層 for 迴圈 + break | ✅ 完全相同 |
| **JSON 解析** | 3 種格式 | 3 種格式 | ✅ 完全相同 |
| **預設返回值** | 1 | 1 | ✅ 完全相同 |
| **日誌前綴** | `[SPEED_MDI]` | `[RPM_MDI]` | ⚠️ 僅前綴不同 |
| **總行數** | 70 行 | 74 行 | ⚠️ RPM 多 4 行（空行） |

**結論**：此方法邏輯完全相同，只有日誌前綴不同。✅

---

## 📋 _resolve_lap_numbers() 方法對比 (Line 201-220)

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 全部 | 邏輯完全相同 | 邏輯完全相同 | ✅ 完全相同 |

**詳細對比**：
- 方法簽名：✅ 相同
- 處理 lap1：✅ 相同
- 處理 lap2：✅ 相同
- 異常處理：✅ 相同
- 唯一差異：日誌前綴 `[SPEED_MDI]` vs `[RPM_MDI]`

---

## 📋 _on_data_loaded() 和 _on_load_error() 方法對比

### Speed 的 _on_data_loaded() (Line 222-240)

```python
def _on_data_loaded(self, data: dict):
    """處理數據載入完成"""
    try:
        print(f"[SPEED_MDI_DATA] ========== 數據載入完成回調 ==========")
        print(f"[SPEED_MDI_DATA] 📦 接收到數據類型: {type(data)}")
        print(f"[SPEED_MDI_DATA] 📦 接收到數據鍵值: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict) and 'speed_data' in data:
            speed_data = data['speed_data']
            print(f"[SPEED_MDI_DATA] 📊 speed_data 鍵值: {list(speed_data.keys())}")
            print(f"[SPEED_MDI_DATA] 📊 distance 點數: {len(speed_data.get('distance', []))}")
            print(f"[SPEED_MDI_DATA] 📊 driver1_speed 點數: {len(speed_data.get('driver1_speed', []))}")
            print(f"[SPEED_MDI_DATA] 📊 driver2_speed 點數: {len(speed_data.get('driver2_speed', []))}")
        self._is_loading = False
        print(f"[SPEED_MDI_DATA] 🚀 即將發送 data_loaded 信號...")
        print(f"[SPEED_MDI_DATA] 📡 信號接收者數量: {self.receivers(self.data_loaded)}")
        self.data_loaded.emit(data)
        print(f"[SPEED_MDI_DATA] ✅ data_loaded 信號已發送")
    except Exception as e:
        print(f"[ERROR] [SPEED_MDI_DATA] 數據處理失敗: {e}")
        import traceback
        traceback.print_exc()
        self.error_occurred.emit(f"數據處理失敗: {str(e)}")
```

### RPM 的 _on_data_loaded() (Line 143-155)

```python
def _on_data_loaded(self, data):
    """數據載入完成回調"""
    try:
        print(f"[RPM_MDI_DATA] ✅ RPM數據載入完成")
        self._is_loading = False
        self.loading_progress.emit(100)
        self.status_changed.emit("RPM數據載入完成")
        self.data_loaded.emit(data)
    except Exception as e:
        print(f"[ERROR] [RPM_MDI_DATA] 處理載入完成回調時發生錯誤: {e}")
        self._on_load_error(f"數據處理失敗: {str(e)}")
```

**問題 9**：_on_data_loaded() 實現複雜度差異巨大
- Speed: 22 行代碼，包含大量診斷日誌
- RPM: 13 行代碼，簡潔明確
- Speed 特有：
  - 詳細的數據類型檢查
  - speed_data 內容檢查
  - 信號接收者數量檢查
  - 逐步日誌記錄
- RPM 特有：
  - 更新進度到 100%
  - 更新狀態訊息
- **建議**：Speed 應該簡化為 RPM 的簡潔版本，移除診斷代碼

### _on_load_error() 對比

| 方面 | Speed (Line 242-246) | RPM (Line 147-152) | 差異 |
|------|---------------------|-------------------|------|
| **方法簽名** | `_on_load_error(self, error_message: str)` | `_on_load_error(self, error_msg)` | ⚠️ 參數名不同 |
| **文檔字串** | `"""處理載入錯誤"""` | `"""數據載入錯誤回調"""` | ⚠️ 描述不同 |
| **日誌** | 1 行 | 1 行 | ✅ 相同 |
| **狀態重置** | `self._is_loading = False` | `self._is_loading = False` | ✅ 相同 |
| **進度更新** | ❌ 無 | ✅ `self.loading_progress.emit(0)` | ❌ RPM 多一項 |
| **狀態訊息** | ❌ 無 | ✅ `self.status_changed.emit(f"載入失敗: {error_msg}")` | ❌ RPM 多一項 |
| **錯誤信號** | ✅ 有 | ✅ 有 | ✅ 相同 |

**問題 10**：_on_load_error() 的完整性不同
- RPM 更完整：包含進度重置和狀態訊息更新
- Speed 較簡單：只有基本錯誤處理
- **建議**：Speed 應該添加進度和狀態訊息更新

---

## 📋 cleanup() 方法對比 (Line 256-307 vs 275-320)

### Speed 的 cleanup() (Line 256-307)

```python
def cleanup(self):
    """
    清理 SpeedDataManager 資源
    
    修復記憶體洩漏：清理 DataLoader 的 API Worker 執行緒
    """
    try:
        print(f"[SPEEDDATAMANAGER] 🧹 開始清理資源...")
        
        # 1. 清理 DataLoader 及其 QThread
        if hasattr(self, '_speed_loader') and self._speed_loader:
            try:
                # 調用 loader 的 cleanup() 方法（清理 API worker 執行緒）
                if hasattr(self._speed_loader, 'cleanup'):
                    self._speed_loader.cleanup()
                    print(f"[SPEEDDATAMANAGER] ✅ 已清理 loader 執行緒")
                
                # 斷開信號連接
                try:
                    self._speed_loader.data_loaded.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_error.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.status_changed.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_progress.disconnect()
                except Exception:
                    pass
                
                # 標記為待刪除
                self._speed_loader.deleteLater()
                self._speed_loader = None
                
            except Exception as e:
                print(f"[ERROR] [SPEEDDATAMANAGER] 清理 loader 失敗: {e}")
        
        # 2. 清理內部狀態
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self._is_loading = False
        
        print(f"[SPEEDDATAMANAGER] ✅ 資源清理完成")
        
    except Exception as e:
        print(f"[ERROR] [SPEEDDATAMANAGER] cleanup() 失敗: {e}")
        import traceback
        traceback.print_exc()
```

### RPM 的 cleanup() (Line 275-320)

```python
def cleanup(self):
    """
    清理 RPMDataManager 資源
    
    修復記憶體洩漏：清理 TelemetryDataLoader 的 API Worker 執行緒
    """
    try:
        print(f"[RPMDATAMANAGER] 🧹 開始清理資源...")
        
        # 1. 清理 TelemetryDataLoader 及其 QThread
        if hasattr(self, '_speed_loader') and self._speed_loader:
            try:
                # 調用 loader 的 cleanup() 方法（清理 API worker 執行緒）
                if hasattr(self._speed_loader, 'cleanup'):
                    self._speed_loader.cleanup()
                    print(f"[RPMDATAMANAGER] ✅ 已清理 loader 執行緒")
                
                # 斷開信號連接
                try:
                    self._speed_loader.data_loaded.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_error.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.status_changed.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_progress.disconnect()
                except Exception:
                    pass
                
                # 標記為待刪除
                self._speed_loader.deleteLater()
                self._speed_loader = None
                
            except Exception as e:
                print(f"[ERROR] [RPMDATAMANAGER] 清理 loader 失敗: {e}")
        
        # 2. 清理內部狀態
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self._is_loading = False
        
        print(f"[RPMDATAMANAGER] ✅ 資源清理完成")
        
    except Exception as e:
        print(f"[ERROR] [RPMDATAMANAGER] cleanup() 失敗: {e}")
        import traceback
        traceback.print_exc()
```

**問題 11**：RPM cleanup() 有錯誤 - 檢查的是 `_speed_loader` 而不是 `rpm_loader`
- RPM Line 285: `if hasattr(self, '_speed_loader') and self._speed_loader:`
- 這是複製貼上的錯誤！
- RPM 應該檢查 `self.rpm_loader`，而不是 `self._speed_loader`
- **這是 RPM 的 BUG！**
- **建議**：修復 RPM 的 cleanup() 方法

**除了上述錯誤外，兩個 cleanup() 方法結構完全相同**：
- ✅ 都清理 loader
- ✅ 都調用 loader.cleanup()
- ✅ 都斷開 4 個信號
- ✅ 都調用 deleteLater()
- ✅ 都清理內部狀態
- ✅ 都有異常處理和 traceback

---

## 📋 AnalysisModule 類別定義對比 (Line 310-360)

### Line 310-320: 類別定義和信號

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 310 | `class SpeedAnalysisModule(IAnalysisModule):` | `class RPMAnalysisModule(IAnalysisModule):` | ⚠️ 僅類別名稱不同 |
| 311 | `    """速度分析主模組"""` | `    """RPM分析主模組"""` | ⚠️ 僅描述不同 |
| 312 | (空行) | (空行) | ✅ 完全相同 |
| 313 | `    # 信號定義` | `    # 信號定義 - 與速度模組保持一致` | ⚠️ RPM 多一個註解 |
| 314 | `    module_error = pyqtSignal(str)` | `    module_error = pyqtSignal(str)` | ✅ 完全相同 |
| 315 | `    parameters_updated = pyqtSignal(dict)` | `    parameters_updated = pyqtSignal(dict)` | ✅ 完全相同 |

### Line 317-330: __init__ 方法開頭

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 317 | `    def __init__(self, parent=None):` | `    def __init__(self, parent=None):` | ✅ 完全相同 |
| 318 | `        super().__init__(parent)` | `        super().__init__(parent)` | ✅ 完全相同 |
| 319 | (空行) | (空行) | ✅ 完全相同 |
| 320 | `        # ✅ 設置分析類型（用於批次更新識別）- 統一命名與其他模組一致` | `        # ✅ 設置分析類型（用於批次更新識別）` | ⚠️ Speed 註解更詳細 |
| 321 | `        self.analysis_type = 'speed'` | `        self.analysis_type = 'rpm'` | ⚠️ 僅類型名稱不同 |
| 322-330 | 參數和組件初始化 | 參數和組件初始化 | ✅ 完全相同 |

### Line 331-345: 組件初始化

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 331-345 | 完全相同的屬性列表 | 完全相同的屬性列表 | ✅ 完全相同 |

**詳細列表**：
- `self.current_year = "2025"`
- `self.current_race = "Japan"`
- `self.current_session = "R"`
- `self.parameter_provider = None`
- `self.driver1 = "VER"`
- `self.driver2 = "VER"`
- `self.lap1 = 1`
- `self.lap2 = 1`
- `self.data_manager = None`
- `self.speed_chart_widget = None` (Speed) vs `self.rpm_chart_widget = None` (RPM)
- `self.main_widget = None`
- `self.parent_window = None`
- `self._initialized = False`

---

## 📋 initialize_module() 方法對比 (Line 347-400)

### Line 347-360: 方法開頭和數據管理器創建

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 347 | `    def initialize_module(self, parent_widget=None, **kwargs) -> bool:` | `    def initialize_module(self, parent_widget=None, **kwargs) -> bool:` | ✅ 完全相同 |
| 348 | `        """初始化模組 - 實現抽象方法"""` | `        """初始化模組 - 實現抽象方法"""` | ✅ 完全相同 |
| 349 | `        try:` | `        try:` | ✅ 完全相同 |
| 350 | `            print(f"[SPEED_MDI] 初始化速度分析模組")` | `            print(f"[RPM_MDI] 初始化RPM分析模組")` | ⚠️ 僅日誌不同 |
| 351 | (空行) | (空行) | ✅ 完全相同 |
| 352 | `            # 創建數據管理器` | `            # 創建數據管理器` | ✅ 完全相同 |
| 353 | `            self.data_manager = SpeedDataManager()` | `            self.data_manager = RPMDataManager()` | ⚠️ 僅類別名不同 |
| 354 | ❌ **缺少** | `            self.data_manager.module_ref = self` | ❌ **Speed 缺少此行** |
| 355 | `            self.data_manager.data_loaded.connect(self._update_chart)` | `            self.data_manager.data_loaded.connect(self._update_chart)` | ✅ 完全相同 |
| 356 | `            self.data_manager.error_occurred.connect(self._handle_error)` | `            self.data_manager.error_occurred.connect(self._handle_error)` | ✅ 完全相同 |

**問題 12**：Speed 缺少 module_ref 設置
- RPM Line 354: `self.data_manager.module_ref = self`
- Speed 沒有這行代碼
- 這導致 DataManager 無法訪問父模組
- **建議**：Speed 應該添加此行

### Line 358-370: 圖表組件創建

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 358 | `            # 創建速度圖表組件` | `            # 創建RPM圖表組件` | ⚠️ 僅描述不同 |
| 359 | `            from .speed_analysis_chart_widget import SpeedAnalysisChartWidget` | `            from .rpm_analysis_chart_widget import RPMAnalysisChartWidget` | ⚠️ 僅類別名不同 |
| 360 | `            self.speed_chart_widget = SpeedAnalysisChartWidget()` | `            self.rpm_chart_widget = RPMAnalysisChartWidget()` | ⚠️ 僅屬性名不同 |
| 361 | (空行) | (空行) | ✅ 完全相同 |
| 362 | `            # 連接圈數變更信號` | `            # 連接圈數變更信號` | ✅ 完全相同 |
| 363 | `            self.speed_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)` | `            self.rpm_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)` | ⚠️ 僅屬性名不同 |
| 364 | (空行) | (空行) | ✅ 完全相同 |
| 365 | `            # 設置初始圈數` | `            # 設置初始圈數` | ✅ 完全相同 |
| 366 | `            self.speed_chart_widget.set_lap_numbers(self.lap1, self.lap2)` | `            self.rpm_chart_widget.set_lap_numbers(self.lap1, self.lap2)` | ⚠️ 僅屬性名不同 |
| 367 | (空行) | (空行) | ✅ 完全相同 |
| 368 | `            # 設置主界面` | `            # 設置主界面` | ✅ 完全相同 |
| 369 | `            self._setup_ui()` | `            self._setup_ui()` | ✅ 完全相同 |

### Line 371-400: 註冊到分析模組管理器

| 行號 | Speed | RPM | 差異 |
|------|-------|-----|------|
| 371-385 | 註冊邏輯 | 註冊邏輯 | ✅ 結構完全相同 |

**詳細對比**：
- 導入管理器：✅ 相同
- 創建 module_id：✅ 相同格式（`f"speed_analysis_{id(self)}"` vs `f"rpm_analysis_{id(self)}"`)
- 註冊模組：✅ 相同
- 註冊圖表組件：✅ 相同
- 保存引用：✅ 相同
- 異常處理：✅ 相同

---

## 🎯 總結：前 400 行的主要差異

### ✅ 完全相同的部分（~70%）

1. ✅ 標準庫導入（100% 相同）
2. ✅ PyQt5 導入（100% 相同）
3. ✅ 信號定義（100% 相同）
4. ✅ 大部分方法結構（相同邏輯）
5. ✅ 初始化流程（相同順序）
6. ✅ 圖表組件創建（相同模式）
7. ✅ 分析模組管理器註冊（相同流程）

### ⚠️ 命名差異（~20%）

8. ⚠️ 類別名稱（Speed* vs RPM*）
9. ⚠️ 方法名稱（*speed* vs *rpm*）
10. ⚠️ 屬性名稱（speed_* vs rpm_*）
11. ⚠️ 日誌前綴（SPEED vs RPM）

### ❌ 重大差異（~10%）

**差異 1：導入順序不同**
- Speed: tr → IAnalysisModule
- RPM: IAnalysisModule → tr
- **建議**：統一為 RPM 順序

**差異 2：DataManager 缺少 module_ref**
- Speed: ❌ 無 `self.module_ref`
- RPM: ✅ 有 `self.module_ref = None`
- **建議**：Speed 添加此屬性

**差異 3：loader 變數命名不一致**
- Speed: `self._speed_loader` (私有)
- RPM: `self.rpm_loader` (公開)
- **建議**：統一為公開變數

**差異 4：load_*_data() 返回邏輯不同**
- Speed: 直接返回 success
- RPM: 檢查 success 並執行額外處理
  - 成功：更新進度、記錄日誌
  - 失敗：重置狀態、發送錯誤
- **建議**：Speed 採用 RPM 的完整邏輯

**差異 5：_check_and_load_telemetry_if_needed() 實現不同**
- Speed: 極簡版（11 行）
- RPM: 完整版（39 行）
  - 檢查 module_ref
  - 搜尋 3 種檔案模式
  - 在 3 個目錄中搜尋
- **建議**：Speed 實現完整版

**差異 6：_on_data_loaded() 複雜度不同**
- Speed: 22 行（大量診斷日誌）
- RPM: 13 行（簡潔明確）
- **建議**：Speed 簡化為 RPM 版本

**差異 7：_on_load_error() 完整性不同**
- Speed: 缺少進度和狀態更新
- RPM: 完整的錯誤處理
- **建議**：Speed 添加進度和狀態更新

**差異 8：initialize_module() 缺少 module_ref 設置**
- Speed: ❌ 無 `self.data_manager.module_ref = self`
- RPM: ✅ 有此行
- **建議**：Speed 添加此行

**差異 9：RPM cleanup() 有 BUG**
- RPM 檢查的是 `_speed_loader`，應該是 `rpm_loader`
- **建議**：修復 RPM 的 cleanup() 方法

---

## 📊 修復優先級

### 🔴 最高優先級（必須立即修復）

1. ✅ Speed 添加 `self.module_ref = None` (Line 45)
2. ✅ Speed 在 initialize_module() 添加 `self.data_manager.module_ref = self` (Line 354)
3. ✅ Speed 實現完整的 _check_and_load_telemetry_if_needed() (Line 118-128)
4. ✅ Speed 採用 RPM 的 load_*_data() 返回邏輯 (Line 110-118)
5. ⚠️ RPM 修復 cleanup() 中的 `_speed_loader` 錯誤 (Line 285)

### 🟡 高優先級（盡快修復）

6. ✅ 統一 loader 變數命名（私有 vs 公開）
7. ✅ Speed 簡化 _on_data_loaded() 為 RPM 版本
8. ✅ Speed 添加 _on_load_error() 的進度和狀態更新

### 🟢 中優先級（建議修復）

9. ✅ 統一導入順序（IAnalysisModule → tr）
10. ✅ 統一註解用詞
11. ✅ 統一縮排（23 vs 24 空格）

---

**總結**：Speed 和 RPM 模組在結構上高度相似（~70% 相同），但有多處關鍵差異需要修復。最重要的是 module_ref 的設置和 _check_and_load_telemetry_if_needed() 的完整實現。
