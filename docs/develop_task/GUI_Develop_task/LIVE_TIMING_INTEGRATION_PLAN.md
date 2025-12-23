# Live Timing 模組整合計畫

> **目標**：將 `demo_live_position_tracking.py` (8,761 行) 拆分為模組化結構，完全整合到主 GUI (`f1t_gui_main.py`)
> 
> **建立日期**：2025-12-03
> **最後更新**：2025-12-04
> **狀態**：進行中 (Phase 3 完成)

---

## 1. 現狀分析

### 1.1 Demo Live 結構 (22 個類別)

| 類型 | 類別 | 行數範圍 | 說明 |
|------|------|----------|------|
| **數據源** | `F1SignalRClient` | 88-571 | F1 官方 SignalR 客戶端 |
| | `RealTimeLiveF1Worker` | 572-677 | 即時數據工作執行緒 |
| | `RealTimeLiveF1DataSource` | 678-1150 | 即時數據源管理 |
| | `LocalLiveF1DataSource` | 1151-1309 | 本地 JSON 歷史數據源 |
| | `LiveF1DataSource` | 1310-1557 | 通用數據源介面 |
| **數據處理** | `LivePositionDataProcessor` | 1558-2426 | 位置數據處理器 |
| | `PitLossConfigLoader` | 4465-4610 | Pit Loss 設定載入器 |
| **可視化 Widget** | `TrackMapWidget` | 2427-3329 | 賽道地圖 |
| | `CircleMapWidget` | 3330-3743 | 圓形賽道地圖 |
| | `LapTimeDistributionWidget` | 3744-4087 | 圈速分佈圖 |
| | `TyreStrategyWidget` | 4088-4178 | 輪胎策略 (舊版) |
| | `TyreStrategyChartWidget` | 4179-4393 | 輪胎策略圖表 |
| | `TyreStrategyChartDialog` | 4394-4464 | 輪胎策略對話框 |
| | `PitWindowWidget` | 4611-5105 | Pit Window 進站策略 |
| | `RaceInfoWidget` | 5106-5197 | 賽事資訊面板 |
| | `RaceControlMessagesWidget` | 5198-5351 | 比賽控制訊息 |
| | `SHAPExplanationWidget` | 5352-5557 | SHAP 勝率分析 |
| | `RaceInsightsWidget` | 5558-5961 | 賽況提示 |
| | `PitStopTableWidget` | 5962-6213 | 進站統計表 |
| | `LiveRankingTableWidget` | 6214-6779 | 即時排名表 |
| | `TimelineControlWidget` | 6780-7013 | 時間軸控制器 |
| **主窗口** | `LivePositionTrackingMainWindow` | 7014-8761 | 整合所有組件 |

### 1.2 主 GUI 架構

- **MDI (Multi-Document Interface)** 多文檔介面
- **模組化設計**：每個分析功能在 `modules/gui/` 下有獨立資料夾
- **Dock Widget**：可停靠的輔助面板
- **國際化**：使用 `tr()` 函數

---

## 2. 整合架構設計

### 2.1 目標架構

```
主 GUI (MDI Area)
    │
    ├── 📡 Live Timing 控制面板 (Dock Widget - 底部)
    │       ├── 數據源管理 (即時/歷史切換)
    │       ├── 賽事選擇器 (年份/賽事)
    │       ├── 時間軸控制 (歷史模式)
    │       ├── 播放控制 (播放/暫停/速度)
    │       └── 連線狀態指示
    │
    └── MDI 子視窗 (可自由排列、縮放、關閉)
            ├── 🗺️ 賽道地圖視窗
            ├── ⭕ 圓形地圖視窗
            ├── 📊 即時排名視窗
            ├── 🔧 Pit Window 視窗
            ├── 🛞 輪胎策略視窗
            ├── 📢 比賽控制訊息視窗
            ├── 💡 賽況提示視窗
            ├── 📈 SHAP 分析視窗
            └── ⏱️ 圈速分佈視窗
```

### 2.2 數據共享機制

使用 **單例 `LiveTimingDataManager`** 作為數據中心：

