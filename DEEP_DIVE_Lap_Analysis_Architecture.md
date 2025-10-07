# 🏎️ F1T Lap Analysis 深度架構研究報告

**作者**: F1T Team  
**日期**: 2025-10-07  
**版本**: 1.0.0  
**狀態**: 📚 知識文件

---

## 📋 目錄

1. [架構總覽](#1-架構總覽)
2. [核心組件詳解](#2-核心組件詳解)
3. [數據流分析](#3-數據流分析)
4. [API-ONLY 模式實現](#4-api-only-模式實現)
5. [連動系統架構](#5-連動系統架構)
6. [模組化設計模式](#6-模組化設計模式)
7. [關鍵技術點](#7-關鍵技術點)
8. [最佳實踐](#8-最佳實踐)
9. [常見問題與解決方案](#9-常見問題與解決方案)

---

## 1. 架構總覽

### 1.1 系統概述

Lap Analysis 是 F1T 系統中最複雜的模組之一，負責處理 F1 賽車的圈速遙測數據分析。系統採用 **三層架構設計**：

```
┌─────────────────────────────────────────────────────────────┐
│                     GUI 層 (用戶界面)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Speed Module │  │  RPM Module  │  │ Gear Module  │      │
│  │   (速度分析)  │  │  (轉速分析)   │  │  (檔位分析)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
├─────────┼──────────────────┼──────────────────┼─────────────┤
│                     數據層 (數據處理)                          │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │       TelemetryDataLoader (統一數據載入器)          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐   │    │
│  │  │ API Client │  │ JSON Cache │  │ CLI Backup │   │    │
│  │  └────────────┘  └────────────┘  └────────────┘   │    │
│  └───────────────────────────────────────────────────┘    │
│                          │                                  │
├──────────────────────────┼─────────────────────────────────┤
│                     CLI 層 (後端引擎)                         │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────┐     │
│  │  Function 13: 車手遙測比較分析                      │     │
│  │  (driver_comparison_advanced.py)                  │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 支援的遙測類型

| 遙測類型 | CLI 功能 | 數據欄位 | 單位 | GUI 模組 |
|---------|---------|---------|------|---------|
| Speed | 13 | Speed | km/h | speed_analysis/ |
| RPM | 13 | RPM | rpm | rpm_analysis/ |
| Gear | 13 | nGear | gear | gear_analysis/ |
| Throttle | 13 | Throttle | % | Throttle_analysis/ |
| Brake | 13 | Brake | % | brake_analysis/ |
| Acceleration | 13 | Acceleration | m/s² | acceleration_analysis/ |
| SpeedDiff | 13 | speed_difference | km/h | speeddiff_analysis/ |
| DistanceDiff | 13 | distance_difference | m | distancediff_analysis/ |

### 1.3 目錄結構

```
modules/gui/lap_analysis/
├── __init__.py
├── telemetry_data_loader_base.py      # 🔑 統一數據載入器基類
├── analysis_module_manager.py         # 📊 模組管理器
├── linkage/                            # 🔗 連動系統
│   ├── linkage_mixin.py               # 連動混合類
│   ├── linkage_manager.py             # 連動管理器
│   └── MIGRATION_GUIDE.md             # 連動系統遷移指南
├── speed_analysis/                     # 速度分析模組
│   ├── speed_analysis_mdi.py          # MDI 主模組
│   ├── speed_analysis_data_loader.py  # 數據載入器
│   └── speed_analysis_chart_widget.py # 圖表組件
├── rpm_analysis/                       # RPM 分析模組
│   ├── rpm_analysis_mdi.py
│   ├── rpm_analysis_data_loader.py
│   └── rpm_analysis_chart_widget.py
├── gear_analysis/                      # 檔位分析模組
├── throttle_analysis/                  # 油門分析模組
├── brake_analysis/                     # 煞車分析模組
├── acceleration_analysis/              # 加速度分析模組
├── speeddiff_analysis/                 # 速度差異分析
└── distancediff_analysis/              # 距離差異分析
```

---

## 2. 核心組件詳解

### 2.1 TelemetryDataLoader - 統一數據載入器

**檔案**: `telemetry_data_loader_base.py`  
**行數**: 1200+ 行  
**作用**: 所有遙測分析模組的共用數據載入邏輯

#### 2.1.1 關鍵特性

```python
class TelemetryDataLoader(QObject):
    """
    遙測數據載入器基類
    
    核心功能：
    1. 統一的 API-ONLY 模式實現
    2. 自動 JSON 緩存管理
    3. CLI 備援機制（手動模式）
    4. 請求去重與並發控制
    5. 數據格式驗證與轉換
    """
    
    # 支援的遙測類型映射
    TELEMETRY_TYPES = {
        'speed': {
            'display_name': '速度分析',
            'data_field': 'Speed',
            'unit': 'km/h',
            'debug_prefix': 'SPEED'
        },
        'rpm': {
            'display_name': 'RPM分析',
            'data_field': 'RPM',
            'unit': 'rpm',
            'debug_prefix': 'RPM'
        },
        # ... 其他遙測類型
    }
```

#### 2.1.2 信號系統

```python
# 標準信號定義（所有遙測模組共用）
data_loaded = pyqtSignal(dict)      # 數據載入完成
load_progress = pyqtSignal(int)     # 載入進度 (0-100)
load_error = pyqtSignal(str)        # 載入錯誤
status_changed = pyqtSignal(str)    # 狀態變更
```

#### 2.1.3 API-ONLY 實現

```python
def load_telemetry_data(self, year, race, session, driver1, driver2, lap1, lap2):
    """
    API-ONLY 模式載入流程：
    
    1. 參數正規化與驗證
    2. 請求去重檢查
    3. 優先通過 API 獲取數據
    4. API 失敗 → 檢查本地 JSON 緩存
    5. 本地緩存也不存在 → 提示手動操作
    6. ❌ 絕不自動啟動 CLI 進程
    """
    
    # 步驟1: 請求標識與去重
    request_token = self._next_request_token()
    incoming_session['request_token'] = request_token
    
    # 步驟2: 啟動 API 請求
    self._start_api_request(request_token)
```

#### 2.1.4 請求去重機制

```python
def _build_request_signature(self, params: Dict) -> Tuple:
    """建立請求簽章，用於比對參數是否一致"""
    return (
        params.get('year'),
        params.get('race'),
        params.get('session'),
        params.get('driver1'),
        params.get('driver2_effective'),
        params.get('lap1'),
        params.get('lap2'),
        params.get('single_driver_mode')
    )

def _sessions_match(self, active_session, incoming_session) -> bool:
    """檢查即將載入的參數是否與目前正在處理的相同"""
    if not active_session:
        return False
    
    active_signature = active_session.get('signature')
    incoming_signature = incoming_session.get('signature')
    
    return active_signature == incoming_signature
```

### 2.2 TelemetryApiWorker - API 請求執行緒

```python
class TelemetryApiWorker(QThread):
    """Background worker responsible for fetching telemetry comparison data via REST API."""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def run(self):
        """
        執行流程：
        1. 構建 API 請求參數
        2. POST /api/v2/analysis/execute
        3. 驗證響應格式
        4. 發送成功/失敗信號
        """
        
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params = {
            "function_id": 13,  # 車手遙測比較分析
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
            "driver1": self.params.get("driver1"),
            "driver2": self.params.get("driver2"),
            "lap1": self.params.get("lap1"),
            "lap2": self.params.get("lap2"),
        }
        
        response = requests.post(endpoint, params=query_params, timeout=75.0)
        self.success.emit({"data": response.json()["data"], ...})
```

### 2.3 Analysis Module Manager - 模組管理器

**檔案**: `analysis_module_manager.py`  
**作用**: 管理多個圈速分析模組的生命週期和統計面板顯示

#### 2.3.1 自動統計面板控制

```python
class AnalysisModuleManager(QObject):
    """
    圈速分析模組管理器 - 單例模式
    
    核心功能：
    1. 追蹤活躍的分析模組數量
    2. 當開啟 ≥3 個模組時，自動隱藏統計面板
    3. 統一管理圖表組件的顯示狀態
    """
    
    HIDE_STATISTICS_THRESHOLD = 3  # 隱藏統計信息的模組數量閾值
    
    def _update_statistics_visibility(self):
        """更新統計面板顯示狀態"""
        active_count = len(self._active_modules)
        should_show_statistics = active_count < self.HIDE_STATISTICS_THRESHOLD
        
        if self._statistics_visible != should_show_statistics:
            # 通知所有註冊的圖表組件
            self._notify_chart_widgets_visibility_change(should_show_statistics)
            self.statistics_visibility_changed.emit(should_show_statistics)
```

### 2.4 Linkage System - 連動系統

**檔案**: `linkage/linkage_mixin.py`  
**作用**: 提供圖表之間的 X 軸位置同步和點擊連動

#### 2.4.1 連動混合類

```python
class LapAnalysisLinkageMixin:
    """
    圈速分析連動混合類
    
    提供：
    - 雙層連動控制（主開關 + 個別開關）
    - X軸位置同步（滑鼠追蹤）
    - 點擊位置同步（固定線）
    - 連動線繪製
    """
    
    def __init_linkage__(self):
        """初始化連動功能"""
        self.linkage_enabled = True          # 模組本地連動開關
        self.master_linkage_enabled = True   # 主視窗總開關狀態
        self.is_sending_linkage = False      # 避免循環信號發送
        
        # 連動數據
        self.linkage_distance_value = None   # 連動接收的距離值
        self.linkage_y_relative = 0.5        # Y軸相對位置
        self.show_linkage_line = False       # 是否顯示連動線
        
        # 固定線數據
        self.fixed_distance_value = None
        self.show_fixed_line = False
```

#### 2.4.2 信號流向

```
┌────────────────┐     mouseMoveEvent     ┌────────────────┐
│  Speed Chart   │ ──────────────────────▶│ Linkage Manager│
└────────────────┘                         └────────┬───────┘
                                                    │
                                                    │ broadcast
                                                    │
                    ┌───────────────────────────────┼──────────────┐
                    │                               │              │
           ┌────────▼────────┐           ┌─────────▼──────┐  ┌───▼─────────┐
           │   RPM Chart     │           │  Gear Chart    │  │Throttle Chart│
           │ on_x_linkage_   │           │ on_x_linkage_  │  │on_x_linkage_ │
           │   received()    │           │   received()   │  │  received()  │
           └─────────────────┘           └────────────────┘  └──────────────┘
```

---

## 3. 數據流分析

### 3.1 完整數據流程圖

```
用戶操作
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  GUI Layer: SpeedAnalysisModule                          │
│  ├─ update_lap_parameters(year, race, session, ...)     │
│  └─ data_manager.load_speed_data(...)                   │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Data Layer: SpeedAnalysisDataLoader                     │
│  └─ load_telemetry_data(year, race, session, ...)       │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Base Layer: TelemetryDataLoader                         │
│  ├─ 參數正規化與驗證                                      │
│  ├─ 請求去重檢查                                         │
│  └─ 決定數據來源                                         │
└──────────────────┬───────────────────────────────────────┘
                   │
       ┌───────────┴──────────────┐
       │                          │
       ▼                          ▼
┌─────────────┐          ┌────────────────┐
│  API 模式    │          │  本地 JSON 模式 │
│             │          │                │
│  步驟1: API │          │  步驟1: 搜尋   │
│   請求啟動   │          │   JSON 檔案    │
│             │          │                │
│  步驟2:     │          │  步驟2: 載入   │
│  TelemetryApi│         │   檔案內容     │
│  Worker執行  │          │                │
│             │          │  步驟3: 格式   │
│  步驟3: 響應│          │   驗證         │
│   處理      │          │                │
│             │          │  步驟4: 數據   │
│  步驟4: 格式│          │   轉換         │
│   驗證      │          └────────┬───────┘
│             │                   │
│  步驟5: 數據│                   │
│   轉換      │                   │
└─────┬───────┘                   │
      │                           │
      └───────────┬───────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │  _handle_api_success  │
      │  或                   │
      │  _load_json_file     │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │ _process_telemetry_   │
      │        data           │
      │                       │
      │ 1. 提取基本資訊       │
      │ 2. 構建標準化結構     │
      │ 3. 計算統計數據       │
      └───────────┬───────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │   data_loaded 信號     │
      │   發送到 GUI          │
      └───────────┬───────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  GUI Layer: SpeedAnalysisModule                          │
│  └─ _update_chart(data)                                 │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Chart Layer: SpeedAnalysisChartWidget                   │
│  └─ update_speed_data(data)                             │
│      ├─ 提取速度數據                                     │
│      ├─ 重新繪製圖表                                     │
│      └─ 更新統計面板                                     │
└──────────────────────────────────────────────────────────┘
```

### 3.2 JSON 數據格式

#### 3.2.1 API 響應格式

```json
{
  "success": true,
  "message": "分析完成",
  "data": {
    "metadata": {
      "year": 2025,
      "race": "Japan",
      "session": "R",
      "driver1": "VER",
      "driver2": "LEC",
      "lap_number1": 15,
      "lap_number2": 23,
      "analysis_timestamp": "2025-10-07T14:30:00"
    },
    "results": {
      "comparison_info": {
        "driver1": "VER",
        "driver2": "LEC",
        "act_lap1_number": 15,
        "act_lap2_number": 23,
        "lap_time1": "1:30.123",
        "lap_time2": "1:30.456",
        "compound1": "SOFT",
        "compound2": "MEDIUM",
        "tyre_life1": 5,
        "tyre_life2": 12
      },
      "telemetry_comparison": {
        "Speed": {
          "distance": [0, 10, 20, 30, ..., 5300],
          "driver1_data": [120, 150, 180, 220, ..., 280],
          "driver2_data": [118, 148, 175, 215, ..., 275]
        },
        "RPM": {
          "distance": [...],
          "driver1_data": [...],
          "driver2_data": [...]
        }
        // ... 其他遙測類型
      }
    }
  },
  "execution_time": "2.5秒",
  "timestamp": "2025-10-07T14:30:00",
  "request_id": "uuid-xxxxx"
}
```

#### 3.2.2 處理後的內部格式

```python
processed_data = {
    "metadata": {
        "drivers": [
            {
                "code": "VER",
                "lap_number": 15,
                "lap_time": "1:30.123",
                "compound": "SOFT",
                "tyre_life": 5
            },
            {
                "code": "LEC",
                "lap_number": 23,
                "lap_time": "1:30.456",
                "compound": "MEDIUM",
                "tyre_life": 12
            }
        ],
        "sectors": [...],
        "year": 2025,
        "race": "Japan",
        "session": "R",
        "telemetry_type": "speed",
        "display_name": "速度分析",
        "unit": "km/h"
    },
    "speed_data": {  # 或 rpm_data, gear_data 等
        "distance": [0, 10, 20, ..., 5300],
        "driver1_speed": [120, 150, 180, ..., 280],
        "driver2_speed": [118, 148, 175, ..., 275],
        "driver1_name": "VER",
        "driver2_name": "LEC"
    },
    "statistics": {
        "driver1": {
            "max": 320.5,
            "min": 80.2,
            "avg": 245.7,
            "count": 531
        },
        "driver2": {
            "max": 318.3,
            "min": 82.1,
            "avg": 243.9,
            "count": 531
        }
    }
}
```

---

## 4. API-ONLY 模式實現

### 4.1 政策背景

**日期**: 2025-10-03  
**原因**: 禁止 GUI 直接啟動 CLI 進程，強制通過 API 獲取數據

### 4.2 實現細節

#### 4.2.1 禁止的模式

```python
# ❌ 禁止：啟動 CLI 進程
def _generate_data_via_cli(self, **kwargs):
    """
    [已禁用] 通過 CLI 生成數據
    
    ⚠️ API-ONLY 模式: 此方法已禁用
    """
    self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
    self._debug("💡 提示: 請使用 API 獲取數據")
    return False

# ❌ 禁止：subprocess 執行 CLI
subprocess.run(["python", "f1_analysis_modular_main.py", "-f", "13"])
```

#### 4.2.2 正確的模式

```python
# ✅ 正確：通過 API 獲取數據
def _start_api_request(self, request_token):
    """啟動 API 請求"""
    worker_params = {
        "year": params.get('year'),
        "race": params.get('race'),
        "session": params.get('session'),
        "driver1": driver1,
        "driver2": driver2,
        "lap1": lap1,
        "lap2": lap2
    }
    
    self._api_worker = TelemetryApiWorker(
        self._api_base_url,
        worker_params,
        timeout=75.0,
        request_token=request_token
    )
    self._api_worker.start()

# ✅ 正確：讀取已存在的 JSON
data = self._load_json_data(json_file_path)

# ✅ 正確：提示用戶手動執行
self.load_error.emit("找不到數據檔案且 CLI 調用已禁用，請使用 API 獲取數據")
```

### 4.3 本地後備機制

```python
def _fallback_to_local(self, reason: str, request_token):
    """本地 JSON 後備流程"""
    # 檢查政策
    if not self._allow_local_fallback:
        self._debug(f"本地 JSON 後備被停用: {reason}")
        return False
    
    # 搜尋本地 JSON
    json_file = self._find_telemetry_data_file(...)
    
    if json_file:
        # 載入本地 JSON
        self._load_json_file(json_file, request_token)
        return True
    
    # ❌ 不再自動啟動 CLI
    self._debug("本地 JSON 不存在，請手動執行 CLI 或通過 API 獲取")
    return False
```

---

## 5. 連動系統架構

### 5.1 連動管理器

```python
class LinkageManager(QObject):
    """
    圈速分析連動管理器 - 單例模式
    
    管理所有圖表組件的連動行為：
    - X 軸位置同步
    - 點擊位置同步
    - 主開關控制
    """
    
    # 全域連動信號
    x_linkage_signal = pyqtSignal(float, float)    # (distance, y_relative)
    x_linkage_clear = pyqtSignal()
    click_linkage_signal = pyqtSignal(float)       # (distance)
    click_linkage_clear = pyqtSignal()
    master_linkage_changed = pyqtSignal(bool)      # (enabled)
    
    def register_module(self, module_widget):
        """註冊圖表組件到連動系統"""
        if module_widget not in self._registered_modules:
            # 連接信號
            self.x_linkage_signal.connect(module_widget.on_x_linkage_received)
            self.click_linkage_signal.connect(module_widget.on_click_linkage_received)
            # ...
            
            self._registered_modules.append(module_widget)
```

### 5.2 連動繪製

```python
class LapAnalysisLinkageDrawingMixin:
    """連動線繪製混合類"""
    
    def draw_linkage_line(self, painter, chart_rect, distance_data, ...):
        """
        繪製連動線 (來自其他圖表的X軸位置)
        
        步驟:
        1. 計算 X 座標位置
        2. 繪製垂直虛線
        3. 繪製數據標籤（顯示當前位置的數值）
        """
        
        # 計算X座標
        relative_pos = (self.linkage_distance_value - min_distance) / distance_range
        x_pos = chart_rect.left() + int(relative_pos * chart_rect.width())
        
        # 繪製連動垂直線
        painter.setPen(QPen(QColor(128, 128, 128), 1, Qt.DashLine))
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 繪製標籤
        self._draw_linkage_label(painter, chart_rect, x_pos, ...)
```

---

## 6. 模組化設計模式

### 6.1 三層架構模式

```
┌─────────────────────────────────────────────────────────┐
│  MDI 層 (速度分析為例)                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SpeedAnalysisModule (IAnalysisModule)            │  │
│  │ ├─ initialize_module()                           │  │
│  │ ├─ update_parameters(year, race, session)        │  │
│  │ ├─ update_lap_parameters(driver1, driver2, ...)  │  │
│  │ └─ cleanup()                                     │  │
│  └──────────────┬───────────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  數據管理層                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SpeedDataManager                                 │  │
│  │ └─ SpeedAnalysisDataLoader                       │  │
│  │     └─ TelemetryDataLoader (基類)                 │  │
│  └──────────────┬───────────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  圖表層                                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SpeedAnalysisChartWidget                         │  │
│  │ ├─ LapAnalysisLinkageMixin                       │  │
│  │ ├─ LapAnalysisLinkageDrawingMixin                │  │
│  │ └─ update_speed_data(data)                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 6.2 繼承鏈

```python
# 數據載入器繼承鏈
SpeedAnalysisDataLoader
    └─ TelemetryDataLoader (基類)
        └─ QObject

# 圖表組件繼承鏈
SpeedAnalysisChartWidget
    ├─ QWidget
    ├─ LapAnalysisLinkageMixin
    └─ LapAnalysisLinkageDrawingMixin

# MDI 模組繼承鏈
SpeedAnalysisModule
    └─ IAnalysisModule (介面)
        └─ QObject
```

---

## 7. 關鍵技術點

### 7.1 請求Token機制

**目的**: 防止重複請求和過時響應

```python
class TelemetryDataLoader:
    def __init__(self):
        self._active_request_token = 0  # 當前活躍的請求標識
    
    def _next_request_token(self) -> int:
        """取得下一個請求標識值"""
        self._active_request_token += 1
        return self._active_request_token
    
    def _on_api_success(self, payload):
        """處理API成功響應"""
        request_token = payload.get("request_token")
        
        # 檢查是否為過時請求
        if request_token != self._active_request_token:
            self._debug(f"忽略過時的 API 響應 (token {request_token})")
            return
        
        # 處理最新的響應
        self._handle_api_success(...)
```

### 7.2 單車手模式處理

```python
def load_telemetry_data(self, ..., driver1, driver2, ...):
    """載入遙測數據"""
    
    # 正規化車手代碼
    driver1_normalized = self._normalize_driver_code(driver1)
    driver2_normalized = self._normalize_driver_code(driver2)
    
    # 判斷單/雙車手模式
    single_driver_mode = (
        driver2_normalized is None or 
        driver2_normalized == driver1_normalized
    )
    
    # 單車手模式：使用 driver1 作為 driver2
    effective_driver2 = (
        driver2_normalized if driver2_normalized 
        else driver1_normalized
    )
    
    # API 請求時傳入 effective_driver2
    worker_params = {
        "driver1": driver1_normalized,
        "driver2": effective_driver2,  # 保證 API 總是收到兩個車手
        ...
    }
```

### 7.3 數據格式驗證

```python
def _validate_telemetry_data(self, raw_data: dict) -> bool:
    """驗證遙測數據格式"""
    
    # 檢查基本結構
    if not isinstance(raw_data, dict):
        return False
    
    if 'results' not in raw_data:
        return False
    
    results = raw_data['results']
    
    # 根據遙測類型選擇不同的驗證路徑
    if self.telemetry_type in ['speeddiff', 'distancediff']:
        # 差異分析數據直接在 results 下
        telemetry_data = results[self.config['data_field']]
        required_fields = ['distance', self.config['data_field']]
    else:
        # 常規遙測數據在 telemetry_comparison 下
        telemetry_comp = results['telemetry_comparison']
        telemetry_data = telemetry_comp[self.config['data_field']]
        required_fields = ['distance', 'driver1_data', 'driver2_data']
    
    # 檢查必要欄位
    for field in required_fields:
        if field not in telemetry_data:
            return False
    
    # 驗證數據長度一致性
    distance_data = telemetry_data.get('distance', [])
    if len(distance_data) == 0:
        return False
    
    return True
```

### 7.4 統計計算

```python
def _calculate_statistics(self, data: List[float]) -> dict:
    """計算統計數據 - 自動過濾 None 值"""
    if not data:
        return {"max": 0, "min": 0, "avg": 0, "count": 0}
    
    # 過濾掉 None 值 (重要！)
    valid_data = [x for x in data if x is not None]
    
    if not valid_data:
        return {"max": 0, "min": 0, "avg": 0, "count": 0}
    
    return {
        "max": max(valid_data),
        "min": min(valid_data),
        "avg": sum(valid_data) / len(valid_data),
        "count": len(valid_data)
    }
```

---

## 8. 最佳實踐

### 8.1 創建新的遙測分析模組

#### 步驟1: 創建數據載入器

```python
# modules/gui/lap_analysis/your_analysis/your_analysis_data_loader.py

from ..telemetry_data_loader_base import TelemetryDataLoader

class YourAnalysisDataLoader(TelemetryDataLoader):
    """您的分析數據載入器"""
    
    def __init__(self, parent=None):
        # 指定遙測類型（必須在 TELEMETRY_TYPES 中已定義）
        super().__init__('your_type', parent)
    
    # 向後兼容的載入方法
    def load_your_data(self, year, race, session, driver1, driver2, lap1, lap2):
        """載入數據 - 向後兼容接口"""
        return self.load_telemetry_data(
            year, race, session, driver1, driver2, lap1, lap2
        )
```

#### 步驟2: 創建圖表組件

```python
# modules/gui/lap_analysis/your_analysis/your_analysis_chart_widget.py

from PyQt5.QtWidgets import QWidget
from ..linkage.linkage_mixin import (
    LapAnalysisLinkageMixin,
    LapAnalysisLinkageDrawingMixin
)

class YourAnalysisChartWidget(QWidget, 
                               LapAnalysisLinkageMixin, 
                               LapAnalysisLinkageDrawingMixin):
    """您的分析圖表組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動功能
        self.__init_linkage__()
        self.set_update_callback(self.update)
        
        # 設置 UI
        self._setup_ui()
    
    def update_your_data(self, data: dict):
        """更新數據並重繪圖表"""
        # 提取數據
        your_data = data.get('your_data', {})
        distance = your_data.get('distance', [])
        driver1_values = your_data.get('driver1_your_type', [])
        driver2_values = your_data.get('driver2_your_type', [])
        
        # 重繪圖表
        self.update()
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        
        # 繪製您的圖表
        self._draw_your_chart(painter)
        
        # 繪製連動線（如果啟用）
        if self.show_linkage_line:
            self.draw_linkage_line(painter, chart_rect, ...)
```

#### 步驟3: 創建 MDI 模組

```python
# modules/gui/lap_analysis/your_analysis/your_analysis_mdi.py

from modules.gui.interfaces.analysis_module import IAnalysisModule

class YourAnalysisModule(IAnalysisModule):
    """您的分析主模組"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_loader = None
        self.chart_widget = None
    
    def initialize_module(self, **kwargs):
        """初始化模組"""
        # 創建數據載入器
        self.data_loader = YourAnalysisDataLoader()
        self.data_loader.data_loaded.connect(self._update_chart)
        
        # 創建圖表組件
        self.chart_widget = YourAnalysisChartWidget()
        
        # 註冊到分析模組管理器
        from ..analysis_module_manager import get_analysis_module_manager
        manager = get_analysis_module_manager()
        manager.register_module(f"your_analysis_{id(self)}", self, "your_analysis")
        manager.register_chart_widget(self.chart_widget)
        
        return True
    
    def update_parameters(self, year, race, session, **kwargs):
        """更新參數"""
        return self.data_loader.load_your_data(
            year, race, session,
            kwargs.get('driver1', 'VER'),
            kwargs.get('driver2', 'LEC'),
            kwargs.get('lap1', 1),
            kwargs.get('lap2', 1)
        )
```

### 8.2 信號連接最佳實踐

```python
# ✅ 正確：使用具名方法
self.data_loader.data_loaded.connect(self._on_data_loaded)

# ✅ 正確：使用 lambda 時保存引用
self.my_timer = QTimer()
self.my_timer.timeout.connect(lambda: self._check_status())

# ❌ 錯誤：直接使用 lambda 可能被垃圾回收
QTimer.singleShot(1000, lambda: self._do_something())  # 可能失效

# ✅ 正確：保存 QTimer 引用
self._delayed_timer = QTimer()
self._delayed_timer.setSingleShot(True)
self._delayed_timer.timeout.connect(self._do_something)
self._delayed_timer.start(1000)
```

### 8.3 除錯輸出規範

```python
# ✅ 統一的除錯格式
def _debug(self, message: str):
    """統一的除錯輸出"""
    prefix = self.config['debug_prefix']  # 例如: 'SPEED'
    print(f"[{prefix} DEBUG] {message}")

# ✅ 階段性輸出
print(f"[SPEED_MDI] ========== 載入速度數據 ==========")
print(f"[SPEED_MDI] 參數: {year} {race} {session}")
print(f"[SPEED_MDI] ========== 載入完成 ==========")

# ✅ 使用表情符號標示狀態
print(f"[SPEED_MDI] ✅ 數據載入成功")
print(f"[SPEED_MDI] ❌ 數據載入失敗")
print(f"[SPEED_MDI] 🔄 重新載入中...")
print(f"[SPEED_MDI] 💡 提示: 請檢查網路連線")
```

---

## 9. 常見問題與解決方案

### 9.1 數據載入問題

#### Q1: 為什麼 data_loaded 信號沒有被接收？

**可能原因**:
1. 信號未正確連接
2. 信號接收者已被垃圾回收
3. 信號發送者和接收者不在同一執行緒

**解決方案**:
```python
# 檢查信號連接
print(f"信號接收者數量: {self.receivers(self.data_loaded)}")

# 確保保存對象引用
self.data_loader = SpeedAnalysisDataLoader()  # 保存引用!
self.data_loader.data_loaded.connect(self._on_data_loaded)

# 檢查執行緒
print(f"Loader執行緒: {self.data_loader.thread()}")
print(f"接收者執行緒: {self.thread()}")
```

#### Q2: API 請求總是超時

**可能原因**:
1. API 服務器未啟動
2. 網路問題
3. 請求參數錯誤

**解決方案**:
```python
# 檢查 API 可用性
def _is_api_available(self) -> bool:
    try:
        health_url = f"{self._api_base_url}/health"
        response = requests.get(health_url, timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

# 設置合適的超時時間
self._api_timeout = 75.0  # 秒

# 啟用除錯輸出
self._debug_enabled = True
```

### 9.2 連動問題

#### Q3: 連動線不顯示

**可能原因**:
1. 未註冊到連動管理器
2. 主開關或個別開關被關閉
3. 繪製邏輯錯誤

**解決方案**:
```python
# 檢查註冊狀態
from ..linkage import linkage_manager
if linkage_manager:
    print(f"已註冊模組數: {len(linkage_manager._registered_modules)}")
    print(f"主開關狀態: {linkage_manager.master_linkage_enabled}")

# 檢查個別開關
print(f"個別連動開關: {self.linkage_enabled}")
print(f"連動完全啟用: {self._is_linkage_fully_enabled()}")

# 檢查連動數據
print(f"連動距離值: {self.linkage_distance_value}")
print(f"顯示連動線: {self.show_linkage_line}")
```

#### Q4: 點擊連動失效

**可能原因**:
1. 滑鼠事件未正確處理
2. 距離計算錯誤
3. 信號未發送

**解決方案**:
```python
def mousePressEvent(self, event):
    """處理滑鼠點擊"""
    if not self._is_linkage_fully_enabled():
        return super().mousePressEvent(event)
    
    # 檢查點擊位置
    print(f"點擊座標: {event.pos()}")
    
    # 計算距離值
    distance_value = self._calculate_distance_from_x(event.x())
    print(f"計算距離: {distance_value}")
    
    # 發送連動信號
    self.send_click_linkage_signal(distance_value, self.click_linkage_signal)
    print(f"已發送點擊連動信號")
```

### 9.3 性能問題

#### Q5: 圖表繪製卡頓

**可能原因**:
1. 數據點過多
2. 重繪頻率過高
3. 繪製邏輯未優化

**解決方案**:
```python
# 數據降採樣
def _downsample_data(self, data, max_points=1000):
    """降低數據密度"""
    if len(data) <= max_points:
        return data
    
    step = len(data) // max_points
    return data[::step]

# 使用緩存
def paintEvent(self, event):
    """繪製事件"""
    # 如果數據未變化，使用緩存的 pixmap
    if not self._data_changed:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)
        return
    
    # 重新繪製並更新緩存
    self._render_to_cache()
    self._data_changed = False

# 限制重繪頻率
def _on_mouse_move(self, event):
    """滑鼠移動事件"""
    # 使用計時器節流
    if not hasattr(self, '_update_timer'):
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.update)
    
    if not self._update_timer.isActive():
        self._update_timer.start(16)  # 約 60 FPS
```

### 9.4 內存洩漏

#### Q6: 模組關閉後內存未釋放

**可能原因**:
1. 信號未正確斷開
2. 計時器未停止
3. 循環引用

**解決方案**:
```python
def cleanup(self):
    """清理資源"""
    # 從連動管理器解除註冊
    if hasattr(self, 'chart_widget'):
        from ..linkage import linkage_manager
        if linkage_manager:
            linkage_manager.unregister_module(self.chart_widget)
    
    # 從分析模組管理器解除註冊
    if hasattr(self, '_analysis_manager'):
        self._analysis_manager.unregister_module(self._module_id)
        self._analysis_manager.unregister_chart_widget(self.chart_widget)
    
    # 停止所有計時器
    if hasattr(self, '_generation_timer'):
        self._generation_timer.stop()
        self._generation_timer.deleteLater()
    
    # 斷開所有信號
    if hasattr(self, 'data_loader'):
        try:
            self.data_loader.data_loaded.disconnect()
            self.data_loader.load_error.disconnect()
        except:
            pass
    
    # 刪除組件
    if hasattr(self, 'chart_widget'):
        self.chart_widget.deleteLater()
    
    print(f"[CLEANUP] 資源清理完成")
```

---

## 總結

Lap Analysis 系統是 F1T 專案中設計最精良的模組之一，展現了以下優秀特性：

### 🎯 設計優勢

1. **高度模組化**: 基於 `TelemetryDataLoader` 基類，8 種遙測類型共享 85% 代碼
2. **API-ONLY 模式**: 嚴格遵守 2025-10-03 政策，杜絕 GUI 直接啟動 CLI
3. **智能連動**: 完善的圖表連動系統，支援 X 軸同步和點擊聯動
4. **自動管理**: 基於模組數量自動調整統計面板顯示
5. **向後兼容**: 新架構完全兼容舊版 API

### 📚 關鍵學習點

- **統一基類模式**: 消除代碼重複的最佳實踐
- **請求去重機制**: 防止重複載入的完整方案
- **信號驅動架構**: PyQt5 信號槽的專業應用
- **混合類設計**: 功能組合的優雅實現
- **資源管理**: 完善的清理和生命週期控制

### 🚀 未來改進方向

1. 數據緩存策略優化（LRU Cache）
2. 更智能的數據降採樣算法
3. WebSocket 實時數據推送
4. 多語言支援完善
5. 性能監控和分析工具

---

**文件版本**: 1.0.0  
**最後更新**: 2025-10-07  
**維護者**: F1T Team  
**授權**: 內部知識文件

