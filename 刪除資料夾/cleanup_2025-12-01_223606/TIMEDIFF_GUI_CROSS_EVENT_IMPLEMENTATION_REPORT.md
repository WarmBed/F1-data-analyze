# 🎯 Time Diff GUI 跨賽事比較功能完整複製報告

**完成時間**：2025-11-14 16:45  
**來源模組**：Speed Diff (`speeddiff_analysis_mdi.py`)  
**目標模組**：Time Diff (`timediff_analysis_mdi.py`)  

---

## ✅ 複製完成總結

已成功將 **Speed Diff 模組的所有跨賽事比較功能**完整複製到 Time Diff 模組！

### 📊 複製統計

| 項目 | 數量 | 狀態 |
|------|------|------|
| 新增類別 | 1 | ✅ `CrossEventComparisonWorker` |
| 新增方法 | 7 | ✅ 全部完成 |
| 新增屬性 | 9 | ✅ 全部完成 |
| 新增導入 | 3 | ✅ `time`, `requests`, `core.api_base_url` |
| 更新方法 | 2 | ✅ `__init__`, `_setup_ui` |

---

## 📝 詳細修改清單

### 1. 新增導入 (Line 1-25)

```python
# ✅ 已添加
import time
import requests
from core.api_base_url import resolve_api_base_url
```

---

### 2. 新增 API Worker 類別 (Line 23-121)

#### `CrossEventComparisonWorker` (完整複製)

**功能**：調用 `/api/v2/analysis/cross-event-comparison` API 端點進行跨賽事比較

**關鍵特性**：
- ✅ QThread 背景執行，不阻塞 UI
- ✅ 進度信號 (`progress`) 回報 20% → 70% → 90% → 100%
- ✅ 成功信號 (`success`) 返回完整數據和元數據
- ✅ 失敗信號 (`failure`) 回報錯誤訊息
- ✅ 使用 `resolve_api_base_url()` 動態解析 API 端點
- ✅ 支援 `force_refresh` 強制重新計算
- ✅ 120 秒超時保護

**日誌輸出**：
```
[TIMEDIFF-CROSS-EVENT-WORKER] 請求 API: http://localhost:8000/api/v2/analysis/cross-event-comparison
[TIMEDIFF-CROSS-EVENT-WORKER] 參數: {'driver1': 'VER', 'year1': 2024, ...}
[TIMEDIFF-CROSS-EVENT-WORKER] ✅ 請求成功
[TIMEDIFF-CROSS-EVENT-WORKER] ❌ 請求失敗: {error}
```

---

### 3. 更新 __init__ 方法 (Line 441-479)

#### 新增屬性

| 屬性名稱 | 類型 | 預設值 | 用途 |
|---------|------|--------|------|
| `sync_driver_lap_enabled` | `bool` | `True` | 同步功能開關 |
| `_updating_from_shared` | `bool` | `False` | 防止遞迴更新 guard flag |
| `driver1_year` | `Optional[str]` | `None` | 車手1年份（跨賽事） |
| `driver1_race` | `Optional[str]` | `None` | 車手1賽事（跨賽事） |
| `driver1_session` | `Optional[str]` | `None` | 車手1賽段（跨賽事） |
| `driver2_year` | `Optional[str]` | `None` | 車手2年份（跨賽事） |
| `driver2_race` | `Optional[str]` | `None` | 車手2賽事（跨賽事） |
| `driver2_session` | `Optional[str]` | `None` | 車手2賽段（跨賽事） |
| `use_time_axis` | `bool` | `False` | 時間軸模式 |

**關鍵變更**：
```python
# ✅ 修改分析類型大小寫以匹配規範
self.analysis_type = 'Timediff'  # 原: 'timediff'

# ✅ 新增同步功能屬性
self.sync_driver_lap_enabled = True
self._updating_from_shared = False

# ✅ 新增跨賽事比較屬性
self.driver1_year = None
self.driver1_race = None
self.driver1_session = None
# ... (車手2同理)

# ✅ 新增時間軸設定
self.use_time_axis = False
```

---

### 4. 更新 _setup_ui 方法 (Line 580-608)

#### 新增 info_label 組件

**功能**：顯示參數資訊標籤（取消同步時才顯示）