```python
class LiveTimingDataManager(QObject):
    """Live Timing 數據管理器 (單例)
    
    職責:
    1. 管理數據源 (即時/歷史)
    2. 處理快照數據
    3. 廣播更新到所有訂閱的 Widget
    4. 維護當前賽事狀態
    """
    
    # === 信號定義 ===
    snapshot_updated = pyqtSignal(dict)           # 當前快照更新
    race_loaded = pyqtSignal(dict)                # 賽事載入完成
    race_unloaded = pyqtSignal()                  # 賽事卸載
    connection_status_changed = pyqtSignal(str)   # 連線狀態變更
    playback_state_changed = pyqtSignal(str)      # 播放狀態 (playing/paused/stopped)
    time_changed = pyqtSignal(float)              # 當前時間變更 (秒)
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'LiveTimingDataManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### 2.3 Widget 訂閱模式

每個 Widget 訂閱 `LiveTimingDataManager` 的信號：

```python
class TrackMapMDI(QMdiSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("賽道地圖"))
        
        # 創建內部 Widget
        self.track_map = TrackMapWidget()
        self.setWidget(self.track_map)
        
        # 訂閱數據管理器
        self.data_manager = LiveTimingDataManager.get_instance()
        self.data_manager.snapshot_updated.connect(self._on_snapshot_updated)
        self.data_manager.race_loaded.connect(self._on_race_loaded)
        self.data_manager.race_unloaded.connect(self._on_race_unloaded)
    
    def _on_snapshot_updated(self, snapshot: dict):
        self.track_map.update_driver_positions(snapshot.get('drivers', {}))
    
    def _on_race_loaded(self, race_info: dict):
        if track_data := race_info.get('track_data'):
            self.track_map.load_track_outline(track_data)
    
    def _on_race_unloaded(self):
        self.track_map.clear()
```

---

## 3. 檔案結構規劃

### 3.1 新架構設計原則

採用 **兩層架構**：
- **`core/`** - 核心數據層（數據源、處理器、共享管理器）
- **`live_timing_modules/`** - 各功能模組（每個模組包含自己的 Widget + MDI）

這種設計的優點：
1. **高內聚**：每個功能模組的 Widget 和 MDI 放在一起，便於維護
2. **低耦合**：模組間通過 `LiveTimingDataManager` 通訊，無直接依賴
3. **易擴展**：新增模組只需在 `live_timing_modules/` 下創建新資料夾

### 3.2 目錄結構

```
modules/gui/live_timing/
├── __init__.py                     # 模組總入口
│
├── core/                           # 核心數據層 ⭐
│   ├── __init__.py
│   ├── data_manager.py             # 單例數據管理器 (LiveTimingDataManager)
│   ├── signalr_client.py           # F1 官方 SignalR 客戶端
│   ├── realtime_source.py          # 即時數據源 (RealTimeLiveF1DataSource)
│   ├── local_source.py             # 本地歷史數據源 (LocalLiveF1DataSource)
│   ├── position_processor.py       # 位置數據處理器 (LivePositionDataProcessor)
│   ├── pit_loss_config.py          # Pit Loss 設定載入器 (PitLossConfigLoader)
│   └── base_live_mdi.py            # Live Timing MDI 基類 (BaseLiveTimingMDI)
│
└── live_timing_modules/            # 功能模組區 ⭐
    ├── __init__.py
    │
    ├── track_map/                  # 賽道地圖模組
    │   ├── __init__.py
    │   ├── track_map_widget.py     # 賽道地圖 Widget (~900 行)
    │   └── track_map_mdi.py        # 賽道地圖 MDI 包裝
    │
    ├── circle_map/                 # 圓形地圖模組
    │   ├── __init__.py
    │   ├── circle_map_widget.py    # 圓形地圖 Widget (~400 行)
    │   └── circle_map_mdi.py       # 圓形地圖 MDI 包裝
    │
    ├── ranking_table/              # 即時排名模組
    │   ├── __init__.py
    │   ├── ranking_widget.py       # 即時排名表 Widget (~560 行)
    │   └── ranking_mdi.py          # 即時排名 MDI 包裝
    │
    ├── pit_window/                 # Pit Window 模組
    │   ├── __init__.py
    │   ├── pit_window_widget.py    # Pit Window Widget (~500 行)
    │   └── pit_window_mdi.py       # Pit Window MDI 包裝
    │
    ├── tyre_strategy/              # 輪胎策略模組
    │   ├── __init__.py
    │   ├── tyre_strategy_widget.py # 輪胎策略圖 Widget (~300 行)
    │   ├── tyre_chart_widget.py    # 輪胎圖表 Widget
    │   └── tyre_strategy_mdi.py    # 輪胎策略 MDI 包裝
    │
    ├── race_control/               # 比賽控制訊息模組
    │   ├── __init__.py
    │   ├── race_control_widget.py  # 比賽控制訊息 Widget (~150 行)
    │   └── race_control_mdi.py     # 比賽控制 MDI 包裝
    │
    ├── race_insights/              # 賽況提示模組
    │   ├── __init__.py
    │   ├── race_insights_widget.py # 賽況提示 Widget (~400 行)
    │   └── race_insights_mdi.py    # 賽況提示 MDI 包裝
    │
    ├── race_info/                  # 賽事資訊模組
    │   ├── __init__.py
    │   ├── race_info_widget.py     # 賽事資訊面板 Widget (~90 行)
    │   └── race_info_mdi.py        # 賽事資訊 MDI 包裝
    │
    ├── shap_analysis/              # SHAP 勝率分析模組
    │   ├── __init__.py
    │   ├── shap_widget.py          # SHAP 分析 Widget (~200 行)
    │   └── shap_mdi.py             # SHAP MDI 包裝
    │
    ├── lap_distribution/           # 圈速分佈模組
    │   ├── __init__.py
    │   ├── lap_distribution_widget.py  # 圈速分佈 Widget (~340 行)
    │   └── lap_distribution_mdi.py     # 圈速分佈 MDI 包裝
    │
    ├── pit_stop_table/             # 進站統計模組
    │   ├── __init__.py
    │   ├── pit_stop_widget.py      # 進站統計表 Widget (~250 行)
    │   └── pit_stop_mdi.py         # 進站統計 MDI 包裝
    │
    ├── timeline_control/           # 時間軸控制模組
    │   ├── __init__.py
    │   ├── timeline_widget.py      # 時間軸控制 Widget (~230 行)
    │   └── timeline_mdi.py         # 時間軸 MDI 包裝 (或作為 Dock)
    │
    └── control_panel/              # 控制面板模組 (Dock Widget)
        ├── __init__.py
        ├── live_timing_dock.py     # 主 Dock Widget
        ├── source_selector.py      # 數據源選擇器組件
        ├── race_selector.py        # 賽事選擇器組件
        ├── playback_controls.py    # 播放控制組件
        └── connection_status.py    # 連線狀態組件
