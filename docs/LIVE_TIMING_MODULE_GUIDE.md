# Live Timing 模組完整解說

> **F1T 賽車數據分析系統 - 即時計時架構指南**  
> 版本: 2.0 | 更新日期: 2025-12-18

---

## 📚 目錄

1. [架構概覽](#架構概覽)
2. [核心模組 (Core)](#核心模組-core)
3. [視覺化模組 (Live Timing Modules)](#視覺化模組-live-timing-modules)
4. [工具模組 (Utils)](#工具模組-utils)
5. [UI 組件 (Widgets)](#ui-組件-widgets)
6. [數據流](#數據流)
7. [開發指南](#開發指南)

---

## 架構概覽

### 整體結構

```
modules/gui/live_timing/
├── core/                      # 核心引擎
│   ├── data_manager.py        # 數據管理器 (中央調度)
│   ├── local_source.py        # 本地數據源
│   ├── api_client.py          # API 客戶端
│   ├── realtime_database.py   # 即時數據庫
│   ├── database_reader.py     # 數據庫讀取器
│   ├── f1_api_downloader.py   # F1 API 下載器
│   ├── base_live_mdi.py       # MDI 基類
│   ├── module_factory.py      # 模組工廠
│   ├── position_processor.py  # 位置數據處理器
│   └── global_sync_signal.py  # 全局同步信號
│
├── live_timing_modules/       # 可視化模組 (25+ 個)
│   ├── control_panel.py       # 控制面板
│   ├── control_dock.py        # 控制停靠窗
│   ├── track_map.py           # 賽道地圖
│   ├── circle_map.py          # 圓形地圖
│   ├── ranking_tower.py       # 排名塔
│   ├── pit_window.py          # 進站窗口
│   ├── tyre_strategy.py       # 輪胎策略
│   ├── driver_strategy.py     # 車手策略
│   ├── chase_strategy.py      # 追逐策略 (新)
│   ├── battle_insight.py      # 戰鬥洞察 (新)
│   ├── lap_time_distribution.py  # 圈速分佈
│   ├── race_control_messages.py  # 賽會訊息
│   ├── speed_trace.py         # 速度軌跡
│   ├── throttle_trace.py      # 油門軌跡
│   ├── brake_trace.py         # 剎車軌跡
│   ├── gear_trace.py          # 檔位軌跡
│   ├── drs_trace.py           # DRS 軌跡
│   ├── rpm_trace.py           # 轉速軌跡
│   ├── lap_history.py         # 圈時歷史
│   ├── sector_comparison.py   # 扇區對比
│   └── track_weather.py       # 賽道天氣
│
├── utils/                     # 工具類
│   ├── fuel_saving_detector.py      # 省油偵測
│   └── sector_fuel_saving_detector.py  # 扇區省油偵測
│
└── widgets/                   # UI 組件
    ├── f1tv_auth_dialog.py    # F1TV 認證對話框
    ├── f1tv_web_auth_dialog.py  # F1TV Web 認證
    └── f1tv_webview_auth.py   # F1TV WebView 認證
```

---

## 核心模組 (Core)

### 1. LiveTimingDataManager (`data_manager.py`)

**角色**: 系統的心臟，統一管理所有數據源和模組

#### 主要職責:
1. **數據源管理**: 協調本地 JSON、API 和即時數據庫
2. **模組註冊**: 管理所有視覺化模組的訂閱關係
3. **事件分發**: 將數據更新廣播給訂閱模組
4. **會話管理**: 處理賽事會話的載入/切換

#### 核心方法:

```python
class LiveTimingDataManager(QObject):
    # 信號定義
    data_updated = pyqtSignal(dict)              # 數據更新
    session_loaded = pyqtSignal(dict)            # 會話載入
    playback_position_changed = pyqtSignal(int)  # 回放位置改變
    error_occurred = pyqtSignal(str)             # 錯誤發生
    
    def load_session(self, year, race, session_type):
        """載入賽事會話"""
        
    def start_playback(self):
        """開始回放"""
        
    def pause_playback(self):
        """暫停回放"""
        
    def seek_to_frame(self, frame_index):
        """跳轉到指定幀"""
        
    def register_module(self, module):
        """註冊視覺化模組"""
        
    def unregister_module(self, module):
        """取消註冊模組"""
```

#### 數據流轉:
```
載入會話 → 選擇數據源 → 數據解析 → 廣播更新
   ↓
[本地 JSON] → LocalLiveF1DataSource
[API 請求] → LiveTimingAPIClient
[即時數據] → RealtimeDatabase
   ↓
註冊模組接收 data_updated 信號
```

---

### 2. LocalLiveF1DataSource (`local_source.py`)

**角色**: 本地 JSON 檔案數據源

#### 功能:
- 讀取 `Live_timing_test/` 目錄的 JSON 檔案
- 支援回放模式 (逐幀播放)
- 支援跳轉 (Seek)

#### 數據格式:
```json
{
  "timestamp": "2024-03-24T14:30:00.000Z",
  "Position.z": {
    "1": {"X": 1234, "Y": 5678, "Z": 100},
    "44": {"X": 2345, "Y": 6789, "Z": 105}
  },
  "TimingData": {
    "Lines": {
      "1": {
        "RacingNumber": "1",
        "Position": "1",
        "GapToLeader": "+0.000",
        "IntervalToPositionAhead": {
          "Value": "+0.000"
        }
      }
    }
  }
}
```

#### 核心方法:
```python
class LocalLiveF1DataSource:
    def load_json_file(self, file_path):
        """載入單個 JSON 檔案"""
        
    def get_frame_at(self, index):
        """獲取指定索引的幀"""
        
    def get_total_frames(self):
        """獲取總幀數"""
```

---

### 3. LiveTimingAPIClient (`api_client.py`)

**角色**: 連接外部 API 獲取歷史數據

#### 功能:
- 連接 `https://api.f1telemetrystationpro.org`
- 支援緩存機制
- 異步請求處理

#### 端點:
```python
GET /live_timing/sessions       # 獲取會話列表
GET /live_timing/data/{year}/{race}/{session}  # 獲取賽事數據
```

---

### 4. RealtimeDatabase (`realtime_database.py`)

**角色**: SQLite 即時數據庫 (用於直播場景)

#### 功能:
- 即時寫入 F1 直播數據
- 支援多表索引查詢
- 自動清理舊數據

#### 表結構:
```sql
-- 位置數據
CREATE TABLE position_data (
    timestamp TEXT,
    driver_number TEXT,
    x REAL,
    y REAL,
    z REAL
);

-- 計時數據
CREATE TABLE timing_data (
    timestamp TEXT,
    driver_number TEXT,
    position INTEGER,
    gap_to_leader TEXT,
    last_lap_time TEXT
);

-- 輪胎數據
CREATE TABLE tyre_data (
    timestamp TEXT,
    driver_number TEXT,
    compound TEXT,
    age INTEGER
);
```

---

### 5. BaseLiveTimingMDI (`base_live_mdi.py`)

**角色**: 所有 Live Timing 模組的基類

#### 核心功能:
1. **自動註冊**: 創建時自動向 DataManager 註冊
2. **數據接收**: 實現 `on_data_update()` 接收數據
3. **會話同步**: 響應會話載入事件
4. **資源清理**: 關閉時自動取消註冊

#### 子類必須實現:
```python
class YourModule(BaseLiveTimingMDI):
    def on_data_update(self, data: dict):
        """處理數據更新"""
        # 解析 data
        # 更新 UI
        
    def on_session_loaded(self, session_info: dict):
        """會話載入回調"""
        # 初始化賽道信息
        # 重置狀態
```

---

### 6. LiveTimingModuleFactory (`module_factory.py`)

**角色**: 模組工廠，統一管理所有 Live Timing 模組

#### 模組註冊表:
```python
MODULE_REGISTRY = {
    # 視覺化模組
    "Track Map": "track_map",
    "Circle Map": "circle_map",
    "Live Ranking": "ranking_tower",
    "Pit Window": "pit_window",
    "Tyre Strategy": "tyre_strategy",
    "Driver Strategy": "driver_strategy",
    
    # 戰鬥分析
    "Battle Insight": "battle_insight",
    "Chase Strategy": "chase_strategy",
    
    # 遙測軌跡
    "Speed Trace": "speed_trace",
    "Throttle Trace": "throttle_trace",
    "Brake Trace": "brake_trace",
    "Gear Trace": "gear_trace",
    "DRS Trace": "drs_trace",
    "RPM Trace": "rpm_trace",
    
    # 圈時分析
    "Lap Time Distribution": "lap_time_distribution",
    "Lap History - Lap Time": "lap_history_lap_time",
    "Lap History - S1": "lap_history_s1",
    "Lap History - S2": "lap_history_s2",
    "Lap History - S3": "lap_history_s3",
    
    # 扇區對比
    "Sector Comparison - S1": "sector_comparison_s1",
    "Sector Comparison - S2": "sector_comparison_s2",
    "Sector Comparison - S3": "sector_comparison_s3",
    
    # 其他
    "Race Control Messages": "race_control_messages",
    "Track Weather": "track_weather",
}
```

#### 使用方式:
```python
factory = LiveTimingModuleFactory.get_instance()
module = factory.create_module("Track Map", parent_widget)
```

---

### 7. F1APIDownloader (`f1_api_downloader.py`)

**角色**: 下載 F1 官方 API 數據

#### 功能:
- 使用 FastF1 庫獲取歷史數據
- 自動緩存到 `f1_analysis_cache/`
- 支援遙測數據下載

#### 使用範例:
```python
from modules.gui.live_timing.core import download_race_data

data = download_race_data(
    year=2024,
    race="Japan",
    session="R"  # R=Race, Q=Qualifying, FP1/2/3=Practice
)
```

---

### 8. DatabaseReader (`database_reader.py`)

**角色**: 從即時數據庫讀取數據

#### 功能:
- 高效查詢 SQLite 數據庫
- 支援時間範圍過濾
- 緩存查詢結果

---

### 9. GlobalSyncSignal (`global_sync_signal.py`)

**角色**: 全局事件總線

#### 信號:
```python
class GlobalSyncSignal(QObject):
    # 回放控制
    playback_started = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_stopped = pyqtSignal()
    
    # 時間同步
    time_synced = pyqtSignal(str)  # timestamp
    
    # 車手選擇
    driver_selected = pyqtSignal(str)  # driver_number
```

---

## 視覺化模組 (Live Timing Modules)

### 1. Control Panel (`control_panel.py`)

**角色**: 主控制面板，管理播放/暫停/跳轉

#### UI 組件:
- 播放/暫停按鈕
- 進度條 (可拖動跳轉)
- 速度控制 (0.5x ~ 4x)
- 會話選擇器

#### 功能:
```python
class LiveTimingControlPanel(BaseLiveTimingMDI):
    def on_play_clicked(self):
        """播放"""
        
    def on_pause_clicked(self):
        """暫停"""
        
    def on_seek_slider_changed(self, value):
        """跳轉"""
        
    def on_speed_changed(self, speed):
        """調整速度"""
```

---

### 2. Track Map (`track_map.py`)

**角色**: 2D 賽道地圖，顯示車輛實時位置

#### 功能:
- 顯示所有車輛位置 (基於 X/Y 坐標)
- 顏色編碼 (車隊顏色)
- 實時軌跡繪製
- 點擊車輛顯示詳情

#### 數據需求:
```python
data["Position.z"] = {
    "1": {"X": 1234, "Y": 5678, "Z": 100},
    "44": {"X": 2345, "Y": 6789, "Z": 105}
}
```

#### Widget:
```python
class TrackMapWidget(QWidget):
    def paintEvent(self, event):
        # 繪製賽道輪廓
        # 繪製車輛位置
        # 繪製軌跡
```

---

### 3. Circle Map (`circle_map.py`)

**角色**: 環形賽道地圖，顯示車輛相對位置

#### 功能:
- 以領先車為 12 點鐘方向
- 其他車輛按圈數百分比排列
- 顯示間隔差距

#### 計算邏輯:
```python
angle = (lap_distance / track_length) * 360°
```

---

### 4. Ranking Tower (`ranking_tower.py`)

**角色**: 實時排名塔

#### 功能:
- 顯示當前排名
- 與領先車差距
- 與前車間隔
- 最後圈速
- 輪胎信息 (配方 + 年齡)

#### 表格列:
| Pos | # | Driver | Team | Gap | Int | Last Lap | Tyre |
|-----|---|--------|------|-----|-----|----------|------|
| 1 | 1 | VER | Red Bull | Leader | - | 1:32.123 | M-15 |
| 2 | 44 | HAM | Mercedes | +2.345 | +2.345 | 1:32.456 | M-15 |

---

### 5. Pit Window (`pit_window.py`)

**角色**: 進站窗口分析

#### 功能:
- 顯示每位車手的進站次數
- 預測最佳進站時機
- 顯示進站損失時間

#### 邏輯:
```python
# 計算進站窗口
undercut_window = current_lap + 2 to current_lap + 5
overcut_window = current_lap + 6 to current_lap + 10

# 考慮因素:
# - 輪胎衰退
# - 交通狀況
# - Safety Car 機率
```

---

### 6. Tyre Strategy (`tyre_strategy.py`)

**角色**: 輪胎策略視覺化

#### 功能:
- 顯示每位車手的配方選擇
- 輪胎年齡條
- 預測輪胎壽命

#### UI:
```
VER  [SSSSSSSSSSSS][MMMMMMMMMMMMMMMMMMMM][HHHHHHHHHHHHHHHHHH]
     Lap 1-12      Lap 13-33             Lap 34-53
     
HAM  [MMMMMMMMMMMMMMMM][HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH]
     Lap 1-17          Lap 18-53
```

---

### 7. Driver Strategy (`driver_strategy.py`)

**角色**: 車手策略對比

#### 功能:
- 選擇兩位車手
- 對比圈速曲線
- 對比輪胎策略
- 預測結果

---

### 8. Chase Strategy (`chase_strategy.py`) ⭐ **新功能**

**角色**: 追逐策略分析器

#### 功能:
- **實時間隔追蹤**: 監控追逐車手與前車的間隔變化
- **超車預測**: 基於速度差和DRS可用性預測超車時機
- **策略建議**: 提供進站策略建議（Undercut/Overcut）
- **輪胎性能對比**: 對比雙方輪胎年齡和性能差異

#### 核心算法:
```python
# 超車預測模型
def predict_overtake(gap, speed_diff, drs_available, laps_remaining):
    # 計算追趕率
    closing_rate = speed_diff * lap_time
    
    # 考慮 DRS 加成
    if drs_available:
        closing_rate *= 1.3  # DRS 約增加 30% 速度
    
    # 計算剩餘圈數需求
    laps_to_overtake = gap / closing_rate
    
    # 返回預測
    return {
        'possible': laps_to_overtake <= laps_remaining,
        'estimated_lap': current_lap + laps_to_overtake,
        'confidence': calculate_confidence(...)
    }
```

#### UI 組件:
```
┌─────────────────────────────────────┐
│ Chase Strategy Analysis             │
├─────────────────────────────────────┤
│ Chaser:  VER (P2) → Target: LEC (P1)│
│                                     │
│ Current Gap: 2.345s ▼ -0.123s/lap  │
│ Speed Diff: +0.234s/lap             │
│ DRS: Available ✓                    │
│                                     │
│ Prediction:                         │
│ ┌─────────────────────────────┐   │
│ │ Overtake at Lap 42          │   │
│ │ Confidence: 78%             │   │
│ │ Strategy: Keep pushing      │   │
│ └─────────────────────────────┘   │
│                                     │
│ [Gap Evolution Chart]               │
└─────────────────────────────────────┘
```

---

### 9. Battle Insight (`battle_insight.py`) ⭐ **新功能**

**角色**: 戰鬥洞察分析器

#### 功能:
- **近距離戰鬥偵測**: 自動識別間隔 < 1.5s 的車手對
- **超車記錄**: 記錄所有超車事件和位置
- **戰鬥熱度**: 評估戰鬥激烈程度
- **扇區優勢分析**: 對比車手在各扇區的優勢

#### 核心邏輯:
```python
# 戰鬥偵測
def detect_battles(timing_data):
    battles = []
    for driver in drivers:
        interval = get_interval_to_ahead(driver)
        if interval < 1.5:  # 1.5秒內視為戰鬥
            battles.append({
                'ahead': get_driver_ahead(driver),
                'behind': driver,
                'gap': interval,
                'intensity': calculate_intensity(...)
            })
    return battles

# 戰鬥熱度計算
def calculate_intensity(gap_history):
    # 間隔變化越大 = 越激烈
    gap_variance = np.var(gap_history)
    
    # DRS 使用頻率
    drs_usage = count_drs_activations()
    
    # 位置交換次數
    position_swaps = count_position_changes()
    
    intensity = (gap_variance * 0.4 +
                 drs_usage * 0.3 +
                 position_swaps * 0.3)
    
    return min(intensity, 100)  # 0-100 分
```

#### UI 顯示:
```
┌─────────────────────────────────────┐
│ Battle Insight                      │
├─────────────────────────────────────┤
│ Active Battles (3)                  │
│                                     │
│ ⚔️ P1 vs P2: VER vs LEC            │
│ Gap: 0.834s | Heat: ████████ 89%   │
│ DRS: 12/15 zones | Swaps: 4        │
│                                     │
│ ⚔️ P5 vs P6: NOR vs PIA            │
│ Gap: 1.234s | Heat: ██████ 67%     │
│ DRS: 8/15 zones | Swaps: 2         │
│                                     │
│ Overtakes (5)                       │
│ Lap 12: HAM → VER (T1)              │
│ Lap 18: NOR → SAI (T14)             │
│ Lap 23: VER → HAM (T1) ⚡ DRS      │
└─────────────────────────────────────┘
```

---

### 10. Lap Time Distribution (`lap_time_distribution.py`)

**角色**: 圈速分佈直方圖

#### 功能:
- 顯示所有車手的圈速分佈
- 過濾 Safety Car 圈
- 對比中位數/平均值

---

### 11. Speed Trace (`speed_trace.py`)

**角色**: 速度軌跡圖

#### 功能:
- 顯示車輛在賽道上的速度變化
- 疊加多位車手對比
- 標記剎車點/加速點

---

### 12. Throttle/Brake/Gear Trace (`throttle_trace.py`, `brake_trace.py`, `gear_trace.py`)

**角色**: 遙測軌跡圖 (油門/剎車/檔位)

#### 功能:
- 顯示遙測數據隨賽道距離變化
- 支援多車手疊加
- 同步顯示 (鎖定賽道位置)

---

### 13. Lap History (`lap_history.py`)

**角色**: 圈時歷史曲線

#### 變體:
- **Lap Time**: 完整圈時
- **S1**: 第一扇區時間
- **S2**: 第二扇區時間
- **S3**: 第三扇區時間

#### 功能:
- 顯示每圈時間變化
- 標記進站圈
- 標記最快圈

---

### 14. Sector Comparison (`sector_comparison.py`)

**角色**: 扇區時間對比

#### 功能:
- 選擇兩位車手
- 對比 S1/S2/S3 時間
- 顯示優勢/劣勢

---

### 15. Race Control Messages (`race_control_messages.py`)

**角色**: 賽會訊息列表

#### 功能:
- 顯示所有 Race Control 訊息
- 過濾類型 (Flag/Penalty/Investigation)
- 時間戳排序

---

### 16. Track Weather (`track_weather.py`)

**角色**: 賽道天氣監控

#### 功能:
- 顯示賽道溫度
- 空氣溫度
- 濕度
- 降雨機率

---

## 工具模組 (Utils)

### 1. FuelSavingDetector (`fuel_saving_detector.py`)

**角色**: 省油模式偵測器

#### 功能:
- 偵測車手是否在省油 (降低油門)
- 基於速度差異分析

#### 算法:
```python
def detect_fuel_saving(current_speed, reference_speed):
    speed_diff = reference_speed - current_speed
    if speed_diff > 5:  # 速度慢於參考值 5 km/h
        return True
    return False
```

---

### 2. SectorFuelSavingDetector (`sector_fuel_saving_detector.py`)

**角色**: 扇區省油偵測器

#### 功能:
- 分析每個扇區的省油行為
- 識別哪些彎角在省油

---

## UI 組件 (Widgets)

### 1. F1TV Auth Dialog (`f1tv_auth_dialog.py`)

**角色**: F1TV 登入對話框

#### 功能:
- 輸入 F1TV 帳號密碼
- 獲取認證 Token
- 保存 Session

---

### 2. F1TV Web Auth (`f1tv_web_auth_dialog.py`)

**角色**: F1TV Web 認證

#### 功能:
- 使用 WebView 進行 OAuth 認證
- 自動捕獲 Token

---

## 數據流

### 完整數據流程圖

```
[數據源]
   ↓
┌─────────────────────────────────────┐
│ LocalLiveF1DataSource               │  ← 本地 JSON
│ LiveTimingAPIClient                 │  ← 外部 API
│ RealtimeDatabase                    │  ← 即時數據庫
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ LiveTimingDataManager               │  ← 中央調度器
│ - 解析數據                          │
│ - 處理事件                          │
│ - 廣播更新                          │
└─────────────────────────────────────┘
   ↓ (data_updated 信號)
┌─────────────────────────────────────┐
│ 已註冊的視覺化模組                  │
│ ├─ TrackMap                         │
│ ├─ RankingTower                     │
│ ├─ PitWindow                        │
│ ├─ TyreStrategy                     │
│ ├─ ChaseStrategy ⭐                 │
│ ├─ BattleInsight ⭐                 │
│ └─ ... (其他模組)                   │
└─────────────────────────────────────┘
   ↓
[UI 更新]
```

---

## 開發指南

### 如何新增 Live Timing 模組

#### 步驟 1: 創建模組文件

```python
# modules/gui/live_timing/live_timing_modules/your_module.py

from ..core.base_live_mdi import BaseLiveTimingMDI
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class YourModuleMDI(BaseLiveTimingMDI):
    """您的模組說明"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Your Module")
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        self.label = QLabel("Your Module Content")
        layout.addWidget(self.label)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setWidget(widget)
    
    def on_data_update(self, data: dict):
        """處理數據更新 (必須實現)"""
        # 解析 data
        position_data = data.get("Position.z", {})
        timing_data = data.get("TimingData", {})
        
        # 更新 UI
        self.label.setText(f"Received data: {len(position_data)} cars")
    
    def on_session_loaded(self, session_info: dict):
        """會話載入回調 (可選)"""
        year = session_info.get("year")
        race = session_info.get("race")
        self.label.setText(f"Loaded: {year} {race}")
```

#### 步驟 2: 註冊到工廠

```python
# modules/gui/live_timing/core/module_factory.py

class LiveTimingModuleFactory:
    MODULE_REGISTRY = {
        # ... 現有模組
        
        # 新增您的模組
        "Your Module": "your_module",
        "你的模組": "your_module",  # 支援中文
    }
    
    def _import_module_class(self, module_key: str):
        # ... 現有代碼
        
        elif module_key == "your_module":
            from ..live_timing_modules.your_module import YourModuleMDI
            module_class = YourModuleMDI
```

#### 步驟 3: 添加到選單

```python
# windows/managers/live_timing_manager.py

class LiveTimingManager:
    def setup_menu(self, live_timing_menu: QMenu):
        # ... 現有代碼
        
        # 添加您的模組
        self._add_module_action(live_timing_menu, 'your_module')
```

#### 步驟 4: 測試

```python
# 在主視窗打開 Live Timing → Your Module
```

---

### 數據結構參考

#### Position.z 數據
```json
{
  "Position.z": {
    "1": {"X": 1234.56, "Y": 5678.90, "Z": 100.0},
    "44": {"X": 2345.67, "Y": 6789.01, "Z": 105.0}
  }
}
```

#### TimingData 數據
```json
{
  "TimingData": {
    "Lines": {
      "1": {
        "RacingNumber": "1",
        "Position": "1",
        "GapToLeader": "+0.000",
        "IntervalToPositionAhead": {"Value": "+0.000"},
        "LastLapTime": {"Value": "1:32.123"},
        "Sectors": [
          {"Value": "28.123"},
          {"Value": "35.456"},
          {"Value": "28.544"}
        ]
      }
    }
  }
}
```

#### CarData.z 數據
```json
{
  "CarData.z": {
    "1": {
      "Speed": 285,
      "Throttle": 100,
      "Brake": 0,
      "Gear": 8,
      "RPM": 11500,
      "DRS": 12
    }
  }
}
```

---

### 最佳實踐

#### 1. 性能優化
```python
# ✅ 正確: 批量更新 UI
def on_data_update(self, data: dict):
    self.setUpdatesEnabled(False)  # 暫停 UI 更新
    
    # 更新所有組件
    self._update_positions(data)
    self._update_timing(data)
    self._update_tyres(data)
    
    self.setUpdatesEnabled(True)  # 恢復 UI 更新
    self.update()  # 單次重繪

# ❌ 錯誤: 多次觸發重繪
def on_data_update(self, data: dict):
    self.label1.setText("...")  # 觸發重繪
    self.label2.setText("...")  # 觸發重繪
    self.label3.setText("...")  # 觸發重繪
```

#### 2. 記憶體管理
```python
# ✅ 正確: 限制歷史數據
class YourModule(BaseLiveTimingMDI):
    def __init__(self):
        super().__init__()
        self.history = []  # 歷史數據
        self.max_history = 1000  # 限制長度
    
    def on_data_update(self, data):
        self.history.append(data)
        
        # 清理舊數據
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
```

#### 3. 錯誤處理
```python
# ✅ 正確: 優雅處理缺失數據
def on_data_update(self, data: dict):
    try:
        position_data = data.get("Position.z", {})
        if not position_data:
            self._show_no_data_message()
            return
        
        # 處理數據...
        
    except Exception as e:
        self._logger.error(f"Error updating data: {e}")
        self._show_error_message(str(e))
```

---

### 常見問題 (FAQ)

#### Q1: 如何獲取當前會話信息？
```python
session_info = self.data_manager.get_session_info()
year = session_info.get("year")
race = session_info.get("race")
session_type = session_info.get("session_type")
```

#### Q2: 如何手動觸發數據更新？
```python
# 在 DataManager 中
self.data_manager.refresh_data()
```

#### Q3: 如何添加自定義信號？
```python
class YourModule(BaseLiveTimingMDI):
    # 定義自定義信號
    custom_event = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        # 連接信號
        self.custom_event.connect(self._on_custom_event)
    
    def _on_custom_event(self, data):
        # 處理自定義事件
        pass
```

#### Q4: 如何與其他模組通信？
```python
# 使用 GlobalSyncSignal
from modules.gui.live_timing.core import GlobalSyncSignal

signal_bus = GlobalSyncSignal.get_instance()
signal_bus.driver_selected.emit("1")  # 廣播車手選擇

# 在其他模組中監聽
signal_bus.driver_selected.connect(self._on_driver_selected)
```

---

## 總結

Live Timing 系統是 F1T 的核心功能之一，採用**模組化**設計：

1. **核心層** (`core/`): 提供數據管理、數據源、基類等基礎設施
2. **模組層** (`live_timing_modules/`): 25+ 個可視化模組，各司其職
3. **工具層** (`utils/`): 提供輔助功能 (省油偵測等)
4. **UI層** (`widgets/`): 提供認證對話框等 UI 組件

所有模組通過 `LiveTimingDataManager` 統一協調，使用信號/槽機制進行通信，確保**鬆耦合**和**可擴展性**。

---

**維護者**: F1T 開發團隊  
**最後更新**: 2025-12-18  
**版本**: 2.0