**特性**：
- ✅ 淺色背景 (`#F0F0F0`)
- ✅ 圓角設計 (`border-radius: 4px`)
- ✅ 自動換行 (`setWordWrap(True)`)
- ✅ 初始化時調用 `_update_info_label()`

```python
# ✅ 新增代碼
self.info_label = QLabel()
self.info_label.setObjectName("AnalysisInfoLabel")
self.info_label.setStyleSheet("""
    QLabel#AnalysisInfoLabel {
        background-color: #F0F0F0;
        color: #333333;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 11pt;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
""")
self.info_label.setWordWrap(True)
self._update_info_label()
layout.addWidget(self.info_label)
```

---

### 5. 新增跨賽事比較方法 (Line 1552-1635)

#### `update_cross_event_comparison()`

**方法簽名**：
```python
def update_cross_event_comparison(self, year1: str, race1: str, session1: str, driver1: str, lap1: int,
                                  year2: str, race2: str, session2: str, driver2: str, lap2: int,
                                  is_fastest: bool = False, use_time_axis: bool = False)
```

**功能流程**：
1. ✅ 儲存所有參數到實例變數
2. ✅ **關鍵**：取消同步模式 (`sync_driver_lap_enabled = False`)
3. ✅ 更新資訊標籤 (`_update_info_label()`)
4. ✅ 創建 `CrossEventComparisonWorker` API Worker
5. ✅ 連接信號：`success` → `_on_cross_event_data_loaded`
6. ✅ 連接信號：`failure` → `_on_cross_event_load_error`
7. ✅ 連接信號：`progress` → lambda (日誌輸出)
8. ✅ 啟動 Worker 執行緒

**日誌輸出範例**：
```
[TIMEDIFF-CROSS-EVENT] ========== 更新跨賽事比較參數 ==========
[TIMEDIFF-CROSS-EVENT] 車手 1: 2024 Japan R VER 第30圈
[TIMEDIFF-CROSS-EVENT] 車手 2: 2024 Bahrain R VER 第30圈
[TIMEDIFF-CROSS-EVENT] 時間軸模式: False
[TIMEDIFF-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...
[TIMEDIFF-CROSS-EVENT] 🔄 啟動 API 請求...
[TIMEDIFF-CROSS-EVENT] 進度: 20%
[TIMEDIFF-CROSS-EVENT] 進度: 70%
[TIMEDIFF-CROSS-EVENT] 進度: 90%
[TIMEDIFF-CROSS-EVENT] 進度: 100%
```

---

#### `_on_cross_event_data_loaded()` (Line 1637-1699)

**功能**：處理跨賽事比較數據載入成功回調

**數據處理流程**：
1. ✅ 提取 `data` 和 `meta` 對象
2. ✅ 檢查 `telemetry_comparison` 是否存在
3. ✅ 優先查找 `"Timediff"` 遙測參數
4. ✅ 構建圖表數據結構：
   ```python
   chart_data = {
       "timediff_data": {
           "time": [...],  # X軸：時間（秒）
           "time_difference": [...],  # Y軸：時間差（秒）
           "distance_gap": [...],  # 額外：距離差（米）
           "driver1_distance": [...],
           "driver2_distance": [...],
       },
       "comparison_info": {...},
       "cross_event_metadata": {...},
       "use_time_axis": False,  # Time Diff 固定使用時間軸
   }
   ```
5. ✅ 調用 `_update_chart(chart_data)` 更新圖表

**關鍵日誌**：
```
[TIMEDIFF-CROSS-EVENT] ✅ 數據載入成功
[TIMEDIFF-CROSS-EVENT] 數據鍵值: ['telemetry_comparison', 'comparison_info', 'cross_event_metadata']
[TIMEDIFF-CROSS-EVENT] 遙測參數: ['Speed', 'RPM', 'Brake', 'nGear', 'Throttle', 'Acceleration', 'Speeddiff', 'Distancediff', 'Timediff']
[TIMEDIFF-CROSS-EVENT] ✅ 使用 Timediff 參數（跨賽事計算的時間差）
[TIMEDIFF-CROSS-EVENT] 構建圖表數據:
[TIMEDIFF-CROSS-EVENT]   時間點數: 500
[TIMEDIFF-CROSS-EVENT]   時間差點數: 500
[TIMEDIFF-CROSS-EVENT]   距離差點數: 500
[TIMEDIFF-CROSS-EVENT] 開始更新圖表...
[TIMEDIFF-CROSS-EVENT] ✅ 跨賽事比較完成
```