```

### 3.3 模組與原始類別對應表

| 模組資料夾 | 原始類別 | 行數 | 說明 |
|-----------|---------|------|------|
| `core/data_manager.py` | 新建 | ~200 | 單例數據管理器 |
| `core/signalr_client.py` | `F1SignalRClient` | 88-571 | F1 SignalR 客戶端 |
| `core/realtime_source.py` | `RealTimeLiveF1Worker` + `RealTimeLiveF1DataSource` | 572-1150 | 即時數據源 |
| `core/local_source.py` | `LocalLiveF1DataSource` + `LiveF1DataSource` | 1151-1557 | 本地/通用數據源 |
| `core/position_processor.py` | `LivePositionDataProcessor` | 1558-2426 | 位置處理器 |
| `core/pit_loss_config.py` | `PitLossConfigLoader` | 4465-4610 | Pit Loss 設定 |
| `core/base_live_mdi.py` | 新建 | ~150 | MDI 基類 |
| `track_map/` | `TrackMapWidget` | 2427-3329 | 賽道地圖 |
| `circle_map/` | `CircleMapWidget` | 3330-3743 | 圓形地圖 |
| `ranking_table/` | `LiveRankingTableWidget` | 6214-6779 | 即時排名 |
| `pit_window/` | `PitWindowWidget` | 4611-5105 | Pit Window |
| `tyre_strategy/` | `TyreStrategyWidget` + `TyreStrategyChartWidget` | 4088-4464 | 輪胎策略 |
| `race_control/` | `RaceControlMessagesWidget` | 5198-5351 | 比賽控制 |
| `race_insights/` | `RaceInsightsWidget` | 5558-5961 | 賽況提示 |
| `race_info/` | `RaceInfoWidget` | 5106-5197 | 賽事資訊 |
| `shap_analysis/` | `SHAPExplanationWidget` | 5352-5557 | SHAP 分析 |
| `lap_distribution/` | `LapTimeDistributionWidget` | 3744-4087 | 圈速分佈 |
| `pit_stop_table/` | `PitStopTableWidget` | 5962-6213 | 進站統計 |
| `timeline_control/` | `TimelineControlWidget` | 6780-7013 | 時間軸控制 |
| `control_panel/` | 從 `LivePositionTrackingMainWindow` 拆分 | - | 控制面板 |

---

## 4. 主 GUI 整合點

### 4.1 選單結構

```
選單列
├── 檔案 (F)
├── 分析 (A)
├── Live Timing (L)                 # 新增
│   ├── 顯示控制面板
│   ├── ─────────────
│   ├── 賽道地圖
│   ├── 圓形地圖
│   ├── 即時排名
│   ├── Pit Window
│   ├── 輪胎策略
│   ├── 比賽控制訊息
│   ├── 賽況提示
│   ├── SHAP 分析
│   ├── 圈速分佈
│   ├── 進站統計
│   ├── ─────────────
│   ├── 預設佈局
│   │   ├── 完整佈局 (所有視窗)
│   │   ├── 精簡佈局 (排名+地圖+Pit)
│   │   └── 策略佈局 (Pit+輪胎+賽況)
│   └── 關閉所有 Live Timing 視窗
├── 視窗 (W)
└── 說明 (H)
```

### 4.2 Dock Widget 整合

```python
# f1t_gui_main.py

def _setup_live_timing(self):
    """設置 Live Timing 模組"""
    from modules.gui.live_timing.live_timing_modules.control_panel import LiveTimingDock
    
    # 創建控制面板 Dock
    self.live_timing_dock = LiveTimingDock(self)
    self.addDockWidget(Qt.BottomDockWidgetArea, self.live_timing_dock)
    self.live_timing_dock.hide()  # 預設隱藏
    
    # 創建選單
    self._create_live_timing_menu()

def _create_live_timing_menu(self):
    """創建 Live Timing 選單"""
    from modules.gui.live_timing.live_timing_modules.track_map import TrackMapMDI
    from modules.gui.live_timing.live_timing_modules.circle_map import CircleMapMDI
    from modules.gui.live_timing.live_timing_modules.ranking_table import RankingMDI
    from modules.gui.live_timing.live_timing_modules.pit_window import PitWindowMDI
    from modules.gui.live_timing.live_timing_modules.tyre_strategy import TyreStrategyMDI
    # ... 其他模組
    
    live_menu = self.menuBar().addMenu(tr("Live Timing"))
    
    # 控制面板
    action_dock = live_menu.addAction(tr("顯示控制面板"))
    action_dock.setCheckable(True)
    action_dock.toggled.connect(self.live_timing_dock.setVisible)
    
    live_menu.addSeparator()
    
    # Widget 子視窗註冊表
    self._live_mdi_registry = {
        "track_map": TrackMapMDI,
        "circle_map": CircleMapMDI,
        "ranking": RankingMDI,
        "pit_window": PitWindowMDI,
        "tyre_strategy": TyreStrategyMDI,
        # ... 其他模組
    }
    
    for key, mdi_class in self._live_mdi_registry.items():
        action = live_menu.addAction(mdi_class.DISPLAY_NAME)
        action.triggered.connect(lambda _, k=key: self._open_live_mdi(k))

def _open_live_mdi(self, widget_key: str):
    """開啟 Live Timing MDI 子視窗"""
    mdi_class = self._live_mdi_registry.get(widget_key)
    if mdi_class:
        mdi_window = mdi_class(self)
        self.mdi_area.addSubWindow(mdi_window)
        mdi_window.show()
```

### 4.3 模組 Import 結構

```python
# modules/gui/live_timing/__init__.py

"""Live Timing 模組總入口"""

# 核心組件
from .core.data_manager import LiveTimingDataManager
from .core.base_live_mdi import BaseLiveTimingMDI

# 功能模組 - 按需 import
# from .live_timing_modules.track_map import TrackMapMDI
# from .live_timing_modules.ranking_table import RankingMDI
# ...

__all__ = [
    'LiveTimingDataManager',
    'BaseLiveTimingMDI',
]
```

```python
# modules/gui/live_timing/live_timing_modules/__init__.py

"""Live Timing 功能模組入口"""