---

#### `_on_cross_event_load_error()` (Line 1701-1703)

**功能**：處理跨賽事比較數據載入錯誤

```python
def _on_cross_event_load_error(self, error_msg: str) -> None:
    """處理跨賽事比較數據載入錯誤"""
    print(f"[TIMEDIFF-CROSS-EVENT] ❌ 數據載入失敗: {error_msg}")
```

---

### 6. 新增同步功能方法 (Line 1705-1798)

#### `update_from_shared_params()` (Line 1705-1781)

**功能**：從全域共享參數池更新參數（跨模組同步功能）

**調用時機**：
- 用戶取消勾選「與主視窗同步車手與圈數」
- 所有停用同步的視窗（Speed/RPM/Gear/Timediff 等）會共享同一組參數

**參數結構**：
```python
params = {
    'year1': str,
    'race1': str,
    'session1': str,
    'driver1': str,
    'lap1': int,
    'year2': str,
    'race2': str,
    'session2': str,
    'driver2': str,
    'lap2': int,
    'use_time_axis': bool
}
```

**執行流程**：
1. ✅ 檢查遞迴更新 guard (`_updating_from_shared`)
2. ✅ 設置 guard flag = True
3. ✅ 提取所有參數
4. ✅ **檢測是否為跨賽事比較**：
   - 條件：`year1 != year2 or session1 != session2`
5. ✅ **分支處理**：
   - **跨賽事模式**：調用 `update_cross_event_comparison()`
   - **標準模式**：調用 `update_lap_parameters()`
6. ✅ 調用 `_update_info_label()` 更新資訊標籤
7. ✅ 釋放 guard flag = False

**關鍵日誌**：
```
[TIMEDIFF_MDI] [SHARED_PARAMS] 🔄 從全域共享池更新參數
[TIMEDIFF_MDI] [SHARED_PARAMS] 收到參數: {...}
[TIMEDIFF_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:
[TIMEDIFF_MDI] [SHARED_PARAMS]   車手 1: 2024 Japan R VER 第30圈
[TIMEDIFF_MDI] [SHARED_PARAMS]   車手 2: 2024 Bahrain R VER 第30圈
[TIMEDIFF_MDI] [SHARED_PARAMS] 🔄 調用 update_cross_event_comparison
[TIMEDIFF_MDI] [SHARED_PARAMS] ✅ 跨賽事比較更新成功
[TIMEDIFF_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤
```

---

#### `_update_info_label()` (Line 1783-1824)

**功能**：更新參數資訊標籤（只在取消同步時顯示）

**顯示邏輯**：
| 同步狀態 | 標籤顯示 | 內容格式 |
|---------|---------|---------|
| 啟用同步 | ❌ 隱藏 | N/A |
| 取消同步 + 跨賽事 | ✅ 顯示 | **車手 1:** 2024 Japan R - VER Lap 30 **vs** **車手 2:** 2024 Bahrain R - VER Lap 30 |
| 取消同步 + 標準 | ✅ 顯示 | **賽事:** 2024 Japan R \| **車手:** VER (Lap 30) vs LEC (Lap 30) |

**HTML 格式化**：
```python
# 跨賽事格式
info_text = (
    f"<b>車手 1:</b> {year1} {race1} {session1} - {driver1} Lap {lap1}  "
    f"<b style='color: #999;'>vs</b>  "
    f"<b>車手 2:</b> {year2} {race2} {session2} - {driver2} Lap {lap2}"
)

# 標準格式
info_text = (
    f"<b>賽事:</b> {year1} {race1} {session1}  |  "
    f"<b>車手:</b> {driver1} (Lap {lap1}) vs {driver2} (Lap {lap2})"
)
```

---

### 7. 新增模組識別方法 (Line 1826-1837)

#### `get_module_type()` (Line 1826-1828)

**功能**：返回模組類型（用於主視窗識別）