# MDI 類別 - 用於主 GUI 選單註冊
from .track_map import TrackMapMDI
from .circle_map import CircleMapMDI
from .ranking_table import RankingMDI
from .pit_window import PitWindowMDI
from .tyre_strategy import TyreStrategyMDI
from .race_control import RaceControlMDI
from .race_insights import RaceInsightsMDI
from .race_info import RaceInfoMDI
from .shap_analysis import ShapMDI
from .lap_distribution import LapDistributionMDI
from .pit_stop_table import PitStopMDI

__all__ = [
    'TrackMapMDI',
    'CircleMapMDI',
    'RankingMDI',
    'PitWindowMDI',
    'TyreStrategyMDI',
    'RaceControlMDI',
    'RaceInsightsMDI',
    'RaceInfoMDI',
    'ShapMDI',
    'LapDistributionMDI',
    'PitStopMDI',
]
```

---

## 5. 執行計畫

### Phase 1: 核心架構 (Day 1-2) ✅ 完成

- [x] 創建 `modules/gui/live_timing/` 目錄結構
- [x] 創建 `core/__init__.py`
- [x] 實作 `core/data_manager.py` - `LiveTimingDataManager` 單例 (~400 行)
- [x] 拆分數據源類別到 `core/`
  - [ ] `signalr_client.py` - F1SignalRClient (待完成)
  - [ ] `realtime_source.py` - RealTimeLiveF1Worker + RealTimeLiveF1DataSource (待完成)
  - [x] `local_source.py` - LocalLiveF1DataSource + LiveF1DataSource (~400 行)
- [x] 拆分 `core/position_processor.py` - LivePositionDataProcessor (~700 行)
- [ ] 拆分 `core/pit_loss_config.py` - PitLossConfigLoader (待完成)
- [x] 實作 `core/base_live_mdi.py` - BaseLiveTimingMDI 基類 (~200 行)
- [ ] 撰寫 core 模組單元測試

### Phase 2: 控制面板 (已提前完成) ✅ 完成

- [x] 創建 `live_timing_modules/control_panel.py` (~350 行)
- [x] 實作賽事選擇器 (年份/賽事)
- [x] 實作播放控制 (播放/暫停/停止/速度)
- [x] 實作時間軸滑桿控制
- [x] 連接 LiveTimingDataManager 信號

### Phase 3: 賽道地圖 ✅ 完成

- [x] 創建 `live_timing_modules/track_map.py` (~400 行)
- [x] 實作 `TrackMapWidget` - 賽道視覺化組件
- [x] 實作 `LiveTimingTrackMap` - MDI 包裝類
- [x] 賽道輪廓繪製 (Position.json 數據)
- [x] 車手位置標記
- [x] 彎道/扇區標記
- [x] 整合到主 GUI 選單

### Phase 4: 功能模組拆分 (進行中)

**優先級 1 (核心功能)**
- [x] `track_map/` - 賽道地圖 ✅
- [ ] `ranking_table/` - 即時排名 (下一步)
  - [ ] `ranking_widget.py`
  - [ ] `ranking_mdi.py`
- [ ] `pit_window/` - Pit Window
  - [ ] `pit_window_widget.py`
  - [ ] `pit_window_mdi.py`

**優先級 2 (策略分析)**
- [ ] `tyre_strategy/` - 輪胎策略
- [ ] `race_control/` - 比賽控制訊息
- [ ] `race_insights/` - 賽況提示

**優先級 3 (輔助功能)**
- [ ] `circle_map/` - 圓形地圖
- [ ] `shap_analysis/` - SHAP 分析
- [ ] `lap_distribution/` - 圈速分佈
- [ ] `race_info/` - 賽事資訊
- [ ] `pit_stop_table/` - 進站統計

**優先級 4 (控制元件)**
- [ ] `timeline_control/` - 時間軸控制 (已整合到 control_panel)

### Phase 5: 主 GUI 整合 ✅ 基礎完成

- [x] 在 `f1t_gui_main.py` 添加 `_setup_live_timing_menu()` 方法
- [x] 添加 Live Timing 選單項目
- [x] 啟用 Control Panel 選單項目
- [x] 啟用 Track Map 選單項目
- [x] 實作 `_open_live_timing_control_panel()` 方法
- [x] 實作 `_open_live_timing_track_map()` 方法
- [ ] 添加 Dock Widget 到主視窗
- [ ] 實作預設佈局功能
- [ ] 添加鍵盤快捷鍵
- [ ] 更新 `__init__.py` 導出結構

### Phase 6: 測試與清理 (待完成)

### Phase 6: 測試與清理 (待完成)

- [ ] 完整測試歷史回放模式
- [ ] 完整測試即時模式 (如可用)
- [ ] 測試多視窗同步
- [ ] 測試播放控制
- [ ] 效能優化 (記憶體、更新頻率)
- [ ] 保留 `demo_live_position_tracking.py` 作為備份
- [ ] 更新文檔

---

## 6. 已完成的檔案清單

### 6.1 核心模組 (core/)

| 檔案 | 行數 | 狀態 | 說明 |
|------|------|------|------|
| `__init__.py` | ~20 | ✅ 完成 | 模組導出 |
| `data_manager.py` | ~400 | ✅ 完成 | 單例數據管理器 |
| `local_source.py` | ~400 | ✅ 完成 | 本地/遠端數據源 |
| `position_processor.py` | ~700 | ✅ 完成 | 位置數據處理器 |
| `base_live_mdi.py` | ~200 | ✅ 完成 | MDI 基類 |
| `signalr_client.py` | - | ⏳ 待完成 | F1 SignalR 客戶端 |
| `realtime_source.py` | - | ⏳ 待完成 | 即時數據源 |
| `pit_loss_config.py` | - | ⏳ 待完成 | Pit Loss 設定 |

### 6.2 功能模組 (live_timing_modules/)

| 檔案 | 行數 | 狀態 | 說明 |
|------|------|------|------|
| `__init__.py` | ~20 | ✅ 完成 | 模組導出 |
| `control_panel.py` | ~350 | ✅ 完成 | 播放控制面板 MDI |
| `track_map.py` | ~400 | ✅ 完成 | 賽道地圖 MDI |
| `ranking_tower.py` | - | ⏳ 待完成 | 即時排名塔 |
| `pit_window.py` | - | ⏳ 待完成 | Pit Window |
| `tyre_strategy.py` | - | ⏳ 待完成 | 輪胎策略 |
| `circle_map.py` | - | ⏳ 待完成 | 圓形地圖 |

### 6.3 主 GUI 整合

| 檔案 | 修改項目 | 狀態 |
|------|----------|------|
| `f1t_gui_main.py` | `_setup_live_timing_menu()` | ✅ 完成 |
| `f1t_gui_main.py` | `_open_live_timing_control_panel()` | ✅ 完成 |
| `f1t_gui_main.py` | `_open_live_timing_track_map()` | ✅ 完成 |
| `f1t_gui_main.py` | Live Timing 選單項目 | ✅ 部分完成 |

---

## 7. 核心類別設計

### 6.1 LiveTimingDataManager (單例)

```python
# modules/gui/live_timing/core/data_manager.py

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, Dict, Any