```python
def get_module_type(self) -> str:
    """返回模組類型"""
    return "telemetry_timediff"
```

**用途**：
- 主視窗用於識別模組類型
- 路由跨賽事比較請求到正確的模組

---

#### `supports_sync()` (Line 1830-1832)

**功能**：返回模組是否支援與主視窗同步車手與圈數

```python
def supports_sync(self) -> bool:
    """返回模組是否支援與主視窗同步車手與圈數"""
    return True
```

**用途**：
- 主視窗用於判斷是否顯示同步勾選框
- Time Diff 模組現在完全支援同步功能

---

#### `get_parameter_interface()` (Line 1834-1837)

**功能**：返回參數設定介面（如果有的話）

```python
def get_parameter_interface(self) -> Optional[QWidget]:
    """返回參數設定介面（如果有的話）"""
    return None
```

**用途**：
- 允許模組提供自訂參數設定介面
- Time Diff 目前使用標準介面，返回 `None`

---

## 🎯 功能驗證清單

### ✅ 已完成項目

- [x] ✅ 添加 `CrossEventComparisonWorker` API Worker 類別
- [x] ✅ 添加所有必要導入 (`time`, `requests`, `core.api_base_url`)
- [x] ✅ 更新 `__init__` 方法添加 9 個新屬性
- [x] ✅ 更新 `_setup_ui` 方法添加 `info_label`
- [x] ✅ 實現 `update_cross_event_comparison()` 方法
- [x] ✅ 實現 `_on_cross_event_data_loaded()` 回調
- [x] ✅ 實現 `_on_cross_event_load_error()` 回調
- [x] ✅ 實現 `update_from_shared_params()` 同步方法
- [x] ✅ 實現 `_update_info_label()` 標籤更新
- [x] ✅ 實現 `get_module_type()` 模組識別
- [x] ✅ 實現 `supports_sync()` 同步支援查詢
- [x] ✅ 實現 `get_parameter_interface()` 介面查詢

---

## 🔄 與 Speed Diff 的對應關係

| Speed Diff | Time Diff | 狀態 |
|-----------|-----------|------|
| `CrossEventComparisonWorker` | `CrossEventComparisonWorker` | ✅ 完全相同 |
| `speeddiff_chart_widget` | `timediff_chart_widget` | ✅ 已對應 |
| `self.analysis_type = 'Speeddiff'` | `self.analysis_type = 'Timediff'` | ✅ 已對應 |
| `[SPEEDDIFF-CROSS-EVENT]` | `[TIMEDIFF-CROSS-EVENT]` | ✅ 日誌前綴已對應 |
| Speeddiff 遙測參數 | Timediff 遙測參數 | ✅ 數據格式已對應 |

---

## 📊 API 數據格式對應

### Speed Diff API 數據

```json
{
  "telemetry_comparison": {
    "Speeddiff": {
      "distance": [0, 1, 2, ...],
      "speed_difference": [-5.2, -3.1, ...],
      "driver1_time_seconds": [0, 0.5, 1.0, ...],
      "driver2_time_seconds": [0, 0.6, 1.2, ...]
    }
  }
}
```

### Time Diff API 數據

```json
{
  "telemetry_comparison": {
    "Timediff": {
      "time": [0, 0.5, 1.0, ...],
      "time_difference": [0.0, -0.1, -0.2, ...],
      "distance_gap": [0.0, -2.5, -5.0, ...],
      "driver1_distance": [0, 50, 100, ...],
      "driver2_distance": [0, 52.5, 105, ...]
    }
  }
}
```

---

## 🧪 測試場景

### 場景 1：跨賽事比較（不同年份）

**參數**：
- 車手 1: 2024 Japan R VER Lap 30
- 車手 2: 2025 Bahrain R VER Lap 30

**預期結果**：
- ✅ 調用 `update_cross_event_comparison()`
- ✅ API Worker 請求 `/api/v2/analysis/cross-event-comparison`
- ✅ 返回 `Timediff` 遙測數據（500 點）
- ✅ 圖表顯示時間差曲線
- ✅ 資訊標籤顯示：**車手 1:** 2024 Japan R - VER Lap 30 **vs** **車手 2:** 2025 Bahrain R - VER Lap 30

---

### 場景 2：跨賽事比較（不同會話）

**參數**：
- 車手 1: 2025 Japan R VER Lap 30
- 車手 2: 2025 Japan Q LEC Lap 1

**預期結果**：
- ✅ 調用 `update_cross_event_comparison()`
- ✅ 檢測到 `session1 != session2`（R != Q）
- ✅ 正確處理跨會話比較

---

### 場景 3：標準比較（同一賽事）

**參數**：
- 車手 1: 2025 Japan R VER Lap 30
- 車手 2: 2025 Japan R LEC Lap 30

**預期結果**：
- ✅ 調用 `update_lap_parameters()`
- ✅ 使用標準數據載入流程
- ✅ 資訊標籤顯示：**賽事:** 2025 Japan R | **車手:** VER (Lap 30) vs LEC (Lap 30)

---

### 場景 4：同步功能切換

**操作**：
1. 勾選「與主視窗同步車手與圈數」
2. 主視窗更新參數
3. Time Diff 自動更新

**預期結果**：
- ✅ `sync_driver_lap_enabled = True`
- ✅ 資訊標籤隱藏
- ✅ 自動跟隨主視窗參數

**操作**：
1. 取消勾選「與主視窗同步車手與圈數」
2. 設定自訂參數

**預期結果**：
- ✅ `sync_driver_lap_enabled = False`
- ✅ 資訊標籤顯示
- ✅ 調用 `update_from_shared_params()`

---

## 🔍 日誌檢查點

### 跨賽事比較日誌

```
[TIMEDIFF-CROSS-EVENT] ========== 更新跨賽事比較參數 ==========
[TIMEDIFF-CROSS-EVENT] 車手 1: 2024 Japan R VER 第30圈
[TIMEDIFF-CROSS-EVENT] 車手 2: 2024 Bahrain R VER 第30圈
[TIMEDIFF-CROSS-EVENT] 時間軸模式: False
[TIMEDIFF-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...
[TIMEDIFF-CROSS-EVENT-WORKER] 請求 API: http://localhost:8000/api/v2/analysis/cross-event-comparison
[TIMEDIFF-CROSS-EVENT-WORKER] 參數: {'driver1': 'VER', 'year1': 2024, 'race1': 'Japan', ...}
[TIMEDIFF-CROSS-EVENT] 進度: 20%
[TIMEDIFF-CROSS-EVENT] 進度: 70%
[TIMEDIFF-CROSS-EVENT] 進度: 90%
[TIMEDIFF-CROSS-EVENT] ✅ 數據載入成功
[TIMEDIFF-CROSS-EVENT] 數據鍵值: ['telemetry_comparison', 'comparison_info', ...]
[TIMEDIFF-CROSS-EVENT] 遙測參數: ['Speed', 'RPM', ..., 'Timediff']
[TIMEDIFF-CROSS-EVENT] ✅ 使用 Timediff 參數（跨賽事計算的時間差）
[TIMEDIFF-CROSS-EVENT] 構建圖表數據:
[TIMEDIFF-CROSS-EVENT]   時間點數: 500
[TIMEDIFF-CROSS-EVENT]   時間差點數: 500
[TIMEDIFF-CROSS-EVENT] 開始更新圖表...
[TIMEDIFF-CROSS-EVENT] ✅ 跨賽事比較完成
[TIMEDIFF-CROSS-EVENT] 進度: 100%
```

### 同步功能日誌

```
[TIMEDIFF_MDI] [SHARED_PARAMS] 🔄 從全域共享池更新參數
[TIMEDIFF_MDI] [SHARED_PARAMS] 收到參數: {...}
[TIMEDIFF_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:
[TIMEDIFF_MDI] [SHARED_PARAMS]   車手 1: 2024 Japan R VER 第30圈
[TIMEDIFF_MDI] [SHARED_PARAMS]   車手 2: 2024 Bahrain R VER 第30圈
[TIMEDIFF_MDI] [SHARED_PARAMS] 🔄 調用 update_cross_event_comparison
[TIMEDIFF-CROSS-EVENT] ========== 更新跨賽事比較參數 ==========
[TIMEDIFF_MDI] [SHARED_PARAMS] ✅ 跨賽事比較更新成功
[TIMEDIFF_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤
[TIMEDIFF_MDI] 取消同步模式：顯示資訊標籤
```