class LiveTimingDataManager(QObject):
    """Live Timing 數據管理器 (單例)
    
    職責:
    1. 管理數據源 (即時/歷史)
    2. 處理快照數據
    3. 廣播更新到所有訂閱的 Widget
    4. 維護當前賽事狀態
    """
    
    # === 信號定義 ===
    snapshot_updated = pyqtSignal(dict)           # 當前快照更新
    race_loaded = pyqtSignal(dict)                # 賽事載入完成 (race_info)
    race_unloaded = pyqtSignal()                  # 賽事卸載
    connection_status_changed = pyqtSignal(str)   # 連線狀態: connected/disconnected/error
    playback_state_changed = pyqtSignal(str)      # 播放狀態: playing/paused/stopped
    playback_speed_changed = pyqtSignal(float)    # 播放速度: 0.5x, 1x, 2x, ...
    time_changed = pyqtSignal(float)              # 當前時間 (秒)
    progress_changed = pyqtSignal(float)          # 進度 (0.0 ~ 1.0)
    
    _instance: Optional['LiveTimingDataManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'LiveTimingDataManager':
        """獲取單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        
        # 數據源
        self._data_source = None
        self._position_processor = None
        
        # 當前狀態
        self._current_snapshot: Dict[str, Any] = {}
        self._race_info: Dict[str, Any] = {}
        self._playback_state: str = "stopped"
        self._playback_speed: float = 1.0
        
    # === 公開 API ===
    
    def load_race(self, year: int, race: str, session: str = "R") -> bool:
        """載入賽事數據"""
        pass
    
    def unload_race(self) -> None:
        """卸載當前賽事"""
        pass
    
    def play(self) -> None:
        """開始播放"""
        pass
    
    def pause(self) -> None:
        """暫停播放"""
        pass
    
    def stop(self) -> None:
        """停止播放"""
        pass
    
    def set_speed(self, speed: float) -> None:
        """設定播放速度"""
        pass
    
    def seek(self, time_seconds: float) -> None:
        """跳轉到指定時間"""
        pass
    
    def get_current_snapshot(self) -> Dict[str, Any]:
        """獲取當前快照"""
        return self._current_snapshot.copy()
```

### 6.2 BaseLiveTimingMDI (MDI 基類)

```python
# modules/gui/live_timing/core/base_live_mdi.py

from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from typing import Optional
from core.gui_i18n import tr
from .data_manager import LiveTimingDataManager

class BaseLiveTimingMDI(QMdiSubWindow):
    """Live Timing MDI 子視窗基類
    
    提供:
    - 自動訂閱 LiveTimingDataManager
    - 統一的視窗樣式
    - 錯誤處理方法
    - 記憶體清理機制
    """
    
    # 子類必須覆寫
    DISPLAY_NAME: str = "Base Live MDI"
    DEFAULT_SIZE: tuple = (400, 300)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 獲取數據管理器
        self.data_manager = LiveTimingDataManager.get_instance()
        
        # 設置視窗屬性
        self.setWindowTitle(tr(self.DISPLAY_NAME))
        self.resize(*self.DEFAULT_SIZE)
        self.setWindowFlags(
            Qt.SubWindow | 
            Qt.WindowMinimizeButtonHint | 
            Qt.WindowMaximizeButtonHint
        )
        
        # 創建內部 Widget
        self._setup_widget()
        
        # 訂閱數據管理器信號
        self._subscribe_to_data_manager()
    
    def _setup_widget(self) -> None:
        """設置內部 Widget - 子類必須實現"""
        raise NotImplementedError
    
    def _subscribe_to_data_manager(self) -> None:
        """訂閱數據管理器信號"""
        self.data_manager.snapshot_updated.connect(self._on_snapshot_updated)
        self.data_manager.race_loaded.connect(self._on_race_loaded)
        self.data_manager.race_unloaded.connect(self._on_race_unloaded)
    
    def _on_snapshot_updated(self, snapshot: dict) -> None:
        """處理快照更新 - 子類應覆寫"""
        pass
    
    def _on_race_loaded(self, race_info: dict) -> None:
        """處理賽事載入 - 子類應覆寫"""
        pass
    
    def _on_race_unloaded(self) -> None:
        """處理賽事卸載 - 子類應覆寫"""
        pass
    
    def _show_error(self, title: str, message: str) -> None:
        """顯示錯誤對話框"""
        QMessageBox.critical(self, tr(title), tr(message))
    
    def _show_warning(self, title: str, message: str) -> None:
        """顯示警告對話框"""
        QMessageBox.warning(self, tr(title), tr(message))
    
    def closeEvent(self, event) -> None:
        """視窗關閉時清理資源"""
        # 斷開信號連接
        try:
            self.data_manager.snapshot_updated.disconnect(self._on_snapshot_updated)
            self.data_manager.race_loaded.disconnect(self._on_race_loaded)
            self.data_manager.race_unloaded.disconnect(self._on_race_unloaded)
        except (TypeError, RuntimeError):
            pass  # 信號可能已斷開
        
        # 調用子類清理方法
        self._cleanup()
        
        super().closeEvent(event)
    
    def _cleanup(self) -> None:
        """清理資源 - 子類可覆寫"""
        pass
```

### 6.3 模組 MDI 範例 (TrackMapMDI)

```python
# modules/gui/live_timing/live_timing_modules/track_map/track_map_mdi.py

from ...core.base_live_mdi import BaseLiveTimingMDI
from .track_map_widget import TrackMapWidget
from core.gui_i18n import tr

class TrackMapMDI(BaseLiveTimingMDI):
    """賽道地圖 MDI 子視窗"""
    
    DISPLAY_NAME = "track_map"  # 翻譯鍵
    DEFAULT_SIZE = (600, 500)
    
    def _setup_widget(self) -> None:
        """設置內部 Widget"""
        self.track_map = TrackMapWidget()
        self.setWidget(self.track_map)
    
    def _on_snapshot_updated(self, snapshot: dict) -> None:
        """更新車手位置"""
        if drivers := snapshot.get('drivers'):
            self.track_map.update_driver_positions(drivers)
    
    def _on_race_loaded(self, race_info: dict) -> None:
        """載入賽道數據"""
        if track_data := race_info.get('track_data'):
            self.track_map.load_track_outline(track_data)
    
    def _on_race_unloaded(self) -> None:
        """清除賽道地圖"""
        self.track_map.clear()
    
    def _cleanup(self) -> None:
        """清理資源"""
        self.track_map.cleanup()
```

---

## 7. 技術規範

### 7.1 國際化

所有用戶可見字串使用 `tr()` 函數：

```python
from core.gui_i18n import tr

class TrackMapWidget(QWidget):
    def __init__(self):
        self.setWindowTitle(tr("track_map"))
        self.btn_zoom_in = QPushButton(tr("zoom_in"))
```

### 7.2 主題支援

繼承主 GUI 的深色主題：

```python
# 使用 QSS 樣式表繼承
self.setStyleSheet("""
    QWidget {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
""")
```

### 7.3 命名規範

| 類型 | 命名規則 | 範例 |
|------|---------|------|
| 模組資料夾 | snake_case | `track_map/`, `pit_window/` |
| Widget 類別 | PascalCase + Widget | `TrackMapWidget`, `PitWindowWidget` |
| MDI 類別 | PascalCase + MDI | `TrackMapMDI`, `PitWindowMDI` |
| 檔案名 | snake_case | `track_map_widget.py`, `track_map_mdi.py` |

---

## 8. 問答記錄

### Q1: 控制面板位置?
**A**: Bottom Dock Widget，可拖曳到其他位置或浮動。

### Q2: 預設佈局?
**A**: 提供三種預設佈局：
- **完整佈局**：開啟所有視窗並平鋪
- **精簡佈局**：排名 + 地圖 + Pit Window
- **策略佈局**：Pit Window + 輪胎策略 + 賽況提示

### Q3: 即時模式優先級?
**A**: 先完成歷史回放模式，即時模式作為進階功能。

### Q4: 可以用 UniversalAnalysisMDI 嗎?
**A**: 不建議直接使用。`UniversalAnalysisMDI` 設計用於 FastF1 API 的單次請求/響應模式，而 Live Timing 需要持續的串流數據更新。建議創建專用的 `BaseLiveTimingMDI` 基類。

### Q5: 新架構與舊架構的差異?
**A**: 
- **舊架構**：`widgets/` + `mdi/` 分開
- **新架構**：`live_timing_modules/` 下每個功能有獨立資料夾，Widget 和 MDI 放在一起
- **優點**：高內聚、易維護、易擴展

---

## 9. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 拆分過程中破壞現有功能 | 高 | 保留原檔案直到完全測試通過 |
| 多視窗同步延遲 | 中 | 使用 Qt 信號機制確保同步 |
| 記憶體佔用增加 | 中 | 按需載入，關閉時釋放資源 |
| 即時模式不穩定 | 低 | 標記為實驗性功能 |
| 循環 import | 中 | 使用延遲 import 或 TYPE_CHECKING |

---

## 10. 成功指標

- [ ] 所有 Widget 可獨立開啟/關閉
- [ ] 多視窗數據同步正常 (延遲 < 50ms)
- [ ] 歷史回放播放流暢 (60 FPS)
- [ ] 記憶體使用合理 (< 500MB)
- [ ] 無崩潰或未處理異常
- [ ] 主 GUI 啟動時間無明顯增加 (< 1 秒)
- [ ] 所有模組可獨立 import 無錯誤
- [ ] 通過 mypy 類型檢查 (可選)

---

## 11. 版本歷史

| 日期 | 版本 | 變更說明 |
|------|------|----------|
| 2025-12-03 | 1.0 | 初始規劃 |
| 2025-12-03 | 1.1 | 調整架構：改用 `core/` + `live_timing_modules/` 結構 |
| 2025-12-03 | 1.2 | 主 GUI 新增 Live Timing 選單 (灰色不可選用)，已添加多國語言翻譯 |
| 2025-12-04 | 2.0 | **Phase 1-3 完成**：核心架構、控制面板、賽道地圖已整合到主 GUI |