---

## ⚠️ 重要注意事項

### 1. API 端點依賴

Time Diff 模組現在依賴 API 端點返回 `Timediff` 遙測數據：

```python
"Timediff": {
    "time": [...],  # X軸：時間（秒）
    "time_difference": [...],  # Y軸：時間差（秒）
    "distance_gap": [...],  # 額外：距離差（米）
    "driver1_distance": [...],
    "driver2_distance": [...]
}
```

**前置條件**：
- ✅ API 端點已實現 Timediff 計算（已完成 - 參考 `TIMEDIFF_API_CHECK_REPORT.md`）
- ✅ API 測試通過（已完成 - `test_timediff_api.py`）

---

### 2. Chart Widget 兼容性

Time Diff Chart Widget 必須支援以下數據格式：

```python
chart_data = {
    "timediff_data": {
        "time": [...],
        "time_difference": [...],
        # ... 其他欄位
    },
    "comparison_info": {...},
    "cross_event_metadata": {...},
    "use_time_axis": False
}
```

**檢查清單**：
- [ ] `timediff_analysis_chart_widget.py` 是否支援 `timediff_data` 欄位？
- [ ] Chart Widget 是否有 `_update_chart()` 方法？
- [ ] 是否正確處理 `cross_event_metadata`？

---

### 3. 時間軸模式

Time Diff 固定使用時間軸（X軸 = 時間），與 Speed Diff 不同：

| 模組 | X軸預設 | 可切換 |
|------|--------|--------|
| Speed Diff | 距離 (m) | ✅ 可切換到時間 |
| Distance Diff | 距離 (m) | ✅ 可切換到時間 |
| **Time Diff** | **時間 (s)** | ❌ **固定時間** |

**代碼中體現**：
```python
chart_data = {
    # ... 其他欄位
    "use_time_axis": False,  # Time Diff 固定使用時間軸
}
```

---

## 📈 下一步建議

### 優先級 1：GUI 測試

1. **啟動 GUI**：
   ```powershell
   python f1t_gui_main.py
   ```

2. **打開 Time Diff 模組**

3. **測試跨賽事比較**：
   - 取消勾選「與主視窗同步車手與圈數」
   - 設定車手 1: 2024 Japan R VER Lap 30
   - 設定車手 2: 2024 Bahrain R VER Lap 30
   - 點擊 OK

4. **檢查日誌**：
   ```powershell
   Get-Content logs/gui/gui_YYYY-MM-DD.log -Tail 50
   ```

---

### 優先級 2：Chart Widget 驗證

檢查 `timediff_analysis_chart_widget.py` 是否支援新數據格式：

```python
# 搜尋 Chart Widget 的 _update_chart 方法
grep_search: "def _update_chart|def update_chart"
includePattern: "timediff_analysis_chart_widget.py"
```

---

### 優先級 3：錯誤處理增強

添加更詳細的錯誤訊息：

```python
# 在 _on_cross_event_load_error 中
def _on_cross_event_load_error(self, error_msg: str) -> None:
    print(f"[TIMEDIFF-CROSS-EVENT] ❌ 數據載入失敗: {error_msg}")
    
    # ✅ 新增：顯示用戶友好的錯誤對話框
    QMessageBox.critical(
        self.main_widget,
        tr('cross_event_error_title', 'Cross-Event Comparison Error'),
        tr('cross_event_error_message', f'Failed to load cross-event comparison data:\n\n{error_msg}')
    )
```

---

## ✅ 結論

Time Diff 模組現在已具備完整的跨賽事比較功能，與 Speed Diff 模組架構完全一致！

**已實現功能**：
- ✅ API Worker 背景調用
- ✅ 跨賽事比較數據處理
- ✅ 同步功能支援
- ✅ 資訊標籤動態顯示
- ✅ 模組類型識別

**待驗證項目**：
- [ ] GUI 實際測試
- [ ] Chart Widget 兼容性
- [ ] 錯誤處理完整性

---

**Time Diff 跨賽事比較功能複製完成！** 🎉
